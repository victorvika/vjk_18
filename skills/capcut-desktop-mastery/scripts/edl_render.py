#!/usr/bin/env python3
"""Render an EDL (edit decision list) into a finished video with ffmpeg.

This is the portable backend of the capcut-desktop-mastery skill: any agent that
can run bash + ffmpeg can now actually cut a video, not just describe how to.

    python3 edl_render.py plan.json --workdir work
    python3 edl_render.py plan.json --dry-run          # print the commands only
    python3 edl_render.py plan.json --validate-only    # check the EDL

EDL schema: see ../references/edl-format.md or ../assets/edl.example.json
Requires: python 3.8+, ffmpeg with libx264 + libass.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_FONT = "DejaVu Sans"
MIN_SPEED, MAX_SPEED = 0.1, 10.0

FONT_DIRS = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
    "/System/Library/Fonts",
    "C:/Windows/Fonts",
]


def find_fonts_dir(explicit: Optional[str] = None) -> Optional[str]:
    """libass needs a usable font directory; without one it silently fails."""
    if explicit:
        return explicit if os.path.isdir(explicit) else None
    for candidate in FONT_DIRS:
        if os.path.isdir(candidate):
            return candidate
    return None


def escape_filter_path(path: str) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


# ---------------------------------------------------------------------------
# EDL parsing and validation
# ---------------------------------------------------------------------------

class EDLError(ValueError):
    """Raised when the edit decision list is malformed."""


@dataclass
class Clip:
    source: str
    start: float
    end: float
    speed: float = 1.0
    volume: float = 1.0
    label: str = ""

    @property
    def duration(self) -> float:
        return (self.end - self.start) / self.speed


@dataclass
class EDL:
    output: str
    width: int
    height: int
    fps: int
    clips: List[Clip]
    background: str = "black"
    music: Optional[Dict[str, Any]] = None
    captions: Optional[Dict[str, Any]] = None
    export: Dict[str, Any] = field(default_factory=dict)
    loudness: Optional[float] = None

    @property
    def duration(self) -> float:
        return sum(c.duration for c in self.clips)


TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)$")


def parse_time(value: Any) -> float:
    """Accept 12.5, "12.5", "1:30", "1:02:03.25", "00:00:05"."""
    if isinstance(value, (int, float)):
        if value < 0:
            raise EDLError(f"negative time: {value}")
        return float(value)
    if not isinstance(value, str):
        raise EDLError(f"invalid time type: {type(value).__name__}")
    text = value.strip()
    if not text:
        raise EDLError("empty time value")
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return float(text)
    m = TIME_RE.match(text)
    if not m:
        raise EDLError(f"invalid time: {value!r} (use 12.5, 1:30 or 1:02:03.5)")
    hours, minutes, seconds = m.groups()
    total = int(hours or 0) * 3600 + int(minutes) * 60 + float(seconds)
    if float(seconds) >= 60:
        raise EDLError(f"seconds out of range in {value!r}")
    return total


def fmt_time(seconds: float) -> str:
    """Seconds -> 'H:MM:SS.mmm' for SRT/ASS output."""
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def load_edl(path: str) -> EDL:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        raise EDLError(f"EDL not found: {path}")
    except json.JSONDecodeError as exc:
        raise EDLError(f"EDL is not valid JSON: {exc}")
    return parse_edl(raw, base_dir=os.path.dirname(os.path.abspath(path)))


def parse_edl(raw: Dict[str, Any], base_dir: str = ".") -> EDL:
    if not isinstance(raw, dict):
        raise EDLError("EDL root must be a JSON object")

    clips_raw = raw.get("clips")
    if not isinstance(clips_raw, list) or not clips_raw:
        raise EDLError("EDL needs a non-empty 'clips' array")

    canvas = raw.get("canvas") or {}
    width = int(canvas.get("width", 1080))
    height = int(canvas.get("height", 1920))
    if width <= 0 or height <= 0:
        raise EDLError("canvas width/height must be positive")
    if width % 2 or height % 2:
        raise EDLError("canvas width/height must be even numbers (H.264 yuv420p)")

    fps = int(raw.get("fps", 30))
    if not 1 <= fps <= 120:
        raise EDLError("fps must be between 1 and 120")

    clips: List[Clip] = []
    for i, c in enumerate(clips_raw):
        if not isinstance(c, dict):
            raise EDLError(f"clip {i} must be an object")
        src = c.get("source")
        if not src:
            raise EDLError(f"clip {i} is missing 'source'")
        resolved = src if os.path.isabs(src) else os.path.normpath(os.path.join(base_dir, src))
        if "in" not in c and "out" not in c:
            # whole file: mark as 0..inf, resolved lazily at render time
            start, end = 0.0, c.get("duration")
            if end is None:
                raise EDLError(f"clip {i} needs 'in'/'out' or 'duration'")
            end = parse_time(end)
        else:
            start = parse_time(c.get("in", 0))
            if "out" not in c:
                raise EDLError(f"clip {i} needs 'out' (or use 'duration')")
            end = parse_time(c["out"])
            if end <= start:
                raise EDLError(f"clip {i}: 'out' must be greater than 'in'")

        speed = float(c.get("speed", 1.0))
        if not MIN_SPEED <= speed <= MAX_SPEED:
            raise EDLError(f"clip {i}: speed must be between {MIN_SPEED} and {MAX_SPEED}")

        volume = float(c.get("volume", 1.0))
        if not 0 <= volume <= 2:
            raise EDLError(f"clip {i}: volume must be between 0 and 2")

        clips.append(Clip(resolved, start, end, speed, volume, c.get("label", "")))

    export = raw.get("export") or {}
    if export.get("crf") is not None and not 0 <= int(export["crf"]) <= 51:
        raise EDLError("export.crf must be between 0 and 51")

    music = raw.get("music")
    if music is not None:
        if not isinstance(music, dict) or not music.get("source"):
            raise EDLError("music must be an object with a 'source'")
        m_src = music["source"]
        music = dict(music)
        music["source"] = m_src if os.path.isabs(m_src) else os.path.normpath(os.path.join(base_dir, m_src))

    captions = raw.get("captions")
    if captions is not None:
        if not isinstance(captions, dict):
            raise EDLError("captions must be an object")
        srt = captions.get("srt") or captions.get("file")
        if not srt:
            raise EDLError("captions needs an 'srt' path")
        captions = dict(captions)
        captions["srt"] = srt if os.path.isabs(srt) else os.path.normpath(os.path.join(base_dir, srt))

    out = raw.get("output") or "out.mp4"

    return EDL(
        output=out,
        width=width,
        height=height,
        fps=fps,
        clips=clips,
        background=str(raw.get("background", "black")),
        music=music,
        captions=captions,
        export=export,
        loudness=raw.get("loudness"),
    )


# ---------------------------------------------------------------------------
# ffmpeg command building
# ---------------------------------------------------------------------------

def run(cmd: List[str], dry_run: bool, label: str) -> None:
    printable = " ".join(_quote(a) for a in cmd)
    print(f"[{label}] {printable}" if dry_run else f"[{label}] running...", flush=True)
    if dry_run:
        return
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or "").strip().splitlines()[-12:])
        raise RuntimeError(f"ffmpeg failed during {label} (exit {proc.returncode}):\n{tail}")


def _quote(arg: str) -> str:
    return f'"{arg}"' if " " in arg else arg


def has_audio(ffmpeg: str, path: str) -> bool:
    proc = subprocess.run([ffmpeg, "-hide_banner", "-i", path], capture_output=True, text=True)
    return "Audio:" in (proc.stderr or "")


def atempo_chain(speed: float) -> List[str]:
    """atempo only accepts 0.5-2.0 per instance; chain for extreme speeds."""
    if abs(speed - 1.0) < 1e-6:
        return []
    parts: List[str] = []
    remaining = speed
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        parts.append("atempo=0.5")
        remaining /= 0.5
    parts.append(f"atempo={remaining:.6f}")
    return parts


def audio_filter(clip: Clip) -> str:
    chain = [f"atrim=start={clip.start:.3f}:end={clip.end:.3f}", "asetpts=PTS-STARTPTS"]
    chain += atempo_chain(clip.speed)
    if abs(clip.volume - 1.0) > 1e-6:
        chain.append(f"volume={clip.volume:.3f}")
    chain += ["aresample=48000", "aformat=channel_layouts=stereo"]
    return ",".join(chain)


def video_filter(edl: EDL, clip: Clip) -> str:
    speed_part = "" if abs(clip.speed - 1.0) < 1e-6 else f"setpts=PTS/{clip.speed:.6f},"
    return (
        f"trim=start={clip.start:.3f}:end={clip.end:.3f},{speed_part}setpts=PTS-STARTPTS,"
        f"scale={edl.width}:{edl.height}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={edl.width}:{edl.height}:(ow-iw)/2:(oh-ih)/2:color={edl.background},"
        f"setsar=1,fps={edl.fps},format=yuv420p"
    )


def normalize_cmd(ffmpeg: str, edl: EDL, clip: Clip, out_path: str, with_audio: bool) -> List[str]:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", clip.source]
    if with_audio:
        cmd += ["-vf", video_filter(edl, clip), "-af", audio_filter(clip)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-vf", video_filter(edl, clip), "-shortest"]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(edl.fps),
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart", out_path,
    ]
    return cmd


def concat_cmd(ffmpeg: str, list_path: str, out_path: str) -> List[str]:
    return [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", list_path,
            "-c", "copy", out_path]


def build_audio_graph(edl: EDL) -> Optional[str]:
    """Return a filter_complex string for [0:a] + music -> [aout], or None."""
    if not edl.music:
        return None
    vol = float(edl.music.get("volume", 0.2))
    fade_in = float(edl.music.get("fade_in", 0.5))
    fade_out = float(edl.music.get("fade_out", 1.0))
    total = edl.duration
    duck = bool(edl.music.get("duck", True))
    music_chain = [f"volume={vol:.3f}"]
    if fade_in > 0:
        music_chain.append(f"afade=t=in:st=0:d={fade_in:.2f}")
    if fade_out > 0 and total > fade_out:
        music_chain.append(f"afade=t=out:st={total - fade_out:.2f}:d={fade_out:.2f}")
    music_chain.append("aresample=48000")
    m = ",".join(music_chain)
    if duck:
        return (
            f"[0:a]asplit=2[voice][sc];"
            f"[1:a]{m}[bed];"
            f"[bed][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[ducked];"
            f"[voice][ducked]amix=inputs=2:duration=first:normalize=0[aout]"
        )
    return f"[1:a]{m}[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0[aout]"


def final_cmd(ffmpeg: str, edl: EDL, base_path: str, out_path: str,
              ass_path: Optional[str], workdir: str,
              fonts_dir: Optional[str] = None) -> List[str]:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", base_path]
    audio_graph = build_audio_graph(edl)
    if edl.music:
        cmd += ["-stream_loop", "-1", "-i", edl.music["source"]]

    filters: List[str] = []
    if ass_path:
        sub = f"ass={escape_filter_path(os.path.abspath(ass_path))}"
        resolved_fonts = find_fonts_dir(fonts_dir)
        if resolved_fonts:
            sub += f":fontsdir={escape_filter_path(resolved_fonts)}"
        filters.append(sub)
    if filters:
        cmd += ["-vf", ",".join(filters)]

    if audio_graph:
        graph = audio_graph
        if edl.loudness:
            graph = (graph.replace("[aout]", "[mixed]")
                 + f";[mixed]loudnorm=I={edl.loudness}:TP=-1.5:LRA=11,aresample=48000[aout]")
        cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[aout]"]
    else:
        cmd += ["-map", "0:v", "-map", "0:a?"]
        if edl.loudness:
            cmd += ["-af", f"loudnorm=I={edl.loudness}:TP=-1.5:LRA=11,aresample=48000"]

    exp = edl.export or {}
    codec = str(exp.get("codec", "h264")).lower()
    vcodec = "libx265" if codec in {"h265", "hevc", "libx265"} else "libx264"
    cmd += ["-c:v", vcodec, "-preset", str(exp.get("preset", "medium"))]
    if exp.get("bitrate"):
        cmd += ["-b:v", str(exp["bitrate"])]
    else:
        cmd += ["-crf", str(exp.get("crf", 20))]
    cmd += [
        "-pix_fmt", "yuv420p", "-r", str(edl.fps),
        "-c:a", "aac", "-b:a", str(exp.get("audio_bitrate", "192k")),
        "-movflags", "+faststart", "-shortest", out_path,
    ]
    return cmd


# ---------------------------------------------------------------------------
# Captions: SRT -> ASS with a real pixel font size
# ---------------------------------------------------------------------------

SRT_TIME = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def srt_to_ass(srt_text: str, edl: EDL, captions: Dict[str, Any]) -> str:
    font = captions.get("font", DEFAULT_FONT)
    size = int(captions.get("font_size", 54))
    outline = int(captions.get("outline", 3))
    bold = -1 if captions.get("bold", True) else 0
    align = {"bottom": 2, "center": 5, "top": 8}.get(str(captions.get("position", "bottom")), 2)
    safe = float(captions.get("safe_bottom_pct", 12 if edl.height < edl.width else 22))
    margin_v = int(edl.height * safe / 100)
    margin_h = int(edl.width * 0.06)

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {edl.width}",
        f"PlayResY: {edl.height}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        f"{bold},0,0,0,100,100,0,0,1,{outline},0,{align},{margin_h},{margin_h},{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    events: List[str] = []
    for block in re.split(r"\n\s*\n", srt_text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            continue
        m = SRT_TIME.search(lines[idx])
        if not m:
            continue
        start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4).ljust(3, "0")) / 1000
        end = int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8).ljust(3, "0")) / 1000
        text = r"\N".join(ln.strip() for ln in lines[idx + 1:])
        text = text.replace("{", r"\{").replace("}", r"\}")
        events.append(f"Dialogue: 0,{fmt_time(start)},{fmt_time(end)},Default,,0,0,0,,{text}")

    return "\n".join(header + events) + "\n"


# ---------------------------------------------------------------------------
# Render pipeline
# ---------------------------------------------------------------------------

def render(edl: EDL, ffmpeg: str, workdir: str, dry_run: bool = False) -> Dict[str, Any]:
    workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    out_path = os.path.abspath(edl.output)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    for clip in edl.clips:
        if not os.path.exists(clip.source):
            raise EDLError(f"source not found: {clip.source}")
    if edl.music and not os.path.exists(edl.music["source"]):
        raise EDLError(f"music not found: {edl.music['source']}")

    normalized: List[str] = []
    for i, clip in enumerate(edl.clips):
        out = os.path.join(workdir, f"clip_{i:03d}.mp4")
        with_audio = has_audio(ffmpeg, clip.source) if not dry_run else True
        run(normalize_cmd(ffmpeg, edl, clip, out, with_audio), dry_run, f"normalize {i:02d}")
        normalized.append(out)

    list_path = os.path.join(workdir, "concat.txt")
    if not dry_run:
        with open(list_path, "w", encoding="utf-8") as fh:
            for path in normalized:
                fh.write(f"file '{path.replace(chr(92), '/')}'\n")

    base_path = os.path.join(workdir, "base.mp4")
    run(concat_cmd(ffmpeg, list_path, base_path), dry_run, "concat")

    ass_path: Optional[str] = None
    if edl.captions:
        srt_path = edl.captions["srt"]
        if not os.path.exists(srt_path):
            raise EDLError(f"captions not found: {srt_path}")
        if not dry_run:
            with open(srt_path, "r", encoding="utf-8-sig") as fh:
                ass_text = srt_to_ass(fh.read(), edl, edl.captions)
            ass_path = os.path.join(workdir, "captions.ass")
            with open(ass_path, "w", encoding="utf-8") as fh:
                fh.write(ass_text)
        else:
            ass_path = os.path.join(workdir, "captions.ass")

    if edl.captions and find_fonts_dir(edl.captions.get("fonts_dir")) is None:
        print("warning: no font directory found - caption burn may fail. "
              "Set captions.fonts_dir to a folder containing your .ttf files.", file=sys.stderr)

    run(final_cmd(ffmpeg, edl, base_path, out_path, ass_path, workdir,
                  edl.captions.get("fonts_dir") if edl.captions else None),
        dry_run, "final")
    return {
        "output": out_path,
        "duration": round(edl.duration, 3),
        "canvas": f"{edl.width}x{edl.height}",
        "fps": edl.fps,
        "clips": len(edl.clips),
    }


def find_ffmpeg(explicit: Optional[str]) -> str:
    for candidate in (explicit, os.environ.get("FFMPEG_BIN"), shutil.which("ffmpeg")):
        if candidate and shutil.which(candidate):
            return candidate
    raise RuntimeError(
        "ffmpeg not found. Install it, or set --ffmpeg / FFMPEG_BIN, "
        "or `pip install imageio-ffmpeg` and use its bundled binary."
    )


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Render an EDL to a finished video with ffmpeg.")
    p.add_argument("edl", help="path to the EDL json")
    p.add_argument("--workdir", default=None, help="scratch folder (default: temp dir)")
    p.add_argument("--ffmpeg", default=None, help="ffmpeg binary (default: PATH / FFMPEG_BIN)")
    p.add_argument("--dry-run", action="store_true", help="print ffmpeg commands, render nothing")
    p.add_argument("--validate-only", action="store_true", help="validate the EDL and exit")
    p.add_argument("--keep-work", action="store_true", help="keep intermediate files")
    args = p.parse_args(argv)

    try:
        edl = load_edl(args.edl)
    except EDLError as exc:
        print(f"EDL error: {exc}", file=sys.stderr)
        return 2

    print(f"EDL ok: {len(edl.clips)} clips, {edl.duration:.2f}s, {edl.width}x{edl.height} @ {edl.fps}fps")
    if args.validate_only:
        return 0

    try:
        ffmpeg = find_ffmpeg(args.ffmpeg)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    temp = args.workdir is None
    workdir = args.workdir or tempfile.mkdtemp(prefix="edl_render_")

    try:
        result = render(edl, ffmpeg, workdir, dry_run=args.dry_run)
    except (EDLError, RuntimeError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp and not args.keep_work and not args.dry_run:
            shutil.rmtree(workdir, ignore_errors=True)

    if args.dry_run:
        print("dry run complete - no files written")
    else:
        print("done:", json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
