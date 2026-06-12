# Register profile: scientific

Defines what "human" means for scientific / academic prose (papers, abstracts,
technical reports). The rewriter uses this as its brief; `scripts/stylo.py`
enforces the numeric bands from `corpus/scientific/reference-stats.json`, which are
calibrated on real PubMed + arXiv abstracts and **invert** several spontaneous
expectations.

## What human scientific writing actually looks like

- **Passive voice is normal and often correct.** "Samples were collected", "it was
  observed that". Do not reflexively convert to active or invent an actor.
- **Hedging is precision, not weakness.** "may suggest", "is consistent with",
  "appears to", "to our knowledge". These encode the strength of a claim. Keep them
  exactly; removing them changes the science.
- **Nominalization and formal vocabulary.** "administration", "utilization",
  "characterization". Words like crucial, underscore, interplay, novel appear in
  real papers (the tell-rate ceiling here is ~3x the spontaneous one).
- **Longer, more uniform sentences.** Lower rhythm variation is human here. Do not
  force choppy short sentences for "voice".
- **Impersonal stance, zero contractions.** "We" in methods is fine; "I feel" is
  not. Contraction rate near zero is correct, not a tell.
- **Exact figures, citations, qualifiers.** Keep every number, p-value, sample
  size, and caveat.

## Generation guidance (for the rewriter)

- Preserve idiomatic passive voice. Do not add a fake "we" just to go active.
- Keep all hedges, qualifiers, and statistical caveats verbatim in meaning.
- Do not add contractions, personal anecdote, rhetorical questions, or punchy
  fragments.
- Vary sentence length only modestly; uniform cadence is acceptable.
- Keep every numeric result and citation.

## Tell priority for this register (still fix these)

Genuine AI-isms remain tells even in science:
1. Significance inflation ("stands as a testament", "a pivotal moment in the
   evolution of", "marking a paradigm shift").
2. Promotional language ("groundbreaking", "vibrant", "revolutionary").
3. Hollow -ing analyses ("highlighting the importance of", "underscoring the need").
4. Rule-of-three padding, generic upbeat conclusions, "challenges and future
   prospects" filler, signposting ("In this section, we will explore").

## NOT tells here (do NOT remove)

Passive voice. Hedging. Nominalization. Long, uniform sentences. Zero contractions.
Formal vocabulary, including crucial / underscore / interplay in moderation. These
are the scientific register, and the calibrated bands treat them as in-band.

## Anti-over-correction rule

The failure mode here is "humanizing" a paper into a blog: forcing active voice,
adding contractions and personal voice, chopping sentences, stripping hedges. That
reads *tampered*, not human, and it can change the claims. Match the scientific
band. The scorer enforces this automatically: against `corpus/scientific/`, zero
contractions and uniform rhythm are in-band and are NOT flagged as over-correction.
