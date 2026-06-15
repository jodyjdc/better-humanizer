# Eval report — humanizer-pro vs original humanizer

Blind A/B on `eval/ai_samples/` (5 AI-generated spontaneous passages). Each is
rewritten two ways and scored against the human band calibrated from 120 real
human texts (see `corpus/spontaneous/PROVENANCE.md`):

- **baseline** = original-humanizer style: tells deleted, but scrubbed flat (no
  contractions, no em dash, even rhythm). `eval/out/<name>.baseline.txt`
- **pro** = humanizer-pro, register-faithful. `eval/out/<name>.pro.txt`

Success = pro is closer to the human band, less over-corrected, and keeps meaning.

## Reproduce

```bash
python3 eval/run_eval.py --register spontaneous   # objective stylometric table
# then, for the independent semantic half, run eval/judge_blind.md per sample
# (X/Y in random order) with a model not in the loop.
```

## Stylometric result (objective, from run_eval.py)

| sample | base_dist | pro_dist | base self-tells | pro self-tells | closer-to-human |
|--------|-----------|----------|-----------------|----------------|-----------------|
| 01-tech-opinion | 0.832 | **0.438** | 2 | 0 | **pro** |
| 02-travel | 0.715 | **0.452** | 2 | 1 | **pro** |
| 03-productivity | 0.574 | **0.452** | 1 | 0 | **pro** |
| 04-food | 0.731 | **0.373** | 2 | 0 | **pro** |
| 05-personal | 0.767 | **0.386** | 2 | 0 | **pro** |
| **mean** | **0.724** | **0.420** | **1.8** | **0.2** | **pro 5/5** |

`dist` = distance to the human band (lower is better). `self-tells` =
over-correction flags (lower is better). Pro wins every sample on the objective
score, and is far less over-corrected: the baseline's tell-scrubbing pushes it
*out* of the human band (flat rhythm, missing contractions), exactly the failure
mode humanizer-pro is built to avoid.

## Blind human-ness verdict (semantic half)

The blind panel (`eval/judge_blind.md`) is wired and runnable. It must be run with
a model **outside the loop** to count as independent — grading rewrites with the
same model that wrote them is not a real test. That run is the remaining step to
fill this section. Indicative read (same-family, not independent): the pro
rewrites carry a first-person point of view and uneven rhythm the baseline
versions lack, and both preserve the source's core claims.

## Verdict

- closer-to-human (objective stylometric): **pro 5/5**, mean distance 0.420 vs 0.724
- over-correction: pro 0.2 self-tells/sample vs baseline 1.8
- meaning: preserved in both (no claims dropped or invented)
- independent blind human-ness vote: pending an out-of-loop model run

## Scientific register (phase 2)

Same machinery, recalibrated on 120 PubMed + arXiv abstracts. The bands invert the
spontaneous ones (longer and more uniform sentences, zero contractions, ~3x AI-tell
tolerance), so the tool no longer treats passive voice or formality as a defect.

| sample | base_dist | pro_dist | closer-to-human |
|--------|-----------|----------|-----------------|
| 01-ml-health | 0.582 | **0.281** | **pro** |
| 02-climate | 1.116 | **0.529** | **pro** |
| 03-crispr | 0.747 | **0.208** | **pro** |
| 04-quantum | 0.739 | **0.184** | **pro** |
| **mean** | **0.796** | **0.301** | **pro 4/4** |

baseline = original-style rewrite (tells removed but register-flattened: shorter,
active, hedges stripped). pro = tells removed while preserving the scientific
register. Pro wins 4/4.

### Register-awareness (the phase-2 proof)

One scientific passage (`eval/out/scientific/01-ml-health.pro.txt`), scored under
both registers:

- under **scientific**: dist 0.281, **0** self-tells (in-band, recognized as human)
- under **spontaneous**: dist 0.470, **2** self-tells (its uniform rhythm and zero
  contractions are wrongly flagged as over-correction)

A single-register humanizer would "fix" the paper's passive voice and add
contractions, damaging it. humanizer-pro adapts to the register instead.

## Literary register (phase 3)

Calibrated on 120 human short stories (r/WritingPrompts). Highest tolerance for the
devices other registers flag (em dashes, fragments, varied rhythm).

