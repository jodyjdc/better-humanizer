# Sprint 2 — Register Expansion (+4 registers) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Grow from 3 to 7 calibrated registers — adding **business, journalism, social-media, technical-docs** — reusing the exact Sprint-1 machinery (fetch → profile → calibrate → eval), and prove the inverting-norms thesis across 7 registers in one fingerprint table.

**Architecture:** Each register is a `registers/<name>.md` brief + a calibrated `corpus/<name>/` (raw gitignored, stats committed) + entries in `fetch_corpus.py`'s `SOURCES`. The discourse + tell machinery is unchanged. One real code change: `clean()` gains markdown normalization (technical-docs answers are markdown-heavy — links, blockquotes, rules — which otherwise corrupt the stylometry).

**Tech Stack:** Python 3 stdlib only; HuggingFace rows API (no deps); stdlib test runner.

**Scope note:** academic-essay (the roadmap's 5th register) is deferred — every clean, dated, pre-LLM student-essay corpus on the HF rows API is gated; shipping an undated source (e.g. IvyPanda) would violate the project's "genuinely human, pre-LLM" guarantee. It returns when a clean source is found.

---

## Locked, verified data sources (probed via the rows API)

| Register | dataset | config | field | epoch | notes |
|---|---|---|---|---|---|
| business | `Yale-LILY/aeslc` | default | `email_body` | Enron ~2000 | emails; med 425 chars; salutations/signatures are authentic register |
| journalism | `abisee/cnn_dailymail` | 3.0.0 | `article` | pre-2018 | long (med 3621), multi-paragraph → exercises `paragraph_cv`; strip datelines |
| social-media | `webis/tldr-17` | default | `content` | Reddit pre-2017 | informal first-person; med 803; relaxed sentence floor |
| technical-docs | `lvwerra/stack-exchange-paired` | default | `response_j` | SE pre-2021 | accepted answers; **markdown-heavy** → needs clean() upgrade |

---

## File Structure

- `scripts/fetch_corpus.py` — **modify**: add the 4 sources to `SOURCES`; upgrade `clean()` for markdown.
- `scripts/build_reference.py` — unchanged (already register-agnostic).
- `scripts/stylo.py` — **modify**: add the 4 registers to `DEFAULT_DISCOURSE_BANDS` (fallback before calibration; `_default` already covers them, so this is optional polish — see Task 6).
- `registers/{business,journalism,social-media,technical-docs}.md` — **create**: register briefs.
- `corpus/<name>/{reference-stats.json,PROVENANCE.md}` — **create** (raw gitignored).
- `eval/run_eval.py`, `Makefile` — **modify**: add the 4 registers to the loops with per-register fetch thresholds.
- `eval/ai_samples/<name>/*.txt`, `eval/out/<name>/*.{baseline,pro}.txt` — **create**: A/B eval set.
- `eval/REPORT.md`, `README.md`, `SKILL.md`, `CHANGELOG.md` — **modify**: 7-register fingerprint, v0.3.0.

---

## Task 1: Markdown-aware `clean()`

**Files:** Modify `scripts/fetch_corpus.py`; Test `tests/test_fetch_clean.py` (new).

- [ ] **Step 1: Write the failing test** — create `tests/test_fetch_clean.py`:

```python
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import fetch_corpus as fc


def test_clean_strips_markdown_link_keeps_anchor():
    assert "Java Web Start" in fc.clean("look to [Java Web Start](https://x.com/a/b).")
    assert "http" not in fc.clean("see [docs](https://example.com/page).")


def test_clean_removes_blockquote_markers_and_rules():
    out = fc.clean("> quoted line\n\n---\n\nreal text here.")
    assert ">" not in out
    assert "---" not in out
    assert "real text here" in out


def test_clean_strips_inline_code_and_bare_urls():
    out = fc.clean("use the `printf` call; ref https://example.com/x now.")
    assert "printf" in out          # keep the word, drop the backticks
    assert "`" not in out
    assert "http" not in out


def test_clean_preserves_plain_prose():
    s = "A normal sentence, with a comma — and an em dash. Nothing to strip!"
    assert fc.clean(s) == s
```

- [ ] **Step 2: Run to verify fail** — `python3 tests/run.py fetch_clean` → FAIL (markdown not stripped).

- [ ] **Step 3: Implement** — in `scripts/fetch_corpus.py`, add module-level regexes near the existing `TAG_RE`:

```python
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")   # [anchor](url) -> anchor
MD_RULE_RE = re.compile(r"(?m)^\s*(?:[-*_]\s*){3,}\s*$")  # --- *** ___ horizontal rules
MD_BQ_RE = re.compile(r"(?m)^\s*>+\s?")                  # > blockquote markers
URL_RE = re.compile(r"https?://\S+")
CODE_RE = re.compile(r"`+([^`]*)`+")                      # `code` -> code
```

Then, in `clean()`, apply markdown normalization AFTER `html.unescape` + tag strip and BEFORE the whitespace collapse. Insert these lines right after the existing `text = TAG_RE.sub(" ", text)` line:

```python
    text = MD_LINK_RE.sub(r"\1", text)   # [anchor](url) -> anchor
    text = CODE_RE.sub(r"\1", text)      # `code` -> code
    text = MD_RULE_RE.sub(" ", text)     # horizontal rules -> space
    text = MD_BQ_RE.sub("", text)        # drop blockquote markers
    text = URL_RE.sub(" ", text)         # drop bare URLs
```

- [ ] **Step 4: Run to verify pass** — `python3 tests/run.py fetch_clean` → PASS. Then `python3 tests/run.py` → all PASS (the change is additive; existing fetch tests, if any, must still pass).

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_corpus.py tests/test_fetch_clean.py
git commit -m "feat(fetch): markdown-aware clean() for technical-docs corpus"
```

---

## Task 2: Add the 4 sources to `fetch_corpus.py`

**Files:** Modify `scripts/fetch_corpus.py`.

- [ ] **Step 1: Add SOURCES entries** — extend the `SOURCES` dict with the 4 verified sources:

```python
    # Business prose: Enron emails (AESLC, Zhang & Tetreault 2019; emails ~2000).
    "business": [
        {"name": "aeslc", "dataset": "Yale-LILY/aeslc", "config": "default",
         "split": "train", "field": "email_body",
         "offsets": [0, 2000, 4000, 6000, 8000], "target": 120},
    ],
    # Journalism: CNN/DailyMail news articles (Hermann et al. 2015 / See et al. 2017,
    # pre-2018). Long, multi-paragraph, structured lede.
    "journalism": [
        {"name": "cnndm", "dataset": "abisee/cnn_dailymail", "config": "3.0.0",
         "split": "train", "field": "article",
         "offsets": [0, 5000, 10000, 15000], "target": 120},
    ],
    # Social media: Reddit posts (Webis-TLDR-17, Völske et al. 2017, pre-LLM).
    # Informal, first-person, fragments and lowercase are HUMAN here.
    "social-media": [
        {"name": "reddit", "dataset": "webis/tldr-17", "config": "default",
         "split": "train", "field": "content",
         "offsets": [1000, 30000, 80000, 150000, 250000], "target": 120},
    ],
    # Technical docs: accepted Stack Exchange answers (lvwerra/stack-exchange-paired,
    # pre-2021). Imperative, code-switching, lists. Markdown normalized by clean().
    "technical-docs": [
        {"name": "stackexchange", "dataset": "lvwerra/stack-exchange-paired",
         "config": "default", "split": "train", "field": "response_j",
         "offsets": [0, 10000, 25000, 50000], "target": 120},
    ],
```

- [ ] **Step 2: Verify the dict parses** — `python3 -c "import sys; sys.path.insert(0,'scripts'); import fetch_corpus; print(sorted(fetch_corpus.SOURCES))"` → lists all 7 registers including the 4 new.

- [ ] **Step 3: Commit**

```bash
git add scripts/fetch_corpus.py
git commit -m "feat(fetch): add business/journalism/social-media/technical-docs sources"
```

---

## Task 3: Fetch + calibrate the 4 corpora

This task runs the network fetch and calibration. Per-register thresholds differ (emails are short; articles are long; Reddit sentences are few). **Inspect each corpus after fetch** — confirm it reads as genuinely human and on-register before calibrating.

**Files:** generates `corpus/<name>/raw/*.txt` (gitignored) + commits `reference-stats.json`.

- [ ] **Step 1: Fetch all four** (per-register thresholds):

```bash
python3 scripts/fetch_corpus.py --register business     --min-chars 200 --max-chars 2400 --min-sents 3
python3 scripts/fetch_corpus.py --register journalism   --min-chars 800 --max-chars 4500 --min-sents 6
python3 scripts/fetch_corpus.py --register social-media  --min-chars 250 --max-chars 2400 --min-sents 2
python3 scripts/fetch_corpus.py --register technical-docs --min-chars 300 --max-chars 3000 --min-sents 4
```
Expected: each prints `total <N> texts` with N close to 120 (≥ 100 acceptable).

- [ ] **Step 2: Eyeball quality** — for each register, read 3 random raw files:

```bash
for r in business journalism social-media technical-docs; do echo "=== $r ==="; ls corpus/$r/raw | head -3 | while read f; do echo "--- $f"; head -c 300 "corpus/$r/raw/$f"; echo; done; done
```
Confirm: business reads like email; journalism like news (datelines acceptable or note for cleaning); social-media like Reddit; technical-docs like prose with NO leftover `[](url)`, `>` or bare URLs (validates Task 1). If technical-docs still shows markdown artifacts, fix `clean()` (Task 1) and re-fetch before proceeding.

- [ ] **Step 3: Calibrate**

```bash
for r in business journalism social-media technical-docs; do python3 scripts/build_reference.py --register $r; done
```
Expected: four `wrote ... (N texts)` lines.

- [ ] **Step 4: Sanity-check the bands** — confirm register differentiation, e.g.:

```bash
python3 -c "
import json
for r in ('business','journalism','social-media','technical-docs','spontaneous','scientific','literary'):
    b=json.load(open(f'corpus/{r}/reference-stats.json'))['bands']
    print(f'{r:16} emdash_ceil={b[\"em_dash_rate\"][\"ceiling\"]:.3f} contr_ceil={b[\"contraction_rate\"][\"ceiling\"]:.3f} para_cv_floor={b[\"paragraph_cv\"][\"floor\"]:.3f} tell_ceil={b[\"tell_rate\"][\"ceiling\"]:.3f}')
"
```
Expected sane contrasts: social-media high contractions + high exclaim; business low contractions; journalism `paragraph_cv` floor > 0 (multi-paragraph, finally live); technical-docs distinct tell tolerance. If any band is degenerate (all zeros, or a register looks identical to another), investigate the corpus before committing.

- [ ] **Step 5: Write PROVENANCE.md** for each new register (mirror an existing `corpus/scientific/PROVENANCE.md`): dataset name + citation, field, epoch/pre-LLM rationale, license note, "raw not redistributed, reproduce via fetch_corpus.py".

- [ ] **Step 6: Commit** (stats + provenance only; raw is gitignored)

```bash
git add corpus/business corpus/journalism corpus/social-media corpus/technical-docs
git commit -m "feat(corpus): calibrate business/journalism/social-media/technical-docs (120 each)"
```

---

## Task 4: Register profiles

**Files:** Create `registers/{business,journalism,social-media,technical-docs}.md`.

Each profile mirrors the structure of `registers/scientific.md` (read it first) and must state, grounded in the calibrated bands from Task 3: what is HUMAN here, what is a TELL here, and the anti-over-correction note. Key per-register theses:

- [ ] **business** — polite hedging, nominalization, salutations/sign-offs, near-zero contractions and em dashes are human; transitions acceptable. Tell = marketing fluff, hollow affirmatives, signposting. Don't inject casual contractions.
- [ ] **journalism** — inverted-pyramid lede, short declarative sentences, source attribution ("officials said"), multi-paragraph structure are human; NOT tells. Tell = editorializing adjectives, era-framing openers. Keep attributions.
- [ ] **social-media** — fragments, lowercase, minimal formal punctuation, slang, first-person, emoji are HUMAN here (this register inverts scientific hardest). Tell = corporate polish, signposting, "let's dive in". Do NOT formalize.
- [ ] **technical-docs** — imperative mood ("Run X"), code-switching, terse lists, second person are human; NOT tells. Tell = marketing ("seamless", "robust"), hollow conclusions. Keep imperatives and specificity.

- [ ] **Commit**

```bash
git add registers/
git commit -m "feat(registers): business, journalism, social-media, technical-docs profiles"
```

---

## Task 5: Eval — A/B set for the 4 registers

**Files:** Create `eval/ai_samples/<name>/*.txt` and `eval/out/<name>/*.{baseline,pro}.txt`; modify `eval/run_eval.py` if its register list is hard-coded (it is parametrized by `--register`, so likely no change).

For each new register, create **4** AI-generated source passages (`eval/ai_samples/<name>/NN-topic.txt`) that exhibit that register's typical AI tells, then two rewrites each:
- `*.baseline.txt` — original-humanizer style (tells deleted but register-flattened / over-corrected).
- `*.pro.txt` — register-faithful rewrite per `registers/<name>.md`.

- [ ] Create the 16 AI samples (4 per register), topic-appropriate (business email, news story, Reddit post, technical answer).
- [ ] Create the 32 rewrites (baseline + pro per sample).
- [ ] **Run the eval:**

```bash
for r in business journalism social-media technical-docs; do python3 eval/run_eval.py --register $r; echo; done
```
Expected: pro closer-to-human on every sample. If pro loses, diagnose via the scorecards — fix the `*.pro.txt` rewrite to be more register-faithful (it's a writing fix, not a band fix), never edit the band to win.

- [ ] **Commit**

```bash
git add eval/ai_samples eval/out
git commit -m "feat(eval): A/B sets for 4 new registers (pro beats baseline)"
```

---

## Task 6: DEFAULT_DISCOURSE_BANDS polish + Makefile

**Files:** Modify `scripts/stylo.py`, `Makefile`.

- [ ] **Step 1: Add the 4 registers to `DEFAULT_DISCOURSE_BANDS`** in `scripts/stylo.py` (the `_default` entry already covers them, so this is a small accuracy polish so a pre-calibration fallback is register-shaped). Use values informed by Task 3's calibrated bands. If Task 3's calibrated values are already in `reference-stats.json` (they are), `score()` uses those and this is belt-and-suspenders — keep it minimal or skip if time-constrained (note the skip).

- [ ] **Step 2: Extend the `Makefile`** `corpus` and `eval` targets to include the 4 new registers with the per-register fetch thresholds from Task 3 Step 1.

- [ ] **Step 3: Run** `python3 tests/run.py` → all PASS.

- [ ] **Commit**

```bash
git add scripts/stylo.py Makefile
git commit -m "chore: default discourse bands + Makefile for 4 new registers"
```

---

## Task 7: Docs — 7-register fingerprint + v0.3.0

**Files:** Modify `eval/REPORT.md`, `README.md`, `SKILL.md`, `CHANGELOG.md`.

- [ ] **Step 1: eval/REPORT.md** — add a Sprint 2 section with the 4 registers' A/B results, and extend the fingerprint table to all **7** registers (pull the real numbers from each `reference-stats.json`): rows for em-dash ceiling, contractions, paragraph_cv floor, transition-opener ceiling, AI-tell tolerance. Add a one-line "register-awareness" proof: score one social-media text under `social-media` vs `scientific` and show the self-tell flip.

- [ ] **Step 2: README.md** — update "Three registers ship" → seven; refresh the differs-sharply sentence with a social-media-vs-scientific contrast; update the "5/5…4/4" results line to include the new registers.

- [ ] **Step 3: SKILL.md** — update the Scope section's register list to all seven.

- [ ] **Step 4: CHANGELOG.md** — add `## 0.3.0 — 2026-06-15` entry summarizing the 4 registers, the markdown-clean upgrade, and the deferred academic-essay.

- [ ] **Step 5:** `python3 tests/run.py` → all PASS. Verify every number written in REPORT.md against live `reference-stats.json` / eval output.

- [ ] **Step 6: Commit + tag**

```bash
git add eval/REPORT.md README.md SKILL.md CHANGELOG.md
git commit -m "docs: 7-register fingerprint; CHANGELOG 0.3.0"
git tag v0.3.0
```

---

## Self-Review (completed during planning)

**Spec coverage:** Roadmap Sprint 2 = +5 registers; scoped to +4 (academic deferred, justified). Each register: source (Task 2), corpus+calibration (Task 3), profile (Task 4), eval (Task 5), docs (Task 7). The markdown-clean prerequisite for technical-docs is Task 1. Discourse machinery reused unchanged (Sprint 1).

**Placeholder scan:** Dataset IDs/configs/fields are real and rows-API-verified (not guessed). Fetch thresholds derived from measured length distributions. The one soft spot — exact calibrated band values — is intentionally produced by Task 3, not pre-written, and sanity-gated in Task 3 Step 4.

**Consistency:** Register directory names (`social-media`, `technical-docs`) are used identically across `SOURCES` keys, `corpus/<name>/`, `registers/<name>.md`, eval subdirs, and the Makefile. `clean()` upgrade is tested for both new behavior and non-damage to plain prose.

**Risk:** if a corpus fetches < 100 usable texts (thresholds too strict) or reads contaminated/off-register, Task 3 Step 2/4 catches it before calibration — adjust thresholds/offsets and re-fetch rather than proceeding.
