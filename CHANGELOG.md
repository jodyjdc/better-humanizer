# Changelog

## 0.1.0 — 2026-06-12

First release. A measured, self-improving humanizer that targets the real human
distribution per register instead of deleting a fixed list of tells.

- **Stylometric scorer** (`scripts/stylo.py`, standard library only): sentence-length
  burstiness, lexical diversity (MTLD), function-word fingerprint, punctuation rates,
  AI-tell density, and **self-tell flags** that catch over-correction (scrubbing a
  text flat is itself a tell). Composite distance to the human band, with an outlier
  veto. 25 tests via `python3 tests/run.py`.
- **Three registers**, each calibrated on 120 genuinely-human, pre-LLM texts:
  spontaneous (IMDB + Yelp reviews), scientific (PubMed + arXiv abstracts), literary
  (r/WritingPrompts stories). Bands differ sharply (em-dash ceiling 0.00 → 1.71),
  proving "human" is register-specific. Tell tolerance is calibrated per register.
- **LLM judge panel** (`judges/`): adversarial detector, register fidelity, meaning
  fidelity, parametrized by register.
- **Orchestrator** (`SKILL.md`, `/humanizer-pro`): generate K candidates → hybrid
  score → veto → keep best → iterate on the judges' critique.
- **Blind A/B eval** (`eval/`): humanizer-pro beats the original-style baseline on
  every sample — 5/5 spontaneous, 4/4 scientific, 4/4 literary.
- **Reproducible corpus** (`scripts/fetch_corpus.py`): pulls human pre-2022 text via
  the HuggingFace rows API; only derived `reference-stats.json` is committed, raw
  texts are gitignored.
- **Explicit non-goal**: no commercial-detector evasion. Target is the human
  distribution, not a specific classifier.
