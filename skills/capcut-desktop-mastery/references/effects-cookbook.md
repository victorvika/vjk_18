# Effects cookbook

Every recipe is written as: goal → clicks → starting values → what "good" looks like.
Starting values are for 1080p timelines; scale proportionally for 4K.

---

## <a id="keyframes"></a>Keyframes - the one concept that unlocks everything

A keyframe is a snapshot of a value at a moment in time. Two keyframes = one change.
Three or more = a move that evolves.

1. Put the playhead where the change should **start**.
2. Click the **diamond icon** next to a parameter (Scale, Position, Rotation, Opacity, Volume).
   It turns blue/filled = keyframe created.
3. Move the playhead to where the change should **end**.
4. Change the value. CapCut creates the second keyframe automatically.

Rules that separate good from twitchy:

- **Ease the ends.** Right-click a keyframe → ease in / ease out, or open the curve editor.
  Linear keyframes look mechanical; eased ones look like a camera operator.
- **Keep 2-3 keyframes per move.** Five keyframes for a 2-second push-in is over-animated.
- **Match movement speed across layers.** If the background zooms in 5 %/s, the text overlay
  should not move at 20 %/s.
- **Prefer Scale + Position together** for a "camera" feel: scaling to 110 % and drifting
  10 px left reads as a real lens move.

Tamil: "Keyframe-na oru frame-la value-a lock pannuradhu. Rendu keyframe vaiththaa, naduvula
CapCut smooth-a interpolate pannum - adhu-thaan animation."

---

## <a id="pip"></a>Picture-in-picture (chapter 10, 00:50:49)

**Goal:** a face cam, product shot, or screen recording over a main video.

1. Put the background clip on **V1**, the overlay clip on **V2** (drag it above).
2. Select the overlay → `Video > Basic` → **Scale** ~30-40 % for a face cam on 16:9.
3. **Position** it: keep a 5 % margin from the edge. Never kiss the frame border.
4. Border, two ways:
   - If the build has **Border/Stroke**, set 4-6 px white.
   - Otherwise: duplicate the overlay on a lower track, scale it +4 %, and push brightness to
     +80 / saturation to 0 to fake a white plate. Expand it with `Scale` so it peeks out evenly.
5. In/out: `Animation > In > Slide` 0.4 s, or keyframe Position from off-frame.
6. Optional shadow: duplicate the overlay on a track below, blacken it (brightness -100),
   offset 6 px, opacity 35 %.

**Looks right when:** the overlay reads as one object with the background, not a floating rectangle.

Common mistake: scaling to 50 % and placing it dead centre. It looks like a split screen, not PIP.

---

## <a id="cutout"></a>Cutout / background removal (chapters 11-12)

### <a id="greenscreen"></a>Green screen (chapter 12, 00:55:18)

1. Stack: background on **V1**, green-screen clip on **V2**.
2. Select the green clip → `Video > Cutout > Chroma key`.
3. Use the **eyedropper** and click a mid-tone area of the green - not a highlight, not a shadow.
4. Starting values: **Strength 30-50**, **Shadow 10-20**, **Highlight 10-20**. Labels vary by build;
   the sliders always do the same three jobs: core removal, dark-edge recovery, bright-edge recovery.
5. Cleanup order: raise Strength until the background is gone → lower it 5 points → fix Shadow →
   fix Highlight. Over-strength eats hair and fingers.
6. **Spill** (green rim on skin) fix: reduce saturation of green in `Adjust > HSL`, or add a slight
   magenta tint, or shoot with the subject 1.5 m away from the screen next time.
7. If the shot is soft or the lighting is uneven, `Auto cutout` often beats chroma key.

### Auto cutout (AI subject removal)

`Video > Cutout > Auto cutout` → choose Subject → it mattes the person automatically.
- Great for: clean single subject, decent contrast against background.
- Bad for: hair against busy backgrounds, transparent objects, two people crossing.
- Always scrub the result frame by frame at cuts; the mask flickers there.

Tamil: "Green screen-la light uneven-a irunthaal chroma key kashtam. Auto cutout use pannunga -
aana hair edges-a manual-a check pannunga."

---

## <a id="roto"></a>Rotoscoping - what CapCut can and cannot do (chapter 11, 00:53:57)

Honest version: CapCut Desktop does **not** have a frame-by-frame roto brush like After Effects.
What it has:

| Need | CapCut approach | Quality |
|---|---|---|
| Isolate a person from a background | `Auto cutout` | Good for clean shots, 80-90 % usable |
| Isolate a solid-colour object | `Chroma key` | Very good if lit evenly |
| Isolate a shape (logo, screen) | `Mask` + keyframes on position/scale/rotation | Good for geometric objects |
| Isolate a moving person edge-by-edge | Mask keyframing every 5-10 frames | Painful, average result |
| Precise matte with motion blur and hair | Not available | Export to After Effects / DaVinci |

