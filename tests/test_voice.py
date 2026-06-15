import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_reference  # noqa: E402


def _voice_dir(words_per_text, n_texts):
    tmp = pathlib.Path(tempfile.mkdtemp())
    d = tmp / "voice"
    d.mkdir()
    sent = "I really think this little place is the best, honestly. "
    body = sent * max(1, words_per_text // 9)  # ~9 words per sentence
    for i in range(n_texts):
        (d / f"v{i:02d}.txt").write_text(body + "\n", encoding="utf-8")
    return tmp, d


def test_voice_large_sample_uses_own_bands():
    tmp, d = _voice_dir(words_per_text=300, n_texts=8)  # ~2400 words > 1500
    out = tmp / "voices" / "me" / "reference-stats.json"
    rc = build_reference.main(["--voice-sample", str(d), "--label", "me",
                               "--out-root", str(tmp / "voices")])
    assert rc == 0
    stats = json.loads(out.read_text())
    assert stats["calibrated"] is True
    assert stats["voice_blend_weight"] == 1.0   # large sample, no blend


def test_voice_small_sample_blends_and_warns():
    tmp, d = _voice_dir(words_per_text=40, n_texts=3)  # ~120 words << 1500
    out = tmp / "voices" / "tiny" / "reference-stats.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_reference.py"),
         "--voice-sample", str(d), "--label", "tiny",
         "--register", "spontaneous", "--out-root", str(tmp / "voices")],
        capture_output=True, text=True)
    assert proc.returncode == 0
    assert "warning" in proc.stderr.lower()
    stats = json.loads(out.read_text())
    assert 0.0 < stats["voice_blend_weight"] < 1.0   # blended
