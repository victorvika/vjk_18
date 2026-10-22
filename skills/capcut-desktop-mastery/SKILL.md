---
name: capcut-desktop-mastery
description: Coach and execute CapCut Desktop (PC/Mac) video edits end to end - project setup, rough and fine cutting, LUTs and colour, audio ducking, captions, picture-in-picture, rotoscoping, chroma key, keyframe animation, zoom/punch-in effects, and platform-correct export. Use when the user wants to edit a video in CapCut, asks how a CapCut tool works, needs export settings for YouTube, Shorts, Reels, TikTok, or WhatsApp, or references the Tamil "Mastering CapCut" masterclass by Prakash.
metadata:
  source_video: https://youtu.be/BSTuxpc9FU0
  source_title: Mastering CapCut (Basic to Advanced) தமிழ் 2025 - Full Masterclass - Prakash
  source_duration: 1:13:09
  version: 1.0.0
  languages: en, ta
---

# CapCut Desktop Mastery

Turn CapCut Desktop footage into a finished, platform-ready export without guessing.
Covers the full path: setup → cut → sound → text → effects → colour → export.

## Language contract

Reply in the user's language. Default for this skill: **English technical terms + Tamil explanation**.

- Keep CapCut's own button/menu names in **English** so the user can find them on screen:
  `Split`, `Speed > Curve`, `Chroma key`, `Auto captions`, `Export`.
- Explain the *why* in Tamil (or Tanglish if that is how the user writes).
- Example: "Clip-a select panni **Split** (Ctrl+B) pannunga — playhead-la irukkura exact frame-la rendu pieces-a cut aagum."

Never translate UI labels into Tamil; it breaks the matching with what is on screen.

## Step 0 - Intake (ask before touching a timeline)

Ask these five, then start. If the user is impatient, assume the defaults in brackets and say so.

1. **Platform + aspect** - YouTube 16:9, Reels/Shorts/TikTok 9:16, IG feed 4:5? [Reels 9:16]
2. **Target length** and how much raw footage exists. [30 s from ~2 min]
3. **Style reference** - talking head, vlog, montage, product demo, podcast clip?
4. **Must-keep moments** - exact quotes, product shots, CTA.
5. **Deliverables** - one master file, or master + 2 vertical cutdowns?

Then write a one-paragraph **edit plan** and an `assets/edit-plan.template.md` copy before cutting.
Do not start cutting from a vague request.

## Step 1 - Project setup (60 seconds, saves hours)

1. Open CapCut Desktop → **Create project**.
2. Set canvas **before** importing: the aspect dropdown next to the preview, or `Format` in project settings.
   - 16:9 → 1920×1080 · 9:16 → 1080×1920 · 4:5 → 1080×1350 · 1:1 → 1080×1080
3. Match **frame rate to the footage**, not to a habit. 30 fps source → 30 fps timeline.
   Mixed 24/30/60 fps clips: pick the highest and let CapCut conform, or transcode the odd ones out.
4. Keep the project folder flat and boring:
   ```
   project-name/
     footage/  audio/  luts/  overlays/  exports/
   ```
5. Import LUTs once: `Adjustments > LUT > Import` (`.cube` files). Free packs: freshluts.com, lutify.me samples.
6. 4K footage on a weak machine: enable **Proxy** if your build has it, or make 1080p editing copies.

Full panel-by-panel tour: `references/tools-map.md`.

## Step 2 - Assembly, then cut (never both at once)

The masterclass order matters. Three separate passes, no multitasking:

**Pass 1 - Assembly.** Drop every usable clip in shooting order. No trimming. Goal: see the whole story.

**Pass 2 - Rough cut ("radio edit").** Close your eyes to the picture; cut for the story.
- `Ctrl+B` splits at the playhead. Delete the dead air.
- Cut on pauses, never mid-word or mid-breath. Leave 2-3 frames of air around speech.
- Remove: false starts, "um", repeated takes, camera adjustments, walking.
- Ripple delete gaps: right-click the gap → delete and close gap (or select the gap and hit `Delete`).

**Pass 3 - Fine cut.** Now polish timing.
- Every cut: does the next shot start on the word it should? Nudge ±3 frames.
- Vary shot length. Three cuts of identical length feel robotic; 2 s / 4 s / 1.5 s feels edited.
- Add **J-cuts and L-cuts**: detach audio (`right-click > Detach audio`), slide the audio 6-12 frames earlier (J) or later (L) than the picture. This single trick makes edits feel professional.

Checkpoint: watch the cut muted. If the story still reads, the edit is sound.

## Step 3 - Sound (cheapest quality win)

1. **Music bed** at 15-25 % volume under dialogue, 100 % for montage sections.
2. **Duck manually**: keyframe music volume down 3-6 dB on the first word of each sentence, back up on the pause. Automation beats a constant low level.
3. **SFX**: whooshes on transitions, subtle hits on cuts, UI clicks for text pops. Keep them 6-10 dB under dialogue.
4. **Clean the voice first**: `Audio > Enhance voice` (light), `Noise reduction` only if hiss is audible - it thins the voice.
5. **Loudness target**: dialogue peaks around -6 dB, overall mix around -14 LUFS for social, -16 dBFS peak for safety.
6. Fade every track in/out 0.3-0.5 s. Abrupt starts are the #1 amateur tell.

Details and the SFX placement map: `references/audio-and-text.md`.

## Step 4 - Text and captions

