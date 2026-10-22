# Using this skill with Gemini / ChatGPT / Claude

Straight answer first, then the workflow.

## What an AI chat can and cannot do with video

| Capability | ChatGPT | Gemini | Claude (with this skill) |
|---|---|---|---|
| Watch/understand an uploaded clip | Yes (short files) | Yes (strong, long context) | Yes, if the agent has file access |
| Cut clips on a timeline like CapCut | No GUI, ever | No GUI, ever | No GUI, ever |
| Run ffmpeg on your files | Partly (Code Interpreter, size/time limits) | No, not in the consumer app | Yes, if it has bash |
| Produce a precise edit plan | Yes, very good | Yes, very good | Yes |
| Burn captions, mix music, render MP4 | Only inside Code Interpreter | No | Yes, via `scripts/edl_render.py` |
| Match CapCut's LUT/effect library exactly | No | No | No |

**Conclusion:** an AI chat is the **director**, not the editor. It decides what gets cut and in
what order. Something has to execute that decision - either you in CapCut, or a render script.

There is no way around this: neither Gemini nor ChatGPT will hand back a finished, frame-accurate
CapCut project file. CapCut has no documented EDL/XML import, so no AI can generate one for it.

## Installing this skill in Gemini / ChatGPT

Both products can hold the skill as **reference knowledge**. Then the model follows this
workflow instead of giving generic editing advice.

### Gemini - a Gem

1. `gemini.google.com` → **Gems** → **New Gem**.
2. Paste the text of `SKILL.md` into the instructions box.
3. Attach `references/edl-format.md`, `references/effects-cookbook.md`, `assets/prompt-pack.md`
   as knowledge files.
4. Save as e.g. "CapCut Director".
5. Chat with it, attach your clips, and ask for a shot list + EDL.
   Gemini cannot run ffmpeg, so you execute route A or hand the EDL to a machine that can.

### ChatGPT - a Custom GPT

1. `chatgpt.com` → **Explore GPTs** → **Create**.
2. Instructions: paste `SKILL.md`.
3. Knowledge: upload `SKILL.md`, `references/*.md`, `assets/edl.example.json`
   (20 files max, so drop the less relevant references).
4. Capabilities: enable **Code Interpreter** if you want it to attempt a rough render
   (short clips only, upload size limits apply).
5. Ask for the shot list + EDL, same as above.

### Claude - project or Skill

- **Project knowledge:** upload the whole skill folder content into a project.
- **Claude Code / agent with bash:** copy the folder to `~/.claude/skills/` and it triggers
  automatically. This is the only setup where the edit is *actually rendered*, because the
  agent can run `scripts/edl_render.py`.

### The one-sentence test

After installing, ask:

> "45-second vertical Reel from these clips, Tamil captions, hard cuts only. Give me a shot list
> and a plan.json for the renderer."

If the model returns a table with timecodes plus a valid JSON block, the skill is loaded correctly.
If it returns a paragraph about "the importance of storytelling", it is not.

## The three workable setups

### Setup A - AI plans, you cut in CapCut (best quality, most control)

```
you ──clips + brief──> AI chat ──shot list + EDL──> you ──> CapCut ──> MP4
```

1. Upload the clips (or describe them with timestamps) to Gemini/ChatGPT.
2. Ask for a **shot list** and an **EDL JSON** (schema in `edl-format.md`, prompt in
   `assets/prompt-pack.md`).
3. Follow the shot list in CapCut. The EDL is the paper edit: exact in/out points, order, speed.
4. Use `scripts/export_plan.py` for the export numbers.

Best for: client work, anything with colour grading or complex effects.

### Setup B - AI plans, script renders (fastest, fully automated)

```
you ──clips──> AI chat ──plan.json──> you run edl_render.py ──> MP4 ──> tweak in CapCut if needed
```

1. AI produces `plan.json` (an EDL) + `captions.srt` (via `make_srt.py`).
2. Run:
   ```bash
   python3 scripts/edl_render.py plan.json --workdir work
   ```
3. The script trims, re-frames to the canvas, applies speed changes, concatenates, ducks the
   music under the voice, burns captions, and encodes a platform-ready MP4.
4. Open the MP4 in CapCut only if you want a grade, an effect, or a fancy transition.

Best for: talking-head reels, podcast clips, batch cutdowns, and anything where you already
know the edit and just need it rendered.

### Setup C - Claude Code / agent with bash (the full loop)

Give the agent this skill and the footage folder. It can read the clips' metadata, propose a
plan, render it, watch the result, and iterate. That is what `edl_render.py` exists for.

## Reality checks to give the user

- **"Can ChatGPT edit my video?"** It can plan the edit perfectly and, in Code Interpreter,
  render a rough cut. It cannot use CapCut's effects, LUTs, or templates.
- **"Can Gemini edit my video?"** Gemini can watch and reason about it well, but it cannot output
  a video file. Ask it for a plan, then execute the plan.
- **"Will the AI pick good cuts?"** Only if you give it the transcript with timestamps or ask it
  to describe the footage shot by shot. Blind guessing produces generic edits.
- **Upload limits matter.** Long 4K files may be rejected or downscaled. For anything over
  ~5 minutes, send the transcript + a shot list instead of the video.

## What to give the AI (this is the part people get wrong)

Minimum viable brief:

```
1. Clips or transcript with timestamps
2. Target: platform, canvas, length
3. Audience + one-sentence goal
4. Must-keep moments (quotes, product shots, CTA)
5. Style reference ("fast cuts, no music, Tamil captions")
6. Output format: shot list + EDL JSON + SRT
```

Without #5 and #6 you get vague advice. With them you get something a script can execute.

## The handoff contract

Ask for exactly this, every time:

```json
{
  "shot_list": [
    {"order": 1, "source": "IMG_0142.mp4", "in": "0:04.2", "out": "0:09.8", "why": "hook - hands on the fabric"},
    {"order": 2, "source": "IMG_0145.mp4", "in": "0:31.0", "out": "0:34.5", "why": "proof - finished blouse"}
  ],
  "edl": { "...": "see edl-format.md" },
  "captions": "SRT text",
  "export": {"platform": "reels", "width": 1080, "height": 1920, "fps": 30}
}
```

The `why` field is not decoration. It is how you audit an AI edit in 30 seconds instead of
watching the whole thing twice.

## Where AI genuinely helps

- **Transcript-based rough cutting** - "cut everything that is not the answer to the question"
- **Hook writing** - 10 variants, pick one
- **Caption cleanup** - fix ASR errors, split lines, translate
- **Shot-list generation** from a long recording
- **Repurposing** - one 20-minute interview into 5 vertical clips with in/out points
- **QA** - paste the transcript and the caption file, ask what mismatches

## Where AI still fails

- Judging whether a cut *feels* right (rhythm, breath, comedy timing)
- Colour grading that matches a brand
- Anything requiring the viewer's gut reaction
- Frame-accurate comedy timing (it will be 4-6 frames off)

Say this out loud to the user instead of overselling.
