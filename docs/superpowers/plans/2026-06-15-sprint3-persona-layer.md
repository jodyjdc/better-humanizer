# Sprint 3 — Persona Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Let the humanizer target a *specific writer* — the user's own voice, an expertise level, or a named persona — while keeping every target measured on real data.

**Architecture:** One mechanism — `score()` compares against a selectable **band-set**. Add: (a) Flesch–Kincaid-tercile expertise band-sets per register, (b) voice band-sets calibrated from user text (with a small-sample blend), (c) personas = register+tier+lexicon overrides. Resolution precedence: persona > voice > expertise > register. All new flags optional; no flag = v0.3.0 behavior exactly.

**Tech Stack:** Python 3 stdlib only; stdlib test runner (`python3 tests/run.py`).

---

## Background for the engineer

- `scripts/stylo.py` is the scorer. Key existing pieces:
  - `tokenize(text)` → word tokens; `split_sentences(text)` → sentence strings.
  - `load_reference(register)` → reads `corpus/<register>/reference-stats.json`.
  - `tell_hits(text, lexicon)` → per-entry tell counts; `_term_pattern(term)` builds the word-boundary regex.
  - `score(text, register="spontaneous", ref=None)` → resolves `ref` (defaults to `load_reference(register)`), computes banded features, `tell_rate`, discourse, composite `stylo_distance`. The tell line is `tells = tell_hits(text, _load_lexicon())`.
  - `_main()` argparse currently has only `file` + `--register`.
- `scripts/build_reference.py` has `aggregate(texts) -> (bands, fw)` and a `main()` that reads `corpus/<reg>/**/*.txt`, calls `aggregate`, writes `reference-stats.json`. Raw corpora (120 texts/register) are present locally.
- Test runner: `python3 tests/run.py <substr>` runs matching `tests/test_*.py`. Tests are plain `test_*` functions with `assert`.
- The 7 registers: spontaneous, scientific, literary, business, journalism, social-media, technical-docs.

---

## File structure

- `scripts/stylo.py` — add `_count_syllables`, `flesch_kincaid_grade`; extend `load_reference` with `expertise`; add `load_bands`, `load_persona`; add `allow`/`deny` to `tell_hits` and `score`; extend `_main` CLI + a `_resolve_target` helper.
- `scripts/build_reference.py` — add `expertise_tiers()` + emit `expertise-{novice,expert}.json`; add `--voice-sample/--label/--register` path with blend.
- `personas/{reddit-power-user,seasoned-journalist,startup-founder,academic-humanist}.json` — create.
- `corpus/<reg>/expertise-{novice,expert}.json` — generated + committed (14 files).
- `voices/` — gitignored.
- `tests/test_expertise.py`, `tests/test_voice.py`, `tests/test_persona.py` — create.
- `eval/REPORT.md`, `README.md`, `SKILL.md`, `AGENTS.md`, `CHANGELOG.md` — update; tag `v1.0.0`.

---

## Task 1: Flesch–Kincaid readability in stylo.py

**Files:** Modify `scripts/stylo.py` (add after `flesch`?? no — add after the `lexical()` block, near other text metrics, before the "Composite scoring" section). Test: `tests/test_expertise.py` (new).

- [ ] **Step 1: Write the failing tests** — create `tests/test_expertise.py`:

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402


def test_count_syllables():
    assert stylo._count_syllables("cat") == 1
    assert stylo._count_syllables("cake") == 1          # silent trailing e
    assert stylo._count_syllables("table") == 2         # -le keeps its syllable
    assert stylo._count_syllables("syllable") == 3
    assert stylo._count_syllables("running") == 2
    assert stylo._count_syllables("") == 0


def test_flesch_kincaid_grade_orders_by_complexity():
    simple = "The cat sat on the mat. The dog ran. We had fun all day."
    dense = ("The epistemological ramifications of phenomenological inquiry "
             "necessitate a reconsideration of foundational presuppositions "
             "underlying contemporary hermeneutic methodologies.")
    assert stylo.flesch_kincaid_grade(dense) > stylo.flesch_kincaid_grade(simple)


def test_flesch_kincaid_grade_empty_is_zero():
    assert stylo.flesch_kincaid_grade("") == 0.0
