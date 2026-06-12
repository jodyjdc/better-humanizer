# Corpus provenance — spontaneous register

`reference-stats.json` is calibrated from genuinely-human, pre-ChatGPT (pre-2022)
opinion writing. Only the derived **statistics** are committed; the raw texts are
not redistributed (they live in `raw/`, which is gitignored). Reproduce with
`scripts/fetch_corpus.py` then `scripts/build_reference.py`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| IMDB reviews | `stanfordnlp/imdb` (Maas et al., 2011) | movie reviews | 2011 and earlier | published 2011, long before generative LLMs |
| Yelp reviews | `Yelp/yelp_review_full` (Zhang et al., 2015) | business reviews | 2015 and earlier | published 2015, pre-LLM |

Fetched via the HuggingFace datasets rows API (JSON over HTTP). Current build: 120
texts (60 + 60), each cleaned of HTML, filtered to 300–2400 chars and >= 4
sentences. See `reference-stats.json` -> `n_texts`.

## Why these are a sensible choice

- **Provably human.** Both datasets predate ChatGPT (Nov 2022) by years, so there
  is no AI contamination risk — the core requirement for a "what human looks like"
  reference.
- **Register match.** First-person opinion prose (reviews) is squarely the
  spontaneous/colloquial register: personal stance, contractions, uneven rhythm.
- **License-clean for this use.** These are standard public NLP research datasets.
  We compute and commit only aggregate statistics, never republish the texts.

## Known limitations (honest)

- **Review skew.** Reviews lean evaluative and can run ranty; a blog/forum/email
  mix would broaden the register. Adding sources is just more entries in
  `fetch_corpus.py`'s `SOURCES`.
- **Domain skew.** Films and restaurants. Style statistics (sentence length,
  function words, punctuation) are fairly topic-independent, so this matters less
  than it looks, but it is not zero.
- **English only.** Bands are English-specific.

To personalize instead, drop your own writing into `raw/` (or any `*.txt` under
this folder) and re-run `build_reference.py`; the human target becomes you.
