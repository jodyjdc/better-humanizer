# Changelog

## 0.2.0 — 2026-06-14

Sprint 1 of the v2 roadmap: document-level awareness + a refreshed tell catalog.

- **Discourse structure** in the scorer (`scripts/stylo.py`): `transition_density`
  (sentence-opening connective overuse), `structural_opener_rate` (thesis/summary
  scaffolds), and `paragraph_cv` (uniform paragraphs = machine-like). One-tailed,
  calibrated asymmetrically, excluded from the hard outlier veto, and folded into
  `stylo_distance` via `DISCOURSE_WEIGHT`.
- **Enriched tell catalog** (`lexicons/ai_tells.json`): post-2023 LLMisms —
  `transitional_overuse`, `era_framing`, `structural_formulas`,
  `hollow_affirmatives`, plus extended `ai_vocabulary` ("shed light on",
  "pave the way for", "state-of-the-art", "game-changing", "cutting-edge", ...).
  Cross-entry duplicate terms de-duplicated so no span is double-counted.
- **Recalibrated** all three registers; the transition-opener ceiling is itself
  register-specific (0.19 / 0.63 / 0.08 spontaneous / scientific / literary). Blind
  A/B eval holds with no regression: spontaneous 5/5, scientific 4/4, literary 4/4.
- 42 tests via `python3 tests/run.py`.

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
