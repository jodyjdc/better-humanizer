# Sprint 1 — Discourse Structure + Enriched Tell Catalog — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the stylometric scorer document-level eyes (transition overuse, uniform paragraphs, thesis/summary scaffolds) and refresh the AI-tell catalog with post-2023 LLMisms — improving all three existing registers with no new corpus.

**Architecture:** Three new *directional* discourse features are added to `scripts/stylo.py` and handled exactly like the existing `tell_rate` special feature — calibrated asymmetrically in `scripts/build_reference.py`, stored under `bands`, scored in a dedicated block that is **excluded from the hard `stylo_outlier` veto**, and folded into `stylo_distance` via a new `DISCOURSE_WEIGHT`. The tell catalog (`lexicons/ai_tells.json`) gains four new entries plus an extension of the existing `ai_vocabulary` entry. The three committed `reference-stats.json` files are recalibrated locally from the already-present raw corpora, then the evals confirm no regression.

**Tech Stack:** Python 3 standard library only (no pytest — tests run via `python3 tests/run.py`). JSON lexicon. Make targets.

---

## Background the engineer needs

- `scripts/stylo.py` is the scorer. Key existing pieces you will reuse:
  - `split_sentences(text)` → list of sentence strings.
  - `tokenize(text)` → list of lowercased word tokens.
  - `WORD_RE` — compiled regex matching a word (used to test "does this fragment contain a word").
  - `_extract_features(text)` → dict of the **symmetric** banded features (sentence length, mtld, etc.). **Do NOT add the discourse features here** — that loop in `build_reference.py` applies a symmetric `floor = mean − sd` band, which is wrong for one-tailed features.
  - `score(text, register, ref)` → the composite. Note the ordering inside it: the `stylo_outlier` veto is computed (`any abs(z) > 3`) **before** `tell_rate` is appended to `features`. Anything appended after that line is therefore excluded from the veto. The discourse block goes there too.
  - `tell_rate` is the template to copy: it is calibrated in its own block in `build_reference.py` (not via `FEATURE_KEYS`), stored under `bands["tell_rate"]`, and scored as `TELL_WEIGHT * tell_excess` where only the *excess over ceiling* counts.
- `scripts/build_reference.py` calibrates a register's bands from `corpus/<register>/**/*.txt`. The raw corpora ARE present locally (120 texts each for spontaneous / scientific / literary), so recalibration needs no network.
- `tests/run.py` discovers every `test_*` function in `tests/test_*.py`. Run a subset with a filter: `python3 tests/run.py stylo` runs `tests/test_stylo.py`.
- Existing lexicon entry IDs in use: `1,3,4,5,6,7,8,9,12,13,20,21,22,23,24,25,27,28,32,33`. New entries use `34,35,36,37`.
- `OVER_CORRECTION`, `TELL_WEIGHT`, `SELF_TELL_WEIGHT` constants live near line 260 of `stylo.py`; add `DISCOURSE_WEIGHT` and the discourse band/key constants next to them.

---

## File Structure

- `scripts/stylo.py` — **modify**: add discourse feature extraction (`_paragraphs`, `_sentence_starts_with`, `discourse`, the opener phrase tuples) near the other extractors; add `DISCOURSE_WEIGHT`, `DISCOURSE_KEYS`, `DEFAULT_DISCOURSE_BANDS` near the other constants; add the discourse scoring block inside `score()`.
- `scripts/build_reference.py` — **modify**: add a discourse-calibration block (sibling of the `tell_rate` block) emitting asymmetric bands.
- `lexicons/ai_tells.json` — **modify**: 4 new entries + extend entry id 7.
- `tests/test_stylo.py` — **modify**: discourse extractor + scoring tests.
- `tests/test_lexicon.py` — **modify**: new-entry coverage.
- `corpus/{spontaneous,scientific,literary}/reference-stats.json` — **regenerate + commit**.
- `SKILL.md`, `README.md`, `CHANGELOG.md` — **modify**: document the new scorecard fields and v0.2.0.

---

## Task 1: Discourse feature extractor

**Files:**
- Modify: `scripts/stylo.py` (add after `rule_of_three`, before the "Function-word fingerprint" section, ~line 213)
- Test: `tests/test_stylo.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_stylo.py` (after `test_rule_of_three`, around line 96):