```

- [ ] **Step 2: Run to verify fail** — `python3 tests/run.py expertise` → FAIL (`_count_syllables` missing).

- [ ] **Step 3: Implement** — in `scripts/stylo.py`, add immediately after the `lexical(text)` function (it ends right before the `# Punctuation, structure, contractions` banner):

```python
# --------------------------------------------------------------------------
# Readability (Flesch-Kincaid grade) — the expertise axis
# --------------------------------------------------------------------------
_VOWELS = "aeiouy"


def _count_syllables(word):
    """Heuristic syllable count: vowel groups, with the trailing-silent-e rule
    (but '-le' endings keep their syllable: table -> 2, cake -> 1)."""
    word = word.lower()
    if not word:
        return 0
    count, prev_vowel = 0, False
    for ch in word:
        is_v = ch in _VOWELS
        if is_v and not prev_vowel:
            count += 1
        prev_vowel = is_v
    if word.endswith("e") and not word.endswith("le") and count > 1:
        count -= 1
    return max(1, count)


def flesch_kincaid_grade(text):
    """Flesch-Kincaid grade level: higher = more advanced/complex prose.
    The standard readability index; here it is the measured expertise axis."""
    sents = split_sentences(text)
    words = tokenize(text)
    if not sents or not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    return 0.39 * (len(words) / len(sents)) + 11.8 * (syllables / len(words)) - 15.59
```

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py expertise` → PASS; `python3 tests/run.py` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/stylo.py tests/test_expertise.py
git commit -m "feat(stylo): Flesch-Kincaid grade (the measured expertise axis)"
```

---

## Task 2: Expertise tiers in build_reference

**Files:** Modify `scripts/build_reference.py`. Test: `tests/test_expertise.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_expertise.py`:

```python
def test_expertise_tiers_split_by_complexity():
    import build_reference  # build_reference.py inserts scripts/ on sys.path at import
    simple = ["See the cat. See the dog. We run and play. It is fun. Yes it is."] * 6
    complex_ = [("The epistemological ramifications of phenomenological inquiry "
                 "necessitate reconsideration of foundational presuppositions "
                 "underpinning contemporary hermeneutic methodology and praxis.")] * 6
    novice, expert = build_reference.expertise_tiers(simple + complex_)
    # Expert tier must read as higher-grade than novice tier.
    import statistics
    nov_fk = statistics.fmean(stylo.flesch_kincaid_grade(t) for t in novice)
    exp_fk = statistics.fmean(stylo.flesch_kincaid_grade(t) for t in expert)
    assert exp_fk > nov_fk
```

(Note: `tests/test_expertise.py` already inserts `scripts/` on `sys.path` from Task 1, and `build_reference.py` itself inserts `scripts/` at import — so `import build_reference` works.)

- [ ] **Step 2: Run to verify fail** — `python3 tests/run.py expertise` → FAIL (`expertise_tiers` missing).

- [ ] **Step 3a: Implement `expertise_tiers`** — in `scripts/build_reference.py`, add after the `aggregate()` function:

```python
def expertise_tiers(texts):
    """Split texts into novice (lowest-FK third) and expert (highest-FK third)
    by Flesch-Kincaid grade. The middle third is unused: 'practitioner' is the
    full-register band-set. Returns (novice_texts, expert_texts)."""
    graded = sorted(texts, key=stylo.flesch_kincaid_grade)
    third = max(1, len(graded) // 3)
    return graded[:third], graded[-third:]
```

- [ ] **Step 3b: Emit tier files from `main()`** — in `scripts/build_reference.py` `main()`, after the block that writes the full `reference-stats.json` (the `out_path.write_text(...)` + its `print`), and only when not building a voice sample, add:

