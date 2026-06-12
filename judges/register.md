<!-- Judge lens 2 of 3. Register fidelity for spontaneous prose. Returns
     register_fit + critique; consumed by the SKILL.md aggregation. -->

# Register-fidelity lens (spontaneous)

Does CANDIDATE read like genuine human *spontaneous* writing: a real blog post,
forum comment, personal email, or opinion piece? The question is not "is it
clean". It is "does this read like the uneven, personal, contraction-using prose a
person actually writes?"

Penalize:
- stiffness and missing contractions
- flat, even sentence rhythm
- no point of view; encyclopedic neutrality
- press-release or marketing gloss
- over-laundered prose that reads scrubbed rather than written

CANDIDATE:
"""
{{CANDIDATE}}
"""

Return STRICT JSON, nothing else:

```json
{
  "register_fit": 0,
  "breaks": ["<what pulls it out of the spontaneous register>"],
  "critique": ["<actionable fix>"]
}
```
