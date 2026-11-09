# Claude for Open Source — Eligibility Check: `victorvika/vjk_18`

Checked against: https://www.anthropic.com/claude-for-oss-terms
Checked on: 2026-11-09

---

## TL;DR (முடிவு)

**இந்த repo இப்போ terms-ஐ meet பண்ணல.** ஆனா இதுவே பெரிய பிரச்சனை இல்ல — ஏன்னா இந்த program-ல
**repo-வோட size அல்ல criteria**; criteria எல்லாமே **உங்களோட (applicant-ஓட) OSS activity**-ஐ பத்தி.
அந்த அளவுக்கு public GitHub-ல verify ஆகுற activity இப்போ இல்லை.

**இப்போ apply பண்ண வேண்டாம்.** முன்னாடி நல்லா build பண்ணிட்டு apply பண்றது தான் சரியான வழி
(கீழ Section 4-ல plan இருக்கு).

---

## 1. இந்த repo-வோட தற்போதைய நிலை

| விஷயம் | நிலை |
|---|---|
| Commits | 2 மட்டும் (2018 initial commit, 2019 README) |
| Files | `README.md` மட்டும் (content: `<script>alret('1')</script>`) |
| Star / fork | 1 star / 0 forks |
| Dependents | 0 |
| License | **இல்லை** (இப்போ சேர்த்திருக்கேன் — கீழ பாருங்க) |
| Package registry-ல publish ஆனது | இல்லை (npm / PyPI / crates.io-ல எதுவும் இல்லை) |
| External contributors | 0 |
| PRs / issues | 0 |

அதாவது: இது ஒரு **code இல்லாத, யாரும் depend பண்ணாத, license இல்லாத** near-empty repo.

> **Note:** 2026-11-07-ல `vjk_18`-க்கு push event இருந்தது ஆனா `master`-ல கடைசி commit இன்னும்
> 2019-தான். அந்த push-எல்லாம் remote-ல இருக்கிற `arena/*` branches-ல மாட்டிக்கிச் சிக்கியிருக்கு —
> `master`-க்கு merge ஆகல. அதனால GitHub-ஓட பார்வைக்கு இது 2019-ல நின்ன இடத்துலேயே இருக்கு.

---

## 2. Terms Section 2 — Criteria vs. உங்கள் நிலை

### Maintainer Track (2.1) — எந்த ஒரு bullet-உம் match ஆகல

| Criteria | தேவை | உங்க நிலை |
|---|---|---|
| Dependent repositories | ≥ 500 | 0 |
| Dependent packages | ≥ 100 | 0 |
| Monthly downloads (எல்லா packages சேர்த்து) | ≥ 200,000 | 0 |
| Foundation / language project-ல maintainer | ஆம் | இல்லை |
| 12 மாசத்துல merge ஆன PRs (வேற யாரோட repo-ல) | ≥ 100 | **0** (total merged PRs = 0) |
| ஒரு repo-ல 12 மாசத்துல unique external contributors | ≥ 20 | 0 |
| OpenSSF criticality score | ≥ 0.4 | 0 (score இல்லை) |

### Ecosystem Impact Track (2.2) — Discretionary

Ecosystem இது இல்லாம இருக்க முடியாத அளவுக்கு critical-ஆன project-ஐ maintain பண்றவங்களுக்கு.
`vjk_18` அதுவும் இல்லை. வேற எந்த repo-வும் (உங்களோடவை எல்லாமே forks) அந்த அளவுக்கு இல்லை.

### General Requirements (2.3)

| தேவை | நிலை |
|---|---|
| Natural person, 18+ | ✅ (நீங்கள்) |
| Claude.ai available country-ல resident (India) | ✅ |
| GitHub account ≥ 2 ஆண்டு பழையது, good standing | ✅ 2018-03-ல இருந்து |
| **கடந்த 90 நாள்ல public OSS activity (commit / PR / review / release)** | ⚠️ borderline — forks & arena branches push மட்டும்; merged PR, review, issue எதுவும் இல்லை |
| **OSI-approved license-ல distribute ஆகுற project-ஐ maintain/contribute பண்றது** | ⚠️ **ஒரு repo-லயும் license இல்லை** (21 repos-ல 8-க்கு மட்டும் upstream license, அவை எல்லாம் fork) |
| Anthropic employee / family இல்லை | ✅ |

