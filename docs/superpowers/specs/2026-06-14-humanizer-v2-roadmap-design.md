# humanizer-pro v2 — Roadmap Design

**Date:** 2026-06-14
**Status:** Approved (brainstorming)
**Author:** Jody Cecchetto (delegated to Claude)
**Supersedes nothing** — extends `2026-06-12-humanizer-pro-design.md` (v0.1.0).

---

## Goal

Make humanizer-pro produce prose indistinguishable from the full range of human
writers — from the most expert/literate/artistic to the most casual — across
every practical register. v0.1.0 proved the thesis ("human" is register-specific)
on three registers. v2 closes the three gaps that still let an LLM be spotted:

1. **No discourse-structure awareness.** The scorer only sees sentence-level
   statistics. It is blind to the most obvious LLM tells: thesis-first openers,
   three-part parallelism, uniform paragraphs, transition-word overdose, and
   formulaic conclusions.
2. **Stale tell catalog + narrow register coverage.** The catalog predates the
   post-GPT-4 LLMisms; only 3 of ~8 practically-needed registers exist.
3. **No persona/expertise layer.** The target is always "the average human in
   the register". There is no way to aim at a *specific kind* of writer (an
   expert vs. a layperson, or the user's own voice).

## Non-Goals (unchanged from v0.1.0)

- **No commercial-detector evasion.** No GPTZero / Turnitin / watermark APIs.
  The target is the human distribution, framed as writing quality, not deception.
- No new third-party runtime dependencies. `stylo.py` stays standard-library.
- No GUI / web service. This remains a Claude Code skill + scripts.

## Architecture Overview

v2 is delivered as **three sequential sprints**, each producing working, tested,
eval-backed software on its own. Each sprint gets its own implementation plan
under `docs/superpowers/plans/`. The shared machinery (hybrid scorer, judge
panel, calibrated bands, eval harness) is reused unchanged; sprints extend it,
they do not rebuild it.

```
Sprint 1  Discourse + Tells     (no new corpus; improves all existing registers)
Sprint 2  Register expansion    (+5 registers, same machinery, new corpora)
Sprint 3  Persona layer         (voice-sample + expertise axis + named personas)
```

Dependency order is deliberate: Sprint 1 has zero corpus dependency and improves
the system immediately; Sprint 2's new registers (social-media, technical-docs)
stress-test Sprint 1's discourse features (fragments and lists are tells in
scientific prose but *human* there); Sprint 3 layers on top of a broad register
base so personas have registers to specialize.

---

## Sprint 1 — Discourse Structure + Enriched Tell Catalog

**Goal:** Give the scorer eyes for paragraph- and document-level structure, and
refresh the tell catalog with post-2023 LLMisms. No new corpus needed; this
improves spontaneous, scientific, and literary immediately.

### Files

- Modify: `scripts/stylo.py` — add a discourse-feature section + fold a
  `discourse_distance` term into `stylo_distance`.
- Modify: `scripts/build_reference.py` — calibrate the new discourse bands from
  the existing corpora (rerun `make corpus` regenerates all `reference-stats.json`).
- Modify: `lexicons/ai_tells.json` — add ~25 post-2023 patterns across new entries.
- Modify: `tests/test_stylo.py`, `tests/test_lexicon.py` — new coverage.
- Modify: `SKILL.md` — document the new scorecard fields.

### New discourse features (in `stylo.py`)

All three are computed from the raw text (no new dependencies). Each is
**directional** — only one tail is an AI tell — so they are NOT added to the
symmetric `FEATURE_KEYS` calibration (whose `floor = mean − 1·sd` band would wrongly
punish, e.g., a text that uses *fewer* transitions than average). They follow the
existing **`tell_rate` pattern** instead: a dedicated calibration block in
`build_reference.py` and a dedicated penalty term in `score()`. Ranges below are
illustrative, not the calibrated bands.

| Feature | Definition | Bad direction (the tell) | Illustrative human vs. LLM |
|---|---|---|---|
| `transition_density` | Count of transition words used as **sentence openers** (Moreover, Furthermore, Additionally, Consequently, Hence, Thus, Therefore, In conclusion, Ultimately) per 100 words. Mid-sentence uses are NOT counted (legitimate). | too **high** (above ceiling) | Human ≈ 0.5–3; LLM ≈ 5–15 |
| `paragraph_cv` | Coefficient of variation of paragraph lengths (split on blank lines / `\n\n+`, length in words). Computed over multi-paragraph texts only; single-paragraph input → `null`. | too **low** (below floor = uniform) | Human ≈ 0.4–0.9; LLM ≈ 0.1–0.25 |
| `structural_opener_rate` | Fraction of sentences that begin with a thesis/summary scaffold from a fixed phrase list ("In this analysis", "In today's", "This paper", "To summarize", "In conclusion", "Overall", "First and foremost", "Last but not least"). | too **high** (above ceiling) | Human ≈ 0–0.05; LLM ≈ 0.1–0.4 |

### Scorer integration

