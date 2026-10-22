# Export and delivery

The export dialog is the last chance to lose quality. Four numbers decide it:
**resolution, frame rate, bitrate, codec.**

## The export dialog, field by field

| Field | What to choose | Why |
|---|---|---|
| **Name** | `client_topic_platform_vNN` | Version numbers save arguments later |
| **Location** | the project's `exports/` folder | Never the desktop |
| **Resolution** | exactly the timeline canvas, or 2× | Upscaling adds nothing |
| **Frame rate** | match the source footage | Mismatch = judder or duplicated frames |
| **Bitrate** | `Recommended` for review, `Higher` for upload | `Custom` only when you know why |
| **Codec** | H.264 (AVC) | H.265/HEVC is smaller but far less compatible |
| **Format** | MP4 | MOV only for ProRes-style intermediate work |
| **Audio** | AAC, 320 kbps, 48 kHz | 128 kbps dulls dialogue |
| **Cover** | export a frame for thumbnails | Saves a separate screenshot step |

## Target table

| Target | Canvas | FPS | Bitrate (H.264) | Notes |
|---|---|---|---|---|
| YouTube 1080p | 1920×1080 | 24-60 | 8-12 Mbps | 60 fps → 12 Mbps |
| YouTube 4K | 3840×2160 | 24-60 | 45-68 Mbps | 4K only from real 4K sources |
| Shorts | 1080×1920 | 30-60 | 10-16 Mbps | bottom 25 % + right 15 % are UI |
| Reels | 1080×1920 | 30-60 | 10-16 Mbps | IG re-encodes; give it a clean source |
| TikTok | 1080×1920 | 30-60 | 8-12 Mbps | same safe zones |
| IG feed | 1080×1350 | 30 | 8-12 Mbps | 4:5 uses the most screen |
| IG square | 1080×1080 | 30 | 6-10 Mbps | grid layouts |
| LinkedIn | 1920×1080 | 25-30 | 8-12 Mbps | assume muted viewing |
| WhatsApp status | 720×1280 | 30 | 3-5 Mbps | brutal compression; big text |
| Client master | match source | match source | 16-40 Mbps | H.264 for compatibility |

Use `scripts/export_plan.py` to generate these numbers with warnings instead of retyping the table:

```bash
python3 scripts/export_plan.py reels --duration 0:45
python3 scripts/export_plan.py youtube-1080p --fps 60 --source-width 1920 --source-height 1080
python3 scripts/export_plan.py --list
```

## Why exports look bad (and the actual fix)

| Symptom | Real cause | Fix |
|---|---|---|
| Soft / mushy details | bitrate too low, or upscaled source | raise bitrate, export at source resolution |
| Blocky motion in fast pans | low bitrate + high fps | 12+ Mbps at 1080p60, or slow the pan |
| Colours shift after upload | player colour management, HDR mismatch | export SDR Rec.709, avoid "Smart HDR" for social |
| Dark and crushed | timeline graded on a bright monitor | grade at ~50 % brightness, check on a phone |
| Text shimmer / moiré | thin fonts at small size | heavier weight, larger size, 2 px stroke |
| Audio out of sync after upload | variable frame rate phone footage | transcode to constant 30 fps before editing |
| Huge file | H.264 at "Higher" on a long video | accept it, or use H.265 for archive only |

## Frame rate reality check

- **24 fps** - cinematic, motion blur, not for fast action.
- **30 fps** - the social default, smallest files, safe everywhere.
- **60 fps** - gaming, sport, slow motion; doubles the bitrate requirement.
- **Mixing** 24 and 30 fps clips on a 30 fps timeline duplicates frames and causes micro-judder.
  Convert the odd clip or commit to one rate.
- **Slow motion needs headroom:** a 0.5× ramp on 30 fps footage plays 15 unique frames per second.
  It will stutter. Shoot 60 or 120 fps for slow motion.

## Variable frame rate (VFR) - the hidden sync bug

Phone screen recordings and some Android cameras record VFR. CapCut assumes constant frame rate,
so audio drifts progressively. Symptom: sync is fine at 0:00 and 2 seconds off at 4:00.

Fix before importing:

```bash
ffmpeg -i input.mp4 -vf "fps=30" -c:v libx264 -crf 18 -c:a aac -b:a 192k output.mp4
```

Or use HandBrake with "Constant Framerate" ticked. Then edit. No amount of nudging in the
timeline fixes VFR properly.

## Delivery structure for clients

```
client-name/
  exports/
    client_topic_reels_v01.mp4        <- review copy, Recommended bitrate
    client_topic_reels_v02_final.mp4  <- approved, Higher bitrate
  project/
    client_topic.capcut/              <- CapCut draft folder
  assets/
    fonts.txt                         <- font names + links used
    music.txt                         <- track, artist, licence
```

Always ship a **licence note** for music and fonts. A client who gets a copyright strike will not
care that the edit was beautiful.

## Archive rules

- Keep the **CapCut draft folder** plus the **original footage**. Drafts reference media by path -
  move the media and the project opens offline.
- Before archiving, run `File > ... > Collect/Consolidate` if the build offers it; otherwise zip the
  draft folder and the footage folder together with matching names.
- Keep the final MP4 at `Higher` bitrate. Re-encoding an already-compressed export is the fastest
  way to lose quality on a future re-cut.

## Naming conventions that survive a year

```
YYYYMMDD_client_topic_platform_vNN[_final].mp4
20251022_arun_salon-tour_reels_v03_final.mp4
```

Rules: no spaces, no "finalfinal", no "new", version numbers always two digits.
