# Register profile: social-media

Defines what "human" means for social-media prose (Reddit-style posts: informal,
first-person, opinion- and anecdote-driven). The rewriter uses this as its brief;
`scripts/stylo.py` enforces the numeric bands from
`corpus/social-media/reference-stats.json`, calibrated on real pre-LLM Reddit posts.
This register **inverts the formal registers hardest** — applying business- or
science-report rules here is the maximal over-correction failure.

## What human social-media writing actually looks like

- **Contractions everywhere.** The contraction ceiling is ~4.54. "aren't going to
  work", "you'll have to export it", "won't be recalculating". Their absence reads
  like a press release, not a person.
- **Informal first person and direct address.** "Sorry buddy", "Imagine it's 1992",
  "Can you really see that?" The writer talks to the reader and from the self.
- **Fragments and casual asides.** "And it is sized the same as your text." "hey
  presto!" Parentheticals, trailing thoughts, sentences that start with "And" or
  "Or". People interrupt themselves and don't tidy it up.
- **Loose rhythm.** Sentence length runs 13–27 words with wide variation
  (cv 0.32–0.88) — a short jab next to a rambling explanation. Some exclamation is
  natural (ceiling 0.67), but em dashes are rare (ceiling 0.10), the lowest of the
  new registers; this register reaches for casual punctuation, not the literary dash.
- **Opinion and anecdote.** A take, a personal story, a "this is their screw up"
  judgment. Voice and stance are the whole point.

## Generation guidance (for the rewriter)

- **Keep it informal.** Use contractions, keep first person, keep the direct address
  to the reader. Do not raise the register.
- Keep fragments, casual asides, and sentences that open with "And" / "Or" / "But".
- Vary sentence length on purpose; do not even out the rhythm into smooth prose.
- Keep the opinion and the anecdote. A real reaction beats neutral summary here.
- Prefer plain, casual words. Cut delve, leverage, robust, seamless, underscore.

## Tell priority for this register (fix these first)

1. Corporate polish and over-formalization: smoothing casual phrasing into
   marketing-deck prose, de-contracting, raising the register.
2. Signposting: "Let's dive in", "In this post, I'll break down", "Here are the key
   takeaways."
3. Forced structure: turning a rambling personal take into headed sections, bullet
   lists, and a tidy conclusion it never had.
4. AI vocabulary ("robust", "seamless", "leverage"), generic upbeat conclusions,
   sycophancy ("Great question!").

## NOT tells here (do NOT remove)

Contractions. Fragments. Casual asides and parentheticals. Lowercase and loose
punctuation. First person, direct address, opinion, and anecdote. Wide sentence-length
variation. The calibrated bands treat all of these as in-band.

## Anti-over-correction rule

The failure mode here is the maximal one: "cleaning up" a Reddit post into a
corporate blog by formalizing the tone, de-contracting, deleting the fragments and
asides, evening out the rhythm, and bolting on structure. That is the opposite of
human for this register — the casual tone and fragments *are* the register, and the
bands prove it (contractions ~4.54, loose cv, near-zero em dashes). Match the
social-media band. If `stylo.py` flags a contraction rate near the floor or a
flattened rhythm, you over-corrected — put the casual voice back.