- New constant `DISCOURSE_WEIGHT = 0.05`, applied like `TELL_WEIGHT`.
- `build_reference.py` gains a discourse-calibration block (sibling of the existing
  `tell_rate` block) that emits **asymmetric** bands:
  - `transition_density`, `structural_opener_rate`: `floor = 0`, `ceiling = mean + 1.5·sd`.
  - `paragraph_cv`: `floor = max(0, mean − 1.5·sd)`, `ceiling = +∞` (only the floor
    is penalized), calibrated over the multi-paragraph texts in the corpus only.
- `score()` gains a `discourse_excess` term — the sum of the directional violations
  (transition_density and structural_opener_rate above ceiling; paragraph_cv below
  floor), each normalized by its band width — added to the composite as
  `DISCOURSE_WEIGHT * discourse_excess`, exactly like `tell_excess`. The three
  features are reported under `features` for transparency but, like `tell_rate`,
  are **excluded from the `stylo_outlier` veto** so a single structural quirk never
  hard-disqualifies an otherwise in-band candidate.
- **Fallback bands:** until the user reruns `make corpus`, `stylo.py` ships a
  hard-coded `DEFAULT_DISCOURSE_BANDS` dict keyed by register; calibrated bands in
  `reference-stats.json` override it when present.
- `paragraph_cv == null` (single paragraph) is omitted from `discourse_excess` and
  from the calibration sample.

### Enriched tell catalog (~25 new patterns)

New / extended entries in `ai_tells.json` (machine-readable terms + regexes,
same schema as existing):

- `transitional_overuse` — sentence-initial Moreover / Furthermore / Additionally
  / Consequently / Notably / Importantly (regex anchored to sentence start).
- `era_framing` — "in today's", "in an era of", "in the age of", "in the realm of",
  "in the world of", "in the rapidly evolving".
- `structural_formulas` — "first and foremost", "last but not least",
  "let's explore", "let's unpack", "let's dive deeper", "to summarize",
  "without further ado", "the bottom line is".
- `hollow_affirmatives` — sentence-initial "Absolutely!", "Certainly!",
  "Of course!", "Great question!", "Indeed,".
- `ai_vocabulary` (extend existing id 7) — add: "shed light on", "pave the way for",
  "state-of-the-art", "game-changing", "cutting-edge", "unpack", "deep dive",
  "navigate the", "at the forefront", "harness the power".

Each new term is verified NOT to fire on the existing human corpora above the
calibrated `tell_rate` ceiling (the catalog change reruns `make corpus` and the
eval to confirm no regression).

### Testing

- `transition_density` counts sentence-openers only, not mid-sentence uses.
- `paragraph_cv` returns `null` for single-paragraph text and is excluded.
- `structural_opener_rate` fires on a thesis-first opener, not on normal prose.
- A uniform-paragraph, transition-heavy AI sample scores higher `discourse_distance`
  than a register-true human sample.
- New lexicon entries are valid JSON, regexes compile, and fire on positive
  examples / stay silent on negatives.
- Regression: the three existing registers' evals still pass after recalibration.

### Done criteria

All tests green (`make test`); `make corpus` recalibrates discourse bands; the
existing-register evals show no regression (still ≥ baseline); a synthetic
structurally-AI sample is now correctly penalized where v0.1.0 missed it.

---

## Sprint 2 — Register Expansion (+5 registers)

**Goal:** Go from 3 to 8 registers, covering the practical span of human writing.
Same machinery: each register is a `registers/<name>.md` brief + a calibrated
`corpus/<name>/` + the existing `{{REGISTER}}`-parametrized judges.

### New registers

| Register | Corpus source (HuggingFace, pre-LLM where possible) | Inverting norms (what is *human* here) |
|---|---|---|
| `business` | Enron email corpus / public earnings-call transcripts | polite hedging, nominalization, zero em-dash, transitions acceptable |
| `journalism` | CNN/DailyMail (pre-2018, `cnn_dailymail`) | structured lede, short sentences, source attribution is human not tell |
| `social-media` | Reddit comments / tweets (pre-2020) | fragments, lowercase, minimal formal punctuation, slang, emoji allowed |
| `academic-essay` | humanities abstracts / essays (e.g. JSTOR-style) | thesis-driven OK, citations, long subordinate sentences |
| `technical-docs` | Stack Overflow answers / GitHub READMEs (pre-2021) | imperative mood, code-switching, lists are human here |

### Why these stress-test Sprint 1

`social-media` and `technical-docs` deliberately invert Sprint 1's assumptions:
fragments and lists are AI tells in scientific prose but the human norm here. The
per-register calibrated discourse bands handle this automatically — proving the
discourse layer is register-aware, not a global rule. This is the same proof the
em-dash ceiling gave in v0.1.0 (0.00 scientific → 1.71 literary).

### Files (per register, ×5)

- Create: `registers/<name>.md` — the brief (norms, what's human, what's a tell here).
- Create: `corpus/<name>/PROVENANCE.md` + calibrated `reference-stats.json`
  (raw texts gitignored, reproducible via `fetch_corpus.py`).
