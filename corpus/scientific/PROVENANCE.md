# Corpus provenance — scientific register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM scientific
prose. Only the derived statistics are committed; raw texts live in `raw/`
(gitignored). Reproduce: `python3 scripts/fetch_corpus.py --register scientific
--max-chars 3000` then `python3 scripts/build_reference.py --register scientific`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| PubMed | `ccdv/pubmed-summarization` | biomedical paper abstracts | <= 2018 | dataset from Cohan et al. 2018, pre-LLM; PubMed abstracts are US-gov / public |
| arXiv | `ccdv/arxiv-summarization` | STEM paper abstracts | <= 2018 | same dataset/era |

The `abstract` field is used: dense, self-contained, human-written scientific
prose. Current build: 120 texts (60 + 60), cleaned and filtered to 300–3000
chars, >= 4 sentences. Texts are pre-tokenized in the source dump; `fetch_corpus.py`
re-attaches punctuation. (Lowercasing in the dump does not affect the calibrated
features, which are case-independent.)

## Why these are a sensible choice

- **Provably human.** Both predate generative LLMs by years.
- **Register match.** Abstracts are the purest concentrated form of the scientific
  register: passive voice, hedging, nominalization, formal vocabulary, longer and
  more uniform sentences.
- **License-clean for this use.** Standard public NLP research datasets; we commit
  only aggregate statistics.

## What this register proves

The scientific bands invert several spontaneous expectations, on real data:
contraction rate is ~0 (and that is human here), sentence rhythm is more uniform,
and the AI-tell tolerance is ~3x higher (real papers use "crucial / underscore /
interplay"). Applying spontaneous-register rules to a paper would damage it; the
calibrated bands prevent that automatically.

## Limitations

Abstracts only (not full-body prose); English; biomedical + STEM skew. Add
sources in `fetch_corpus.py` `SOURCES["scientific"]` to broaden.
