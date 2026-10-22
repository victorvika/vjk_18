#!/usr/bin/env python3
"""CapCut Desktop export planner.

Prints the canvas, resolution, frame rate, bitrate, codec and audio settings
to use in CapCut's Export dialog for a given delivery target.

Examples
--------
    python3 export_plan.py --list
    python3 export_plan.py reels
    python3 export_plan.py youtube-1080p --fps 60 --duration 12:30
    python3 export_plan.py instagram-feed --json

No third-party dependencies; Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
# bitrate_mbps is the *recommended* upload bitrate for H.264 SDR delivery.
# We keep an explicit table rather than a formula so the numbers stay honest
# to what each platform actually asks for.

PLATFORMS: Dict[str, dict] = {
    "youtube-1080p": {
        "label": "YouTube 1080p (SDR)",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "fps_options": [24, 25, 30, 60],
        "bitrate_mbps": 8,
        "bitrate_range": [8, 12],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "60 fps-ku 12 Mbps varaikkum podunga (action / gaming).",
            "Upload panna piragu YouTube re-encode pannum, so source-a crisp-a vaiththukonga.",
        ],
    },
    "youtube-4k": {
        "label": "YouTube 4K (SDR)",
        "aspect": "16:9",
        "width": 3840,
        "height": 2160,
        "fps": 30,
        "fps_options": [24, 25, 30, 60],
        "bitrate_mbps": 45,
        "bitrate_range": [45, 68],
        "codec": "H.264 (AVC) / HEVC",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "45-53 Mbps @ 30fps, 53-68 Mbps @ 60fps.",
            "4K timeline-la 1080p footage-a upscale pannaadheenga - quality-ku use illa.",
        ],
    },
    "shorts": {
        "label": "YouTube Shorts",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "fps_options": [30, 60],
        "bitrate_mbps": 12,
        "bitrate_range": [10, 16],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "Safe zone: bottom 25% + right 15% la text/UI vaikkadheenga.",
            "60 fps use pannaal motion smooth-a irukkum, aana file size perisu.",
        ],
    },
    "reels": {
        "label": "Instagram Reels",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "fps_options": [30, 60],
        "bitrate_mbps": 12,
        "bitrate_range": [10, 16],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "Instagram upload-la re-encode pannum - high bitrate source kuduththa sharpness retain aagum.",
            "Bottom 25% (caption/CTA) + right 15% (buttons) safe zone vituvidunga.",
        ],
    },
    "tiktok": {
        "label": "TikTok",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "fps_options": [30, 60],
        "bitrate_mbps": 10,
        "bitrate_range": [8, 12],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "Right side 15% + bottom 25% la UI overlay irukkum.",
            "TikTok 60 fps supported, aana 30 fps-ey ellaa device-lum smooth.",
        ],
    },
    "instagram-feed": {
        "label": "Instagram Feed (4:5)",
        "aspect": "4:5",
        "width": 1080,
        "height": 1350,
        "fps": 30,
        "fps_options": [30, 60],
        "bitrate_mbps": 10,
        "bitrate_range": [8, 12],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 192-320 kbps, 48 kHz",
        "notes": [
            "Feed-la 4:5 maximum screen space edukkum (1:1-a vida 25% height adhigam).",
        ],
    },
    "instagram-square": {
        "label": "Instagram Square (1:1)",
        "aspect": "1:1",
        "width": 1080,
        "height": 1080,
        "fps": 30,
        "fps_options": [30, 60],
        "bitrate_mbps": 8,
        "bitrate_range": [6, 10],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 192-320 kbps, 48 kHz",
        "notes": ["Grid layout-ku best, aana Reels/Stories-ku 9:16 use pannunga."],
    },
    "whatsapp": {
        "label": "WhatsApp Status / share",
        "aspect": "9:16",
        "width": 720,
        "height": 1280,
        "fps": 30,
        "fps_options": [30],
        "bitrate_mbps": 4,
        "bitrate_range": [3, 5],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 128 kbps, 44.1 kHz",
        "notes": [
            "WhatsApp heavy compression pannum - text periya size-la vaiththu compensate pannunga.",
            "30-60 second-ku mela irunthaal status-a pala clips-a pirikkalaam.",
        ],
    },
    "linkedin": {
        "label": "LinkedIn Feed",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "fps_options": [25, 30],
        "bitrate_mbps": 10,
        "bitrate_range": [8, 12],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 192 kbps, 48 kHz",
        "notes": ["Silent viewing common - captions bake pannidunga."],
    },
    "client-master": {
        "label": "Client master / archive",
        "aspect": "match source",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "fps_options": [24, 25, 30, 60],
        "bitrate_mbps": 20,
        "bitrate_range": [16, 40],
        "codec": "H.264 (AVC)",
        "format": "MP4",
        "audio": "AAC 320 kbps, 48 kHz",
        "notes": [
            "Archive-ku Higher bitrate + H.264 (compatibility) use pannunga, H.265 illa.",
            "Project file-a (.capcut draft) thani-ya backup pannunga.",
        ],
    },
}

PLATFORM_ALIASES = {
    "yt": "youtube-1080p",
    "youtube": "youtube-1080p",
    "youtube-4k": "youtube-4k",
    "4k": "youtube-4k",
    "short": "shorts",
    "shorts": "shorts",
    "yt-shorts": "shorts",
    "reel": "reels",
    "reels": "reels",
    "ig-reels": "reels",
    "tiktok": "tiktok",
    "tt": "tiktok",
    "ig": "instagram-feed",
    "feed": "instagram-feed",
    "instagram": "instagram-feed",
    "square": "instagram-square",
    "whatsapp": "whatsapp",
    "wa": "whatsapp",
    "status": "whatsapp",
    "linkedin": "linkedin",
    "li": "linkedin",
    "master": "client-master",
    "archive": "client-master",
}


@dataclass
class ExportPlan:
    platform: str
    label: str
    aspect: str
    width: int
    height: int
    fps: int
    bitrate_mbps: int
    bitrate_range: List[int]
    codec: str
    format: str
    audio: str
    estimated_size_mb: Optional[float] = None
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_duration(value: str) -> float:
    """Parse '90', '1:30' or '1:02:03' into seconds."""
    value = value.strip()
    if not value:
        raise ValueError("empty duration")
    parts = value.split(":")
    if len(parts) > 3:
        raise ValueError(f"invalid duration: {value}")
    total = 0.0
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"invalid duration: {value}")
        total = total * 60 + int(part)
    if total <= 0:
        raise ValueError("duration must be greater than zero")
    return float(total)


def resolve_platform(name: str) -> str:
    key = name.strip().lower()
    if key in PLATFORMS:
        return key
    if key in PLATFORM_ALIASES:
        return PLATFORM_ALIASES[key]
    raise KeyError(name)


def plan_for(
    platform: str,
    fps: Optional[int] = None,
    duration_seconds: Optional[float] = None,
    source_width: Optional[int] = None,
    source_height: Optional[int] = None,
    source_fps: Optional[float] = None,
) -> ExportPlan:
    key = resolve_platform(platform)
    preset = PLATFORMS[key]

    chosen_fps = preset["fps"]
    warnings: List[str] = []

    if fps is not None:
        if fps <= 0:
            raise ValueError("fps must be greater than zero")
        if fps not in preset["fps_options"]:
            allowed = ", ".join(str(f) for f in preset["fps_options"])
            warnings.append(
                f"{fps} fps is unusual for {preset['label']} (options: {allowed}). "
                f"Using {fps} anyway - verify the platform accepts it."
            )
        chosen_fps = fps

    if source_fps is not None and source_fps > 0:
        if source_fps > chosen_fps + 0.5:
            warnings.append(
                f"Source is {source_fps:g} fps but you are exporting at {chosen_fps} fps - "
                f"{source_fps - chosen_fps:g} frames per second will be dropped. "
                "Use 60 fps output for smooth slow motion."
            )
        if chosen_fps > source_fps + 0.5:
            warnings.append(
                f"Source is {source_fps:g} fps and output is {chosen_fps} fps - "
                "extra frames are duplicated, motion will not get smoother."
            )

    if fps is not None and fps > 60:
        warnings.append("Above 60 fps is not useful for social delivery; keep 24-60.")

    if source_width and source_height:
        if source_width < preset["width"] or source_height < preset["height"]:
            warnings.append(
                f"Source is {source_width}x{source_height} but the target canvas is "
                f"{preset['width']}x{preset['height']} - you are upscaling, which softens detail. "
                "Shoot/export at the target resolution when possible."
            )

    major_ratio = preset["width"] / preset["height"]
    if abs(major_ratio - 16 / 9) > 0.01 and key in {"youtube-1080p", "youtube-4k"}:
        warnings.append("Non-16:9 canvas for YouTube: expect pillarboxing/letterboxing.")

    estimated = None
    if duration_seconds:
        if duration_seconds <= 0:
            raise ValueError("duration must be greater than zero")
        estimated = round(preset["bitrate_mbps"] * duration_seconds / 8, 1)

    return ExportPlan(
        platform=key,
        label=preset["label"],
        aspect=preset["aspect"],
        width=preset["width"],
        height=preset["height"],
        fps=chosen_fps,
        bitrate_mbps=preset["bitrate_mbps"],
        bitrate_range=list(preset["bitrate_range"]),
        codec=preset["codec"],
        format=preset["format"],
        audio=preset["audio"],
        estimated_size_mb=estimated,
        notes=list(preset["notes"]),
        warnings=warnings,
    )


def render(plan: ExportPlan) -> str:
    lo, hi = plan.bitrate_range
    lines = [
        f"CapCut export plan - {plan.label}",
        "=" * 52,
        f"Canvas (aspect)   : {plan.aspect}  ->  {plan.width}x{plan.height}",
        f"Frame rate        : {plan.fps} fps",
        f"Bitrate           : {plan.bitrate_mbps} Mbps  (range {lo}-{hi} Mbps, H.264)",
        f"Codec / container : {plan.codec} / {plan.format}",
        f"Audio             : {plan.audio}",
    ]
    if plan.estimated_size_mb is not None:
        lines.append(f"Estimated size    : ~{plan.estimated_size_mb} MB")
    if plan.notes:
        lines.append("")
        lines.append("Notes")
        lines += [f"  - {n}" for n in plan.notes]
    if plan.warnings:
        lines.append("")
        lines.append("Warnings")
        lines += [f"  ! {w}" for w in plan.warnings]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="export_plan.py",
        description="Recommend CapCut Desktop export settings for a delivery target.",
    )
    p.add_argument("platform", nargs="?", help="delivery target, e.g. reels / youtube-1080p")
    p.add_argument("--list", action="store_true", help="list available presets")
    p.add_argument("--fps", type=int, default=None, help="override frame rate")
    p.add_argument("--duration", default=None, help="clip length, e.g. 90 or 1:30 or 1:02:03")
    p.add_argument("--source-width", type=int, default=None)
    p.add_argument("--source-height", type=int, default=None)
    p.add_argument("--source-fps", type=float, default=None)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        for key, preset in PLATFORMS.items():
            print(f"{key:<18} {preset['label']:<28} {preset['width']}x{preset['height']} @ {preset['fps']}fps")
        return 0

    if not args.platform:
        build_parser().print_help()
        return 2

    try:
        duration = parse_duration(args.duration) if args.duration else None
        plan = plan_for(
            args.platform,
            fps=args.fps,
            duration_seconds=duration,
            source_width=args.source_width,
            source_height=args.source_height,
            source_fps=args.source_fps,
        )
    except KeyError:
        print(f"Unknown platform: {args.platform}", file=sys.stderr)
        print("Run with --list to see options.", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(plan), indent=2))
    else:
        print(render(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
