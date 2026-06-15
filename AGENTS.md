# AGENTS.md — humanizer-pro (Codex entrypoint)

This repo is **humanizer-pro**: a measured, register-aware text humanizer. It rewrites
AI-sounding text so it lands inside the *real human distribution* for its register, and
proves it with a stylometric score instead of guessing.

**Explicit non-goal:** this is NOT a commercial-detector evader (no GPTZero / Turnitin
/ watermark gaming). The target is the human distribution, framed as writing quality —
not deception.

## When to act

When the user asks to humanize / de-AI / rewrite a passage (optionally naming a
register), run the humanizer-pro loop.

## The canonical workflow lives in SKILL.md

The full loop — generate K candidate rewrites → hybrid score (stylometrics + judge
panel) → apply vetoes → keep the best → iterate on the judges' critique — is documented
once in [`SKILL.md`](SKILL.md). **Read it and follow it.** SKILL.md is written with
Claude Code tool names; translate to Codex:

| SKILL.md says | In Codex |
|---|---|
| `Read` / `Write` / `Edit` | your native file tools |
| `Bash` | your native shell |
| `AskUserQuestion` | ask the user inline |
| `Workflow` / parallel candidates & judges | run them sequentially (the logic is identical), or use `spawn_agent` if you have `multi_agent = true` in `~/.codex/config.toml` |

Everything else in SKILL.md — the composite formula, the hard vetoes, K = 3 candidates,
k = 2 iterations, and the register/judge briefs — is platform-agnostic prose. Follow it
verbatim. The result is identical on both platforms because the scoring is deterministic
(a Python subprocess), not model-dependent.

## The deterministic core (identical on every platform)

The scorer is standard-library Python, zero dependencies:

```bash
python3 scripts/stylo.py <candidate-file> --register <register>
```

Optional target overrides (one writer instead of the register average):
`--expertise novice|practitioner|expert`, `--persona <name>` (personas/), or
`--voice <label>` (a voice calibrated via `build_reference.py --voice-sample`).
Precedence: persona > voice > expertise > register.

It prints JSON: `stylo_distance` (lower = closer to the human band), `self_tell_flags`
(over-correction — scrubbing a text flat is itself a tell), `stylo_outlier` (hard veto),
and per-feature `features` (including the discourse features `transition_density`,
`structural_opener_rate`, `paragraph_cv`).

Where everything lives:

- **Registers (7):** spontaneous, scientific, literary, business, journalism,
  social-media, technical-docs.
- **Register briefs:** `registers/<name>.md` — what is human vs. a tell in that register.
- **Judge prompts:** `judges/*.md` — substitute `{{REGISTER}}`.
- **Tell catalog:** `lexicons/ai_tells.json` (single source of truth, shared by the
  scorer and the judges).
- **Human bands:** `corpus/<name>/reference-stats.json` (calibrated on 120 real,
  pre-LLM human texts per register; raw texts are gitignored).

## Recalibrate or add a register (optional)

```bash
python3 scripts/fetch_corpus.py --register <name>     # pull a human corpus (HF rows API, stdlib)
python3 scripts/build_reference.py --register <name>  # recompute the bands
make test    # stdlib test suite (no pytest needed)
make eval    # blind A/B per register
```

## Notes for the Codex sandbox

- If branch/push is blocked (detached HEAD in a managed worktree), commit locally and
  use the App's "Create branch" / "Hand off to local" controls.
- The HF rows API needs working TLS; on some Python builds set `SSL_CERT_FILE` (see
  `scripts/fetch_corpus.py`).
