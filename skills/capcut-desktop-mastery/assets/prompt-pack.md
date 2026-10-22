# Prompt pack - copy, paste, fill the brackets

Prompts for Gemini / ChatGPT / Claude that produce output a renderer (or a human in CapCut)
can actually execute. Vague prompts produce vague edits.

---

## 1. The brief (send this first, with the clips)

```
You are a senior video editor. Plan an edit, do not describe editing theory.

Footage: [upload files, or paste the transcript with timestamps]
Target: [Reels 9:16, 45 seconds, 30 fps]
Audience: [salon owners in Coimbatore]
Goal: [book a colour consultation]
Must-keep: [00:31-00:41 "three hours for a full set"], [00:52 product shot], [CTA line]
Style: [fast cuts, hard cuts only, one zoom at the reveal, Tamil captions]
Constraints: [no music over dialogue, no effects that CapCut free tier cannot do]

Reply with exactly three blocks and nothing else:
1. HOOK - three options, each under 8 words
2. SHOT LIST - table: order | source | in | out | duration | why this shot
3. TOTAL RUNTIME - the sum, and whether it fits [45s]
```

Why it works: it forbids theory, fixes the output shape, and makes the model justify each cut.

---

## 2. Shot list → EDL JSON (for `scripts/edl_render.py`)

```
Convert the shot list above into an EDL JSON for the renderer.

Rules:
- Use this schema exactly: output, canvas{width,height}, fps, clips[{source,in,out,speed,volume,label}], music{source,volume,duck}, captions{srt,font,font_size}, export{crf,preset}, loudness
- Times as "M:SS.s", e.g. "0:04.2"
- Canvas 1080x1920, fps 30
- No fields outside the schema
- No commentary, no markdown fences, JSON only

If a shot has no usable audio, set volume to 0.
```

Then validate:

```bash
python3 scripts/edl_render.py plan.json --validate-only
```

---

## 3. Transcript → captions

```
Clean this transcript into caption lines.

Rules:
- Maximum [32] characters per line, Tamil + English mix
- Break at natural pauses, never mid-phrase
- Keep brand names exactly: [CapCut, Growth Secret]
- Fix ASR errors, but do not paraphrase
- Output one caption per line, no timestamps

[transcript]
```

Then time them:

```bash
python3 scripts/make_srt.py captions.txt --duration 0:45 --lang ta --out captions.srt --check
```

---

## 4. Long video → 5 vertical clips

```
Here is a [22]-minute interview transcript with timestamps.

Find 5 moments that work as standalone vertical clips of 30-60 seconds.

For each: start timecode, end timecode, the hook line, and one sentence on why it stands alone.
Rank by predicted retention, best first.
Skip anything that needs setup to make sense.
```

This is where AI is genuinely excellent - it reads 22 minutes in seconds.

---

## 5. Audit an AI edit before you render

```
Here is the shot list and here is the transcript.

Check for:
1. Any cut that lands mid-word
2. Any claim in the captions that is not supported by the transcript
3. Total runtime vs the 45 second target
4. Shots that appear twice
5. A missing CTA

List problems as a numbered list. If there are none, say "clean".
```

---

## 6. Tamil-specific caption cleanup

```
Fix these Tamil captions.

Rules:
- Keep modern spoken Tamil (Tanglish is fine) - do not convert to formal written Tamil
- Do not translate English technical terms: CapCut, keyframe, export
- Split any line longer than 32 characters
- Keep the meaning identical

[lines]
```

---

## 7. When the AI says it cannot edit video

It is telling the truth. Reframe:

```
You do not need to render anything. Produce the plan and the EDL JSON.
A script will render it locally.
```

This single sentence converts "I can't edit videos" into a usable deliverable.

---

## Anti-patterns

| Bad prompt | Why it fails | Fix |
|---|---|---|
| "Edit this video" | No target, no constraints; you get generic advice | Use prompt 1 with the filled brief |
| "Make it viral" | Unfalsifiable, produces clichés | "Hook must survive muted viewing, first 1.5 s" |
| "Add cool effects" | Effects with no purpose | "One motion idea for the whole clip, name it" |
| Uploading a 4K 12-minute file | Rejected or heavily downscaled | Send transcript + timestamps instead |
| Accepting an edit plan with no `why` | Cannot audit it | Require a reason column |
