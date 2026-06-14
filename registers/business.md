# Register profile: business

Defines what "human" means for internal business email (the working messages
colleagues send each other: action items, attachments, agreements, directives).
The rewriter uses this as its brief; `scripts/stylo.py` enforces the numeric bands
from `corpus/business/reference-stats.json`, calibrated on real pre-LLM Enron
internal email. The headline finding: this register is **semi-formal and
conversational**, not stiff-formal — and a naive "business = formal" rule
over-corrects genuine email into something less human.

## What human business writing actually looks like

- **Contractions are the norm, not a slip.** The contraction ceiling here is ~5.78,
  the **highest of any register** in the project. Real colleagues write "I'll get
  the agreement", "we're close to closing", "let me know how you'd like to handle
  this". Stripping them stiffens the email and reads tampered.
- **Salutations and sign-offs.** "Greg/Phillip,", "Phillip & Keith", "Sincerely,",
  "I look forward to hearing from you." Keep the human framing of a message.
- **Action items and polite directives.** "Please execute and send to...", "I will
  need contracts signed as soon as possible", "let me know how you wish to proceed."
  Imperatives softened by "please" are the register, not bluntness to be padded.
- **References to attachments, agreements, and logistics.** "Attached is the draw
  request", "the business points are in Exhibit C", a filename, an address, a time.
  Keep every concrete reference — these are hard to fabricate and carry the work.
- **Semi-formal, mixed rhythm.** Sentence length runs 8–27 words with moderate
  variation (cv 0.40–0.89). Some terse logistics, some longer explanation. Em dashes
  appear but are rare (ceiling 0.53); exclamation is low (ceiling 1.15).

## Generation guidance (for the rewriter)

- **Keep contractions.** Do not de-contract "I'll / can't / we're" into "I will not
  / cannot" across the board — that is the signature over-correction here.
- Preserve salutations, sign-offs, and the polite directive tone. Don't flatten
  "please send" into a bare command, and don't inflate it into a formal memo.
- Keep every attachment reference, filename, name, address, and deadline verbatim.
- Vary sentence length modestly; do not even it out into report cadence.
- Use plain words for plain things. A status update is a status update.

## Tell priority for this register (fix these first)

1. Marketing fluff: "seamless", "robust", "leverage", "best-in-class" dropped into
   an internal note where nobody is selling anything.
2. Hollow affirmatives and sycophancy: "Absolutely!", "Great question!", "Happy to
   help!" as filler openers.
3. Signposting: "Let's dive in", "In this email, I will outline", "To summarize the
   key points below."
4. Over-formalization: converting contractions to full forms, swapping "get" for
   "obtain", padding a two-line request into a paragraph.

## NOT tells here (do NOT remove)

Contractions (this register tolerates the most of any). Salutations and sign-offs.
Polite imperatives. Attachment and logistics references. A casual-but-professional
register mix. The calibrated bands treat all of these as in-band.

## Anti-over-correction rule

The failure mode here is "professionalizing" an email into a stiff report: stripping
every contraction, deleting the salutation, swapping plain verbs for Latinate ones,
and padding a quick directive into formal prose. That reads *less* human, not more —
the data is explicit that internal email is conversational and contraction-friendly.
Match the business band. If `stylo.py` flags a contraction rate near the floor or a
flattened rhythm, you over-corrected — put the conversational texture back.
