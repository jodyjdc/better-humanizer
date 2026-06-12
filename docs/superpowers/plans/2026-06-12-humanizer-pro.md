# humanizer-pro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a measured, self-improving text rewriter (Claude Code skill + scripts) whose target is the real human distribution for the spontaneous register, and prove it beats the original humanizer in a blind A/B.

**Architecture:** A loop generates K candidate rewrites, scores each with a hybrid scorer (std-lib stylometrics + an LLM judge panel), applies vetoes, selects the best, and iterates using the judges' critique as the gradient. Stylometrics are calibrated against a human reference corpus; the human band has a floor AND a ceiling, so over-correction (e.g. zero em dashes) is itself flagged.

**Tech Stack:** Python 3 standard library only (no pip) for `stylo.py`; Markdown prompt files for the skill, register profile, and judges; `pytest` for tests (the only dev dependency).

---

## File structure (decomposition)

| File | Responsibility |
|---|---|
| `lexicons/ai_tells.json` | The 33 Wikipedia tell patterns as machine-readable terms/regexes. Shared by scorer + judges. |
| `scripts/stylo.py` | Pure-stdlib stylometric scorer. Features, bands, self-tell flags, composite distance, CLI + importable API. |
| `scripts/build_reference.py` | Build `reference-stats.json` (per-feature bands) from a corpus. |
| `corpus/spontaneous/reference-stats.json` | Default heuristic bands (`calibrated:false`), overwritten by real data. |
| `corpus/spontaneous/CORPUS.md` | Sourcing protocol for human reference texts. |
| `registers/spontaneous.md` | Register profile: bands intent, generation guidance, tell priority. |
| `judges/{detector,register,meaning}.md` | Three independent judge-lens rubrics. |
| `SKILL.md` | `/humanizer-pro` orchestrator: the loop, weights, vetoes, K/k/threshold. |
| `eval/run_eval.py` + `eval/ai_samples/*.txt` + `eval/REPORT.md` | Blind A/B proof harness. |
| `tests/test_stylo.py`, `tests/test_build_reference.py` | Unit tests for the deterministic core. |
| `README.md` | What it is, how to run, how it differs from the original. |

Conventions: punctuation/tell **rates** are normalized **per 100 tokens** unless noted. All public `stylo.py` functions take already-read `text: str`. `register` selects the band set from `reference-stats.json`.

---

### Task 1: Tell lexicon

**Files:**
- Create: `lexicons/ai_tells.json`
- Test: `tests/test_lexicon.py`

