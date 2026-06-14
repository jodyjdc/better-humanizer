# Corpus provenance — journalism register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM news prose. Only
the derived statistics are committed; raw texts live in `raw/` (gitignored).
Reproduce: `python3 scripts/fetch_corpus.py --register journalism --min-chars 800
--max-chars 4500 --min-sents 6` then `python3 scripts/build_reference.py --register
journalism`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| CNN/DailyMail | `abisee/cnn_dailymail` (3.0.0) | news articles (`article`) | <= 2017 | Hermann et al. 2015 / See et al. 2017; professionally written news, predates LLMs |

Current build: 120 texts, cleaned and filtered to 800–4500 chars, >= 6 sentences.

## Why these are a sensible choice

- **Provably human.** Professional newsroom copy collected in 2015–2017, pre-LLM.
- **Register match.** Inverted-pyramid lede, short declarative sentences, heavy
  source attribution ("officials said", "according to"), sober tone.
- **License-clean for this use.** Standard public summarization dataset; we commit
  only aggregate statistics.

## What this register proves

Journalism is the **unexcitable** register: exclamation tolerance is near-zero (0.07)
and sentence-opening transitions are the lowest of all seven (0.02) — news doesn't
say "Moreover," it just reports. Source attribution and a structured lede are human
here, not tells. The em-dash ceiling is elevated partly by the dateline convention
("CITY (Reuters) --"); genuine asides also use it.

## Limitations

Two outlets (CNN, DailyMail), English, 2015–2017; hard-news skew (less feature/op-ed
writing). Datelines and the occasional photo-caption fragment survive cleaning. Add
sources in `fetch_corpus.py` `SOURCES["journalism"]` to broaden.
