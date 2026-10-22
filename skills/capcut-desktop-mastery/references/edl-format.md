# EDL format (plan.json)

The edit decision list is the contract between the AI that plans the cut and the script that
renders it. Plain JSON, no CapCut dependency, no schema library needed.

Renderer: `scripts/edl_render.py`

## Minimal example

```json
{
  "output": "exports/reel_v01.mp4",
  "canvas": {"width": 1080, "height": 1920},
  "fps": 30,
  "clips": [
    {"source": "footage/IMG_0142.mp4", "in": "0:04.2", "out": "0:09.8"},
    {"source": "footage/IMG_0145.mp4", "in": "0:31.0", "out": "0:34.5", "speed": 1.5}
  ]
}
```

## Full schema

| Field | Type | Default | Notes |
|---|---|---|---|
| `output` | string | `out.mp4` | Relative to the current directory when rendering |
| `canvas.width` / `canvas.height` | int, even | 1080 × 1920 | Source is scaled to fit, then padded - never stretched |
| `fps` | int 1-120 | 30 | Match the source footage |
| `background` | string | `black` | Padding colour: `black`, `white`, or `#RRGGBB` |
| `clips[]` | array | required | Played in order |
| `clips[].source` | string | required | Relative to the EDL file, or absolute |
| `clips[].in` | time | 0 | Start of the usable part |
| `clips[].out` | time | required* | End of the usable part (*or use `duration`) |
| `clips[].duration` | time | - | Alternative to `out` |
| `clips[].speed` | float 0.1-10 | 1.0 | 2.0 = double speed, 0.5 = slow motion |
| `clips[].volume` | float 0-2 | 1.0 | Per-clip audio gain |
| `clips[].label` | string | "" | Free text, useful for auditing an AI edit |
| `music` | object | none | See below |
| `music.source` | string | required | Audio file, looped to the timeline length |
| `music.volume` | float 0-1 | 0.2 | Bed level under the voice |
| `music.duck` | bool | true | Sidechain-compress the music under dialogue |
| `music.fade_in` / `fade_out` | seconds | 0.5 / 1.0 | Applied to the music only |
| `captions.srt` | string | - | SRT path; burned in with libass |
| `captions.font` | string | DejaVu Sans | Exact family name from the font file |
| `captions.font_size` | int | 54 | Pixels at the canvas height |
| `captions.outline` | int | 3 | Black outline thickness |
| `captions.position` | string | `bottom` | `bottom` / `center` / `top` |
| `captions.safe_bottom_pct` | float | 22 (vertical) / 12 (horizontal) | Margin from the bottom |
| `captions.fonts_dir` | string | auto-detected | Folder containing your `.ttf` files |
| `export.crf` | int 0-51 | 20 | Lower = better quality. 18 = master, 23 = review |
| `export.bitrate` | string | - | Overrides CRF, e.g. `"12M"` |
| `export.codec` | string | `h264` | `h264` (safe) or `h265` (smaller) |
| `export.preset` | string | `medium` | ffmpeg x264 preset |
| `export.audio_bitrate` | string | `192k` | AAC |
| `loudness` | float | none | e.g. `-14` applies EBU R128 loudnorm |

### Time formats accepted everywhere

```
12.5        1:30        1:02:03.5        00:00:05
```

## What the renderer does, in order

1. **Normalise each clip** - trim to `in`/`out`, scale to fit the canvas, pad to exact size,
   conform to the target fps and to yuv420p, keep or generate audio.
2. **Concatenate** - stream copy, so no re-encode of already-normalised clips.
3. **Convert SRT → ASS** - with a real pixel font size and a safe-zone-aware bottom margin.
4. **Final pass** - burn captions, mix `voice + music` (sidechain ducking), optional loudnorm,
   encode H.264/AAC with `+faststart`.

Intermediate files land in `--workdir` and are deleted unless `--keep-work` is passed.

## Guarantees and limits

**Guaranteed**

- Exact canvas size, no stretching (scale-then-pad)
- Constant frame rate output
- Audio present in every clip, even silent sources
- Captions positioned inside the platform safe zone
- Deterministic output: same EDL, same file

**Not supported**

- Transitions between clips (hard cuts only) - use CapCut for anything fancier
- Effects, LUTs, masks, keyframes, PIP
- Variable speed curves (single speed factor per clip only)
- Multi-track overlays
- Animated caption styles

When a job needs any of those, render the base cut here and open the MP4 in CapCut for the finish.
That split is deliberate: the script does the boring 80 %, CapCut does the 20 % that needs eyes.

## Validating before a long render

```bash
python3 scripts/edl_render.py plan.json --validate-only
python3 scripts/edl_render.py plan.json --dry-run      # prints every ffmpeg command
```

`--validate-only` checks the schema, timings, and file paths in milliseconds. Always run it
before a 20-minute render.