```python
# --- Sprint 1: discourse structure ---

def test_discourse_transition_opener_counted():
    # Sentence-initial transitions are the tell; one opener over a short text.
    out = stylo.discourse("Moreover, the system improved. The team shipped it.")
    assert out["transition_density"] > 0


def test_discourse_midsentence_transition_not_counted():
    # "thus"/"therefore" used mid-sentence is legitimate, not a tell.
    out = stylo.discourse("The build was green and thus we shipped the change.")
    assert out["transition_density"] == 0


def test_discourse_structural_opener_rate():
    two = "In today's world, things change. The dog slept by the fire all day."
    out = stylo.discourse(two)
    # One of two sentences opens with a thesis scaffold -> 0.5.
    assert abs(out["structural_opener_rate"] - 0.5) < 1e-9


def test_discourse_no_structural_opener():
    out = stylo.discourse("The dog slept. The cat watched. Rain fell outside.")
    assert out["structural_opener_rate"] == 0.0


def test_discourse_paragraph_cv_single_is_none():
    out = stylo.discourse("Just one paragraph here, no blank line breaks at all.")
    assert out["paragraph_cv"] is None


def test_discourse_paragraph_cv_multi_is_number():
    text = "Short one.\n\nA considerably longer paragraph that runs on for a while "
    text += "with several more words than the first.\n\nMid length here, roughly."
    out = stylo.discourse(text)
    assert out["paragraph_cv"] is not None and out["paragraph_cv"] > 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 tests/run.py stylo`
Expected: 6 new lines `FAIL tests/test_stylo.py::test_discourse_*` with `AttributeError: module 'stylo' has no attribute 'discourse'`.

- [ ] **Step 3: Implement the extractor**

Insert into `scripts/stylo.py` immediately after the `rule_of_three` function (after line 212):

```python
# --------------------------------------------------------------------------
# Discourse structure (document-level tells)
# --------------------------------------------------------------------------
PARA_SPLIT_RE = re.compile(r"\n\s*\n+")

# Connectives that read as an AI tell when they OPEN a sentence. Mid-sentence
# use is legitimate and deliberately NOT counted.
TRANSITION_OPENERS = (
    "moreover", "furthermore", "additionally", "in addition", "consequently",
    "hence", "thus", "therefore", "notably", "importantly", "ultimately",
    "in conclusion",
)

# Thesis / summary scaffolds: a sentence that opens with one of these is doing
# the "set up the essay" move LLMs overuse. ("in conclusion" intentionally also
# appears above — it is both a transition and a summary scaffold.)
STRUCTURAL_OPENERS = (
    "in this analysis", "in this article", "in this essay", "in today's",
    "in an era", "in the age of", "in the realm of", "in the world of",
    "this paper", "this essay", "this article", "to summarize", "in summary",
    "in conclusion", "overall", "first and foremost", "last but not least",
)


def _paragraphs(text):
    """Paragraphs split on blank lines; drop tokenless fragments."""
    return [p for p in PARA_SPLIT_RE.split(text.strip()) if WORD_RE.search(p)]


def _sentence_starts_with(sentence, phrases):
    """True if `sentence` begins with any phrase in `phrases`, case-insensitively,
    ignoring leading quotes/brackets, on a word boundary (so 'overall' does not
    match 'overallocation')."""
    s = sentence.lstrip(" \t\"'“‘(").lower()
    for p in phrases:
        if s.startswith(p) and (len(s) == len(p) or not s[len(p)].isalpha()):
            return True
    return False


def discourse(text):
    """Document-level discourse features. Each is one-tailed (a tell in a single
    direction); paragraph_cv is None when the text has fewer than two paragraphs.

    - transition_density: sentence-opening connectives per 100 tokens (high = tell)
    - structural_opener_rate: fraction of sentences opening with a thesis/summary
      scaffold (high = tell)
    - paragraph_cv: coefficient of variation of paragraph word-lengths
      (low = uniform = tell); None for single-paragraph input
    """
    sents = split_sentences(text)
    n_tok = len(tokenize(text)) or 1
    trans = sum(1 for s in sents if _sentence_starts_with(s, TRANSITION_OPENERS))
    struct = sum(1 for s in sents if _sentence_starts_with(s, STRUCTURAL_OPENERS))
    paras = _paragraphs(text)
    if len(paras) >= 2:
        plens = [len(tokenize(p)) for p in paras]
        pmean = statistics.fmean(plens)
        pcv = (statistics.pstdev(plens) / pmean) if pmean else 0.0
    else:
        pcv = None
    return {
        "transition_density": trans / n_tok * 100,
        "structural_opener_rate": (struct / len(sents)) if sents else 0.0,
        "paragraph_cv": pcv,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 tests/run.py stylo`