```python
    # Expertise tiers: novice (low-FK) and expert (high-FK) band-sets. practitioner
    # is the full reference-stats.json above (so the default flag is backward-compatible).
    novice, expert = expertise_tiers(texts)
    for level, tier_texts in (("novice", novice), ("expert", expert)):
        t_bands, t_fw = aggregate(tier_texts)
        fks = sorted(stylo.flesch_kincaid_grade(t) for t in tier_texts)
        tier_stats = {
            "register": args.register,
            "expertise": level,
            "calibrated": True,
            "n_texts": len(tier_texts),
            "fk_grade_range": [round(fks[0], 2), round(fks[-1], 2)],
            "note": f"{level} tier (FK-grade tercile) of {args.register}, {len(tier_texts)} texts.",
            "bands": t_bands,
            "function_word_vector": t_fw,
        }
        tier_path = out_path.parent / f"expertise-{level}.json"
        tier_path.write_text(json.dumps(tier_stats, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {tier_path} ({len(tier_texts)} texts, FK {tier_stats['fk_grade_range']})")
```

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py expertise` → PASS; `python3 tests/run.py` → all PASS.

- [ ] **Step 5: Generate + commit tier files for all 7 registers** (raw corpora are present locally):

```bash
for r in spontaneous scientific literary business journalism social-media technical-docs; do python3 scripts/build_reference.py --register $r; done
```
Confirm 14 tier files exist and the FK ranges differ (novice range below expert range), e.g.:
```bash
python3 -c "import json; [print(r, json.load(open(f'corpus/{r}/expertise-novice.json'))['fk_grade_range'], json.load(open(f'corpus/{r}/expertise-expert.json'))['fk_grade_range']) for r in ('scientific','social-media')]"
```

```bash
git add corpus/*/expertise-novice.json corpus/*/expertise-expert.json scripts/build_reference.py tests/test_expertise.py
git commit -m "feat(build_reference): Flesch-Kincaid expertise tiers (14 tier band-sets)"
```

(Re-running build_reference rewrites each `reference-stats.json` identically — same corpus, same code — so `git status` should show only the new `expertise-*.json` files. If a `reference-stats.json` shows a diff, investigate before committing.)

---

## Task 3: Expertise resolution in score() + CLI

**Files:** Modify `scripts/stylo.py`. Test: `tests/test_expertise.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_expertise.py`:

```python
def test_load_reference_expertise_selects_tier():
    full = stylo.load_reference("scientific")
    expert = stylo.load_reference("scientific", expertise="expert")
    novice = stylo.load_reference("scientific", expertise="novice")
    assert expert["bands"] != novice["bands"]
    # practitioner is the full band-set
    assert stylo.load_reference("scientific", expertise="practitioner")["bands"] == full["bands"]


def test_expertise_discriminates():
    # A dense, high-grade passage should sit closer to the human band under
    # 'expert' than under 'novice' for the same register.
    dense = ("We demonstrate that the proposed estimator attains the minimax rate "
             "under heteroskedastic noise, and we characterize its asymptotic "
             "distribution via a functional central limit theorem.")
    exp = stylo.score(dense, "scientific", ref=stylo.load_reference("scientific", "expert"))
    nov = stylo.score(dense, "scientific", ref=stylo.load_reference("scientific", "novice"))
    assert exp["stylo_distance"] < nov["stylo_distance"]
```

- [ ] **Step 2: Run to verify fail** — `python3 tests/run.py expertise` → FAIL (`load_reference` takes no `expertise`).

- [ ] **Step 3a: Extend `load_reference`** — in `scripts/stylo.py`, replace the existing `load_reference`:

```python
def load_reference(register, expertise=None):
    """Load the band-set for a register, optionally an expertise tier.
    expertise None/"practitioner" -> the full register bands (backward-compatible);
    "novice"/"expert" -> corpus/<register>/expertise-<level>.json."""
    if expertise in (None, "practitioner"):
        path = ROOT / "corpus" / register / "reference-stats.json"
    else:
        path = ROOT / "corpus" / register / f"expertise-{expertise}.json"
    return json.loads(path.read_text())
```

- [ ] **Step 3b: Add `load_bands` and `load_persona`** — in `scripts/stylo.py`, right after `load_reference`:

```python
def load_bands(path):
    """Load an arbitrary band-set file (e.g. a calibrated voice)."""
    return json.loads(pathlib.Path(path).read_text())


def load_persona(name):
    """Load a persona definition: {register, expertise, lexicon_allow, lexicon_deny}."""
    return json.loads((ROOT / "personas" / f"{name}.json").read_text())
