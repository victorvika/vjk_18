# CapCut Desktop - where everything lives

> CapCut reshuffles labels between builds. If a name below is not on screen, look for the
> **same icon or the same panel position**, and tell the user what the control does instead of
> insisting on a menu path.

## Screen layout

```
+---------------------------------------------------------------+
|  Project name   [Media][Audio][Text][Stickers][Effects]...     |
+------------------+---------------------------+----------------+
|                  |                           |                |
|   Left panel     |     Preview + playback    |  Right panel   |
|   (library)      |     aspect dropdown       |  (inspector)   |
|                  |                           |                |
+------------------+---------------------------+----------------+
|  Toolbar: undo redo | split delete | ...      |   Export       |
|  Timeline: V1 / overlay / text / audio tracks                  |
+---------------------------------------------------------------+
```

## The eight top tabs

| Tab | Contains | Power-user note |
|---|---|---|
| **Media** | Imported video, images, audio. Also `Local`, `Cloud`, `Stock` | Import the whole folder once; do not re-import per clip |
| **Audio** | Music library, SFX library, `Extract audio` | Extract audio from any video clip to a separate track |
| **Text** | Default text, text templates, `Auto captions`, text-to-speech | Auto captions first, then style them - not the reverse |
| **Stickers** | Static and animated overlays | Great for arrows, emoji reactions, cursor clicks |
| **Effects** | Video effects, body effects, character effects | Every effect is a filter on a clip - stack max two |
| **Transitions** | Cross-dissolve, glitch, zoom, whip, and more | Drag onto the **seam** between two clips, not onto a clip |
| **Filters** | One-click looks, organised by mood | Cheaper than a LUT, less controllable |
| **Adjustments** | Brightness, contrast, saturation, HSL, LUT, curves (newer builds) | Supports an adjustment layer for whole-timeline grading |

## The right-hand inspector (changes with selection)

| Selected | Tabs you get | What matters |
|---|---|---|
| Video clip | **Video** (Basic, Mask, Cutout, Blend), **Speed**, **Animation**, **Adjust** | 90 % of real editing happens here |
| Audio clip | **Basic** (volume, fade), **Speed**, **Denoise**, **Enhance voice**, **Voice changer** | Fade handles are also draggable on the waveform |
| Text | **Text** (font, style, colour, stroke, shadow, background, spacing), **Animation**, **Bubble** | Keep two weights max across a whole video |
| Transition | Duration, "apply to all" | Apply to all only when every cut is the same rhythm |

### Video > Basic

- **Opacity** - fade a layer in/out
- **Blend** - Screen, Multiply, Overlay, Soft light… (Screen is the glow hack, Multiply is the shadow hack)
- **Mask** - Linear, Mirror, Circle, Rectangle, Heart, Star, Triangle + Feather + Invert
- **Cutout** - Auto cutout (AI subject removal) and **Chroma key**
- **Scale / Position / Rotation** - each has a keyframe diamond

### Video > Speed

- **Normal** - 0.1× to 100×
- **Curve** - presets (Montage, Hero, Bullet time, Jump cut, Flash in/out) plus a drag-point graph
- **Reverse** - plays the clip backwards (audio also reverses; usually mute it)

### Video > Animation

- **In** / **Out** / **Combo** / **Loop** - presets with a duration slider
- Use for text and overlays. For camera moves, keyframes beat presets.

## Timeline toolbar (appears with a clip selected)

| Tool | What it does | Shortcut |
|---|---|---|
| Split | Cuts at the playhead into two clips | `Ctrl+B` |
| Delete | Removes the clip, **leaves a gap** | `Delete` |
| Ripple delete | Removes the clip **and closes the gap** | right-click menu |
| Freeze | Creates a still frame of the current frame | - |
| Reverse | Flips playback direction | - |
| Mirror | Horizontal flip (fixes flipped phone footage) | - |
| Crop | Reframe inside the canvas | - |
| Rotate | 90° steps | - |
| Volume | Clip gain | - |
| Fade in / out | Audio or video fade | drag handles |
| Detach audio | Splits audio from video onto its own track | right-click |

## Shortcuts worth memorising

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `Ctrl+B` | Split at playhead |
| `Ctrl+Z` / `Ctrl+Shift+Z` | Undo / redo |
| `Ctrl+C` / `Ctrl+V` | Copy / paste |
| `Ctrl+A` | Select all clips |
| `Delete` | Delete selection (leaves gap) |
| `Ctrl` + scroll | Zoom the timeline |
| `Shift` + drag | Constrain a move to one axis |

Open **Settings > Shortcuts** for the authoritative list in the installed build. Do not quote
shortcuts from memory if the user says one does not work - check that panel.

## Track discipline

- **V1** - main story. Nothing else lives here.
- **V2+** - overlays, PIP, B-roll, logos.
- **Text tracks** - one per style group (captions track separate from hook text).
- **Audio** - music on its own track, SFX on another, voice untouched.
- **Adjustment layer** - top video track, spans the whole edit, holds the final LUT/grade.

If a project feels chaotic, it is a track problem, not an effects problem.