Expected: the 6 `test_discourse_*` lines now `PASS`; existing stylo tests still `PASS`; final line `N passed, 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/stylo.py tests/test_stylo.py
git commit -m "feat(stylo): discourse feature extractor (transition/opener/paragraph-cv)"
```

---

## Task 2: Score discourse features into the composite

**Files:**
- Modify: `scripts/stylo.py` — constants near line 270; discourse block inside `score()` after the `tell_rate` block (after line 372); extend `stylo_distance` (line 375).
- Test: `tests/test_stylo.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_stylo.py` (after the discourse-extractor tests from Task 1):

```python
# Multi-paragraph, transition-heavy, scaffold-opening AI structure vs. a human
# passage of similar length and topic.
AI_STRUCTURED = (
    "In today's rapidly evolving landscape, automation reshapes how teams work.\n\n"
    "Moreover, it accelerates routine tasks. Furthermore, it reduces toil. "
    "Additionally, it frees engineers for deeper work.\n\n"
    "In conclusion, the trajectory is clear and the future looks bright."
)
HUMAN_STRUCTURED = (
    "We turned the automation on for a week to see what stuck.\n\n"
    "It chewed through the boring edits fast. Config, scaffolding, the refactors "
    "I keep putting off. Then it confidently broke a test and lied about why.\n\n"
    "So: useful, with a leash. I read every diff before it lands."
)


def test_discourse_features_reported_in_score():
    out = stylo.score(AI_STRUCTURED, "spontaneous")
    assert "transition_density" in out["features"]
    assert "structural_opener_rate" in out["features"]


def test_discourse_distance_penalizes_ai_structure():
    ai = stylo.score(AI_STRUCTURED, "spontaneous")
    human = stylo.score(HUMAN_STRUCTURED, "spontaneous")
    assert ai["stylo_distance"] > human["stylo_distance"]


def test_discourse_single_paragraph_omits_paragraph_cv():
    # SMALL_HUMAN_TEXT is one paragraph -> paragraph_cv must not appear at all.
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous", ref=TEST_REF)
    assert "paragraph_cv" not in out["features"]


def test_discourse_excluded_from_outlier_veto():
    # A wildly transition-stuffed but otherwise short text must not hard-veto
    # solely on discourse (discourse is excluded from stylo_outlier, like tell_rate).
    stuffed = ("Moreover, x.\n\nFurthermore, y.\n\nAdditionally, z.\n\n"
               "Consequently, w.\n\nHence, v.")
    out = stylo.score(stuffed, "spontaneous")
    assert out["features"]["transition_density"]["value"] > 0
    # outlier is driven by the banded shape features, not discourse:
    assert isinstance(out["stylo_outlier"], bool)
    for name in ("transition_density", "structural_opener_rate"):
        assert abs(out["features"][name]["z"]) <= 3 or out["stylo_outlier"] is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 tests/run.py stylo`
Expected: `test_discourse_features_reported_in_score` and `test_discourse_single_paragraph_omits_paragraph_cv` FAIL (discourse keys absent from `features`); `test_discourse_distance_penalizes_ai_structure` may already pass or fail depending on tells alone — it must pass after Step 3/4.

- [ ] **Step 3a: Add the constants**

In `scripts/stylo.py`, immediately after the `SELF_TELL_WEIGHT` definition (after line 270):

