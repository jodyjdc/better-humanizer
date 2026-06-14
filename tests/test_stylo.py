import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402

# Fixed band fixture for LOGIC tests, so they don't depend on the live, frequently
# recalibrated corpus/spontaneous/reference-stats.json. (The live file is exercised
# by test_score_discriminates_ai_from_human, which passes no ref.) These bands keep
# nonzero floors on em_dash/contraction so the over-correction logic is testable
# regardless of whether the current corpus happens to use those features.
TEST_REF = {
    "register": "test", "calibrated": False,
    "bands": {
        "sentence_length_mean": {"floor": 9, "ceiling": 24},
        "sentence_length_cv": {"floor": 0.45, "ceiling": 1.05},
        "mtld": {"floor": 45, "ceiling": 130},
        "ttr": {"floor": 0.40, "ceiling": 0.95},
        "hapax_ratio": {"floor": 0.30, "ceiling": 0.95},
        "em_dash_rate": {"floor": 0.05, "ceiling": 1.5},
        "comma_rate": {"floor": 3.5, "ceiling": 12},
        "contraction_rate": {"floor": 0.8, "ceiling": 6},
        "rule_of_three": {"floor": 0, "ceiling": 2},
        "exclaim": {"floor": 0, "ceiling": 2},
        "bold": {"floor": 0, "ceiling": 1},
        "emoji": {"floor": 0, "ceiling": 1},
    },
    "function_word_vector": {},
}


# --- Task 2: segmentation + structural metrics ---

def test_tokenize_and_sentences():
    t = "Hello world. I can't stop! Really?"
    assert stylo.tokenize(t) == ["hello", "world", "i", "can't", "stop", "really"]
    assert len(stylo.split_sentences(t)) == 3


def test_sentence_lengths_and_burstiness():
    t = "One two three. Four. Five six."
    assert stylo.sentence_lengths(t) == [3, 1, 2]
    b = stylo.burstiness(t)
    assert b["mean"] == 2 and b["sd"] > 0 and b["cv"] > 0


def test_lexical_basic():
    lx = stylo.lexical("the cat sat on the mat and the cat ran")
    assert 0 < lx["ttr"] <= 1
    assert lx["hapax_ratio"] > 0
    assert lx["mean_word_len"] > 0
    assert lx["mtld"] > 0


def test_burstiness_uniform_is_low_cv():
    uniform = stylo.burstiness("aa aa aa. bb bb bb. cc cc cc.")
    assert uniform["cv"] == 0  # AI-flat rhythm -> cv 0


# --- Task 3: punctuation, structural tells, lexicon hits, function words ---

def test_punctuation_em_dash():
    p = stylo.punctuation_rates("A - b, c; d -- e.")  # placeholder, see below
    # use real em/en dashes:
    p = stylo.punctuation_rates("A — b, c; d -- e.")
    assert p["em_dash"] > 0 and p["comma"] > 0 and p["semicolon"] > 0


def test_punctuation_zero_em_dash():
    p = stylo.punctuation_rates("Plain sentence with no dashes here.")
    assert p["em_dash"] == 0


def test_structural_tells():
    s = stylo.structural("## Big Title Here\n- one\n- two\n**bold** \U0001F680")
    assert s["bullet"] == 2 and s["bold"] == 1 and s["emoji"] == 1
    assert s["titlecase_heading"] == 1


def test_tell_hits_counts():
    lex = [{"id": 7, "name": "ai_vocabulary", "category": "language",
            "terms": ["delve", "tapestry"], "regexes": []}]
    h = stylo.tell_hits("We delve into the rich tapestry of delve.", lex)
    assert h["ai_vocabulary"] == 3


def test_tell_hits_regex():
    lex = [{"id": 9, "name": "negative_parallelism", "category": "language",
            "terms": [], "regexes": [r"\bnot just\b[^.?!]{1,60}\bbut\b"]}]
    h = stylo.tell_hits("It's not just a song but a statement.", lex)
    assert h["negative_parallelism"] >= 1


def test_rule_of_three():
    assert stylo.rule_of_three("speed, quality, and adoption matter") >= 1


# --- Sprint 1: discourse structure ---

def test_discourse_transition_opener_counted():
    # Sentence-initial transitions are the tell; one opener over a short text.
    out = stylo.discourse("Moreover, the system improved. The team shipped it.")
    assert out["transition_density"] > 0


def test_discourse_midsentence_transition_not_counted():
    # "thus"/"therefore" used mid-sentence is legitimate, not a tell.
    out = stylo.discourse("The build was green and thus we shipped the change.")
    assert out["transition_density"] == 0


def test_discourse_structural_opener_rate():
    two = "In today's world, things change. The dog slept by the fire all day."
    out = stylo.discourse(two)
    # One of two sentences opens with a thesis scaffold -> 0.5.
    assert abs(out["structural_opener_rate"] - 0.5) < 1e-9


def test_discourse_no_structural_opener():
    out = stylo.discourse("The dog slept. The cat watched. Rain fell outside.")
    assert out["structural_opener_rate"] == 0.0


