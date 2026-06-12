# Reference corpus — spontaneous register

The scorer defines "human" as **inside the distribution of real human writing for
this register**. That distribution comes from the texts in this folder. Quality of
the corpus is the single biggest lever on calibration accuracy.

## What to put here

Drop plain UTF-8 `.txt` files (one text each) into `corpus/spontaneous/`, then run:

```bash
python3 scripts/build_reference.py --register spontaneous
```

This overwrites `reference-stats.json` with bands measured from your texts
(`calibrated: true`). Until then, the shipped file holds heuristic defaults
(`calibrated: false`) — usable, but not measured.

## Sourcing rules

1. **Genuinely human.** The whole method collapses if AI text leaks into the
   reference. Bias hard toward material written **before 30 Nov 2022** (ChatGPT's
   public launch) — pre-launch text is human with very rare exceptions.
2. **License-clean.** Use only text you have the right to store and process:
   - **Your own writing.** Best option. The "human" target becomes *you*, so the
     tool doubles as voice personalization.
   - Public-domain material (old letters, diaries, essays, forum archives with
     compatible licenses).
   - Permissively-licensed corpora (check the license).
3. **No scraping behind paywalls or against a site's terms of service.** Don't
   collect private messages or personal data without consent.
4. **Register match.** This folder is *spontaneous* prose: blog posts, forum
   comments, personal email, opinion. Don't mix in papers or fiction — those get
   their own register folders in phase 2.

## How much

30–50 texts gives stable bands. Fewer works but the bands widen (less
discriminating). More is better up to a point. Aim for variety of authors so the
bands describe the register, not one person — unless personalization to one author
is the goal, in which case use only that author.
