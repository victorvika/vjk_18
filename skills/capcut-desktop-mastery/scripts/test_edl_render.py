#!/usr/bin/env python3
"""Tests for edl_render.py.

    python3 -m unittest test_edl_render -v

Unit tests always run. Integration tests (real ffmpeg renders) are skipped when
ffmpeg is not available - set FFMPEG_BIN or install it on PATH.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import edl_render as er  # noqa: E402

FFMPEG = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")


def probe(path: str):
    """Return dict with duration, width, height, has_audio parsed from ffmpeg -i."""
    proc = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True)
    text = proc.stderr
    out = {"duration": None, "width": None, "height": None, "has_audio": "Audio:" in text}
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if m:
        out["duration"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", text)
    if m:
        out["width"], out["height"] = int(m.group(1)), int(m.group(2))
    return out


class TestParseTime(unittest.TestCase):
    def test_number(self):
        self.assertEqual(er.parse_time(3.5), 3.5)
        self.assertEqual(er.parse_time("12.25"), 12.25)

    def test_clock_formats(self):
        self.assertEqual(er.parse_time("1:30"), 90.0)
        self.assertEqual(er.parse_time("1:02:03.5"), 3723.5)
        self.assertEqual(er.parse_time("00:00:05"), 5.0)

    def test_invalid(self):
        for bad in ["", "abc", "1:99", "-3", None]:
            with self.assertRaises(er.EDLError):
                er.parse_time(bad)


class TestParseEdl(unittest.TestCase):
    def base(self, **over):
        data = {
            "output": "out.mp4",
            "canvas": {"width": 1080, "height": 1920},
            "fps": 30,
            "clips": [{"source": "a.mp4", "in": 0, "out": 2}],
        }
        data.update(over)
        return data

    def test_minimal(self):
        edl = er.parse_edl(self.base())
        self.assertEqual(edl.width, 1080)
        self.assertEqual(edl.height, 1920)
        self.assertEqual(edl.duration, 2.0)
        self.assertEqual(edl.clips[0].start, 0.0)

    def test_speed_affects_duration(self):
        edl = er.parse_edl(self.base(clips=[{"source": "a.mp4", "in": 0, "out": 4, "speed": 2}]))
        self.assertEqual(edl.duration, 2.0)

    def test_relative_source_is_resolved(self):
        edl = er.parse_edl(self.base(), base_dir="/tmp/proj")
        self.assertEqual(edl.clips[0].source, "/tmp/proj/a.mp4")

    def test_missing_clips(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(clips=[]))

    def test_out_before_in(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(clips=[{"source": "a.mp4", "in": 5, "out": 2}]))

    def test_odd_canvas_rejected(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(canvas={"width": 1081, "height": 1920}))

    def test_bad_fps(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(fps=0))

    def test_bad_speed(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(clips=[{"source": "a.mp4", "in": 0, "out": 2, "speed": 50}]))

    def test_bad_crf(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(export={"crf": 99}))

    def test_music_needs_source(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(music={"volume": 0.2}))

    def test_captions_needs_srt(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl(self.base(captions={"font_size": 40}))

    def test_duration_instead_of_out(self):
        edl = er.parse_edl(self.base(clips=[{"source": "a.mp4", "duration": 3}]))
        self.assertEqual(edl.duration, 3.0)

    def test_not_a_dict(self):
        with self.assertRaises(er.EDLError):
            er.parse_edl([])


class TestAtempo(unittest.TestCase):
    def test_normal_speed_is_noop(self):
        self.assertEqual(er.atempo_chain(1.0), [])

    def test_plain_speed(self):
        self.assertEqual(er.atempo_chain(1.5), ["atempo=1.500000"])

    def test_fast_is_chained(self):
        chain = er.atempo_chain(5.0)
        self.assertGreater(len(chain), 1)
        product = 1.0
        for step in chain:
            product *= float(step.split("=")[1])
        self.assertAlmostEqual(product, 5.0, places=4)

    def test_slow_is_chained(self):
        chain = er.atempo_chain(0.25)
        product = 1.0
        for step in chain:
            product *= float(step.split("=")[1])
        self.assertAlmostEqual(product, 0.25, places=4)


class TestFilters(unittest.TestCase):
    def setUp(self):
        self.edl = er.parse_edl({
            "output": "out.mp4",
            "canvas": {"width": 1080, "height": 1920},
            "fps": 30,
            "clips": [{"source": "a.mp4", "in": "1:00", "out": "1:05"}],
        })
        self.clip = self.edl.clips[0]

    def test_video_filter_scales_and_pads(self):
        f = er.video_filter(self.edl, self.clip)
        self.assertIn("trim=start=60.000:end=65.000", f)
        self.assertIn("scale=1080:1920", f)
        self.assertIn("pad=1080:1920", f)
        self.assertIn("fps=30", f)

    def test_audio_filter_trims(self):
        f = er.audio_filter(self.clip)
        self.assertIn("atrim=start=60.000:end=65.000", f)
        self.assertIn("aresample=48000", f)

    def test_normalize_cmd_without_audio_uses_anullsrc(self):
        cmd = er.normalize_cmd("ffmpeg", self.edl, self.clip, "out.mp4", with_audio=False)
        self.assertTrue(any("anullsrc" in part for part in cmd))
        self.assertIn("-shortest", cmd)

    def test_final_cmd_sets_export_settings(self):
        cmd = er.final_cmd("ffmpeg", self.edl, "base.mp4", "out.mp4", None, ".")
        self.assertIn("libx264", cmd)
        self.assertIn("-crf", cmd)
        self.assertIn("-movflags", cmd)

    def test_final_cmd_h265_when_requested(self):
        edl = er.parse_edl({
            "output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 1}],
            "export": {"codec": "h265"},
        })
        cmd = er.final_cmd("ffmpeg", edl, "base.mp4", "out.mp4", None, ".")
        self.assertIn("libx265", cmd)


class TestAudioGraph(unittest.TestCase):
    def test_no_music_without_track(self):
        edl = er.parse_edl({"output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 2}]})
        self.assertIsNone(er.build_audio_graph(edl))

    def test_ducking_uses_sidechain(self):
        edl = er.parse_edl({
            "output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 10}],
            "music": {"source": "m.mp3", "volume": 0.25},
        })
        graph = er.build_audio_graph(edl)
        self.assertIn("sidechaincompress", graph)
        self.assertIn("volume=0.250", graph)

    def test_no_ducking_plain_mix(self):
        edl = er.parse_edl({
            "output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 10}],
            "music": {"source": "m.mp3", "duck": False},
        })
        graph = er.build_audio_graph(edl)
        self.assertNotIn("sidechaincompress", graph)
        self.assertIn("amix", graph)


class TestSrtToAss(unittest.TestCase):
    SRT = "1\n00:00:01,000 --> 00:00:03,500\nHello there\nsecond line\n\n2\n00:00:04,000 --> 00:00:06,000\nVanakkam\n"

    def edl(self, h=1920, w=1080):
        return er.parse_edl({"output": "o.mp4", "canvas": {"width": w, "height": h},
                             "clips": [{"source": "a.mp4", "in": 0, "out": 10}]})

    def test_header_uses_canvas_resolution(self):
        ass = er.srt_to_ass(self.SRT, self.edl(), {})
        self.assertIn("PlayResX: 1080", ass)
        self.assertIn("PlayResY: 1920", ass)

    def test_events_converted_with_line_breaks(self):
        ass = er.srt_to_ass(self.SRT, self.edl(), {})
        self.assertIn("Dialogue: 0,0:00:01.00,0:00:03.50,Default,,0,0,0,,Hello there\\Nsecond line", ass)
        self.assertIn("Dialogue: 0,0:00:04.00,0:00:06.00", ass)

    def test_bottom_margin_respects_safe_zone(self):
        ass = er.srt_to_ass(self.SRT, self.edl(), {"safe_bottom_pct": 25})
        style = next(ln for ln in ass.splitlines() if ln.startswith("Style: Default"))
        margin_v = int(style.split(",")[21])
        self.assertEqual(margin_v, 480)

    def test_custom_font_and_size(self):
        ass = er.srt_to_ass(self.SRT, self.edl(), {"font": "Noto Sans Tamil", "font_size": 64})
        self.assertIn("Noto Sans Tamil,64", ass)


class TestCli(unittest.TestCase):
    def test_bad_json_returns_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{not json")
            path = fh.name
        try:
            self.assertEqual(er.main([path]), 2)
        finally:
            os.unlink(path)

    def test_missing_file_returns_2(self):
        self.assertEqual(er.main(["/tmp/definitely-not-here-1234.json"]), 2)

    def test_validate_only_ok(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 1}]}, fh)
            path = fh.name
        try:
            self.assertEqual(er.main([path, "--validate-only"]), 0)
        finally:
            os.unlink(path)


@unittest.skipUnless(FFMPEG, "ffmpeg not available")
class TestRenderIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="edl_test_")
        cls.a = os.path.join(cls.tmp, "a.mp4")
        cls.b = os.path.join(cls.tmp, "b.mp4")
        cls.music = os.path.join(cls.tmp, "music.m4a")
        for out, src, freq, dur in [
            (cls.a, "testsrc=size=640x360:rate=30", 440, 4),
            (cls.b, "testsrc2=size=320x240:rate=25", 660, 4),
        ]:
            subprocess.run([
                FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", f"{src}:duration={dur}",
                "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={dur}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out,
            ], check=True)
        subprocess.run([
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=2",
            "-c:a", "aac", cls.music,
        ], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_full_render_with_speed_and_music(self):
        edl_path = os.path.join(self.tmp, "plan.json")
        out = os.path.join(self.tmp, "out", "final.mp4")
        with open(edl_path, "w") as fh:
            json.dump({
                "output": out,
                "canvas": {"width": 1080, "height": 1920},
                "fps": 30,
                "clips": [
                    {"source": "a.mp4", "in": 0, "out": 2},
                    {"source": "b.mp4", "in": 0.5, "out": 2.5, "speed": 2},
                ],
                "music": {"source": "music.m4a", "volume": 0.2, "duck": True},
                "export": {"crf": 28, "preset": "ultrafast"},
            }, fh)

        work = os.path.join(self.tmp, "work")
        code = er.main([edl_path, "--workdir", work, "--ffmpeg", FFMPEG])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(out))

        info = probe(out)
        self.assertEqual((info["width"], info["height"]), (1080, 1920))
        self.assertTrue(info["has_audio"])
        # 2s + (2.0/2) = 3s
        self.assertAlmostEqual(info["duration"], 3.0, delta=0.4)

    def test_vertical_canvas_and_silent_clip(self):
        silent = os.path.join(self.tmp, "silent.mp4")
        subprocess.run([
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=size=720x1280:rate=30:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", silent,
        ], check=True)
        edl_path = os.path.join(self.tmp, "silent_plan.json")
        out = os.path.join(self.tmp, "out_silent.mp4")
        with open(edl_path, "w") as fh:
            json.dump({
                "output": out,
                "canvas": {"width": 1080, "height": 1920},
                "fps": 30,
                "clips": [{"source": "silent.mp4", "in": 0, "out": 1.5}],
                "export": {"crf": 30, "preset": "ultrafast"},
            }, fh)
        self.assertEqual(er.main([edl_path, "--ffmpeg", FFMPEG]), 0)
        info = probe(out)
        self.assertEqual((info["width"], info["height"]), (1080, 1920))
        self.assertAlmostEqual(info["duration"], 1.5, delta=0.3)


if __name__ == "__main__":
    unittest.main()
