#!/usr/bin/env python3
"""Tests for export_plan.py - run with: python3 -m unittest discover -s scripts"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_plan as ep  # noqa: E402


class TestParseDuration(unittest.TestCase):
    def test_plain_seconds(self):
        self.assertEqual(ep.parse_duration("90"), 90.0)

    def test_minutes_seconds(self):
        self.assertEqual(ep.parse_duration("1:30"), 90.0)

    def test_hours(self):
        self.assertEqual(ep.parse_duration("1:02:03"), 3723.0)

    def test_rejects_bad_values(self):
        for bad in ["", "abc", "1:aa", "0", "1:2:3:4"]:
            with self.assertRaises(ValueError):
                ep.parse_duration(bad)


class TestResolvePlatform(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(ep.resolve_platform("reels"), "reels")

    def test_alias(self):
        self.assertEqual(ep.resolve_platform("YT"), "youtube-1080p")
        self.assertEqual(ep.resolve_platform(" ig-reels "), "reels")

    def test_unknown(self):
        with self.assertRaises(KeyError):
            ep.resolve_platform("myspace")


class TestPlanFor(unittest.TestCase):
    def test_reels_defaults(self):
        plan = ep.plan_for("reels")
        self.assertEqual(plan.width, 1080)
        self.assertEqual(plan.height, 1920)
        self.assertEqual(plan.aspect, "9:16")
        self.assertEqual(plan.fps, 30)
        self.assertEqual(plan.format, "MP4")
        self.assertFalse(plan.warnings)

    def test_youtube_4k(self):
        plan = ep.plan_for("4k")
        self.assertEqual((plan.width, plan.height), (3840, 2160))
        self.assertGreaterEqual(plan.bitrate_mbps, 45)

    def test_fps_override(self):
        plan = ep.plan_for("youtube-1080p", fps=60)
        self.assertEqual(plan.fps, 60)

    def test_unusual_fps_warns_but_applies(self):
        plan = ep.plan_for("reels", fps=25)
        self.assertEqual(plan.fps, 25)
        self.assertTrue(any("unusual" in w for w in plan.warnings))

    def test_invalid_fps(self):
        with self.assertRaises(ValueError):
            ep.plan_for("reels", fps=0)

    def test_size_estimate(self):
        plan = ep.plan_for("reels", duration_seconds=60)
        self.assertAlmostEqual(plan.estimated_size_mb, 12 * 60 / 8, places=1)

    def test_upscale_warning(self):
        plan = ep.plan_for("youtube-1080p", source_width=1280, source_height=720)
        self.assertTrue(any("upscaling" in w for w in plan.warnings))

    def test_no_upscale_warning_when_source_is_large(self):
        plan = ep.plan_for("youtube-1080p", source_width=3840, source_height=2160)
        self.assertFalse(any("upscaling" in w for w in plan.warnings))

    def test_source_fps_slowmo_warning(self):
        plan = ep.plan_for("youtube-1080p", fps=30, source_fps=60)
        self.assertTrue(any("dropped" in w for w in plan.warnings))

    def test_duplicate_frames_warning(self):
        plan = ep.plan_for("reels", fps=60, source_fps=30)
        self.assertTrue(any("duplicated" in w for w in plan.warnings))

    def test_plan_is_json_serialisable(self):
        import json
        from dataclasses import asdict

        plan = ep.plan_for("whatsapp", duration_seconds=30)
        json.dumps(asdict(plan))


class TestCli(unittest.TestCase):
    def test_list_runs(self):
        self.assertEqual(ep.main(["--list"]), 0)

    def test_missing_platform_returns_2(self):
        self.assertEqual(ep.main([]), 2)

    def test_unknown_platform_returns_2(self):
        self.assertEqual(ep.main(["nope"]), 2)

    def test_bad_duration_returns_2(self):
        self.assertEqual(ep.main(["reels", "--duration", "abc"]), 2)

    def test_render_contains_key_lines(self):
        text = ep.render(ep.plan_for("reels", duration_seconds=45))
        self.assertIn("1080x1920", text)
        self.assertIn("Frame rate", text)
        self.assertIn("Estimated size", text)


if __name__ == "__main__":
    unittest.main()