Port the 33 patterns from the original SKILL.md into one machine-readable file. Schema per entry:
```json
{
  "id": 7,
  "name": "ai_vocabulary",
  "category": "language",
  "terms": ["delve", "tapestry", "underscore", "pivotal", "..."],
  "regexes": ["\\bnot just\\b.*\\bbut\\b"]
}
```
`terms` are matched case-insensitively as whole words; `regexes` are Python `re` patterns. Cover at least: significance words (#1), promotional (#4), -ing analyses (#3), AI vocabulary (#7), copula-avoidance verbs (#8), negative parallelism (#9), persuasive-authority (#27), signposting (#28), aphorism formulas (#32), conversational openers (#33).

- [ ] **Step 1: Write the failing test**
```python
# tests/test_lexicon.py
import json, re, pathlib
LEX = json.loads((pathlib.Path(__file__).parent.parent / "lexicons/ai_tells.json").read_text())

def test_lexicon_shape():
    assert len(LEX) >= 10
    for e in LEX:
        assert {"id", "name", "category", "terms", "regexes"} <= e.keys()
        for rx in e["regexes"]:
            re.compile(rx)  # must compile

def test_known_terms_present():
    flat = {t.lower() for e in LEX for t in e["terms"]}
    for w in ("delve", "tapestry", "underscore", "pivotal", "nestled"):
        assert w in flat
```
- [ ] **Step 2: Run, verify fail** — `pytest tests/test_lexicon.py -v` → FAIL (file missing).
- [ ] **Step 3: Write `lexicons/ai_tells.json`** with the entries above.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: machine-readable AI tell lexicon"`

---

### Task 2: stylo.py — segmentation + structural metrics (TDD)

**Files:**
- Create: `scripts/stylo.py`
- Test: `tests/test_stylo.py`

Implement: `tokenize(text)->list[str]` (regex `[A-Za-z']+`, lowercased), `split_sentences(text)->list[str]` (split on `[.!?]+` followed by space/EOL/quote; drop empties), `sentence_lengths(text)->list[int]` (tokens per sentence), `burstiness(text)->dict` (`{mean,sd,cv}` of sentence lengths via `statistics`; cv=sd/mean, 0 if mean 0), `lexical(text)->dict` (`ttr`, `mtld`, `hapax_ratio`, `mean_word_len`).

MTLD (forward+backward, threshold 0.72): walk tokens accumulating TTR; each time TTR drops to/below 0.72, increment factor count and reset; partial factor = `(1-ttr)/(1-0.72)`; `mtld_one_dir = n_tokens / total_factors`; return mean of forward and backward passes. Guard < 50 tokens → return TTR-based fallback (document it).

- [ ] **Step 1: Write failing tests**
```python
# tests/test_stylo.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo

def test_tokenize_and_sentences():
    t = "Hello world. I can't stop! Really?"
    assert stylo.tokenize(t) == ["hello","world","i","can't","stop","really"]
    assert len(stylo.split_sentences(t)) == 3

def test_sentence_lengths_and_burstiness():
    t = "One two three. Four. Five six."
    assert stylo.sentence_lengths(t) == [3, 1, 2]
    b = stylo.burstiness(t)
    assert b["mean"] == 2 and b["sd"] > 0 and b["cv"] > 0

def test_lexical_basic():
    lx = stylo.lexical("the cat sat on the mat and the cat ran")
    assert 0 < lx["ttr"] <= 1
    assert lx["hapax_ratio"] > 0
    assert lx["mean_word_len"] > 0

def test_burstiness_uniform_is_low_cv():
    uniform = stylo.burstiness("aa aa aa. bb bb bb. cc cc cc.")
    assert uniform["cv"] == 0  # AI-flat rhythm → cv 0
```
- [ ] **Step 2: Run, verify fail** — `pytest tests/test_stylo.py -v` → FAIL (no module).
- [ ] **Step 3: Implement the functions** in `scripts/stylo.py`.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git commit -am "feat: stylo segmentation + structural metrics"`

---

### Task 3: stylo.py — punctuation, structural tells, lexicon hits, function words (TDD)

**Files:** Modify `scripts/stylo.py`; Test: `tests/test_stylo.py`

Implement (all rates **per 100 tokens** unless a count): `punctuation_rates(text)->dict` (keys: `comma,period,em_dash,en_dash,semicolon,colon,paren,question,exclaim`; em dash = `—` and ` -- `; en dash = `–`), `contraction_rate(text)`, `structural(text)->dict` (`emoji,bold,bullet,titlecase_heading` counts; emoji via unicode ranges; bold via `**...**`; bullet via line-leading `[-*]`/`\d+.`; titlecase heading via markdown `#` line where >60% words capitalized), `tell_hits(text, lexicon)->dict` (per-entry name→count using whole-word term match + regex search), `rule_of_three(text)->int` (`X, Y, and Z` / `X, Y, Z` heuristic), `function_word_vector(text, fw_list)->dict` (normalized counts over a built-in ~150 English function-word list `FUNCTION_WORDS`), `cosine_distance(a,b)->float`.

- [ ] **Step 1: Write failing tests**
```python
def test_punctuation_em_dash():
    p = stylo.punctuation_rates("A — b, c; d -- e.")
    assert p["em_dash"] > 0 and p["comma"] > 0 and p["semicolon"] > 0

def test_structural_tells():
    s = stylo.structural("## Big Title Here\n- one\n- two\n**bold** 🚀")
    assert s["bullet"] == 2 and s["bold"] == 1 and s["emoji"] == 1 and s["titlecase_heading"] == 1

def test_tell_hits_counts(tmp_path):
    lex = [{"id":7,"name":"ai_vocabulary","category":"language","terms":["delve","tapestry"],"regexes":[]}]
    h = stylo.tell_hits("We delve into the rich tapestry of delve.", lex)
    assert h["ai_vocabulary"] == 3

def test_rule_of_three():
    assert stylo.rule_of_three("speed, quality, and adoption matter") >= 1

def test_cosine_distance_identity():
    v = stylo.function_word_vector("the the of and to the", stylo.FUNCTION_WORDS)
    assert stylo.cosine_distance(v, v) < 1e-9
```
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git commit -am "feat: stylo punctuation, tells, function-word vector"`

---

### Task 4: stylo.py — score() with bands, self-tell flags, vetoes + CLI (TDD)

**Files:** Modify `scripts/stylo.py`; Test: `tests/test_stylo.py`

Implement `load_reference(register)->dict` (reads `corpus/<register>/reference-stats.json`), `score(text, register)->dict`. `score` assembles every feature, and for each **banded** feature computes `status` (`below`/`in`/`above`) vs `{floor,ceiling}` and a `z` = signed distance past the nearest band edge / band_width. `self_tell_flags` = features whose `status=="below"` for the **over-correction set** (`em_dash_rate`, `sentence_length_cv`, `contraction_rate`, `rule_of_three`) PLUS any structural-tell that is zero where the human floor is > 0. `stylo_distance` = mean of `abs(z)` over banded features + function-word cosine distance. Vetoes: `stylo_outlier = any abs(z) > 3`. Output dict exactly:
```json
{"register":"spontaneous","features":{"sentence_length_cv":{"value":..,"floor":..,"ceiling":..,"status":"below","z":-1.2}, "...":{}},
 "tells":{"ai_vocabulary":0,"...":0}, "self_tell_flags":["em_dash_rate","sentence_length_cv"],
 "stylo_distance":0.41, "stylo_outlier":false}
```
CLI: `python scripts/stylo.py <file> --register spontaneous` prints the JSON (indent 2). Use `argparse`, `if __name__=="__main__"`.

- [ ] **Step 1: Write failing tests**
```python
def test_score_flags_over_correction(tmp_path, monkeypatch):
    # text with zero em dashes and flat rhythm should self-tell-flag
    flat = "I went there. I saw it. I left then. It was fine. Nothing else."
    out = stylo.score(flat, "spontaneous")
    assert "sentence_length_cv" in out["self_tell_flags"]
    assert out["stylo_distance"] >= 0
    assert set(["register","features","tells","self_tell_flags","stylo_distance","stylo_outlier"]) <= out.keys()

def test_score_human_like_passes(small_human_text):
    out = stylo.score(small_human_text, "spontaneous")
    assert out["stylo_outlier"] is False
```
(Define `small_human_text` fixture in `tests/conftest.py` as a short, varied, real-style paragraph with mixed sentence lengths and one em dash.)
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement `load_reference`, `score`, CLI.** (Depends on Task 5's default `reference-stats.json`; if running strictly in order, write a minimal stub stats file first, then Task 5 finalizes it.)
- [ ] **Step 4: Run, verify pass** — also smoke the CLI: `echo "Hello there." > /tmp/t.txt && python scripts/stylo.py /tmp/t.txt --register spontaneous`.
- [ ] **Step 5: Commit** — `git commit -am "feat: stylo score(), self-tell flags, CLI"`

---

### Task 5: Reference builder + default bands + corpus protocol

**Files:**
- Create: `scripts/build_reference.py`, `corpus/spontaneous/reference-stats.json`, `corpus/spontaneous/CORPUS.md`
- Test: `tests/test_build_reference.py`

`build_reference.py`: read all `corpus/<register>/*.txt`, run each through `stylo` feature extractors, aggregate mean+SD per feature, set `floor=mean-1.0*SD` (clamped ≥0) and `ceiling=mean+1.5*SD`, write `reference-stats.json` with `calibrated:true, n_texts:N, function_word_vector:<avg>`. With 0 texts, leave the shipped heuristic file untouched and print a warning.

Default `reference-stats.json` (heuristic English spontaneous, `calibrated:false`) bands — reasonable starting values, NOT fabricated citations; refine with real data:
```json
{"register":"spontaneous","calibrated":false,"n_texts":0,
 "bands":{
   "sentence_length_mean":{"floor":9,"ceiling":24},
   "sentence_length_cv":{"floor":0.45,"ceiling":1.05},
   "mtld":{"floor":50,"ceiling":120},
   "ttr":{"floor":0.40,"ceiling":0.75},
   "hapax_ratio":{"floor":0.35,"ceiling":0.70},
   "em_dash_rate":{"floor":0.05,"ceiling":1.5},
   "comma_rate":{"floor":4,"ceiling":12},
   "contraction_rate":{"floor":0.8,"ceiling":6},
   "rule_of_three":{"floor":0,"ceiling":2},
   "exclaim":{"floor":0,"ceiling":2},
   "bold":{"floor":0,"ceiling":1},
   "emoji":{"floor":0,"ceiling":1}},
 "function_word_vector":{}}
```
`CORPUS.md`: rules — genuinely human, license-clean, bias to pre-2022; safe sources (your own writing = personalization; public-domain letters/diaries; permissively-licensed corpora); how to run `build_reference.py`; ethical note (no scraping behind paywalls/ToS).

- [ ] **Step 1: Write failing test**
```python
# tests/test_build_reference.py
import json, subprocess, sys, pathlib
def test_build_over_fixture(tmp_path):
    reg = tmp_path / "corpus" / "spontaneous"; reg.mkdir(parents=True)
    (reg / "a.txt").write_text("Short one. A much longer sentence that keeps going for a while, with commas. Mid one here.")
    (reg / "b.txt").write_text("I can't even. Honestly it's wild — really wild. Then it stopped.")
    root = pathlib.Path(__file__).parent.parent
    out = subprocess.run([sys.executable, str(root/"scripts/build_reference.py"),
                          "--register","spontaneous","--corpus-root",str(tmp_path/"corpus"),
                          "--out",str(tmp_path/"stats.json")], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    stats = json.loads((tmp_path/"stats.json").read_text())
    assert stats["calibrated"] is True and stats["n_texts"] == 2
    assert stats["bands"]["sentence_length_cv"]["ceiling"] >= stats["bands"]["sentence_length_cv"]["floor"]
```
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement `build_reference.py`; write default `reference-stats.json` + `CORPUS.md`.**
- [ ] **Step 4: Run, verify pass** + re-run Task 4 tests (now real stats file exists).
- [ ] **Step 5: Commit** — `git commit -am "feat: reference builder, default bands, corpus protocol"`

---

### Task 6: Register profile (spontaneous)

**Files:** Create `registers/spontaneous.md`

Content (no code, this IS the deliverable). Sections required:
- **What human spontaneous writing looks like**: uneven rhythm, contractions, fragments, asides/parentheticals, mild redundancy, a personal stance, the occasional em dash and triad. Cite the band targets by name (defer numbers to `reference-stats.json`).
- **Generation guidance** (for the rewriter): allow `is/are/has`; allow ONE em dash and ONE triad if natural; vary sentence length deliberately; first person OK; keep specific concrete detail.
- **Tell priority for this register**: which of the 33 matter most here (significance inflation, -ing padding, AI vocabulary, rule-of-three overuse, copula avoidance, sycophancy, signposting) and which are acceptable in moderation (a single em dash, one triad, casual register mixing).
- **Anti-over-correction rule**: state explicitly that zero em dashes / flat rhythm / zero contractions are themselves tells; aim for the human band, not the extreme.

- [ ] **Step 1: Write `registers/spontaneous.md`** with all sections above.
- [ ] **Step 2: Commit** — `git commit -am "docs: spontaneous register profile"`

---

### Task 7: Judge panel rubrics

**Files:** Create `judges/detector.md`, `judges/register.md`, `judges/meaning.md`

Each is a self-contained rubric prompt that takes `{source}` and `{candidate}` and returns strict JSON.
- `detector.md` (adversarial): "You are an expert AI-text detector. Find concrete tells in CANDIDATE. Return `{p_ai:0-100, tells:[{quote,why}], critique:[...]}`." Emphasize: judge the *candidate alone* as if found in the wild.
- `register.md`: "Does CANDIDATE read like genuine human spontaneous writing (blog/forum/email)? Return `{register_fit:0-100, breaks:[...], critique:[...]}`."
- `meaning.md`: "Compare CANDIDATE to SOURCE. Return `{fidelity:0-100, dropped:[...], added:[...], distorted:[...]}`. fidelity<70 is a hard fail."

State the aggregation in each file's header comment: loop reads all three, `judge_score = mean(100-p_ai, register_fit, fidelity)` with `fidelity` as a hard veto floor (70).

- [ ] **Step 1: Write the three files.**
- [ ] **Step 2: Commit** — `git commit -am "docs: judge panel rubrics"`

---

### Task 8: SKILL.md orchestrator

**Files:** Create `SKILL.md`

Frontmatter (`name: humanizer-pro`, description, `allowed-tools: Read, Write, Edit, Bash, AskUserQuestion`). Body defines the loop precisely:
1. Inputs: text, `register` (default spontaneous), optional voice sample.
2. **Generate K=3** candidate rewrites with distinct strategies (A: minimal surface fixes; B: rhythm+voice rework; C: aggressive restructure), each guided by `registers/<register>.md` and `lexicons/ai_tells.json`.
3. For each candidate: run `python scripts/stylo.py` (Bash) → stylo scorecard; run the three judges (`judges/*.md`) as inline lenses or sub-agents → judge scorecard.
4. `composite = 0.65*judge_score + 0.35*(100*(1 - min(stylo_distance,1)))`. **Vetoes**: drop candidate if `fidelity<70` OR `stylo_outlier`. **Penalty**: `-5` per `self_tell_flag`.
5. Select best composite. If `best < 85` and iterations `< k=2`: feed that candidate + its concatenated `critique` lists back into a targeted rewrite, re-score.
6. Output: final text + a compact **scorecard** (judge breakdown, stylo_distance, tells removed vs source, self-tells avoided, iterations used). No em/en dash post-check is NOT applied (anti-over-correction: defer to bands).
- Document the `Workflow`-tool option for fanning out K candidates + 3 judges in parallel, with the sequential path as fallback.
- Reference the original's pattern catalog by pointing to `lexicons/ai_tells.json` (single source of truth), not re-listing.

- [ ] **Step 1: Write `SKILL.md`.**
- [ ] **Step 2: Sanity check** — values referenced (K, k, weights, veto floor) match this plan and Task 7.
- [ ] **Step 3: Commit** — `git commit -am "feat: humanizer-pro orchestrator skill"`

---

### Task 9: Eval harness (proof it beats the original)

**Files:** Create `eval/run_eval.py`, `eval/ai_samples/*.txt` (5 seed AI texts), `eval/REPORT.md`

`run_eval.py`: for each `ai_samples/*.txt`, load the **baseline** output and the **pro** output (the script consumes pre-generated rewrites from `eval/out/<name>.baseline.txt` and `eval/out/<name>.pro.txt`, since generation is LLM-driven via the skill), then compute for both: `stylo.score` distance + a **blind** judge verdict. Print a table: per-sample winner (more human), meaning-fidelity for both, mean stylo distance each. The blind judge prompt lives in `eval/judge_blind.md` and is **distinct** from `judges/*` (independent panel). `REPORT.md` is the template the results get written into.

- [ ] **Step 1: Write `eval/run_eval.py` + `eval/judge_blind.md` + 5 `ai_samples/*.txt` + `eval/REPORT.md` template.**
- [ ] **Step 2: Smoke test** — `python eval/run_eval.py --dry-run` lists samples and exits 0 (no rewrites yet).
- [ ] **Step 3: Commit** — `git commit -am "feat: blind A/B eval harness"`

---

### Task 10: README

**Files:** Create `README.md`

Cover: what it is (measured humanizer), the core idea (target the human distribution, floor+ceiling, self-tell flags), how to run (`/humanizer-pro`, `stylo.py`, `build_reference.py`, `run_eval.py`), how it differs from `blader/humanizer` (measurement loop, register awareness, anti-over-correction), and the explicit non-goal (no commercial-detector evasion). Link the spec.

- [ ] **Step 1: Write `README.md`.**
- [ ] **Step 2: Commit** — `git commit -am "docs: README"`

---

## Self-Review

**Spec coverage:** measurement loop → Task 8; hybrid scorer → Tasks 2-5,7; register profile → Task 6; reference corpus → Task 5; self-tell/anti-over-correction → Tasks 4,6; judge panel → Task 7; lexicon → Task 1; eval/success criterion → Task 9; non-goals → Tasks 8,10. All spec sections map to a task.

**Placeholder scan:** test code is concrete; markdown tasks specify exact required sections. Heuristic default bands are intentional and labeled, not TBD.

**Type consistency:** `score()` output keys (`features,tells,self_tell_flags,stylo_distance,stylo_outlier`) are reused identically in Tasks 4, 8, 9. `judge_score`/`fidelity`/`composite` defined in Task 7 and consumed in Task 8 with matching names. `reference-stats.json` band keys in Task 5 match the features computed in Tasks 2-3 and read in Task 4.

**Known ordering note:** Task 4 depends on a stats file finalized in Task 5; handled by a minimal stub in Task 4 step 3, finalized in Task 5 step 4.
