# Register profile: spontaneous

Defines what "human" means for spontaneous / colloquial prose (blog, forum,
personal email, opinion). The rewriter uses this as its brief; `scripts/stylo.py`
enforces the numeric bands from `corpus/spontaneous/reference-stats.json`.

## What human spontaneous writing actually looks like

- **Uneven rhythm.** Sentence length varies a lot (high `sentence_length_cv`). A
  three-word sentence next to a thirty-word one. AI prose clusters around one mid
  length; humans do not.
- **Contractions by default** (don't, it's, I'd). Their absence reads stiff.
- **Fragments and asides.** Parentheticals, the occasional dash, trailing
  thoughts. People interrupt themselves.
- **Mild redundancy and loose structure.** Real writing circles back, repeats a
  word, leaves an end untied.
- **A point of view.** First person, opinions, mixed feelings, the honest "I don't
  know."
- **Concrete, hard-to-fabricate detail.** A specific place, a real number, a weird
  quote. Keep these; never round them off.

## Generation guidance (for the rewriter)

- Use `is / are / has`. Do not dodge the copula with "serves as / stands as".
- Vary sentence length on purpose. Put a short one right after a long one.
- Allow ONE em dash and ONE rule-of-three triad where it is natural. Do not ban
  them (see anti-over-correction).
- First person is fine. A real reaction beats neutral reporting.
- Keep every concrete detail from the source.
- Prefer plain words. Cut delve, leverage, tapestry, underscore, pivotal, vibrant.

## Tell priority for this register (fix these first)

1. Significance inflation (#1), -ing padding (#3), AI vocabulary (#7) — the
   loudest tells here.
2. Copula avoidance (#8), rule-of-three overuse (#10), negative parallelism (#9).
3. Signposting (#28), sycophancy (#22), collaborative artifacts (#20), generic
   upbeat conclusions (#25).

## Acceptable in moderation (do NOT zero out)

One em dash. A single triad. One exclamation. A casual/formal register mix. These
occur in real human spontaneous writing, and the bands expect them at nonzero
rates.

## Anti-over-correction rule

Zero em dashes, flat sentence rhythm (`sentence_length_cv` below floor), or zero
contractions are **themselves tells**: they signal a machine scrubbing, not a
person writing. Aim for the human band (floor AND ceiling), never the extreme. If
`stylo.py` returns a `self_tell_flag`, you over-corrected — add the human texture
back.
