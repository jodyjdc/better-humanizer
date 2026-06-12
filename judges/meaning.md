<!-- Judge lens 3 of 3. Meaning preservation. fidelity < 70 is a HARD veto in the
     loop: a fluent rewrite that drops or distorts the source fails outright. -->

# Meaning-fidelity lens

Compare CANDIDATE against SOURCE. Does the rewrite keep everything the source
says (every claim, fact, number, name, and qualifier) without adding new claims or
distorting meaning?

This is the guardrail against fluent infidelity: a rewrite can read perfectly
human and still be wrong because it dropped a caveat or invented a detail. Catch
that.

SOURCE:
"""
{{SOURCE}}
"""

CANDIDATE:
"""
{{CANDIDATE}}
"""

Return STRICT JSON, nothing else:

```json
{
  "fidelity": 100,
  "dropped": ["<info present in SOURCE but missing from CANDIDATE>"],
  "added": ["<claim in CANDIDATE not supported by SOURCE>"],
  "distorted": ["<meaning that changed>"]
}
```
