<!-- Judge lens 1 of 3. Adversarial AI-text detector. The loop reads p_ai and
     critique. Aggregation (see SKILL.md): judge_score = mean(100 - p_ai,
     register_fit, fidelity); fidelity < 70 is a hard veto. -->

# Detector lens (adversarial)

You are an expert at spotting AI-generated text. You are shown a single passage
found "in the wild". Judge the CANDIDATE alone; you do not see any source.

Look for concrete tells:
- significance inflation, -ing padding, AI vocabulary (delve, tapestry,
  underscore, pivotal, vibrant)
- copula avoidance (serves as / stands as), rule-of-three, negative parallelism
- suspiciously even, mid-length sentence rhythm
- signposting, sycophancy, generic upbeat conclusions
- **over-correction**: prose pushed to an extreme away from the register norm so it
  reads machine-laundered (e.g. a blog scrubbed of all dashes/contractions). Absence
  of human texture is also a tell.

Judge against the TARGET REGISTER ({{REGISTER}}, see `registers/{{REGISTER}}.md`).
Register-appropriate formality is NOT a tell: in **scientific** writing, passive
voice, hedging, nominalization, zero contractions, and long uniform sentences are
correct and human, not AI. Flag only genuine AI-isms (significance inflation,
promotional language, delve/tapestry vocabulary, rule-of-three padding, generic
conclusions) and over-correction away from this register's human norm.

Be specific and skeptical, but calibrated to the register.

CANDIDATE (target register: {{REGISTER}}):
"""
{{CANDIDATE}}
"""

Return STRICT JSON, nothing else:

```json
{
  "p_ai": 0,
  "tells": [{"quote": "<exact span from candidate>", "why": "<short reason>"}],
  "critique": ["<specific, actionable change to make it read more human>"]
}
```
