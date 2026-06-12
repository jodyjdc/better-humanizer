<!-- Judge lens 2 of 3. Register fidelity. The orchestrator substitutes {{REGISTER}}
     and supplies the register profile (registers/{{REGISTER}}.md). Returns
     register_fit + critique; consumed by the SKILL.md aggregation. -->

# Register-fidelity lens

Does CANDIDATE read like genuine human writing in the **{{REGISTER}}** register, as
described in `registers/{{REGISTER}}.md`? The question is not "is it clean" but
"does it match how humans actually write in this register?"

What counts as a break depends on the register:
- **spontaneous**: stiffness, missing contractions, flat rhythm, no point of view,
  encyclopedic neutrality, press-release gloss.
- **scientific**: forced informality, added contractions, a fake first-person
  voice, choppy rhythm, removed hedging or qualifiers, marketing tone, lost numbers
  or citations.
- **literary**: flattened rhythm, stripped em dashes and fragments, deleted
  imagery, killed voice (a police-report rewrite of fiction); or the opposite,
  hollow purple figuration that means nothing precise.

In every register, penalize **over-correction**: prose pushed to an extreme away
from the register's human norm reads tampered, not human.

CANDIDATE (target register: {{REGISTER}}):
"""
{{CANDIDATE}}
"""

Return STRICT JSON, nothing else:

```json
{
  "register_fit": 0,
  "breaks": ["<what pulls it out of the {{REGISTER}} register>"],
  "critique": ["<actionable fix>"]
}
```