1. **Auto captions**: `Text > Auto captions` → language → Generate → fix names and numbers by hand. Never ship raw ASR.
2. Style: one font, two weights max. Caption size on 9:16 → roughly 40-60 px at 1080×1920.
3. **Safe zones** on vertical: keep text out of the bottom 25 % (captions/CTA) and right 15 % (buttons).
4. Hook text on screen for the first 1.5 s, 3-7 words, high contrast.
5. Animate sparingly: one in-animation style for the whole video, not five.

## Step 5 - Effects that carry their weight

Only reach for an effect when it fixes a problem or lands a beat.

| Goal | Technique | Reference |
|---|---|---|
| Two people / screen + face | Picture-in-picture on a second track | `references/effects-cookbook.md#pip` |
| Subject cut out from background | `Cutout > Auto cutout` (clean) or `Chroma key` (green screen) | `references/effects-cookbook.md#cutout` |
| Move around the frame over time | Keyframes on Scale / Position | `references/effects-cookbook.md#keyframes` |
| Energy on a cut | Punch-in zoom (105-115 %) on the incoming clip | `references/effects-cookbook.md#zoom` |
| Slow motion that breathes | `Speed > Curve` with a custom ramp | `references/effects-cookbook.md#speed-ramp` |
| Skin cleanup on a face | `Beauty` / `Retouch`, low strength | `references/effects-cookbook.md#beauty` |
| Clean background swap | Chroma key: pick colour, then Strength → Shadow → Highlight | `references/effects-cookbook.md#greenscreen` |

Hard rule: if an effect needs more than 3 sliders, it is probably hiding a weak cut. Fix the cut.

## Step 6 - Colour (last, always)

1. Correct per clip first: exposure → white balance → contrast. Match shots to each other, not to a look.
2. Then grade globally: one **Adjustment layer** or a LUT over the whole timeline.
3. LUT at 40-70 % intensity. 100 % is a preset look, not a grade.
4. Legal range: highlights below 100 %, blacks above 0 unless you want them crushed on purpose.
5. Skin tones first, sky second, everything else third.

## Step 7 - Export

Use the planner script so the numbers are not guessed:

```bash
python3 scripts/export_plan.py reels --duration 0:45
python3 scripts/export_plan.py youtube-1080p --fps 60 --source-width 1920 --source-height 1080
```

It returns canvas, fps, bitrate, codec, container, audio, estimated file size and warnings
(e.g. upscaling, dropped frames). Then in CapCut: `Export` → set **Resolution**, **Frame rate**,
**Bitrate** (`Recommended` for drafts, `Higher` for upload), **Codec** `H.264`, **Format** `MP4`.

| Target | Canvas | FPS | Bitrate | Notes |
|---|---|---|---|---|
| YouTube 1080p | 1920×1080 | 24-60 | 8-12 Mbps | 60 fps → 12 Mbps |
| YouTube 4K | 3840×2160 | 24-60 | 45-68 Mbps | only if the source is really 4K |
| Reels / Shorts / TikTok | 1080×1920 | 30 or 60 | 10-16 Mbps | platform re-encodes anyway |
| IG feed | 1080×1350 | 30 | 8-12 Mbps | 4:5 wins screen space |
| WhatsApp status | 720×1280 | 30 | 3-5 Mbps | heavy compression, bigger text |
| Client master | match source | match source | 16-40 Mbps | H.264, not H.265 |

Never upscale 1080p to 4K for "quality". Never export H.265 to a client who will open it on an old phone.

## Step 8 - QA gate before you call it done

Run `assets/reel-qa-checklist.md` top to bottom. Minimum:

- [ ] Watch once at 100 % with sound, once muted.
- [ ] First 1.5 s has motion, a face, or a hook - not a logo.
- [ ] Every caption checked against the audio (names, numbers, brand spelling).
- [ ] No black frame, no frozen frame, no 0.2 s flash of a wrong clip.
- [ ] Audio never clips; music does not fight the voice.
- [ ] Export plays on a phone, not just the editing machine.
- [ ] Filename follows `client_topic_platform_vNN.mp4`.

## How to respond while using this skill

- Give **numbered steps in the order of the CapCut UI**, not in the order of theory.
- One decision per step. Say what to click, then what should visibly change.
- Include the **shortcut** where one exists (`Ctrl+B` split, `Space` play, `Ctrl+Z` undo).
- When the user is stuck, ask for a screenshot description of the panel they see - CapCut labels shift between versions, so match on position and icon, not only on words.
- For Tamil-speaking users, explain with a **before/after example** ("cut pannina munnadi ... appuram ...") rather than more jargon.

## Reference map

| File | Read it when |
|---|---|
| `references/video-map.md` | You need the masterclass chapter list, timestamps, and what each chapter teaches |
| `references/tools-map.md` | Any "where is this button / what does this panel do" question |
| `references/effects-cookbook.md` | Building PIP, keyframes, chroma key, roto, speed ramps, zoom, beauty |
| `references/audio-and-text.md` | Mixing levels, ducking, SFX placement, caption styling |
| `references/export-and-delivery.md` | Codec/bitrate questions, client delivery, archive rules |
| `references/troubleshooting.md` | Lag, crash, green screen fringe, washed-out colour, audio drift, export failure |
| `references/tamil-glossary.md` | Choosing the Tamil word for a CapCut concept |

## Scope and honesty

- This skill encodes the workflow and techniques from the linked Tamil masterclass plus standard editing practice. It does not claim to reproduce the video's exact narration.
- CapCut updates its UI often. If a label has moved, describe the *function* and let the user find the equivalent; do not invent a menu path you are unsure of.
- Never promise an AI feature (auto cutout, auto captions) will be perfect. Set the expectation: 80 % automation, 20 % manual cleanup.