```python
# Weight on discourse-structure overuse (transition flooding, uniform paragraphs,
# thesis/summary scaffolds). Same role as TELL_WEIGHT but for document-level tells.
DISCOURSE_WEIGHT = 0.05

DISCOURSE_KEYS = ("transition_density", "structural_opener_rate", "paragraph_cv")

# Fallback discourse bands per register, used until `make corpus` writes calibrated
# ones into reference-stats.json. Directional: transition_density and
# structural_opener_rate penalize ABOVE ceiling; paragraph_cv penalizes BELOW floor
# (uniform = machine-like) and has no ceiling. "_default" covers not-yet-calibrated
# registers (e.g. Sprint 2 additions).
DEFAULT_DISCOURSE_BANDS = {
    "_default": {
        "transition_density": {"floor": 0.0, "ceiling": 3.0},
        "structural_opener_rate": {"floor": 0.0, "ceiling": 0.08},
        "paragraph_cv": {"floor": 0.35, "ceiling": None},
    },
    "spontaneous": {
        "transition_density": {"floor": 0.0, "ceiling": 2.5},
        "structural_opener_rate": {"floor": 0.0, "ceiling": 0.08},
        "paragraph_cv": {"floor": 0.35, "ceiling": None},
    },
    "scientific": {
        "transition_density": {"floor": 0.0, "ceiling": 4.5},
        "structural_opener_rate": {"floor": 0.0, "ceiling": 0.15},
        "paragraph_cv": {"floor": 0.25, "ceiling": None},
    },
    "literary": {
        "transition_density": {"floor": 0.0, "ceiling": 2.0},
        "structural_opener_rate": {"floor": 0.0, "ceiling": 0.06},
        "paragraph_cv": {"floor": 0.40, "ceiling": None},
    },
}
```

- [ ] **Step 3b: Add the discourse scoring block**

In `score()`, insert the following **after** the `tell_excess = max(...)` line (after line 372) and **before** the `base = statistics.fmean(...)` line (line 374):

```python
    # Discourse structure: one-tailed penalties, handled like tell_rate (separate
    # term, appended to `features` AFTER the outlier veto so it never hard-vetoes).
    disc = discourse(text)
    reg_defaults = DEFAULT_DISCOURSE_BANDS.get(
        register, DEFAULT_DISCOURSE_BANDS["_default"]
    )
    discourse_excess = 0.0
    for name in DISCOURSE_KEYS:
        val = disc.get(name)
        if val is None:  # paragraph_cv on single-paragraph input: omit entirely
            continue
        band = bands.get(name) or reg_defaults[name]
        floor = band.get("floor", 0.0)
        ceiling = band.get("ceiling")
        if name == "paragraph_cv":  # low = uniform = tell
            width = floor or 1.0
            if val < floor:
                status, z = "below", (floor - val) / width
                discourse_excess += z
            else:
                status, z = "in", 0.0
        else:  # high = overuse = tell
            if ceiling is not None and val > ceiling:
                width = ceiling or 1.0
                status, z = "above", (val - ceiling) / width
                discourse_excess += z
            else:
                status, z = "in", 0.0
        features[name] = {
            "value": round(val, 4),
            "floor": floor,
            "ceiling": ceiling,
            "status": status,
            "z": round(z, 4),
        }
```

- [ ] **Step 3c: Fold the term into `stylo_distance`**

Change the `stylo_distance` assignment (currently lines 375-380) to add the discourse term:

```python
    base = statistics.fmean(zs) if zs else 0.0
    stylo_distance = (
        base
        + fw_dist
        + TELL_WEIGHT * tell_excess
        + SELF_TELL_WEIGHT * len(self_tells)
        + DISCOURSE_WEIGHT * discourse_excess
    )
```

- [ ] **Step 4: Run the full suite to verify pass + no regression**

Run: `python3 tests/run.py`
Expected: all new `test_discourse_*` PASS; every pre-existing test (including `test_score_feature_status_values`, `test_score_discriminates_ai_from_human`, `test_overcorrection_penalized_in_distance`) still PASS; final line `N passed, 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/stylo.py tests/test_stylo.py
git commit -m "feat(stylo): score discourse structure into composite distance"
```

---

## Task 3: Calibrate discourse bands in build_reference

**Files:**
- Modify: `scripts/build_reference.py` — add a discourse block in `aggregate()` after the `tell_rate` block (after line 41).
- Test: `tests/test_build_reference.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_build_reference.py`. The existing tests in that file run
`build_reference.py` as a subprocess and never import it, so `scripts/` is NOT on
`sys.path` there. This test imports `aggregate()` directly, so it inserts the path
itself (self-contained — works whether run alone or via the full suite):

```python
def test_aggregate_emits_discourse_bands():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
    import build_reference
    texts = [
        "A short line.\n\nA longer paragraph with rather more words than the first one.",
        "Moreover, this opens with a transition. The next sentence is plain though.",
        "In today's world we begin. Then the story wanders somewhere quieter.",
    ]
    bands, _fw = build_reference.aggregate(texts)
    for key in ("transition_density", "structural_opener_rate", "paragraph_cv"):
        assert key in bands
    # transition_density / structural_opener_rate are high-tail: floor pinned to 0.
    assert bands["transition_density"]["floor"] == 0.0
    assert bands["structural_opener_rate"]["floor"] == 0.0
    # paragraph_cv is low-tail: a floor, no ceiling.
    assert bands["paragraph_cv"]["ceiling"] is None
    assert bands["paragraph_cv"]["floor"] >= 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py build_reference`
