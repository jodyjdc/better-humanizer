# Sprint 3 — Persona Layer — Design

**Date:** 2026-06-15
**Status:** Approved (brainstorming; user delegated final calls)
**Extends:** `2026-06-14-humanizer-v2-roadmap-design.md` (Sprint 3). Ships **v1.0.0**.

## Goal

Move the humanizer's target from "the average human in register X" to **a specific
writer**: the user's own voice, a level of expertise, or a named persona — without
abandoning the project's core principle that every target is **measured on real data,
never hand-tuned**.

## Core idea (one mechanism)

`score()` already compares a text against a **band-set** (`reference-stats.json`).
Sprint 3 adds more selectable band-sets, all produced by the same measured pipeline
(`build_reference.py`), plus a thin persona lexicon-override layer. Three ways to pick
the target, resolved by precedence **persona > voice > expertise > register**; exactly
one target is active per scoring run.

Backward compatibility is absolute: with no new flag, behavior is byte-identical to
v0.3.0 (the register's full bands).

---

## Feature 1 — Voice sample ("write like me")

The user supplies their own writing; the target becomes them.

- `build_reference.py --voice-sample <dir> --label <name> [--register <fallback>]`
  reads `*.txt` under `<dir>`, calibrates personal bands, writes
  `voices/<name>/reference-stats.json` (same schema as a register's).
- `stylo.py --voice <name>` (sugar for `--bands voices/<name>/reference-stats.json`)
  scores against the personal bands instead of a register.
- **Small-sample rule (anti-noise, honors "measured"):** measure total words. If
  `>= 1500` words, use the personal bands directly. If fewer, **blend** with the
  `--register` fallback (default `spontaneous`) weighted by data volume:
  `w = min(1.0, words / 1500)`; `band = w * voice_band + (1 - w) * register_band`
  per feature, and the function-word vector blended the same way. Emit a clear
  warning naming the word count and the blend weight. Never present noisy bands as
  if they were fully calibrated.
- `voices/` is **gitignored** (personal user data, not ours to commit). The mechanism
  + docs ship; no personal corpus is committed.

## Feature 2 — Expertise (`--expertise novice | practitioner | expert`)

A measured complexity axis *within* a register, derived from the existing corpora —
no new data, no hand-authored deltas.

- **Axis = Flesch–Kincaid grade level**, the standard readability metric, computed in
  the standard library: `FK = 0.39*(words/sentences) + 11.8*(syllables/words) -
  15.59`. Syllables via the conventional vowel-group heuristic (count vowel runs per
  word, drop a silent trailing "e", floor of 1). New helpers in `stylo.py`:
  `_count_syllables(word)`, `flesch_kincaid_grade(text)`.
- `build_reference.py` sorts a register's 120 texts by FK grade and splits into
  **terciles**: bottom third → `novice`, top third → `expert` (≈40 texts each, enough
  for stable bands). It calibrates each tier with the existing `aggregate()` and
  writes `corpus/<reg>/expertise-novice.json` and `expertise-expert.json` (full band
  schema + a `fk_grade_range` note). The **middle tier is not stored**:
  `practitioner` resolves to the register's full `reference-stats.json` (so the
  default is exactly today's behavior — zero delta, backward-compatible).
- `stylo.py --expertise <level>` loads the matching band-set for `--register`.
- **Design refinement over the roadmap:** store *full per-tier bands*, not deltas.
  Full bands are simpler, more robust, and avoid base+delta composition bugs; the
  effect ("expert tolerates more jargon / longer sentences") is identical.
- These tier files are derived statistics → **committed** (like `reference-stats.json`).

## Feature 3 — Named personas (`--persona <name>`)

Pre-composed targets = a register + an expertise level + optional lexicon overrides.

- `personas/<name>.json`:
  ```json
  {
    "name": "reddit-power-user",
    "register": "social-media",
    "expertise": "practitioner",
    "lexicon_allow": ["honestly", "literally", "tbh"],
    "lexicon_deny": []
  }
  ```
- `stylo.py --persona <name>` resolves to: that register+tier band-set, **plus** a
  lexicon-override layer applied to the AI-tell count — `lexicon_allow` terms are NOT
  counted as tells for this persona (their voice legitimately uses them);
  `lexicon_deny` terms are counted as extra tells. Implemented via
  `tell_hits(text, lexicon, allow=set(), deny=[])`.
- **Four personas**, each grounded in a real register + tier:
  - `reddit-power-user` → social-media + practitioner, allows casual intensifiers.
  - `seasoned-journalist` → journalism + expert, denies editorializing adjectives.
  - `startup-founder` → business + practitioner, allows a little visionary framing,
    denies the worst marketing fluff.
  - `academic-humanist` → literary + expert (long, figurative, argumentative), allows
    em dashes and subordinate clauses.

---

## CLI surface & resolution

`stylo.py [file] [--register R] [--expertise L] [--voice V | --bands PATH]
[--persona P]`

Resolution (highest wins; a warning is printed if more than one target flag is set):
1. `--persona P` → register+tier from the persona file + lexicon overrides.
2. `--voice V` / `--bands PATH` → those bands (no register tier).
3. `--expertise L` (+ `--register R`) → tier bands.
4. `--register R` alone → full register bands (today's behavior).

`build_reference.py`:
- `--register R` → writes `reference-stats.json` **and** the two expertise tiers.
- `--voice-sample DIR --label NAME [--register FALLBACK]` → writes
  `voices/NAME/reference-stats.json` with the small-sample blend rule.

`Makefile`: the `corpus` target already calls `build_reference --register` per
register, which now also emits tiers — no extra wiring needed beyond confirming it.

---

## File structure

- `scripts/stylo.py` — **modify**: add `_count_syllables`, `flesch_kincaid_grade`;
  band-set resolution (`--voice/--bands/--expertise/--persona`); persona lexicon
  override in `tell_hits`/`tell_rate`/`score`.
- `scripts/build_reference.py` — **modify**: emit expertise terciles per register;
  add `--voice-sample/--label/--register` path with the blend rule.
- `personas/*.json` — **create**: 4 persona files.
- `corpus/<reg>/expertise-{novice,expert}.json` — **generated + committed** (7×2=14).
- `voices/` — **gitignored**; `.gitignore` updated.
- `tests/test_expertise.py`, `tests/test_voice.py`, `tests/test_persona.py` — **create**.
- `eval/REPORT.md`, `README.md`, `SKILL.md`, `AGENTS.md`, `CHANGELOG.md` — **modify**.

## Testing

- **FK grade:** `_count_syllables` on known words ("cat"=1, "syllable"=3, "queue"≈1-2);
  `flesch_kincaid_grade` higher for dense academic prose than for simple prose.
- **Tercile split:** `build_reference` over a synthetic corpus emits novice/expert
  files; expert tier has higher FK / longer sentences / higher MTLD than novice.
- **Expertise discrimination:** a high-FK text scores closer-to-human under `expert`
  than under `novice` for the same register; a low-FK text vice versa.
- **Voice round-trip:** hold out N texts from a corpus, calibrate a voice on them;
  those texts score in-band against their own voice bands; a foreign-register text
  scores worse.
- **Voice blend:** a < 1500-word sample triggers the blend (assert the warning fires
  and a band lands between voice-only and register-only).
- **Persona resolution:** `--persona reddit-power-user` resolves to social-media bands;
  a text using an allowed term scores no worse for it (allow works); a denied term
  raises the tell count.
- Backward compatibility: omitting all new flags reproduces v0.3.0 output exactly.

## Eval / proof (REPORT.md)

- **Expertise tier table** per register: show novice vs expert bands diverging on
  sentence length, MTLD, FK range (the "measured expertise" proof).
- **Voice round-trip** demonstration (held-out texts in-band vs a foreign text out).
- **Persona demo:** one slangy social text scored under bare `social-media` vs
  `--persona reddit-power-user` — the persona accepts the voice the register flags.

## Versioning

Sprint 3 completes the v2 roadmap → tag **v1.0.0**, CHANGELOG entry, dual-platform
docs (SKILL.md + AGENTS.md) updated for the new flags.

## Open risks

- **Tercile ≠ true expertise.** FK grade is a *complexity* proxy; within a register it
  correlates with expertise but isn't identical. Documented honestly as a readability
  tier, not a verified competence label.
- **Tiny voice samples** stay noisy even after blending; the warning + blend bound the
  damage but the user must understand a 200-word sample can't fully define a voice.
- **Persona caricature.** Mitigated by building personas from already-calibrated
  register+tier bands plus a *small* curated lexicon list, not free-form vibes.
