import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402


def test_count_syllables():
    assert stylo._count_syllables("cat") == 1
    assert stylo._count_syllables("cake") == 1          # silent trailing e
    assert stylo._count_syllables("table") == 2         # -le keeps its syllable
    assert stylo._count_syllables("syllable") == 3
    assert stylo._count_syllables("running") == 2
    assert stylo._count_syllables("") == 0


def test_flesch_kincaid_grade_orders_by_complexity():
    simple = "The cat sat on the mat. The dog ran. We had fun all day."
    dense = ("The epistemological ramifications of phenomenological inquiry "
             "necessitate a reconsideration of foundational presuppositions "
             "underlying contemporary hermeneutic methodologies.")
    assert stylo.flesch_kincaid_grade(dense) > stylo.flesch_kincaid_grade(simple)


def test_flesch_kincaid_grade_empty_is_zero():
    assert stylo.flesch_kincaid_grade("") == 0.0


def test_expertise_tiers_split_by_complexity():
    import statistics

    import build_reference
    simple = ["See the cat. See the dog. We run and play. It is fun. Yes it is."] * 6
    complex_ = [("The epistemological ramifications of phenomenological inquiry "
                 "necessitate reconsideration of foundational presuppositions "
                 "underpinning contemporary hermeneutic methodology and praxis.")] * 6
    novice, expert = build_reference.expertise_tiers(simple + complex_)
    nov_fk = statistics.fmean(stylo.flesch_kincaid_grade(t) for t in novice)
    exp_fk = statistics.fmean(stylo.flesch_kincaid_grade(t) for t in expert)
    assert exp_fk > nov_fk


def test_load_reference_expertise_selects_tier():
    full = stylo.load_reference("scientific")
    expert = stylo.load_reference("scientific", expertise="expert")
    novice = stylo.load_reference("scientific", expertise="novice")
    assert expert["bands"] != novice["bands"]
    # practitioner is the full band-set (backward-compatible default)
    assert stylo.load_reference("scientific", expertise="practitioner")["bands"] == full["bands"]


def test_expertise_discriminates():
    # A dense, high-grade passage should sit closer to the human band under
    # 'expert' than under 'novice' for the same register.
    dense = ("We demonstrate that the proposed estimator attains the minimax rate "
             "under heteroskedastic noise, and we characterize its asymptotic "
             "distribution via a functional central limit theorem.")
    exp = stylo.score(dense, "scientific", ref=stylo.load_reference("scientific", "expert"))
    nov = stylo.score(dense, "scientific", ref=stylo.load_reference("scientific", "novice"))
    assert exp["stylo_distance"] < nov["stylo_distance"]
