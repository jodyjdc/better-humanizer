<!-- Independent blind judge for the A/B eval. Deliberately NOT one of the loop's
     judges (judges/*.md), so the system cannot win by gaming its own scorer.
     Present the two rewrites in RANDOM order as X and Y; do not reveal which is
     baseline and which is pro. -->

# Blind A/B judge

You are shown a SOURCE passage and two rewrites of it, X and Y, in random order.
You do not know how either was produced. Judge them.

SOURCE:
"""
{{SOURCE}}
"""

REWRITE X:
"""
{{X}}
"""

REWRITE Y:
"""
{{Y}}
"""

Decide:
1. Which reads more like genuine human writing (not "cleaner" — more *human*)?
2. Which is more faithful to the SOURCE's meaning (no dropped, added, or distorted
   claims)?

Return STRICT JSON, nothing else:

```json
{
  "more_human": "X" | "Y" | "tie",
  "more_faithful": "X" | "Y" | "tie",
  "why_human": "<one sentence>",
  "why_faithful": "<one sentence>"
}
```
