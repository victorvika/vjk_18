# Audio and text

Sound is half the video and most beginners treat it as a final touch. Do it at step 3, not step 7.

## Mix levels

CapCut shows volume as a percentage; dB is the reference underneath.

| Element | CapCut volume | Approx level | Notes |
|---|---|---|---|
| Dialogue / voice | 100 % | -12 to -6 dB peak | The reference. Everything else serves this |
| Music under voice | 15-25 % | -24 to -18 dB | If you can follow the lyrics, it is too loud |
| Music in montage (no voice) | 60-100 % | -12 to -6 dB | Now it is the star |
| SFX (whoosh, hit) | 30-50 % | -18 to -12 dB | Start quiet, raise until felt, then lower 3 dB |
| Room tone / ambience | 5-15 % | -30 dB | Kills the "dead silence" feeling between cuts |

**Target loudness:** social platforms normalise around -14 LUFS. Aim for dialogue peaks at
-6 dB and an overall mix near -14 LUFS. CapCut has no LUFS meter - use your ears and a phone
speaker test, or export and check in Audacity/ffmpeg.

## Ducking (music under speech) - do it manually

Auto-ducking is inconsistent in CapCut builds, so keyframe it:

1. Place the music on its own track.
2. Playhead on the first word → keyframe volume at 20 %.
3. 4-8 frames earlier → keyframe at 60 %. That ramp is the "breath" before speech.
4. On the pause after the sentence → keyframe back to 60 %.
5. Repeat per sentence. Tedious for 5 minutes, invisible to the viewer.

Shortcut version: cut the music into blocks and set each block's volume, rather than keyframing.
Cleaner waveform, faster to read.

## Fades and edges

- Every music track: fade in 0.5 s, fade out 1.0-1.5 s. Abrupt cuts are the amateur tell.
- Every SFX: 10-30 ms fade at both ends, or it clicks.
- Dialogue: no fade. Cut at a zero-crossing if a pop appears.

## Music choice

- Match **BPM** to cut rhythm: 90 BPM ≈ a cut every 2 beats (1.33 s). 120 BPM ≈ 1 s.
- Match **energy** to the section, not to the whole video. One track with a drop is better than
  three tracks fighting.
- Instrumental for anything with speech. Lyrics compete with dialogue in the listener's brain.
- Start the music **before** the first cut lands. Music that begins exactly on a cut feels late.

## SFX placement map

| Moment | Sound | Level |
|---|---|---|
| Text pops in | soft click / pop | 20 % |
| Whoosh transition | 0.5-0.8 s whoosh | 30-40 % |
| Zoom / punch-in | short riser or impact | 35 % |
| Scene change | sub-bass hit | 40 % |
| Reveal | reverse cymbal into the cut | 25 % |
| Error / joke beat | record scratch or vine boom | 30 %, ironically |

Keep a personal library folder (`sfx/whoosh/`, `sfx/hits/`, `sfx/ui/`) so you are not searching
the stock library mid-edit.

## Cleaning voice

Order matters:

1. `Enhance voice` - light. One pass. Two passes sounds metallic.
2. `Noise reduction` - only if hiss/AC hum is audible. It thins the voice; 30-50 % max.
3. `Adjust > ...` no EQ in CapCut desktop beyond presets. For real repair use Audacity
   (noise profile → reduction 6-10 dB) and re-import the WAV.
4. Remove breaths **selectively**: cut only the loud ones between sentences, keep the quiet ones.
   Zero breaths sounds robotic.
5. If the voice is distant, do not just raise volume - raise it and add a slight high-pass feel
   via `Enhance voice`, then lower the music bed.

---

# Text and captions

## Sizing and placement

| Canvas | Caption size | Hook size | Safe margin |
|---|---|---|---|
| 1080×1920 (9:16) | 40-60 px | 64-90 px | bottom 25 %, right 15 % |
| 1920×1080 (16:9) | 36-48 px | 60-80 px | 5 % all sides |
| 1080×1350 (4:5) | 38-50 px | 64-80 px | bottom 12 % |

Rules:

- **Two lines maximum** per caption. If it needs three, the sentence is too long.
- Line spacing 1.1-1.3. Tight text is unreadable on a phone.
- High contrast always: white text + 2-4 px black stroke, or a semi-transparent dark plate at 60 %.
- Never pure white on pure white backgrounds; add the stroke first.

## Style system

Pick once, reuse forever:

```
Font        : one sans-serif (Poppins / Montserrat / Inter)
Weights     : Bold for hooks, Regular/Medium for captions
Colour      : white + one accent (brand colour) for keywords only
Stroke      : 2-4 px black
Shadow      : off (stroke does the job)
Animation   : one in-style only (e.g. "Pop" or "Fade up"), 0.2-0.3 s
```

Keyword highlighting: duplicate the caption, change one word's colour. CapCut has no inline
multi-colour inside a single text object - either split into two text objects positioned
side by side, or use the caption template that supports emphasis.

## Auto captions workflow

1. `Text > Auto captions` → language → Generate.
2. **Fix before styling.** Read every line against the audio: names, numbers, brand spelling,
   Tamil/English mix transliteration.
3. Break lines manually at natural pauses. ASR breaks mid-phrase.
4. Style once, then `Apply to all` if the build supports it; otherwise copy-paste the style.
5. Check the last caption - ASR often trails off and leaves a half sentence.

## Tamil text - practical notes

This trips people up more than any effect.

- **Font support:** CapCut's built-in font list is limited for Tamil. If the glyphs render as
  boxes, the font does not carry Tamil. Fix: install a Tamil font system-wide
  (Noto Sans Tamil, Anek Tamil, Catamaran, Mukta Malar) and reopen CapCut.
- **Reliable workaround:** typeset Tamil text in Canva/Figma/Photoshop with a proper Tamil font,
  export PNG with transparent background, import as an overlay. Costs one extra app, guarantees
  correct shaping and ligatures.
- **Auto captions in Tamil:** availability depends on the build and region. If Tamil is missing
  from the language list, do not promise it - caption manually or use a separate transcription
  service and paste the text.
- **Line breaks matter more in Tamil** than in English: long agglutinated words wrap badly.
  Break at word boundaries and keep 4-6 words per line.
- **Avoid decorative/condensed fonts** for Tamil. Tamil glyphs need width; condensed cuts clip
  the vowel signs.

## Text animation budget

- Hook text: 1 animation, fast (0.2 s).
- Captions: no animation, or a single subtle fade. Animated captions on every word are exhausting.
- Lower thirds: slide in 0.3 s, hold 3 s minimum, fade out 0.3 s. If a viewer cannot read it
  twice, it is too fast.

## Read-aloud test

Say every on-screen caption out loud while the video plays. If you stumble, the viewer will too.