**Mask-keyframe workflow** (the practical middle ground):

1. `Video > Basic > Mask > Rectangle` (or Circle/Linear).
2. Scale and feather the mask to hug the subject; feather 4-10 % to soften.
3. Keyframe **Position + Scale + Rotation** every 8-12 frames, aligning the mask to the subject.
4. Where the subject is occluded, add a keyframe pair and animate the mask out of frame.
5. Lock the result by duplicating the clip as a backup before heavy keyframing.

If the user's shot needs true roto (a person walking behind a pole), say it plainly and
recommend After Effects, DaVinci Resolve's Magic Mask, or a dedicated roto tool. Do not
promise CapCut can do it.

---

## <a id="zoom"></a>Zoom effects that look professional (chapter 15, 01:07:33)

Zooms are pacing tools, not decoration.

### 1. Slow push-in (documentary / talking head)
`Scale` 100 % → 108-112 % over 3-5 s, ease in-out. Barely visible, keeps a static shot alive.

### 2. Punch-in on a cut (the energy trick)
Two consecutive clips of the same subject. On the **incoming** clip set `Scale` to 105-115 %
and nudge `Position` to keep the eyes in the same place. The cut lands harder without a transition.

### 3. Whip zoom
`Scale` 100 → 160 in **4-6 frames**, ease out. Add `Effects > Blur > Directional` at the peak
or a whoosh SFX. Use once per 15 s maximum.

### 4. Zoom transition between scenes
Outgoing clip: `Scale` 100 → 140 in 6 frames. Incoming clip starts at 140 → 100 in 6 frames.
Match the focal point (same screen position) or it feels like a glitch.

### 5. Crash zoom for comedy
Snap 100 → 150 in 2 frames, hold 10 frames, snap back. No easing. Deliberately ugly.

**Rule:** if the viewer notices the zoom, it either landed a joke or it failed. Intentional or invisible.

Tamil: "Zoom podhu-dhu 'enna nadakkudhu' nu sollaadhu; 'ippo idhu important' nu sollum. Adhaan
reason illaama zoom panna amateur-a theriyum."

---

## <a id="speed-ramp"></a>Speed ramps (chapter 6, 00:31:40)

1. Select the clip → `Speed > Curve`.
2. Pick a starting preset: **Montage** (fast-slow-fast) or **Hero** (slow at the peak moment).
3. Drag graph points: horizontal axis = time, vertical = speed. Add a point at the moment of impact.
4. Keep the slowest point at **0.4-0.6×** for people; below 0.3× needs 60 fps+ footage or it stutters.
5. **Audio:** curve > "pitch" changes the sound. For music, mute the clip audio and use a separate track.
6. Add a whoosh or riser hitting exactly at the fastest point.

Shoot for the ramp: record the action at 60 fps (or 120 fps) if the camera allows. A ramp on
30 fps footage will always judder at the slow section, and no setting fixes that.

---

## <a id="beauty"></a>Beauty / retouch (chapter 14, 01:02:30)

`Video > Beauty` (or `Retouch`) → face tools: skin, blemish, face shape, eyes, teeth.

- Strength **10-25** for men, **15-35** for women, on 1080p. Above 40 the skin goes plastic.
- Fix **one** thing. Skin evenness is enough; face slimming plus eye enlargement plus teeth
  whitening reads as a filter.
- Beauty works per clip, not per project; matching two clips requires the same values on both.
- It fails on: profile shots, heavy motion blur, low light, more than one face close together.
- Always compare against the original at 100 % zoom. The timeline thumbnail lies.

Tamil: "Beauty effect-a adhigamaa pottaa, face plastic maadhiri aagum. 20-30 % podhum."

---

## Blend modes - the two that earn their keep

| Mode | Use |
|---|---|
| **Screen** | Light leaks, glow, lens flares, fire, dust overlays - black disappears |
| **Multiply** | Shadows, texture, grain, dark vignettes - white disappears |
| **Overlay / Soft light** | Subtle contrast push on a duplicate layer |

Workflow for a light leak: overlay clip on V2 → `Blend > Screen` → lower opacity to 30-60 % →
fade in/out with keyframes.

---

## Freeze frame + reverse (chapter 6)

- **Freeze:** playhead on the frame → `Freeze` → CapCut inserts a still. Extend it to 0.5-2 s.
  Pair with a zoom-in keyframe + a camera shutter SFX for the "moment" effect.
- **Reverse:** `Speed > Reverse`. Mute the audio; reversed speech sounds wrong. Best used on
  splashes, throws, and reveals.

---

## Effect budget

A well-edited 60-second reel:

- 0-2 transitions (a hard cut is not a failure)
- 1 motion idea (zoom or slide, not both)
- 1-2 sound-design layers per section
- 1 grade over everything

If you are stacking effects to fix a boring shot, the shot is the problem. Cut it.
