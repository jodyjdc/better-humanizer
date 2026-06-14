# Corpus provenance — social-media register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM social-media
prose. Only the derived statistics are committed; raw texts live in `raw/`
(gitignored). Reproduce: `python3 scripts/fetch_corpus.py --register social-media
--min-chars 250 --max-chars 2400 --min-sents 2` then `python3
scripts/build_reference.py --register social-media`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| Reddit | `webis/tldr-17` | Reddit posts (`content`) | <= 2017 | Webis-TLDR-17 (Völske et al. 2017); user posts collected pre-LLM |

Current build: 120 texts, cleaned and filtered to 250–2400 chars, >= 2 sentences
(social posts run short, so the sentence floor is relaxed).

## Why these are a sensible choice

- **Provably human.** Reddit submissions gathered in 2017, well before LLMs.
- **Register match.** Informal, first-person, conversational, opinion- and
  anecdote-driven; contractions and direct address are the norm.
- **License-clean for this use.** Standard public NLP dataset; we commit only
  aggregate statistics.

## What this register proves

This register inverts the formal ones hardest. Contraction tolerance is high (~4.5),
sentence rhythm is loose, and the things a "cleaner" would scrub — fragments, casual
asides, first person — are exactly what make it read human. Applying scientific- or
business-report rules here (formalize, de-contract, even out rhythm) is the maximal
over-correction failure.

## Limitations

Reddit only (not Twitter/X, forums, or chat); English; 2017 internet culture; the
TLDR-17 set skews toward posts long enough to have a summary, so the very shortest
social style (one-liners, pure slang) is under-represented. Add sources in
`fetch_corpus.py` `SOURCES["social-media"]` to broaden.
