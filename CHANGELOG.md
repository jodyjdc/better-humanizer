# Changelog

## 1.1.0 — 2026-06-15

Harvested the curated catalog from "Stop Slop" (Hardik Pandya, MIT, ~10k stars)
into our measured, register-aware architecture — taking its strength (a rich
phrase/structure catalog) while rejecting the part our data disproves (register-blind
blanket bans).

- **8 new tell entries** in `lexicons/ai_tells.json` (ids 38–45): `throat_clearing`,
  `emphasis_crutch`, `business_jargon` (circle back / double down / lean into),
  `meta_commentary` (Plot twist / Spoiler / "as we'll see"), `vague_declarative`,
  `binary_contrast` ("the answer isn't X, it's Y", both contracted and expanded),
  `negative_listing` ("not a X… not a Y… a Z"), `rhetorical_setup` ("What if…?").
  False-positive scan: each fires ≤ 6 times across 840 human texts.
- **Deliberately NOT adopted**: Stop Slop's blanket bans (no em dashes, kill all
  adverbs, no passive voice, two-items-beat-three). Our 7-register data shows these
  are register-specific (em-dash 0.00→1.71; passive is human in science; "honestly/
  literally" are human on Reddit — they're even in the reddit-power-user allow list).
  A blanket ban is itself an over-correction tell. A test asserts adverbs stay
  uncatalogued.
- **Recalibrated** all 7 registers (tell ceilings barely moved — the new patterns are
  rare in human prose, so calibration absorbs them and they fire on AI overuse).
  Eval holds with no regression: 25/25.
- 64 tests. Attribution added to LICENSE (MIT).

## 1.0.1 — 2026-06-15

Post-1.0 finishing: the persona `lexicon_allow` direction is now functional
end-to-end (it was unit-tested but no shipped persona exercised it), and a known
limitation is resolved as data-blocked.

- **Persona allow, data-grounded:** `startup-founder` now allows "in order to" and
  "let me know if" — both verified present in the real Enron business corpus. A
  founder email using them scores 0.718 under bare `business` (2 tells) vs 0.393
  under `--persona startup-founder` (0 tells). The persona stops penalizing phrasing
  real business writers actually use.
- **paragraph_cv resolved as data-blocked:** a probe found zero paragraph breaks in
  6 of 7 source datasets (only Stack Exchange answers carry real paragraphs), so
  calibrated paragraph bands can't be derived from these corpora — a data limit, not
  a code gap. Documented in `eval/REPORT.md`.

## 1.0.0 — 2026-06-15

Sprint 3 of the v2 roadmap — the **persona layer**. The target moves from "the
average human in a register" to a *specific writer*, still measured on real data.
This completes the v2 roadmap (structure → registers → persona).

- **Expertise tiers** (`--expertise novice|practitioner|expert`): each register's
  corpus is split into terciles by **Flesch-Kincaid grade** (a stdlib readability
  metric — measured, not hand-tuned). `expert` tolerates longer/denser prose,
  `novice` keeps it simple; `practitioner` is the full register (backward-compatible
  default). 14 committed tier band-sets.
- **Voice** (`--voice <label>`): `build_reference.py --voice-sample <dir>` calibrates
  personal bands from the user's own writing. Samples under ~1500 words are blended
  with a register fallback (weighted by data) with a warning. Voice data is gitignored.
- **Named personas** (`--persona <name>`): register + expertise tier + a lexicon
  allow/deny override. Ships `reddit-power-user`, `seasoned-journalist`,
  `startup-founder`, `academic-humanist`. Resolution precedence:
  persona > voice > expertise > register; all flags optional (no flag = v0.3.0).
- **Proof**: expertise tiers separate cleanly (e.g. scientific FK 5.9–14.2 novice vs
  17.0–26.1 expert) and discriminate (dense prose closer under expert, simple under
  novice); a buzzword passage scores 0.811 under bare business vs 1.764 under
  `--persona startup-founder`. 60 tests via `python3 tests/run.py`.

## 0.3.0 — 2026-06-15

Sprint 2 of the v2 roadmap: register expansion from 3 to 7.

- **Four new registers**, each calibrated on 120 genuinely-human, pre-LLM texts:
  **business** (Enron emails / AESLC), **journalism** (CNN/DailyMail articles),
  **social-media** (Reddit / Webis-TLDR-17), **technical-docs** (Stack Exchange
  answers). Same machinery — `registers/<name>.md` brief + calibrated
  `corpus/<name>/` + the discourse/tell scorer.
- **Markdown-aware `clean()`** (`scripts/fetch_corpus.py`): strips links (keeping
  anchor text), inline code, blockquote markers, horizontal rules, and bare URLs —
  needed so Stack Exchange answers don't corrupt the stylometry.
- **Seven-register fingerprint**: contraction ceiling spans 0.00 (scientific) to
  5.78 (business email); exclamation 0.07 (journalism) to 3.47 (spontaneous);
  AI-tell tolerance 0.22 (literary) to 0.78 (scientific). Two empirical findings:
  internal business email is conversational (not the formal-report stereotype), and
  technical-docs has the widest sentence-length range (6–65).
- **Blind A/B eval**: pro beats the register-blind baseline 12/12 on the new
  registers (25/25 across all seven). `eval/REPORT.md` updated.
- **Deferred**: academic-essay — every clean, dated, pre-LLM student-essay corpus on
  the HF rows API is gated; it returns when a clean source is found.
- **Known limitation**: `paragraph_cv` stays inert (HF sources are paragraph-flattened
  and `clean()` collapses newlines); it works on real multi-paragraph user input but
  isn't calibration-live yet.

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