def test_discourse_paragraph_cv_single_is_none():
    out = stylo.discourse("Just one paragraph here, no blank line breaks at all.")
    assert out["paragraph_cv"] is None


def test_discourse_paragraph_cv_multi_is_number():
    text = "Short one.\n\nA considerably longer paragraph that runs on for a while "
    text += "with several more words than the first.\n\nMid length here, roughly."
    out = stylo.discourse(text)
    assert out["paragraph_cv"] is not None and out["paragraph_cv"] > 0


def test_discourse_structural_opener_word_boundary():
    # "overall" must NOT match "overallocation" at a sentence start (boundary guard).
    out = stylo.discourse("Overallocation of memory crashed the job last night.")
    assert out["structural_opener_rate"] == 0.0


def test_discourse_paragraph_cv_uniform_is_zero():
    # Equal-length paragraphs -> cv 0.0 (the uniform-structure tell), not None.
    text = "one two three four five.\n\nsix seven eight nine ten."
    out = stylo.discourse(text)
    assert out["paragraph_cv"] == 0.0


# Multi-paragraph, transition-heavy, scaffold-opening AI structure vs. a human
# passage of similar length and topic.
AI_STRUCTURED = (
    "In today's rapidly evolving landscape, automation reshapes how teams work.\n\n"
    "Moreover, it accelerates routine tasks. Furthermore, it reduces toil. "
    "Additionally, it frees engineers for deeper work.\n\n"
    "In conclusion, the trajectory is clear and the future looks bright."
)
HUMAN_STRUCTURED = (
    "We turned the automation on for a week to see what stuck.\n\n"
    "It chewed through the boring edits fast. Config, scaffolding, the refactors "
    "I keep putting off. Then it confidently broke a test and lied about why.\n\n"
    "So: useful, with a leash. I read every diff before it lands."
)


def test_discourse_features_reported_in_score():
    out = stylo.score(AI_STRUCTURED, "spontaneous")
    assert "transition_density" in out["features"]
    assert "structural_opener_rate" in out["features"]


def test_discourse_distance_penalizes_ai_structure():
    ai = stylo.score(AI_STRUCTURED, "spontaneous")
    human = stylo.score(HUMAN_STRUCTURED, "spontaneous")
    assert ai["stylo_distance"] > human["stylo_distance"]
    # Guard the discourse wiring itself (the distance gap alone also reflects AI
    # tells): the AI structure must trip the thesis/summary-opener penalty.
    assert ai["features"]["structural_opener_rate"]["status"] == "above"


def test_discourse_single_paragraph_omits_paragraph_cv():
    # SMALL_HUMAN_TEXT is one paragraph -> paragraph_cv must not appear at all.
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous", ref=TEST_REF)
    assert "paragraph_cv" not in out["features"]


def test_discourse_excluded_from_outlier_veto():
    # Discourse z can blow far past 3, but discourse is scored AFTER the outlier
    # veto, so it must never set stylo_outlier. Use a ref with very wide banded
    # bands so the ONLY out-of-band signal is discourse (transition flooding);
    # ref has no discourse keys, so those fall back to DEFAULT_DISCOURSE_BANDS.
    wide = {
        "register": "t", "calibrated": False,
        "bands": {
            "sentence_length_mean": {"floor": 0, "ceiling": 100},
            "sentence_length_cv": {"floor": 0.0, "ceiling": 5},
            "mtld": {"floor": 0, "ceiling": 1000},
            "ttr": {"floor": 0.0, "ceiling": 1.0},
            "hapax_ratio": {"floor": 0.0, "ceiling": 1.0},
            "em_dash_rate": {"floor": 0.0, "ceiling": 100},
            "comma_rate": {"floor": 0.0, "ceiling": 100},
            "contraction_rate": {"floor": 0.0, "ceiling": 100},
            "rule_of_three": {"floor": 0, "ceiling": 100},
            "exclaim": {"floor": 0, "ceiling": 100},
            "bold": {"floor": 0, "ceiling": 100},
            "emoji": {"floor": 0, "ceiling": 100},
        },
        "function_word_vector": {},
    }
    stuffed = ("Moreover, the team shipped. Furthermore, we tested. "
               "Additionally, it scaled. Consequently, users stayed.")
    out = stylo.score(stuffed, "spontaneous", ref=wide)
    # Discourse is wildly out of band...
    assert out["features"]["transition_density"]["z"] > 3
    # ...but it does NOT trip the hard veto (moving the block above the veto fails this).
    assert out["stylo_outlier"] is False


def test_cosine_distance_identity():
    v = stylo.function_word_vector("the the of and to the", stylo.FUNCTION_WORDS)
    assert stylo.cosine_distance(v, v) < 1e-9


def test_cosine_distance_disjoint_is_one():
    a = {"the": 1.0}
    b = {"of": 1.0}
    assert abs(stylo.cosine_distance(a, b) - 1.0) < 1e-9


# --- Task 4: score(), bands, self-tell flags, vetoes ---

