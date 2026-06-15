import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402

LEX = [{"id": 1, "name": "ai_vocabulary", "category": "language",
        "terms": ["leverage", "robust"], "regexes": []}]


def test_tell_hits_allow_suppresses_term():
    base = stylo.tell_hits("we leverage a robust system", LEX)
    allowed = stylo.tell_hits("we leverage a robust system", LEX, allow={"leverage"})
    assert base["ai_vocabulary"] == 2
    assert allowed["ai_vocabulary"] == 1   # 'leverage' no longer counted


def test_tell_hits_deny_adds_terms():
    out = stylo.tell_hits("this is super synergistic", LEX, deny=["synergistic"])
    assert out["persona_deny"] == 1


def test_score_accepts_allow_deny():
    out = stylo.score("we leverage robust synergies", "business",
                      allow={"leverage"}, deny=["synergies"])
    assert "tell_rate" in out["features"]


def test_load_persona_resolves():
    p = stylo.load_persona("reddit-power-user")
    assert p["register"] == "social-media"
    assert "literally" in p["lexicon_allow"]


def test_resolve_target_persona():
    ref, register, allow, deny = stylo._resolve_target(
        register="spontaneous", persona="seasoned-journalist")
    assert register == "journalism"             # persona overrides --register
    assert ref["bands"] == stylo.load_reference("journalism", "expert")["bands"]
    assert "game-changing" in deny


def test_resolve_target_plain_register():
    ref, register, allow, deny = stylo._resolve_target(register="literary")
    assert register == "literary" and allow == set() and deny == []
    assert ref["bands"] == stylo.load_reference("literary")["bands"]
