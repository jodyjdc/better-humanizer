# Register profile: technical-docs

Defines what "human" means for technical documentation (Stack-Exchange-style
answers: imperative instructions, second person, code-switching, problem→solution
structure). The rewriter uses this as its brief; `scripts/stylo.py` enforces the
numeric bands from `corpus/technical-docs/reference-stats.json`, calibrated on real
pre-LLM Stack Exchange accepted answers. This register tolerates the most
AI-flavored vocabulary after scientific, because those words are genuine domain
terms here.

## What human technical writing actually looks like

- **Imperative mood and second person.** "Run X", "Use Java Web Start", "drop all
  dll files in the same directory", "look to Web Start". The reader is told what to
  do, directly. Imperatives are the register, not bluntness to be padded.
- **The widest sentence-length range of any register.** Sentence length spans 6–65
  words with the broadest variation (cv 0.28–1.03): a terse command ("Run the
  build.") sits right beside a long explanatory sentence about why the wrong dll
  loaded. Do not even this out — the spread is human here.
- **Code-switching and specificity.** Inline identifiers, filenames, flags, version
  numbers (`console.log`, `j3dcore-ogl.dll`, "32 vs 64 bit"). Keep every one; the
  technical specifics are the answer.
- **Problem→solution structure and terse enumerated steps.** State the problem,
  give the fix, often as numbered or short stepwise instructions. Keep the
  step-by-step shape; don't dissolve it into a paragraph.
- **Some AI-flavored vocabulary is genuine here.** The tell-tolerance ceiling is
  ~0.75 — the highest of the new registers and second only to scientific — because
  "robust", "leverage", and "seamless" are real domain terms when describing actual
  systems. Em dashes (ceiling 0.85) and contractions ("it's", "you'd", "won't",
  ceiling 3.06) are normal.

## Generation guidance (for the rewriter)

- **Keep imperatives and second person.** Do not convert "Run X" into "One might
  consider running X" — that softens the instruction into essay prose.
- Preserve the full sentence-length spread: keep the terse commands AND the long
  explanations. Do not normalize toward one mid length.
- Keep every identifier, filename, flag, version number, and code reference verbatim.
- Keep the problem→solution shape and any enumerated steps.
- Allow genuine domain vocabulary ("robust", "leverage") where it describes a real
  property — but cut it where it is just marketing tone (see below).

## Tell priority for this register (fix these first)

1. Marketing tone: "powerful", "game-changing", "effortlessly", "blazing-fast"
   layered onto a plain technical answer.
2. Hollow conclusions: "In conclusion, this powerful tool will revolutionize your
   workflow", generic upbeat wrap-ups a real answer never has.
3. Padding: inflating a terse step into a paragraph, restating the question back,
   filler transitions between steps.
4. Signposting ("Let's dive in", "In this guide, we will explore") and sycophancy
   ("Great question!").

## NOT tells here (do NOT remove)

Imperative mood. Second person. Terse commands beside long explanations (the widest
range in the project). Code identifiers and version specifics. Problem→solution
structure and enumerated steps. Genuine domain vocabulary ("robust", "leverage",
"seamless") used precisely. The calibrated bands treat all of these as in-band.

## Anti-over-correction rule

The failure mode here is "writing up" an answer into an essay: converting imperatives
to hedged suggestions, padding terse steps into prose, normalizing the sentence
length, and adding a marketing-flavored conclusion. That reads *less* like a real
answer — the register's signature is terse, specific, imperative instruction with a
wide rhythm spread, and the bands prove it (sentence range 6–65, tell tolerance
~0.75). Match the technical-docs band: keep the imperatives, the specifics, and the
short steps. If `stylo.py` flags `sentence_length_cv` below floor, you flattened the
terse/long contrast — put it back.