Expected: `FAIL tests/test_build_reference.py::test_aggregate_emits_discourse_bands` with `KeyError: 'transition_density'`.

- [ ] **Step 3: Implement the calibration block**

In `scripts/build_reference.py`, inside `aggregate()`, insert after the `tell_rate` block (after line 41, before the `fw_rows = ...` line):

```python
    # Discourse structure: one-tailed, so calibrated asymmetrically here and stored
    # under `bands` but consumed by score()'s dedicated discourse block (like
    # tell_rate), NOT by the symmetric FEATURE_KEYS loop above.
    disc_rows = [stylo.discourse(t) for t in texts]
    for key in ("transition_density", "structural_opener_rate"):
        vals = [r[key] for r in disc_rows]
        m = statistics.fmean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        bands[key] = {"floor": 0.0, "ceiling": round(m + 1.5 * sd, 4)}
    # paragraph_cv: low tail is the tell; floor only, over multi-paragraph texts.
    pcv = [r["paragraph_cv"] for r in disc_rows if r["paragraph_cv"] is not None]
    if pcv:
        m = statistics.fmean(pcv)
        sd = statistics.pstdev(pcv) if len(pcv) > 1 else 0.0
        bands["paragraph_cv"] = {"floor": round(max(0.0, m - 1.5 * sd), 4),
                                 "ceiling": None}
    else:
        bands["paragraph_cv"] = {"floor": 0.0, "ceiling": None}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py build_reference`
Expected: `test_aggregate_emits_discourse_bands` PASS; existing build_reference tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_reference.py tests/test_build_reference.py
git commit -m "feat(build_reference): calibrate asymmetric discourse bands"
```

---

## Task 4: Enrich the AI-tell catalog

**Files:**
- Modify: `lexicons/ai_tells.json` — extend entry id 7, add entries 34–37.
- Test: `tests/test_lexicon.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_lexicon.py`:

```python
def test_new_post2023_entries_present():
    names = {e["name"] for e in LEX}
    for n in ("transitional_overuse", "era_framing", "structural_formulas",
              "hollow_affirmatives"):
        assert n in names, f"missing new entry: {n}"


def test_extended_ai_vocabulary_terms():
    flat = {t.lower() for e in LEX for t in e["terms"]}
    for w in ("shed light on", "pave the way for", "state-of-the-art",
              "game-changing", "cutting-edge", "unpack", "deep dive"):
        assert w in flat, f"missing extended vocab term: {w}"


