# Troubleshooting

Work top-down: symptom → likely cause → cheapest fix first.

## Performance

| Symptom | Cause | Fix |
|---|---|---|
| Timeline lags while scrubbing | 4K/H.265 footage, no proxy | Enable Proxy, or make 1080p H.264 editing copies |
| Preview stutters but export is fine | preview quality | Set preview quality to 1/2 or 1/4 in the preview menu |
| Fan screams, fans out | effects stacked + 4K timeline | Move heavy effects to the end; render a section preview |
| CapCut freezes on import | VFR or odd codec (HEVC 10-bit phone video) | Transcode to H.264 8-bit 30 fps constant |
| Project opens with red "media offline" | files moved/renamed | Point CapCut to the new folder, or restore the original paths |
| Auto-save missing after crash | draft saved in a temp location | Check Documents/CapCut/Drafts and the autosave folder |

## Visual

| Symptom | Cause | Fix |
|---|---|---|
| Green fringe around subject | chroma key over-strength / spill | Lower Strength, raise Shadow, desaturate green in HSL |
| Cutout edge flickers every few frames | AI matte instability | Trim around the flicker, or mask it, or shorten the clip |
| Colours look grey/washed | HDR/HLG footage on an SDR timeline | Convert the clip to Rec.709 before editing, or turn off HDR export |
| Colours look oversaturated after upload | platform tone mapping | Export SDR Rec.709, keep saturation < 110 % |
| Text looks pixellated | scaled up above 100 % or thin font | Recreate at target size, use a heavier weight |
| Black bars on Reels | 16:9 footage in a 9:16 canvas | Reframe with Scale/Position, or set the background fill |
| Exported video has a watermark | a Pro-labelled effect or template used | Replace the Pro asset (crown icon) with a free equivalent |
| Letterboxing appears only on phones | safe-zone mismatch | Keep content inside the central 4:5 area of a 9:16 canvas |

## Audio

| Symptom | Cause | Fix |
|---|---|---|
| Audio drifts out of sync over time | variable frame rate source | Transcode to CFR before editing |
| Click/pop at a cut | cut mid-waveform | Move the cut a few frames, add 10 ms fade |
| Music drowns the voice | no ducking | Keyframe the music to 20 % under speech |
| Harsh "sss" sounds | over-enhanced voice | Reduce Enhance voice, lower the vocal volume 2 dB |
| Echo/roomy dialogue | untreated room | Add a noise gate via Noise reduction, or re-record close-mic |
| Export audio quieter than preview | bitrate too low | AAC 320 kbps, check the master volume keyframes |

## Export

| Symptom | Cause | Fix |
|---|---|---|
| Export stuck at 0 % or 99 % | disk space, or a corrupt clip | Free space, then split the timeline and export in halves |
| Export fails with no message | effect or codec conflict | Remove the newest effect, retry; update CapCut |
| File plays on PC but not on phone | H.265 or MOV | Re-export H.264 MP4 |
| Export is 3× bigger than expected | "Higher" bitrate + 4K + 60 fps | Drop to 1080p30 or use `Recommended` |
| Export takes forever | 4K + heavy effects + H.265 | Export H.264 1080p first as a preview, then the master overnight |
| Download/export blocked on mobile | region/account limits | Desktop build has fewer restrictions; note this to the user |

## "It used to work" checklist

1. Did CapCut auto-update? Labels move; the function usually stays.
2. Did the media move on disk? Offline media breaks exports silently.
3. Is the drive full? CapCut needs 2-3× the project size free.
4. Is the GPU driver current? Preview and export both use hardware encoding.
5. Did you switch machines? Drafts are not portable by default; copy the whole draft folder.

## When to stop debugging CapCut

- True multicam sync → Premiere Pro / Resolve
- Precise roto with hair and motion blur → After Effects / Resolve Magic Mask
- Real audio repair (EQ, compression, de-noise) → Audacity / Resolve Fairlight
- 10-bit HDR delivery → Resolve

Saying "CapCut is the wrong tool for this one shot" is better than burning two hours on a mask
that will still flicker.
