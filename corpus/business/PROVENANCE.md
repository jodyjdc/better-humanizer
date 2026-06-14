# Corpus provenance — business register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM business email
prose. Only the derived statistics are committed; raw texts live in `raw/`
(gitignored). Reproduce: `python3 scripts/fetch_corpus.py --register business
--min-chars 200 --max-chars 2400 --min-sents 3` then
`python3 scripts/build_reference.py --register business`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| AESLC | `Yale-LILY/aeslc` | Enron employee emails (`email_body`) | ~2000–2002 | Annotated Enron Subject Line Corpus (Zhang & Tetreault 2019); the underlying Enron email set predates LLMs by ~two decades |

Current build: 120 texts, cleaned and filtered to 200–2400 chars, >= 3 sentences.

## Why these are a sensible choice

- **Provably human.** The Enron corpus is one of the most-studied real-email
  datasets; it predates generative LLMs by ~20 years.
- **Register match.** Internal business email: salutations and sign-offs, action
  items, references to attachments/agreements, polite directives.
- **License-clean for this use.** Standard public NLP research dataset; we commit
  only aggregate statistics.

## What this register proves

A useful surprise from the data: internal business email is **conversational**, not
formal-report prose. Contraction tolerance is high (ceiling ~5.8, the highest of any
register) and em dashes appear — because real colleagues write "I'll", "can't",
"we're" to each other. A naive "business = stiff and formal" rule would over-correct
genuine email into something less human, not more. The bands capture the real
register: semi-formal, directive, contraction-friendly.

## Limitations

Single organization (Enron), US English, early-2000s corporate culture; internal
email only (not press releases, reports, or marketing copy — those are different
business sub-registers). Add sources in `fetch_corpus.py` `SOURCES["business"]` to
broaden.