def test_new_entry_regexes_fire():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
    import stylo
    hits = stylo.tell_hits(
        "Moreover, this matters. In today's world, first and foremost we adapt. "
        "Absolutely! It is a deep dive that will shed light on the topic.", LEX)
    assert hits["transitional_overuse"] >= 1
    assert hits["era_framing"] >= 1
    assert hits["structural_formulas"] >= 1
    assert hits["hollow_affirmatives"] >= 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 tests/run.py lexicon`
Expected: `test_new_post2023_entries_present`, `test_extended_ai_vocabulary_terms`, `test_new_entry_regexes_fire` FAIL.

- [ ] **Step 3a: Extend entry id 7 (`ai_vocabulary`)**

In `lexicons/ai_tells.json`, find the entry `"id": 7` (the `ai_vocabulary` terms array). Append these terms to its existing `"terms"` list (keep the existing terms; do not remove any; `"navigate the"` is already present so it is NOT repeated):

```json
"shed light on", "pave the way for", "state-of-the-art", "game-changing",
"cutting-edge", "unpack", "deep dive", "at the forefront", "harness the power"
```

- [ ] **Step 3b: Add the four new entries**

In `lexicons/ai_tells.json`, add these four objects to the top-level array (e.g. before the closing `]`; mind the comma after the previous last entry):

```json
{
  "id": 34,
  "name": "transitional_overuse",
  "category": "discourse",
  "terms": [],
  "regexes": ["(?:^|[.?!]\\s+)(?:Moreover|Furthermore|Additionally|Consequently|Notably|Importantly|Hence)\\b"]
},
{
  "id": 35,
  "name": "era_framing",
  "category": "language",
  "terms": ["in today's", "in an era of", "in the age of", "in the realm of", "in the world of", "in the rapidly evolving", "in this digital age"],
  "regexes": []
},
{
  "id": 36,
  "name": "structural_formulas",
  "category": "filler",
  "terms": ["first and foremost", "last but not least", "let's explore", "let's unpack", "let's dive deeper", "to summarize", "without further ado", "the bottom line is"],
  "regexes": []
},
{
  "id": 37,
  "name": "hollow_affirmatives",
  "category": "communication",
  "terms": [],
  "regexes": ["(?:^|[.?!]\\s+)(?:Absolutely|Certainly|Indeed)[!,]", "(?:^|[.?!]\\s+)Great question[!.]", "(?:^|[.?!]\\s+)Of course[!,]"]
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 tests/run.py lexicon`
Expected: all three new tests PASS; existing `test_lexicon_shape` (checks unique ids, compiling regexes), `test_known_terms_present`, `test_names_unique` still PASS; `N passed, 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add lexicons/ai_tells.json tests/test_lexicon.py
git commit -m "feat(lexicon): post-2023 LLMisms (transitions, era framing, affirmatives)"
```

---

## Task 5: Recalibrate the three registers and commit updated stats

This single recalibration picks up BOTH the new discourse bands (Task 3) and the shifted `tell_rate` ceiling caused by the enriched lexicon (Task 4). Raw corpora are present locally, so no fetch is needed.

**Files:**
- Regenerate + commit: `corpus/{spontaneous,scientific,literary}/reference-stats.json`

- [ ] **Step 1: Recalibrate all three registers**

```bash
python3 scripts/build_reference.py --register spontaneous
python3 scripts/build_reference.py --register scientific
python3 scripts/build_reference.py --register literary
```
Expected: three `wrote corpus/<reg>/reference-stats.json (120 texts)` lines.

- [ ] **Step 2: Verify the new bands landed**

Run:
```bash
python3 -c "import json; b=json.load(open('corpus/literary/reference-stats.json'))['bands']; print({k:b[k] for k in ('transition_density','structural_opener_rate','paragraph_cv','tell_rate')})"
```
Expected: all four keys present; `paragraph_cv` has `"ceiling": null`; `transition_density`/`structural_opener_rate` have `"floor": 0.0`.

- [ ] **Step 3: Run the full test suite against the recalibrated stats**

Run: `python3 tests/run.py`
Expected: `N passed, 0 failed`. (The live-data tests `test_score_discriminates_ai_from_human` / `test_score_tell_density_enters_distance` now run against recalibrated bands and must still pass.)

- [ ] **Step 4: Commit**

```bash
git add corpus/spontaneous/reference-stats.json corpus/scientific/reference-stats.json corpus/literary/reference-stats.json
git commit -m "chore(corpus): recalibrate 3 registers with discourse + enriched tells"
```

---

## Task 6: Eval regression check (no register regresses)

**Files:**
- Read-only run of `eval/run_eval.py` against the committed `eval/out/<reg>/*.{baseline,pro}.txt`.

- [ ] **Step 1: Run the eval for all three registers**

```bash
python3 eval/run_eval.py --register spontaneous
python3 eval/run_eval.py --register scientific
python3 eval/run_eval.py --register literary
```
Expected: each prints `stylometric: pro closer-to-human on N/N samples` with `pro` winning every sample (spontaneous 5/5, scientific 4/4, literary 4/4), matching `eval/REPORT.md`.

- [ ] **Step 2: If any sample regressed, diagnose — do NOT loosen bands to pass**

If `pro` loses a sample, compare the two scorecards directly:
```bash
python3 scripts/stylo.py eval/out/<reg>/<name>.pro.txt --register <reg>
python3 scripts/stylo.py eval/out/<reg>/<name>.baseline.txt --register <reg>
```
Inspect the `features` block. A regression most likely means a discourse default/calibrated band is too tight for that register (e.g. a literary `pro` rewrite legitimately uses a transition). The fix is to correct the band in `DEFAULT_DISCOURSE_BANDS` or accept the calibrated value — **never** edit the eval output text to win. Re-run Step 1 after any band fix, then re-commit Task 5's stats if calibration logic changed.

- [ ] **Step 3: Commit (only if Step 2 changed code)**

```bash
git add scripts/stylo.py
git commit -m "fix(stylo): adjust discourse default band after eval regression"
```
If no regression occurred, skip this commit.

---

## Task 7: Document the new scorecard fields and tag v0.2.0

**Files:**
- Modify: `SKILL.md` (the "Score each candidate" section and the "Output" scorecard list)
- Modify: `README.md` (feature summary)
- Modify: `CHANGELOG.md` (new version entry)

- [ ] **Step 1: Update SKILL.md scorecard description**

In `SKILL.md`, in step 2 ("Score each candidate"), after the line that reads back `stylo_distance`, `self_tell_flags`, `stylo_outlier`, `features`, add discourse to the readback list. Change:

```
  Read back `stylo_distance`, `self_tell_flags`, `stylo_outlier`, `features`.
```
to:
```
  Read back `stylo_distance`, `self_tell_flags`, `stylo_outlier`, `features`
  (now including the discourse features `transition_density`,
  `structural_opener_rate`, and `paragraph_cv` — high transition/opener rates and
  a low paragraph_cv are document-level AI tells).
```

In the step 5 "Output" scorecard list, change:
```
   (`p_ai`/`register_fit`/`fidelity`), `stylo_distance`, tells removed vs. source,
   `self_tell_flags` avoided, iterations used.
```
to:
```
   (`p_ai`/`register_fit`/`fidelity`), `stylo_distance`, tells removed vs. source,
   discourse status (transition/opener/paragraph_cv), `self_tell_flags` avoided,
   iterations used.
```

- [ ] **Step 2: Update README.md**

In `README.md`, find the bullet describing the stylometric scorer's features and append discourse to it. Locate the sentence listing "sentence-length burstiness, lexical diversity (MTLD), function-word fingerprint, punctuation rates, AI-tell density" and add ", and document-level discourse structure (transition overuse, paragraph uniformity, thesis/summary scaffolds)" before the period. (If the README has no such bullet, add a new line under the scorer description: `- Document-level discourse features: transition overuse, uniform paragraphs, thesis/summary scaffolds.`)

- [ ] **Step 3: Add the CHANGELOG entry**

In `CHANGELOG.md`, insert above the `## 0.1.0` heading:

```markdown
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
- **Recalibrated** all three registers; evals show no regression (spontaneous 5/5,
  scientific 4/4, literary 4/4).
```

- [ ] **Step 4: Run the full suite one last time**

Run: `python3 tests/run.py`
Expected: `N passed, 0 failed`.

- [ ] **Step 5: Commit and tag**

```bash
git add SKILL.md README.md CHANGELOG.md
git commit -m "docs: document discourse scorecard fields; CHANGELOG 0.2.0"
git tag v0.2.0
```

- [ ] **Step 6: Push (only if the user asks to publish)**

```bash
git push origin main --tags
```
(The repo's remote is `origin` → `github.com/jodyjdc/better-humanizer`. Do not push unless the user requests it.)

---

## Self-Review (completed during planning)

**Spec coverage:** Every Sprint-1 requirement in `2026-06-14-humanizer-v2-roadmap-design.md` maps to a task — discourse features (Tasks 1–3), `DISCOURSE_WEIGHT` + fallback bands + outlier exclusion + null handling (Task 2), asymmetric calibration (Task 3), ~25 new tell patterns (Task 4), recalibration (Task 5), no-regression eval (Task 6), SKILL.md/CHANGELOG + v0.2.0 (Task 7).

**Placeholder scan:** No TBD/TODO/"handle edge cases". Every code step shows complete code; every test step shows the full test; every run step shows the command and expected output.

**Type/name consistency:** `discourse()` returns keys `transition_density` / `structural_opener_rate` / `paragraph_cv`; the same three names are used as `DISCOURSE_KEYS`, as band keys written by `build_reference.aggregate()`, and as `features` entries read by the eval and tests. `DISCOURSE_WEIGHT`, `DEFAULT_DISCOURSE_BANDS` (with `_default`), `_paragraphs`, `_sentence_starts_with`, `PARA_SPLIT_RE`, `TRANSITION_OPENERS`, `STRUCTURAL_OPENERS` are each defined once and referenced consistently. `paragraph_cv` is the one feature with `ceiling: None` and a floor-only penalty everywhere it appears.
