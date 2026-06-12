# Corpus provenance — literary register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM creative prose.
Only the derived statistics are committed; raw texts live in `raw/` (gitignored).
Reproduce: `python3 scripts/fetch_corpus.py --register literary --max-chars 3000`
then `python3 scripts/build_reference.py --register literary`.

## Source

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| WritingPrompts | `euclaise/writingprompts` (Fan et al. 2018) | short fiction from r/WritingPrompts | <= 2018 | collected 2018, pre-LLM; human creative writing |

The `story` field is used: narrative voice, dialogue, figurative language, and
deliberate rhythm variation. Current build: 120 texts pulled across the split (for
author/style variety), cleaned and filtered to 300–3000 chars, >= 4 sentences.

## Why this register matters most

The literary bands vindicate the anti-over-correction thesis hardest, on real data:

- **em-dash ceiling 1.71** vs 0.13 (spontaneous) and 0.00 (scientific) — about 13x
  the casual rate. The em dash, which the original humanizer hard-bans as "one of
  the most reliable AI tells", is a *staple literary device*. Banning it makes
  literary prose less human, not more.
- **highest sentence-length variation** (cv 0.45–0.95) — deliberate pacing, short
  punchy lines next to long flowing ones. Flattening rhythm is maximally wrong here.
- **contractions and exclamation** are common (dialogue), unlike scientific prose.

So "humanizing" literary text means the opposite of the other registers: preserve
the voice, figuration, dashes, and rhythm. The calibrated bands enforce that.

## Limitations (honest)

- **Single source, amateur/community fiction.** Style leans contemporary online
  creative writing, not the full literary canon. Blending in public-domain classics
  (Project Gutenberg) would broaden range; add a source to `fetch_corpus.py`.
- Reddit-origin user content used for aggregate statistics only, never
  redistributed (raw is gitignored). English only.