| sample | base_dist | pro_dist | closer-to-human |
|--------|-----------|----------|-----------------|
| 01-rain | 0.845 | **0.516** | **pro** |
| 02-forest | 0.823 | **0.496** | **pro** |
| 03-love | 0.753 | **0.477** | **pro** |
| 04-noir | 0.815 | **0.385** | **pro** |
| **mean** | **0.809** | **0.469** | **pro 4/4** |

baseline = original-style rewrite (flattened: dashes removed, rhythm evened, imagery
stripped). pro = tells removed while keeping voice, varied rhythm, and specific
imagery. Pro wins 4/4. Notably the flattened baseline (0.81 mean) scores **worse**
than the original AI purple prose (0.66 mean): flattening fiction is the maximal
failure mode, not a fix.

## Seven-register fingerprint (the whole thesis in one table)

Bands from real human corpora; one scorer, seven calibrations (ceilings unless noted):

| feature | spontaneous | scientific | literary | business | journalism | social-media | technical-docs |
|---------|---|---|---|---|---|---|---|
| sentence length (mean) | 10–26 | 16–33 | 8–20 | 8–27 | 16–25 | 13–27 | 6–65 |
| contraction ceiling | 4.34 | **0.00** | 4.96 | **5.78** | 3.10 | 4.54 | 3.06 |
| em-dash ceiling | 0.13 | 0.00 | **1.71** | 0.53 | 1.19 | 0.10 | 0.85 |
| exclamation ceiling | 3.47 | 0.00 | 2.00 | 1.15 | **0.07** | 0.67 | 1.62 |
| transition-opener ceiling | 0.19 | **0.63** | 0.08 | 0.54 | **0.02** | 0.10 | 0.30 |
| AI-tell tolerance | 0.29 | **0.78** | 0.22 | 0.40 | 0.29 | 0.43 | 0.75 |

Every row has a wide spread and several invert. Contractions run from **0.00**
(scientific — and zero is human there) to **5.78** (business email). Em dashes from
0.00 to 1.71 (~13x). Exclamation from 0.07 (journalism is the unexcitable register)
to 3.47. Transition-openers from 0.02 (news never says "Moreover,") to 0.63
(scientific abstracts do). AI-vocabulary tolerance from 0.22 (literary) to 0.78
(scientific). "Human" is not one thing — a one-size humanizer damages most of these
seven registers, and the calibrated bands prevent that automatically.

## Sprint 1: discourse structure + enriched tells

The scorer now also measures document-level structure — sentence-opening transition
density, thesis/summary-opener rate, and paragraph-length uniformity — and the tell
catalog gained the post-2023 LLMisms (era framing, "first and foremost", hollow
affirmatives, etc.). The transition-opener row above is itself register-specific:
scientific abstracts open sentences with "Moreover/Thus" ~3x more than casual prose,
and literary fiction least of all — so a blanket "never start with a connective" rule
would mis-fire, exactly like the em-dash ban. After recalibrating all three registers
on these features, the blind A/B eval holds with no regression: **pro 5/5 / 4/4 / 4/4**.

The third discourse feature, `paragraph_cv` (paragraph-length uniformity), is **inert
across all seven registers**: the HuggingFace source datasets deliver each text as a
single field, and `fetch_corpus.clean()` collapses whitespace, so no corpus preserves
blank-line paragraph breaks — calibration yields a `0.0` floor and the feature never
penalizes (even journalism, expected to be multi-paragraph, flattens this way). It is
wired and tested, and works on real multi-paragraph *input* the user supplies; making
it live in *calibration* is **data-blocked, not code-blocked**: a probe of the source
datasets found zero paragraph breaks in 6 of 7 (CNN/DailyMail, Reddit-TLDR, arXiv,
WritingPrompts all deliver single-block text; only Stack Exchange answers carry real
paragraphs). So calibrated paragraph bands can't be derived from these corpora
regardless of how `clean()` treats newlines. Flagged here rather than left as a silent
no-op.

## Sprint 2: +4 registers (business, journalism, social-media, technical-docs)

Same machinery, four more calibrations (120 human pre-LLM texts each: Enron emails,
CNN/DailyMail articles, Reddit posts, Stack Exchange answers). Blind A/B, distance to
the register's human band (lower is better); baseline = register-blind scrub,
pro = register-faithful rewrite.

