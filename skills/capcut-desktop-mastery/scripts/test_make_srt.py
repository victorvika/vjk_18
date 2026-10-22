#!/usr/bin/env python3
"""Tests for make_srt.py - python3 -m unittest test_make_srt -v"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_srt as ms  # noqa: E402


class TestTimeParsing(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(ms.parse_time("45"), 45.0)

    def test_clock(self):
        self.assertEqual(ms.parse_time("1:30"), 90.0)
        self.assertEqual(ms.parse_time("1:02:03.5"), 3723.5)

    def test_invalid(self):
        for bad in ["", "abc", "1:xx"]:
            with self.assertRaises(ValueError):
                ms.parse_time(bad)

    def test_fmt(self):
        self.assertEqual(ms.fmt(0), "00:00:00,000")
        self.assertEqual(ms.fmt(61.5), "00:01:01,500")
        self.assertEqual(ms.fmt(3661.25), "01:01:01,250")


class TestChunking(unittest.TestCase):
    def test_short_sentence_kept_whole(self):
        self.assertEqual(ms.chunk_text("Vanakkam da.", 40), ["Vanakkam da."])

    def test_long_sentence_wrapped(self):
        text = "This is a fairly long sentence that must be broken into several caption lines."
        chunks = ms.chunk_text(text, 30)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 30 for c in chunks), chunks)

    def test_clause_boundaries_preferred(self):
        text = "First part is here, second part follows, third part ends it."
        chunks = ms.chunk_text(text, 24)
        self.assertTrue(any(c.endswith(",") for c in chunks) or len(chunks) >= 2)

    def test_multiline_input(self):
        chunks = ms.chunk_text("Line one\nLine two\n\nLine three", 40)
        self.assertEqual(len(chunks), 3)

    def test_tamil_chunking(self):
        text = "இந்த வீடியோவை CapCut-ல எடிட் பண்ணி முடிக்கலாம்."
        chunks = ms.chunk_text(text, 20)
        self.assertTrue(all(len(c) <= 20 for c in chunks))

    def test_empty(self):
        self.assertEqual(ms.chunk_text("   \n\n ", 40), [])


class TestTiming(unittest.TestCase):
    def test_total_duration_respected(self):
        rows = ms.time_chunks(["one", "two", "three"], 10.0)
        self.assertAlmostEqual(rows[-1][1], 10.0, places=2)
        self.assertEqual(rows[0][0], 0.0)

    def test_no_overlap(self):
        rows = ms.time_chunks(["alpha beta", "gamma delta", "epsilon"], 12.0)
        for (s1, e1, _), (s2, _, _) in zip(rows, rows[1:]):
            self.assertLessEqual(e1, s2)

    def test_single_chunk(self):
        rows = ms.time_chunks(["hello"], 5.0)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0][1], 5.0, places=2)

    def test_empty(self):
        self.assertEqual(ms.time_chunks([], 5.0), [])


class TestWhisperInput(unittest.TestCase):
    def test_segments_are_rewrapped(self):
        data = {"segments": [
            {"start": 0.0, "end": 3.0, "text": " first caption here "},
            {"start": 3.5, "end": 6.0, "text": "second caption"},
        ]}
        rows = ms.from_whisper(data, 40)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][2], "first caption here")
        self.assertAlmostEqual(rows[0][0], 0.0, places=2)
        self.assertAlmostEqual(rows[1][0], 3.5, places=2)

    def test_long_segment_split(self):
        data = {"segments": [{"start": 0, "end": 10, "text": "a " * 40}]}
        rows = ms.from_whisper(data, 30)
        self.assertGreater(len(rows), 1)


class TestSrtOutput(unittest.TestCase):
    def test_format(self):
        srt = ms.write_srt([(0.5, 2.25, "hello"), (2.5, 4.0, "world")])
        self.assertIn("1\n00:00:00,500 --> 00:00:02,250\nhello", srt)
        self.assertIn("2\n00:00:02,500 --> 00:00:04,000\nworld", srt)

    def test_roundtrip_through_edl_converter(self):
        srt = ms.write_srt([(1.0, 3.0, "Vanakkam")])
        # the ASS converter in edl_render must accept our own SRT
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import edl_render as er
        edl = er.parse_edl({"output": "o.mp4", "clips": [{"source": "a.mp4", "in": 0, "out": 5}]})
        ass = er.srt_to_ass(srt, edl, {})
        self.assertIn("Dialogue: 0,0:00:01.00,0:00:03.00", ass)
        self.assertIn("Vanakkam", ass)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmp):
            os.unlink(os.path.join(self.tmp, f))
        os.rmdir(self.tmp)

    def _write(self, name, content):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_plain_text(self):
        src = self._write("t.txt", "First line here. Second line here.")
        out = os.path.join(self.tmp, "c.srt")
        self.assertEqual(ms.main([src, "--duration", "6", "--out", out]), 0)
        with open(out, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("-->", content)
        self.assertIn("First line here.", content)

    def test_missing_duration(self):
        src = self._write("t.txt", "hello")
        self.assertEqual(ms.main([src, "--out", os.path.join(self.tmp, "c.srt")]), 2)

    def test_json_input(self):
        src = self._write("w.json", json.dumps({"segments": [{"start": 0, "end": 2, "text": "hi"}]}))
        out = os.path.join(self.tmp, "c.srt")
        self.assertEqual(ms.main([src, "--json-input", "--out", out]), 0)

    def test_missing_file(self):
        self.assertEqual(ms.main(["/nope/none.txt", "--duration", "5"]), 2)


if __name__ == "__main__":
    unittest.main()
