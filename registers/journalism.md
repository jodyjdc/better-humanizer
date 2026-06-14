# Register profile: journalism

Defines what "human" means for hard-news prose (wire and newspaper articles:
inverted-pyramid ledes, source attribution, sober reporting). The rewriter uses
this as its brief; `scripts/stylo.py` enforces the numeric bands from
`corpus/journalism/reference-stats.json`, calibrated on real pre-LLM CNN/DailyMail
news copy. This is the **unexcitable** register: it reports, it does not emote.

## What human journalism actually looks like

- **Near-zero exclamation.** The exclamation ceiling here is 0.07 — effectively
  none. News states; it does not exclaim. Exclamation in a news sentence is a loud
  tell.
- **Almost no sentence-opening transitions.** The transition-opener ceiling is 0.02,
  the **lowest of all seven registers**. News doesn't write "Moreover," "Furthermore,"
  "In addition," — it just reports the next fact.
- **Heavy source attribution.** "officials said", "according to Leifman", "he told
  Reuters", "told the Associated Press". Attribution is the backbone of the register;
  it marks who claims what and is human here, not filler to be cut.
- **Inverted-pyramid lede and structure.** The most important facts first, often a
  dateline ("LONDON, England (Reuters) --"), then supporting detail across multiple
  short paragraphs. The em-dash ceiling (1.19) is elevated partly by this dateline
  convention; genuine asides also use it.
- **Short declarative sentences, sober neutral tone.** Sentence length runs 16–25
  words with controlled variation (cv 0.43–0.72). Quotes carry the emotion; the
  reporter's own prose stays flat and factual.

## Generation guidance (for the rewriter)

- **Keep every attribution.** "said", "according to", "told CNN" stay verbatim —
  they are not redundancy to trim.
- Preserve the lede order, the dateline, and the multi-paragraph structure.
- Keep the tone flat and neutral. Do not inject voice, energy, or commentary into
  the reporter's sentences; let quotes do the feeling.
- Keep quotes exact. Keep every name, place, figure, and date.
- Do not add sentence-opening transitions — the band expects almost none.

## Tell priority for this register (fix these first)

1. Editorializing adjectives and opinion creep: "shocking", "stunning",
   "heartbreaking", "remarkable" inserted into the reporter's own voice.
2. Era-framing and significance openers: "In today's world", "In an age of", "Now
   more than ever", "marking a pivotal moment".
3. Exclamation (the ceiling is 0.07 — treat any exclamation in narration as a tell).
4. Sentence-opening transitions ("Moreover," "Furthermore,") and generic upbeat
   conclusions.

## NOT tells here (do NOT remove)

Source attribution ("said", "according to"). The dateline. Short declarative
sentences. The flat, sober, neutral tone. Multi-paragraph inverted-pyramid
structure. Exact quotes and figures. The calibrated bands treat all of these as
in-band.

## Anti-over-correction rule

The failure mode here is "livening up" a news report: adding voice, excitement, and
editorial color, stripping attributions as "redundant", and dropping in transitions
to make it "flow". That destroys the register — news is deliberately unexcitable,
and the bands prove it (exclamation 0.07, transition-openers 0.02, both the lowest in
the project). Match the journalism band: keep the attributions and the flat tone. If
`stylo.py` flags an exclamation rate above the ceiling, you injected feeling the
register does not carry — take it back out.
