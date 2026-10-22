# Skills

Reusable [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
built from reference material in this repo. Each skill is a folder with a `SKILL.md` and optional
`references/`, `assets/`, and `scripts/` that the agent loads only when it needs them.

## Available

| Skill | What it does | Built from |
|---|---|---|
| [`capcut-desktop-mastery`](capcut-desktop-mastery/SKILL.md) | End-to-end CapCut Desktop editing: setup → cut → sound → text → effects → colour → export. English + Tamil explanations. | [Mastering CapCut (Basic to Advanced) தமிழ் 2025](https://youtu.be/BSTuxpc9FU0) by Prakash |

## Structure

```
skills/<skill-name>/
  SKILL.md              # frontmatter (name, description) + instructions  <- <500 lines
  references/*.md       # deep material, loaded on demand
  assets/*.md           # templates and checklists the agent copies
  scripts/*.py          # deterministic helpers the agent runs with bash
```

The `description` in the frontmatter is the only thing loaded at startup, so it has to state
both **what** the skill does and **when** to use it. The body is loaded only when the skill
matches the user's request.

## Using a skill

**Claude Code / any filesystem-based agent**

```bash
# project-level
mkdir -p .claude/skills && cp -r skills/capcut-desktop-mastery .claude/skills/

# or user-level, available in every project
cp -r skills/capcut-desktop-mastery ~/.claude/skills/
```

**claude.ai / API** - zip the skill folder (the zip must contain `SKILL.md` at its root) and
upload it in Settings → Capabilities → Skills, or via the Skills API.

Then just ask: *"Help me cut this 3-minute interview into a 45-second Reel in CapCut."*
The skill triggers on its own.

## Run the helper scripts directly

```bash
cd skills/capcut-desktop-mastery/scripts
python3 -m unittest test_export_plan -v     # 23 tests
python3 export_plan.py reels --duration 0:45
python3 export_plan.py --list
```

No third-party dependencies; Python 3.8+.

## Adding a new skill

1. `mkdir -p skills/<name>/{references,assets,scripts}`
2. Write `SKILL.md` with `name` (lowercase-hyphens, ≤64 chars) and a `description` that says
   what + when (≤1024 chars).
3. Keep the body under 500 lines; push depth into `references/` and link to it.
4. Only add a script when the operation is deterministic and easy to get wrong by hand.
5. Test the script, and test the skill by asking an agent to use it on a real task.
