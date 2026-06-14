# Corpus provenance — technical-docs register

`reference-stats.json` is calibrated from genuinely-human, pre-LLM technical prose.
Only the derived statistics are committed; raw texts live in `raw/` (gitignored).
Reproduce: `python3 scripts/fetch_corpus.py --register technical-docs --min-chars 300
--max-chars 3000 --min-sents 4` then `python3 scripts/build_reference.py --register
technical-docs`.

## Sources

| source | dataset | what | era | why human |
|--------|---------|------|-----|-----------|
| Stack Exchange | `lvwerra/stack-exchange-paired` | accepted answers (`response_j`) | <= 2021 | Stack Exchange data dump; the chosen ("j") answer is the human-upvoted one |

Current build: 120 texts, cleaned and filtered to 300–3000 chars, >= 4 sentences.
Stack Exchange answers are markdown-heavy, so `fetch_corpus.clean()` normalizes
markdown (links → anchor text, code spans → text, blockquote markers and bare URLs
removed) before the stylometry is computed.

## Why these are a sensible choice

- **Provably human.** Community answers from the Stack Exchange dump, pre-LLM.
- **Register match.** Imperative mood ("Run X", "Use Y"), second person,
  code-switching, terse enumerated steps, problem→solution structure.
- **License-clean for this use.** CC BY-SA Stack Exchange content; we commit only
  aggregate statistics and do not redistribute raw posts.

## What this register proves

Technical writing tolerates the most AI-flavored vocabulary of any register (tell
ceiling ~0.75, second only to scientific) because words like "robust", "leverage",
and "seamless" are genuine domain terms here. It also has the widest sentence-length
range (terse commands beside long explanatory sentences), so a uniform-rhythm
penalty would mis-fire. Imperatives and lists are human here, not tells.

## Limitations

Stack Exchange answers only (not official API docs, READMEs, or tutorials); English;
the markdown-flattening that removes code blocks also discards code that is sometimes
load-bearing context. Sentence segmentation is noisier here than in other registers
(stripped lists/code can leave long run-on spans). Add sources in `fetch_corpus.py`
`SOURCES["technical-docs"]` to broaden.