| register | sample | base_dist | pro_dist | winner |
|----------|--------|-----------|----------|--------|
| business | 01-status | 0.469 | **0.229** | pro |
| business | 02-vendor | 0.363 | **0.190** | pro |
| business | 03-followup | 0.358 | **0.267** | pro |
| journalism | 01-council | 0.811 | **0.102** | pro |
| journalism | 02-earnings | 1.834 | **0.085** | pro |
| journalism | 03-vaccine | 2.226 | **0.122** | pro |
| social-media | 01-hottake | 0.511 | **0.243** | pro |
| social-media | 02-anecdote | 0.469 | **0.181** | pro |
| social-media | 03-explainer | 0.467 | **0.279** | pro |
| technical-docs | 01-builderror | 0.269 | **0.185** | pro |
| technical-docs | 02-cors | 0.251 | **0.185** | pro |
| technical-docs | 03-killport | 0.296 | **0.212** | pro |

**pro wins 12/12.** The journalism gap is the widest in the project — a chatty,
de-attributed scrub of a news story (base up to 2.23) lands far outside the sober
news band, while the register-faithful rewrite sits almost on it (0.09–0.12).

### Register-awareness (the Sprint-2 proof)

One social-media rewrite (`eval/out/social-media/01-hottake.pro.txt`), scored under
two registers:

- under **social-media**: dist **0.243** (in-band — its contractions and loose rhythm
  are human here)
- under **scientific**: dist **0.830** (3.4x worse — the same casual prose is out of
  band for a paper)

The bands do the adapting: nothing about the text changed, only the register it is
judged against. A single-register tool would "fix" the Reddit post into something a
scientist might write, destroying it.

## Sprint 3: persona layer (voice, expertise, personas)

The target moves from "the average human in register X" to a *specific writer* —
still measured, never hand-tuned.

### Expertise tiers (measured, not heuristic)

Each register's 120 texts are split into terciles by **Flesch-Kincaid grade** (the
standard readability index, computed in stdlib). `novice` = the low-FK third,
`expert` = the high-FK third; `practitioner` is the full register band-set (so the
default is unchanged). The tiers separate cleanly on real data:

| register | FK novice | FK expert | sentence-len novice→expert | MTLD novice→expert |
|----------|-----------|-----------|----------------------------|--------------------|
| scientific | 5.9–14.2 | 17.0–26.1 | 13–24 → 23–38 | 50–93 → 51–119 |
| journalism | 5.4–10.2 | 11.7–17.1 | 15–21 → 20–27 | 70–136 → 83–143 |
| social-media | 1.3–7.4 | 9.2–16.4 | 11–19 → 19–32 | 59–116 → 67–124 |
| literary | 1.1–4.9 | 6.6–11.7 | 8–12 → 13–25 | 68–126 → 67–149 |

**Discrimination (scientific):** an expert-profile passage scores closer-to-human
under `expert` (0.473) than `novice` (0.522); a simple passage closer under `novice`
(0.861) than `expert` (0.948). The tier you pick changes what counts as human.

### Voice ("write like me")

`build_reference.py --voice-sample <dir>` calibrates personal bands from the user's
own texts; `stylo.py --voice <label>` scores against them. Samples under ~1500 words
are **blended** with a register fallback (weight = words/1500) and a warning is
printed — noisy bands are never presented as fully calibrated. Voice data is
gitignored (personal, not committed).

### Personas

`personas/<name>.json` = register + expertise tier + a small lexicon override, both
directions data-grounded:

- **deny** (enforce a persona's taste): a synergy-laden passage scores **0.811**
  under bare `business` but **1.764** under `--persona startup-founder` (its
  `lexicon_deny` adds 4 buzzword tells).
- **allow** (protect a voice's legitimate phrasing): `startup-founder` allows
  "in order to" and "let me know if" — both verified present in the real Enron
  business corpus. A founder email using them scores **0.718** under bare `business`
  (2 tells) but **0.393** under `--persona startup-founder` (0 tells), because the
  persona stops penalizing phrases real business writers actually use.

Four personas ship: `reddit-power-user`, `seasoned-journalist`, `startup-founder`,
`academic-humanist` — each a real register+tier plus a curated lexicon list.

### The v2 roadmap is complete

Sprint 1 gave the scorer document **structure**; Sprint 2 took it to **seven
registers**; Sprint 3 lets it imitate a **specific writer**. Tagged **v1.0.0**.