```

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py expertise` → PASS; `python3 tests/run.py` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/stylo.py tests/test_expertise.py
git commit -m "feat(stylo): expertise-tier + arbitrary band-set + persona loaders"
```

---

## Task 4: Persona lexicon override (allow/deny)

**Files:** Modify `scripts/stylo.py`. Test: `tests/test_persona.py` (new).

- [ ] **Step 1: Write the failing test** — create `tests/test_persona.py`:

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402

LEX = [{"id": 1, "name": "ai_vocabulary", "category": "language",
        "terms": ["leverage", "robust"], "regexes": []}]


def test_tell_hits_allow_suppresses_term():
    base = stylo.tell_hits("we leverage a robust system", LEX)
    allowed = stylo.tell_hits("we leverage a robust system", LEX, allow={"leverage"})
    assert base["ai_vocabulary"] == 2
    assert allowed["ai_vocabulary"] == 1   # 'leverage' no longer counted


def test_tell_hits_deny_adds_terms():
    out = stylo.tell_hits("this is super synergistic", LEX, deny=["synergistic"])
    assert out["persona_deny"] == 1


def test_score_accepts_allow_deny():
    out = stylo.score("we leverage robust synergies", "business",
                      allow={"leverage"}, deny=["synergies"])
    assert "tell_rate" in out["features"]
```

- [ ] **Step 2: Run to verify fail** — `python3 tests/run.py persona` → FAIL (`tell_hits` has no `allow`).

- [ ] **Step 3a: Extend `tell_hits`** — in `scripts/stylo.py`, replace `tell_hits`:

```python
def tell_hits(text, lexicon, allow=None, deny=None):
    """Count lexicon entry hits (terms + regexes) by name. `allow` is a set of
    lowercased terms NOT to count (a persona legitimately uses them); `deny` is a
    list of extra lowercased terms to count under a synthetic 'persona_deny' entry."""
    allow = allow or set()
    low = text.lower()
    out = {}
    for entry in lexicon:
        count = 0
        for term in entry.get("terms", []):
            if term.lower() in allow:
                continue
            count += len(re.findall(_term_pattern(term), low))
        for rx in entry.get("regexes", []):
            count += len(re.findall(rx, text, flags=re.IGNORECASE | re.MULTILINE))
        out[entry["name"]] = count
    if deny:
        out["persona_deny"] = sum(
            len(re.findall(_term_pattern(t), low)) for t in deny
        )
    return out
```

- [ ] **Step 3b: Thread allow/deny through `score`** — in `scripts/stylo.py`, change the `score` signature and the tell line. Signature:

```python
def score(text, register="spontaneous", ref=None, allow=None, deny=None):
```

And change the tells line inside `score` (currently `tells = tell_hits(text, _load_lexicon())`) to:

```python
    tells = tell_hits(text, _load_lexicon(), allow=allow, deny=deny)
```

