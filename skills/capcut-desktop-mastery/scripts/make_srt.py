#!/usr/bin/env python3
"""Turn a transcript into a timed SRT, without needing speech recognition.

Two inputs are supported:

1. Plain text - a script, a transcript, or caption text. Timing is distributed
   proportionally to the character count across the clip duration.
2. Whisper-style JSON - a list of segments with start/end, re-wrapped into
   readable caption lines.

Usage:
    python3 make_srt.py script.txt --duration 0:45 --out captions.srt
    python3 make_srt.py script.txt --duration 45 --max-chars 34 --lang ta
    python3 make_srt.py whisper.json --json-input --out captions.srt

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, Optional, Tuple

SENTENCE_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")
WORD_GAP = 0.18          # seconds of breathing room between captions
MIN_CAPTION_SECONDS = 0.9
MAX_CAPTION_SECONDS = 6.0

# Tamil packs more meaning per character, so the same reading time needs fewer
# characters on screen. These are empirically sane defaults, not laws.
DEFAULT_MAX_CHARS = {"ta": 32, "hi": 34, "en": 42, "default": 42}


def parse_time(value: str) -> float:
    text = str(value).strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return float(text)
    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"invalid time: {value!r}")
    total = 0.0
    for p in parts:
        if not p.replace(".", "", 1).isdigit():
            raise ValueError(f"invalid time: {value!r}")
        total = total * 60 + float(p)
    return total


def fmt(seconds: float) -> str:
    ms = int(round(max(seconds, 0.0) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, max_chars: int) -> List[str]:
    """Split text into caption-sized chunks: sentences first, then words."""
    chunks: List[str] = []
    for sentence in SENTENCE_SPLIT.split(text):
        sentence = clean(sentence)
        if not sentence:
            continue
        if len(sentence) <= max_chars:
            chunks.append(sentence)
            continue
        # break long sentences at clause boundaries, then greedily by words
        clauses = re.split(r"(?<=[,;:])\s+", sentence)
        current = ""
        for clause in clauses:
            candidate = f"{current} {clause}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.extend(wrap_words(current, max_chars))
            current = clause
        if current:
            chunks.extend(wrap_words(current, max_chars))
    return [c for c in chunks if c]


def wrap_words(text: str, max_chars: int) -> List[str]:
    words = text.split()
    out, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= max_chars or not line:
            line = candidate
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def time_chunks(chunks: List[str], duration: float, gap: float = WORD_GAP) -> List[Tuple[float, float, str]]:
    """Distribute duration across chunks by character weight."""
    if not chunks:
        return []
    total_chars = sum(len(c) for c in chunks) or 1
    usable = max(duration - gap * (len(chunks) - 1), duration * 0.5)
    cursor = 0.0
    out: List[Tuple[float, float, str]] = []
    for chunk in chunks:
        span = usable * len(chunk) / total_chars
        span = max(min(span, MAX_CAPTION_SECONDS), min(MIN_CAPTION_SECONDS, usable))
        start, end = cursor, min(cursor + span, duration)
        if end - start < 0.2:
            break
        out.append((start, end, chunk))
        cursor = end + gap
    # stretch/trim the last caption so the SRT ends where the video does
    if out:
        last_start, _, last_text = out[-1]
        out[-1] = (last_start, max(duration, last_start + 0.4), last_text)
    return out


def from_whisper(data: dict, max_chars: int) -> List[Tuple[float, float, str]]:
    segments = data.get("segments") or data.get("transcription") or []
    out: List[Tuple[float, float, str]] = []
    for seg in segments:
        text = clean(seg.get("text", ""))
        if not text:
            continue
        start = float(seg.get("start", seg.get("start_time", 0)))
        end = float(seg.get("end", seg.get("end_time", start + 2)))
        pieces = chunk_text(text, max_chars)
        if not pieces:
            continue
        for sub_start, sub_end, piece in time_chunks(pieces, max(end - start, 0.5), gap=0.05):
            out.append((start + sub_start, start + sub_end, piece))
    return out


def write_srt(rows: List[Tuple[float, float, str]]) -> str:
    blocks = []
    for i, (start, end, text) in enumerate(rows, 1):
        blocks.append(f"{i}\n{fmt(start)} --> {fmt(end)}\n{text}\n")
    return "\n".join(blocks)


def check_wrapping(rows: List[Tuple[float, float, str]], max_chars: int) -> List[str]:
    warnings = []
    for _, _, text in rows:
        if len(text) > max_chars * 2:
            warnings.append(f"long caption, consider splitting: {text[:40]}...")
        if text.endswith((".", "!", "?")) is False and len(text) > max_chars:
            warnings.append(f"caption has no trailing punctuation: {text[:40]}")
    return warnings


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Build a timed SRT from a transcript.")
    p.add_argument("input", help="plain text transcript, or whisper json with --json-input")
    p.add_argument("--out", default="captions.srt")
    p.add_argument("--duration", required=False, help="total clip length, e.g. 45 or 0:45")
    p.add_argument("--max-chars", type=int, default=None, help="characters per caption line")
    p.add_argument("--lang", default="default", help="ta/hi/en - affects the default line length")
    p.add_argument("--json-input", action="store_true", help="input is whisper-style JSON")
    p.add_argument("--check", action="store_true", help="print warnings about long captions")
    args = p.parse_args(argv)

    max_chars = args.max_chars or DEFAULT_MAX_CHARS.get(args.lang, DEFAULT_MAX_CHARS["default"])

    try:
        with open(args.input, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except FileNotFoundError:
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    if args.json_input:
        try:
            rows = from_whisper(json.loads(raw), max_chars)
        except json.JSONDecodeError as exc:
            print(f"invalid json: {exc}", file=sys.stderr)
            return 2
    else:
        if not args.duration:
            print("--duration is required for plain-text input", file=sys.stderr)
            return 2
        try:
            duration = parse_time(args.duration)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        chunks = chunk_text(raw, max_chars)
        rows = time_chunks(chunks, duration)

    if not rows:
        print("no caption text found", file=sys.stderr)
        return 1

    srt = write_srt(rows)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(srt)

    print(f"wrote {len(rows)} captions -> {args.out}")
    if args.check:
        for warning in check_wrapping(rows, max_chars):
            print(f"  ! {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
