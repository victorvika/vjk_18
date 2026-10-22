# Edit plan - <project name>

> Fill this in before opening CapCut. Ten minutes here saves an hour of re-editing.
> Delete the guidance text in angle brackets.

## 1. Delivery targets

| # | Platform | Canvas | Length | FPS | Deadline |
|---|---|---|---|---|---|
| 1 | <Reels / YouTube / ...> | <1080x1920> | <0:45> | <30> | <date> |
| 2 | <cutdown?> | | | | |

## 2. Source material

| Asset | Count | Notes |
|---|---|---|
| A-roll (main footage) | <n clips, mm:ss> | <camera, fps, resolution> |
| B-roll | <n clips> | <shot at 60fps for slowmo?> |
| Audio | <voice, music, sfx> | <mic used, noise issues> |
| Graphics | <logo, product shots, screenshots> | <formats> |

Checklist: footage copied off the card ☐ · VFR transcoded ☐ · backups made ☐ · LUTs imported ☐

## 3. Story spine

<One sentence: who is this for, what do they get, why should they keep watching.>

Example: "A salon owner watching on Instagram should understand that this colour service takes
3 hours and why it costs what it costs - in 40 seconds."

### Beats (target timings)

| Time | Beat | Content | Visual |
|---|---|---|---|
| 0:00-0:02 | Hook | <the boldest claim or visual> | <close-up / before-after> |
| 0:02-0:10 | Setup | <problem> | <A-roll> |
| 0:10-0:30 | Payoff | <process / proof> | <B-roll + captions> |
| 0:30-0:40 | CTA | <what to do next> | <text on screen> |

## 4. Must-keep moments

- <quote / timecode> - why
- <product shot> - why
- <CTA line>

## 5. Style decisions (decide once)

| Decision | Choice |
|---|---|
| Font (title / caption) | <Poppins Bold / Poppins Medium> |
| Caption style | <white + 3px black stroke, pop-in> |
| Accent colour | <#hex> |
| Music direction | <genre, BPM, instrumental only> |
| Grade | <warm neutral LUT at 55 %> |
| Transition rule | <hard cuts only; one zoom transition at 0:12> |
| Motion rule | <slow push-in on A-roll, punch-in on cuts> |

## 6. Track layout

```
V3  adjustment layer  - global grade
V2  overlays / PIP / logos
V1  main story
T1  captions
T2  hook + CTA text
A1  voice
A2  music
A3  sfx
```

## 7. Export

Settings: <run `scripts/export_plan.py <platform>` and paste the result>

```
Canvas      :
FPS         :
Bitrate     :
Codec       :
Filename    :
```

## 8. Risks

- <e.g. "client footage is 720p; will warn before upscaling">
- <e.g. "music licence pending">
- <e.g. "delivery date is a public holiday">