- Modify: `scripts/fetch_corpus.py` — add the 5 sources to the `SOURCES` dict.
- Modify: `eval/run_eval.py` + `Makefile` — add the 5 registers to the eval loop.
- Create: `eval/ai_samples/<name>/*.txt` — 4–5 AI samples per register.
- Modify: `SKILL.md`, `README.md` — list 8 registers.

### Testing & done criteria

Each new register: ≥100 calibrated human texts; bands visibly differ from the
others (the 8-register fingerprint table extends the em-dash story); blind A/B
eval shows pro ≥ baseline on every sample. `make test` green. The discourse
features from Sprint 1 calibrate sanely on the inverting registers (e.g.
`social-media` `paragraph_cv` and `structural_opener_rate` differ sharply from
`academic-essay`).

---

## Sprint 3 — Persona / Expertise Layer

**Goal:** Aim at a *specific kind* of writer, not just the register average.
Three sub-features, shipped in priority order; each is independently useful.

### 3.1 `--voice-sample` (priority 1)

Already promised in `SKILL.md`, never implemented. The user supplies 3–10 of
their own texts; `build_reference.py` calibrates a personal `reference-stats.json`
that fully overrides the register corpus. Target becomes "write like me".

- Modify: `scripts/build_reference.py` — accept `--voice-sample <dir>` and emit
  `corpus/_voice/<label>/reference-stats.json`.
- Modify: `scripts/stylo.py` — accept `--bands <path>` to score against an
  arbitrary stats file instead of the register default.
- Modify: `SKILL.md` — document the voice-sample flow as a first-class input.
- Guard: if the sample is too small (< ~1500 words total), warn that bands will
  be noisy and fall back to register + voice blend (documented behavior, not silent).

### 3.2 `--expertise novice | practitioner | expert` (priority 2)

Band *modifiers* applied within a register. Stored as a delta file
`corpus/<register>/expertise-<level>.json` that shifts specific bands (jargon /
tell tolerance, sentence length, hedging structure). Expert-scientific tolerates
more domain jargon and structured hedging; novice tightens vocabulary and
shortens sentences.

- Create: `corpus/<register>/expertise-{novice,practitioner,expert}.json` deltas
  for the registers where expertise meaningfully varies (scientific, academic-essay,
  technical-docs, business). Default `practitioner` = the existing calibrated bands
  (delta of zero), so this is backward-compatible.
- Modify: `scripts/stylo.py` — apply the delta on top of the register bands when
  `--expertise` is passed.
- Modify: `registers/<name>.md` — note how expertise shifts the brief.

### 3.3 Named personas (priority 3)

Pre-calibrated profiles combining register + expertise + lexicon tweaks:
`personas/reddit-power-user.json`, `seasoned-journalist.json`,
`startup-founder.json`, `academic-humanist.json`.

- Create: `personas/<name>.json` — references a base register, an expertise level,
  and optional lexicon overrides (e.g. allow/forbid specific terms).
- Modify: `scripts/stylo.py` — `--persona <name>` resolves to base bands + deltas.
- Modify: `SKILL.md` — document personas as a shortcut over the raw flags.

### Testing & done criteria

- `--voice-sample` on a held-out sample of a corpus reproduces that corpus's bands
  within tolerance (round-trip test).
- `--expertise expert` vs `novice` on the same text produces measurably different
  `stylo_distance` (expert-jargon text scores closer-to-human under `expert`).
- A named persona resolves to the expected base + delta and scores a matching
  sample as in-band.
- `make test` green; backward compatibility: omitting all new flags reproduces
  v0.1.0/Sprint-2 behavior exactly.

---

## Cross-Cutting Concerns

- **Backward compatibility:** every new flag is optional; default behavior is
  identical to the prior version. Default `--expertise` is `practitioner` = zero delta.
- **Reproducibility:** all corpora stay gitignored; only derived stats + PROVENANCE
  committed. `make corpus` regenerates everything.
- **Test discipline:** stdlib `tests/run.py` (no pytest in this env). Every sprint
  adds tests before/with implementation (TDD per the plan).
- **Eval discipline:** every sprint ends with `make eval` showing pro ≥ baseline,
  no regression on prior registers.
- **Versioning:** Sprint 1 → v0.2.0, Sprint 2 → v0.3.0, Sprint 3 → v1.0.0.
  Each sprint tags and updates CHANGELOG.md.

## Open Risks

- **Corpus availability:** some Sprint-2 sources (Enron, JSTOR-style) may need a
  substitute if the HF dataset is gated. Fallback substitutes are chosen at plan
  time, not here; PROVENANCE records whatever is actually used.
- **Discourse calibration on short texts:** `paragraph_cv` is unstable on short
  inputs — handled by the `null`-and-exclude rule, but worth watching in eval.
- **Persona overfitting:** named personas risk caricature. Mitigation: they are
  thin combinations of already-calibrated registers + expertise deltas, not
  hand-tuned vibes.
