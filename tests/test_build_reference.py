import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).parent.parent


def test_build_over_fixture():
    tmp = pathlib.Path(tempfile.mkdtemp())
    reg = tmp / "corpus" / "spontaneous"
    reg.mkdir(parents=True)
    (reg / "a.txt").write_text(
        "Short one. A much longer sentence that keeps going for a while, with "
        "several commas and clauses. Mid one here."
    )
    (reg / "b.txt").write_text(
        "I can't even. Honestly it's wild, really wild. Then it just stopped, and "
        "nobody said a word about it afterward."
    )
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_reference.py"),
         "--register", "spontaneous",
         "--corpus-root", str(tmp / "corpus"),
         "--out", str(tmp / "stats.json")],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    stats = json.loads((tmp / "stats.json").read_text())
    assert stats["calibrated"] is True
    assert stats["n_texts"] == 2
    cv = stats["bands"]["sentence_length_cv"]
    assert cv["ceiling"] >= cv["floor"]
    assert stats["function_word_vector"]  # non-empty: both texts have function words
    assert "tell_rate" in stats["bands"]  # register-specific tell tolerance calibrated
    assert stats["bands"]["tell_rate"]["ceiling"] >= 0


def test_build_empty_corpus_is_noop():
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "corpus" / "spontaneous").mkdir(parents=True)
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_reference.py"),
         "--register", "spontaneous",
         "--corpus-root", str(tmp / "corpus"),
         "--out", str(tmp / "stats.json")],
        capture_output=True, text=True,
    )
    assert out.returncode == 0
    assert not (tmp / "stats.json").exists()  # nothing written
    assert "warning" in out.stderr.lower()


def test_aggregate_emits_discourse_bands():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
    import build_reference
    texts = [
        "A short line.\n\nA longer paragraph with rather more words than the first one.",
        "Moreover, this opens with a transition. The next sentence is plain though.",
        "In today's world we begin. Then the story wanders somewhere quieter.",
    ]
    bands, _fw = build_reference.aggregate(texts)
    for key in ("transition_density", "structural_opener_rate", "paragraph_cv"):
        assert key in bands
    # transition_density / structural_opener_rate are high-tail: floor pinned to 0.
    assert bands["transition_density"]["floor"] == 0.0
    assert bands["structural_opener_rate"]["floor"] == 0.0
    # paragraph_cv is low-tail: a floor, no ceiling.
    assert bands["paragraph_cv"]["ceiling"] is None
    assert bands["paragraph_cv"]["floor"] >= 0.0