SMALL_HUMAN_TEXT = (
    "I wasn't sure the cafe would still be open. It was. The barista, same guy "
    "from last winter, just nodded at me like no time had passed. I ordered the "
    "usual, took the seat by the window, and watched the rain do its thing for a "
    "good while. Some mornings you really don't need much more than that."
)


def test_score_output_shape():
    out = stylo.score("Hello there, friend. How are you today?", "spontaneous")
    expected = {"register", "features", "tells", "self_tell_flags",
                "stylo_distance", "stylo_outlier"}
    assert expected <= out.keys()
    assert out["register"] == "spontaneous"
    assert out["stylo_distance"] >= 0


def test_score_flags_over_correction():
    # Flat rhythm + zero em dashes = over-corrected, should self-tell-flag.
    flat = "I went there. I saw it. I left then. It was fine. Nothing else."
    out = stylo.score(flat, "spontaneous", ref=TEST_REF)
    assert "sentence_length_cv" in out["self_tell_flags"]
    assert "em_dash_rate" in out["self_tell_flags"]


def test_score_human_like_not_outlier():
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous", ref=TEST_REF)
    assert out["stylo_outlier"] is False


def test_score_feature_status_values():
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous", ref=TEST_REF)
    for feat in out["features"].values():
        assert feat["status"] in ("below", "in", "above")
        assert "floor" in feat and "ceiling" in feat and "z" in feat


AI_TELLY = (
    "In today's rapidly evolving landscape, this stands as a testament to human "
    "ingenuity. It's not just about speed; it's about unlocking creativity at "
    "scale. These groundbreaking tools, nestled at the intersection of research "
    "and practice, underscore the pivotal role of automation. Ultimately, the "
    "future looks bright."
)
HUMAN_CLEAN = (
    "I used the thing for a week. It's quick at the boring stuff, config and test "
    "scaffolding and the refactors I'd put off. It's also wrong about a third of "
    "the time, which is its own kind of work. So, useful. Not magic. I'm keeping "
    "it, but I read every line before it ships."
)


def test_score_tell_density_enters_distance():
    out = stylo.score(AI_TELLY, "spontaneous")
    assert "tell_rate" in out["features"]
    assert out["features"]["tell_rate"]["value"] > 0


def test_score_discriminates_ai_from_human():
    ai = stylo.score(AI_TELLY, "spontaneous")
    human = stylo.score(HUMAN_CLEAN, "spontaneous")
    # Tell-laden AI text must score a clearly larger distance-to-human.
    assert ai["stylo_distance"] > human["stylo_distance"] + 0.2
    assert sum(ai["tells"].values()) > sum(human["tells"].values())


# Two rewrites with ~zero AI tells, but one is over-corrected (the failure mode
# of the original humanizer: flat rhythm, no em dash, no contractions). These are
# the exact eval/out worked-example texts, where the ordering must hold robustly.
SCRUBBED = (
    "AI coding assistants speed up parts of the work. They help with boilerplate "
    "and repetitive edits. They do not replace judgment, and they can produce "
    "errors. The tools are useful for routine tasks. Used with care, they can save "
    "time. They are not a replacement for review."
)
REGISTER_TRUE = (
    "I gave an AI coding assistant a real week of work. It's genuinely fast at the "
    "dull stuff: boilerplate, config, the repetitive refactors I keep avoiding. "
    "Where it falls down is judgment. It'll write something that looks right, "
    "compiles, and quietly does the wrong thing if you stop reading. So I keep it "
    "on, but I read every line before it ships. Faster, not smarter."
)


def _ref_with_tell_ceiling(ceiling):
    return {
        "register": "t", "calibrated": False,
        "bands": {**TEST_REF["bands"], "tell_rate": {"floor": 0.0, "ceiling": ceiling}},
        "function_word_vector": {},
    }


def test_tell_tolerance_register_calibrated():
    # Same tell-laden text; a register that tolerates more tells (high ceiling)
    # must score it closer to human than a strict register.
    text = "We delve into the crucial interplay of these intricate findings here."
    lax = stylo.score(text, ref=_ref_with_tell_ceiling(50))
    strict = stylo.score(text, ref=_ref_with_tell_ceiling(0.5))
    assert lax["features"]["tell_rate"]["status"] == "in"
    assert strict["features"]["tell_rate"]["status"] == "above"
    assert lax["stylo_distance"] < strict["stylo_distance"]


def test_overcorrection_penalized_in_distance():
    scrubbed = stylo.score(SCRUBBED, "spontaneous", ref=TEST_REF)
    faithful = stylo.score(REGISTER_TRUE, "spontaneous", ref=TEST_REF)
    # Both are tell-free, but the scrubbed one is more over-corrected...
    assert sum(scrubbed["tells"].values()) == 0
    assert len(scrubbed["self_tell_flags"]) > len(faithful["self_tell_flags"])
    # ...and that over-correction must cost it in the objective distance.
    assert scrubbed["stylo_distance"] > faithful["stylo_distance"]