(The rest is unchanged: `tr = sum(tells.values()) ...` now includes any `persona_deny`, and allowed terms are already absent — so persona overrides flow into `tell_excess` automatically.)

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py persona` → PASS; `python3 tests/run.py` → all PASS (existing `tell_hits(text, lex)` callers unaffected — `allow`/`deny` default to None).

- [ ] **Step 5: Commit**

```bash
git add scripts/stylo.py tests/test_persona.py
git commit -m "feat(stylo): persona lexicon override (allow/deny) in tells + score"
```

---

## Task 5: Persona files + `--persona` resolution + full CLI

**Files:** Create `personas/*.json`; modify `scripts/stylo.py` (`_main` + `_resolve_target`). Test: `tests/test_persona.py`.

- [ ] **Step 1: Create the 4 persona files.**

`personas/reddit-power-user.json`:
```json
{
  "name": "reddit-power-user",
  "register": "social-media",
  "expertise": "practitioner",
  "lexicon_allow": ["honestly", "literally", "basically", "tbh", "imo"],
  "lexicon_deny": []
}
```
`personas/seasoned-journalist.json`:
```json
{
  "name": "seasoned-journalist",
  "register": "journalism",
  "expertise": "expert",
  "lexicon_allow": [],
  "lexicon_deny": ["game-changing", "must-visit", "breathtaking", "stunning"]
}
```
`personas/startup-founder.json`:
```json
{
  "name": "startup-founder",
  "register": "business",
  "expertise": "practitioner",
  "lexicon_allow": ["mission", "vision"],
  "lexicon_deny": ["synergy", "best-in-class", "circle back", "low-hanging fruit"]
}
```
`personas/academic-humanist.json`:
```json
{
  "name": "academic-humanist",
  "register": "literary",
  "expertise": "expert",
  "lexicon_allow": [],
  "lexicon_deny": ["delve", "tapestry", "testament"]
}
```

- [ ] **Step 2: Write the failing test** — append to `tests/test_persona.py`:

```python
def test_load_persona_resolves():
    p = stylo.load_persona("reddit-power-user")
    assert p["register"] == "social-media"
    assert "literally" in p["lexicon_allow"]


def test_resolve_target_persona():
    ref, register, allow, deny = stylo._resolve_target(
        register="spontaneous", persona="seasoned-journalist")
    assert register == "journalism"             # persona overrides --register
    assert ref["bands"] == stylo.load_reference("journalism", "expert")["bands"]
    assert "game-changing" in deny


def test_resolve_target_plain_register():
    ref, register, allow, deny = stylo._resolve_target(register="literary")
    assert register == "literary" and allow == set() and deny == []
    assert ref["bands"] == stylo.load_reference("literary")["bands"]
```

- [ ] **Step 3: Run to verify fail** — `python3 tests/run.py persona` → FAIL (`_resolve_target` missing).

- [ ] **Step 4: Implement `_resolve_target` + extend `_main`** — in `scripts/stylo.py`, add before `_main`:

```python
def _resolve_target(register="spontaneous", expertise=None, voice=None,
                    bands=None, persona=None):
    """Resolve CLI target flags to (ref_dict, register_label, allow_set, deny_list).
    Precedence: persona > voice/bands > expertise > register."""
    if persona:
        p = load_persona(persona)
        ref = load_reference(p["register"], p.get("expertise"))
        allow = {t.lower() for t in p.get("lexicon_allow", [])}
        deny = [t.lower() for t in p.get("lexicon_deny", [])]
        return ref, p["register"], allow, deny
    if bands:
        return load_bands(bands), register, set(), []
    if voice:
        return load_bands(ROOT / "voices" / voice / "reference-stats.json"), register, set(), []
    return load_reference(register, expertise), register, set(), []
```

Then replace `_main`:

```python
def _main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="Stylometric scorer for humanizer-pro.")
    ap.add_argument("file", help="path to a UTF-8 text file to score")
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--expertise", choices=["novice", "practitioner", "expert"],
                    default=None)
    ap.add_argument("--voice", default=None, help="voice label under voices/")
    ap.add_argument("--bands", default=None, help="path to an arbitrary band-set json")
    ap.add_argument("--persona", default=None, help="persona name under personas/")
    args = ap.parse_args(argv)

    targets = [bool(args.persona), bool(args.voice or args.bands), bool(args.expertise)]
    if sum(targets) > 1:
        print("warning: multiple target flags set; using precedence "
              "persona > voice/bands > expertise > register", file=sys.stderr)

    ref, register, allow, deny = _resolve_target(
        args.register, args.expertise, args.voice, args.bands, args.persona)
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    print(json.dumps(score(text, register, ref=ref, allow=allow, deny=deny),
                     indent=2, ensure_ascii=False))
```

(Confirm `import sys` is present at the top of `stylo.py`; it is used by `_main`. If not, add it with the other stdlib imports.)

- [ ] **Step 5: Run to verify pass** — `python3 tests/run.py persona` → PASS; `python3 tests/run.py` → all PASS. Smoke-test the CLI:

```bash
printf 'Honestly this keyboard is literally the best, tbh. I love it so much.\n' > /tmp/r.txt
python3 scripts/stylo.py /tmp/r.txt --persona reddit-power-user | python3 -c "import sys,json; d=json.load(sys.stdin); print('register', d['register'], 'dist', d['stylo_distance'])"
```
Expected: `register social-media` and a finite distance.

- [ ] **Step 6: Commit**

```bash
git add personas/ scripts/stylo.py tests/test_persona.py
git commit -m "feat: named personas + full target-resolution CLI (--persona/--voice/--bands/--expertise)"
```

---

## Task 6: Voice sample calibration (with small-sample blend)

**Files:** Modify `scripts/build_reference.py`; `.gitignore`. Test: `tests/test_voice.py` (new).

- [ ] **Step 1: Add `voices/` to `.gitignore`** — append to `.gitignore`:

```
# Personal voice samples: user data, not ours to commit. Calibrate locally via
# build_reference.py --voice-sample.
voices/
```

- [ ] **Step 2: Write the failing test** — create `tests/test_voice.py`:

```python
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_reference  # noqa: E402


def _voice_dir(words_per_text, n_texts):
    tmp = pathlib.Path(tempfile.mkdtemp())
    d = tmp / "voice"
    d.mkdir()
    sent = "I really think this little place is the best, honestly. "
    body = (sent * max(1, words_per_text // 9))  # ~9 words per sentence
    for i in range(n_texts):
        (d / f"v{i:02d}.txt").write_text(body + "\n", encoding="utf-8")
    return tmp, d


def test_voice_large_sample_uses_own_bands():
    tmp, d = _voice_dir(words_per_text=300, n_texts=8)  # ~2400 words > 1500
    out = tmp / "voices" / "me" / "reference-stats.json"
    rc = build_reference.main(["--voice-sample", str(d), "--label", "me",
                               "--out-root", str(tmp / "voices")])
    assert rc == 0
    stats = json.loads(out.read_text())
    assert stats["calibrated"] is True
    assert stats["voice_blend_weight"] == 1.0   # large sample, no blend


def test_voice_small_sample_blends_and_warns():
    tmp, d = _voice_dir(words_per_text=40, n_texts=3)  # ~120 words << 1500
    out = tmp / "voices" / "tiny" / "reference-stats.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_reference.py"),
         "--voice-sample", str(d), "--label", "tiny",
         "--register", "spontaneous", "--out-root", str(tmp / "voices")],
        capture_output=True, text=True)
    assert proc.returncode == 0
    assert "warning" in proc.stderr.lower()
    stats = json.loads(out.read_text())
    assert 0.0 < stats["voice_blend_weight"] < 1.0   # blended
```

- [ ] **Step 3: Implement the voice path** — in `scripts/build_reference.py`:

3a. Add a blend helper after `expertise_tiers`:

```python
def _blend(voice_bands, voice_fw, reg_bands, reg_fw, w):
    """Per-feature weighted blend of two band-sets: w*voice + (1-w)*register."""
    bands = {}
    for key in set(voice_bands) | set(reg_bands):
        v, r = voice_bands.get(key), reg_bands.get(key)
        if v is None:
            bands[key] = r
        elif r is None:
            bands[key] = v
        else:
            out = {}
            for edge in ("floor", "ceiling"):
                a, b = v.get(edge), r.get(edge)
                out[edge] = a if (a is None or b is None) else round(w * a + (1 - w) * b, 4)
            bands[key] = out
    keys = set(voice_fw) | set(reg_fw)
    fw = {k: round(w * voice_fw.get(k, 0.0) + (1 - w) * reg_fw.get(k, 0.0), 6) for k in sorted(keys)}
    return bands, fw
```

3b. Rework `main()` to branch on `--voice-sample`. Add the new args to the argparser (`--voice-sample`, `--label`, `--out-root`) and, at the top of `main()` after parsing, handle the voice branch before the register branch:

```python
    if args.voice_sample:
        import sys as _sys
        vdir = pathlib.Path(args.voice_sample)
        files = sorted(vdir.glob("*.txt"))
        if not files:
            print(f"no .txt in {vdir}", file=_sys.stderr)
            return 1
        texts = [f.read_text(encoding="utf-8") for f in files]
        words = sum(len(stylo.tokenize(t)) for t in texts)
        v_bands, v_fw = aggregate(texts)
        w = min(1.0, words / 1500)
        if w < 1.0:
            reg = stylo.load_reference(args.register)
            v_bands, v_fw = _blend(v_bands, v_fw, reg["bands"],
                                   reg.get("function_word_vector", {}), w)
            print(f"warning: voice sample is {words} words (< 1500); blended with "
                  f"'{args.register}' at weight {round(w, 3)} (bands will be approximate)",
                  file=_sys.stderr)
        out_root = pathlib.Path(args.out_root) if args.out_root else (stylo.ROOT / "voices")
        out_path = out_root / args.label / "reference-stats.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        stats = {
            "register": f"voice:{args.label}",
            "calibrated": True,
            "n_texts": len(files),
            "voice_blend_weight": round(w, 4),
            "note": f"Voice '{args.label}' from {len(files)} texts ({words} words).",
            "bands": v_bands,
            "function_word_vector": v_fw,
        }
        out_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {out_path} (weight {round(w, 3)})")
        return 0
```

Add the argparser lines (next to the existing `--register`/`--out`):
```python
    ap.add_argument("--voice-sample", default=None, help="dir of *.txt to calibrate a voice")
    ap.add_argument("--label", default="me", help="voice label (output subdir)")
    ap.add_argument("--out-root", default=None, help="root dir for voice output (test hook)")
```

Guard the expertise-tier emission (Task 2) so it does NOT run in the voice branch — the voice branch `return 0`s before reaching it, so it is already skipped. Confirm the register branch is unchanged.

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py voice` → PASS; `python3 tests/run.py` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_reference.py tests/test_voice.py .gitignore
git commit -m "feat(build_reference): voice-sample calibration with small-sample blend"
```

---

## Task 7: Docs, eval proof, and v1.0.0

**Files:** Modify `eval/REPORT.md`, `README.md`, `SKILL.md`, `AGENTS.md`, `CHANGELOG.md`.

- [ ] **Step 1: Eval proofs** — gather the real numbers and add a "Sprint 3: persona layer" section to `eval/REPORT.md` with:
  - an **expertise tier table** (novice vs expert FK ranges + a divergent band like sentence-length or MTLD) for ≥3 registers, pulled from the committed `expertise-*.json`;
  - an **expertise discrimination** line (the dense passage from `test_expertise_discriminates`: distance under expert < under novice — quote both numbers from a live `stylo.py` run);
  - a **persona demo** (a slangy social text scored under `social-media` vs `--persona reddit-power-user`: show the allowed terms drop the tell count / distance — quote both).
  Gather numbers with:
```bash
python3 -c "import json; [print(r, json.load(open(f'corpus/{r}/expertise-novice.json'))['fk_grade_range'], json.load(open(f'corpus/{r}/expertise-expert.json'))['fk_grade_range']) for r in ('scientific','social-media','journalism')]"
```

- [ ] **Step 2: README.md** — add a short "Aim at a specific writer" subsection under the core ideas: voice (`--voice`), expertise (`--expertise novice|practitioner|expert`), personas (`--persona`). Note all are optional and measured (FK terciles, real voice calibration).

- [ ] **Step 3: SKILL.md** — add an "Inputs" note that the loop accepts an optional `persona` / `expertise` / `voice` target, and that `stylo.py` takes `--persona/--expertise/--voice/--bands`. Keep DRY (one or two sentences).

- [ ] **Step 4: AGENTS.md** — add the same flags to the "deterministic core" section so Codex users see them.

- [ ] **Step 5: CHANGELOG.md** — add `## 1.0.0 — 2026-06-15` summarizing: voice-sample, FK expertise tiers (measured, not heuristic), named personas, the resolution precedence, and that the v2 roadmap (3 sprints) is complete.

- [ ] **Step 6: Full suite + commit + tag**

```bash
python3 tests/run.py        # all green
git add eval/REPORT.md README.md SKILL.md AGENTS.md CHANGELOG.md
git commit -m "docs: persona layer (voice/expertise/personas); CHANGELOG 1.0.0"
git tag v1.0.0
```

---

## Self-Review (completed during planning)

**Spec coverage:** voice-sample (Task 6), expertise FK terciles (Tasks 1–3), personas + lexicon override (Tasks 4–5), CLI precedence (Task 5), docs+eval+v1.0.0 (Task 7). Backward compat asserted in Tasks 3/4/5 (new params/flags all default to today's behavior).

**Placeholder scan:** All code is concrete; FK formula, blend math, persona JSON, and CLI are fully specified. Eval numbers in Task 7 are produced live (not pre-written) and quoted from real runs.

**Type/name consistency:** `flesch_kincaid_grade`/`_count_syllables` (Task 1) used by `expertise_tiers` (Task 2) and tests (Task 3). `load_reference(register, expertise)` signature consistent across Tasks 2/3/5. `tell_hits(text, lexicon, allow, deny)` (Task 4) called by `score` and `_resolve_target` output (`allow` set, `deny` list) threaded into `score(..., allow=, deny=)` (Tasks 4/5). `voice_blend_weight` key consistent between Task 6 impl and tests. `expertise-<level>.json` path identical in build_reference (Task 2) and load_reference (Task 3).