---

## 3. Repo-ல நான் பண்ணினது (`arena/58948aa5-vjk-18` branch)

1. **`LICENSE` சேர்த்தேன் — MIT (OSI-approved).** Section 2.3-ஓட "at least one project distributed
   under an OSI-approved license" requirement-க்கு இது minimum. GitHub-ல repo page-லயும் license
   badge வரும்.
2. **`README.md`-ல இருந்த `<script>alret('1')</script>`-ஐ நீக்கினேன்.** இது (a) broken JS (typo: `alret`),
   (b) GitHub-ல README-ல inline script render ஆகாது, (c) ஒரு repo-வோட public face-ஆ இது தேவையில்லாத
   risk. பதிலா clean README + license section போட்டிருக்கேன்.

⚠️ **இது மட்டும் போதாது.** License இருப்பதால repo OSI-approved ஆகும், ஆனா eligibility வராது.
Terms-ல explicit-ஆ சொல்லியிருக்கு: criteria "minimum thresholds for consideration" — meeting them
doesn't entitle you to a subscription, மேலும் *"Anthropic evaluates the substance of the underlying
activity"*.

---

## 4. Eligibility வர எப்படி build பண்றது (recommended path)

Terms-ல *"artificially inflated eligibility metrics … contribution-graph padding"* = disqualification
(Section 7) — அதனால **numbers-ஐ fake பண்ண வேண்டாம்**, உண்மையான contribution மட்டும்.

Priority order (கஷ்டம் குறைவு → அதிகம்):

1. **Real open-source contribution** — நீங்கள் use பண்ற tools (Claude Code plugins, revers-engineering
   tooling, TradingView libs — நீங்கள் fork பண்ணியவை)ல genuine bug fixes / PRs. Target: **12 மாசத்துல
   100 merged PRs** (Maintainer Track bullet 4). இது தான் realistically அடையக்கூடிய ஒரே numeric
   threshold. Quality > quantity — typo PRs discount ஆகும்.
2. **உங்களோட சொந்த repo-வை உண்மையா build பண்ணுங்க** — `master`-க்கு merge பண்ணி, docs, release,
   CI, issues template எல்லாம் வச்சு, external contributors-ஐ attract பண்ணுங்க. **20 unique external
   contributors** (bullet 5) அல்லது npm-ல publish பண்ணி **200k monthly downloads** (bullet 2).
3. **License பிரச்சனையை சரி பண்ணுங்க** — நீங்கள் fork பண்ண 13 repos-க்கு upstream license இல்ல
   (Dr.clicker, jailbreaks, TradingView-API, Autorize). இவை உங்களோட maintain-க்கு கீழ இருந்தா,
   upstream LICENSE-ஐ fork-ல சேர்க்கணும், இல்லைன்னா அவை OSS project-ஆ count ஆகாது.

### Timeline expectation

இப்போ apply பண்ணா — eligibility fail, decision final, appeal இல்லை (Section 3.3). Re-apply
restriction இல்லை, ஆனா benefit period-க்கு அப்புறம் தான் re-apply பண்ணலாம் (Section 4.3).
அதனால **6+ மாசம் build பண்ணிட்டு apply பண்றது** தான் sensible.

---

## 5. இப்போ apply பண்ணணும்னா — application-ல என்ன எழுதலாம்

உண்மையா "500 dependents" இல்லைன்னா அதை எழுதாதீங்க — Section 7-ல fraud/revocation. Ecosystem Impact
Track-ல honest-ஆ இதை மாதிரி எழுதலாம் (நீங்கள் இவற்றை build பண்ணிட்டா):

> "I maintain <repo> (MIT, N stars), a <short description> that <N> projects depend on. In the past
> 12 months I merged N pull requests into <upstream repos> fixing <specific issues>, and reviewed N
> contributions from external contributors to <repo>."

---

## 6. Sources

- Terms: https://www.anthropic.com/claude-for-oss-terms (Sections 2.1, 2.2, 2.3, 3.2, 4.3, 7)
- Apply: https://claude.com/contact-sales/claude-for-oss
- GitHub state: `repos/victorvika/vjk_18`, `users/victorvika`, search API (merged PRs = 0),
  npm registry (0 packages), PyPI (404)
