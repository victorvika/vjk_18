# Tamil glossary for CapCut

Use this when explaining in Tamil. The rule from `SKILL.md` still applies:
**UI labels stay in English**, explanations go Tamil.

| English (UI) | Tamil | Tanglish | One-line explanation |
|---|---|---|---|
| Timeline | நேரக்கோடு | timeline | கீழே காட்சிகளை அடுக்கும் இடம் |
| Track | தடம் | track / layer | ஒரு வரிசை; V1 பிரதான காட்சி, V2 மேலடுக்கு |
| Clip | காட்சித் துண்டு | clip | ஒரு வீடியோ/ஆடியோ துண்டு |
| Split | வெட்டு | split / cut | playhead இருக்கும் frame-ல இரண்டாக வெட்டு |
| Trim | ஓரம் சுருக்கு | trim | துண்டின் ஆரம்ப/இறுதி ஓரத்தை இழு |
| Ripple delete | இடைவெளியை மூடு | gap close | நீக்கிய பின் ஏற்படும் இடைவெளியைச் சுருக்கு |
| Transition | மாற்றம் | transition | இரண்டு காட்சிகளுக்கு நடுவேயான மாறுதல் |
| Keyframe | சாவிச் சட்டகம் | keyframe | ஒரு நேரத்தில் ஒரு மதிப்பைப் பிடித்து வைப்பது |
| Frame rate | சட்டக வேகம் | fps | ஒரு வினாடிக்கு எத்தனை படங்கள் |
| Resolution | படிமத் தெளிவு | resolution | 1080p, 4K போன்ற படத்தின் அளவு |
| Bitrate | தரவு வேகம் | bitrate | வினாடிக்கு எவ்வளவு தரவு சேமிக்கப்படுகிறது |
| Aspect ratio | வடிவ விகிதம் | ratio | 16:9, 9:16, 4:5 |
| Crop | வெட்டிச் சுருக்கு | crop | காட்சியின் ஒரு பகுதியை மட்டும் வைத்திரு |
| Mask | மறைப்பு | mask | ஒரு பகுதியை மட்டும் காட்டு, மீதியை மறை |
| Chroma key | நிற அடிப்படை நீக்கம் | green screen | பச்சை நிறத்தை நீக்கி பின்னணி மாற்று |
| Rotoscoping | பொருள் வெட்டு | roto | ஒரு பொருளை மட்டும் தனியாகப் பிரித்தெடு |
| Opacity | ஒளிபுகாநிலை | opacity | எவ்வளவு அடர்த்தி/வெளிப்படைத்தன்மை |
| Blend mode | கலப்பு முறை | blend | இரண்டு அடுக்குகளை எப்படிக் கலக்கிறது |
| Volume | ஒலி அளவு | volume | ஒலியின் சத்தம் |
| Ducking | இசைத் தாழ்வு | ducking | பேச்சின் போது இசையைத் தானாகக் குறைப்பது |
| Fade | மெல்ல மறைதல் | fade | மெதுவாக ஒலி/படம் வருவது அல்லது போவது |
| Caption | வசன வரி | caption | பேச்சுக்கு ஏற்ற எழுத்து |
| Hook | தொடக்க ஈர்ப்பு | hook | முதல் 2 வினாடியில் பார்வையாளரைப் பிடிப்பது |
| B-roll | இடைக்காட்சி | B-roll | பேச்சுக்கு நடுவே காட்டும் துணைக் காட்சி |
| Rough cut | முதல் வெட்டு | rough cut | கதையை மட்டும் சரிசெய்யும் நிலை |
| Fine cut | இறுதி வெட்டு | fine cut | நேரத்தையும் தாளத்தையும் சரிசெய்யும் நிலை |
| Export | ஏற்றுமதி | export | இறுதி கோப்பை உருவாக்கு |
| Render | பதிவாக்கம் | render | கணினி காட்சிகளைக் கணக்கிட்டு பதிவு செய்வது |
| Proxy | மாற்றுப் பதிப்பு | proxy | மெதுவான கணினிக்கு இலகுவான நகல் |

## Keep these in English, always

`Split` · `Keyframe` · `LUT` · `PIP` · `Chroma key` · `Mask` · `Blend` · `Auto captions` · `Export` · `Render`

Why: the user has to physically find these words on screen. Translating them makes the
instruction unusable.

## Sentence templates that actually help

- **Giving a step**
  "Clip-a select pannunga → வலது panel-la **Video** tab → **Mask** → Rectangle."
  *("Select the clip → right panel → Video tab → Mask → Rectangle.")*

- **Explaining a bug**
  "Mask edge flicker aagudhu-na, அது AI mask தெரியாத subject. Strength-அ குறைச்சு, feather 5% கொடுங்க."
  *("If the mask edge flickers, the AI is unsure about the subject. Lower strength, add 5 % feather.")*

- **Explaining a value**
  "Beauty 20-30 % போதும். அதுக்கு மேல போனா தோல் plastic மாதிரி ஆகும்."
  *("20-30 % beauty is enough. Above that, skin looks plastic.")*

- **Correcting a habit**
  "Cut-க்கு முன்னாடி 3 frame இடைவெளி விடுங்க. இல்லைனா பேச்சு துண்டிக்கப்பட்ட மாதிரி கேக்கும்."
  *("Leave 3 frames before the cut, otherwise speech sounds chopped.")*

## Tone

- Talk like a senior editor sitting next to them, not like a manual.
- Use "நீங்க / பண்ணுங்க" (respectful plural), not "நீ / பண்ணு".
- Tanglish is fine when the user writes Tanglish. Tamil script is fine when they write Tamil script.
  Mirror them; do not switch registers mid-answer.
- Short sentences. One idea per line. Editing instructions are read while clicking, not studied.
