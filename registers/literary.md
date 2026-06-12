# Register profile: literary

Defines what "human" means for literary / creative prose (fiction, narrative
essay, artistic writing). The rewriter uses this as its brief; `scripts/stylo.py`
enforces the bands from `corpus/literary/reference-stats.json`, calibrated on real
human short fiction. This register has the **highest tolerance** for the very
devices the other registers (and the original humanizer) treat as tells.

## What human literary writing actually looks like

- **Deliberate rhythm variation.** The highest `sentence_length_cv` of any register.
  A two-word sentence slammed against a long, winding one. Pacing is the craft.
- **Em dashes, semicolons, ellipsis, fragments.** All staples. The em-dash ceiling
  here is ~13x the casual rate. Fragments are sentences when the writer says so.
- **Figurative language that is specific and load-bearing.** A real image does
  work: it tells you something exact you could not get literally.
- **Voice, dialogue, contractions, sensory concrete detail, subtext.** First person,
  present tense, an unreliable narrator: all fair game.

## Generation guidance (for the rewriter)

- **Preserve the voice and the figuration.** Do not flatten prose into a report.
- Vary sentence length hard, on purpose. Keep the short punches and the long runs.
- Keep em dashes, semicolons, ellipses, and fragments where they serve the rhythm.
- Keep dialogue and contractions natural.
- Replace vague images with specific ones; never delete imagery wholesale.

## The hard distinction: genuine vs hollow figuration

This is the only register where the main tell is *quality of imagery*, not its
presence. Cut the hollow AI version; keep (or sharpen) the real thing.

- **Hollow (cut it):** generic, abstract, decorative metaphor that means nothing
  precise. "a tapestry of emotions", "a symphony of gray", "a testament to the
  sky's sorrow", "the dance of light", aphorism formulas ("X is the language of Y",
  "the soul is but a mirror"), manufactured staccato drama, rule-of-three filler,
  "not just walking, he was becoming".
- **Genuine (keep / sharpen):** a specific, surprising, concrete image earning its
  place. "he said her name wrong on purpose"; "the scrubbed, sodium-lit emptiness
  between last call and the first delivery trucks". You could not replace it with a
  plain sentence without losing information.

## Tell priority for this register (still fix)

Hollow figuration and aphorism formulas (above), inflated symbolism, manufactured
punchlines / staccato drama, rule-of-three padding, generic profundity. These are
AI tells even in fiction.

## NOT tells here (do NOT remove)

Em dashes. Semicolons. Ellipsis. Fragments. Specific metaphor and imagery. Wildly
varied sentence length. First person, present tense, dialogue, contractions. The
calibrated bands treat all of these as in-band.

## Anti-over-correction rule

The failure mode here is the worst of the three: "humanizing" fiction into a police
report by stripping dashes, evening out the rhythm, deleting every image, and
killing the voice. That is not more human, it is dead. Match the literary band,
which has the highest tolerance for craft punctuation and rhythm variation in the
whole project. If `stylo.py` flags `sentence_length_cv` below floor, the prose has
been flattened: put the pacing back.
