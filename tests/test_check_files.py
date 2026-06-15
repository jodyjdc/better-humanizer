"""Tests for scripts/check_files.py — the humanize-check Action engine."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_files  # noqa: E402


def test_flags_ai_passes_pro():
    ai = sorted((ROOT / "eval" / "ai_samples" / "literary").glob("*.txt"))
    pro = sorted((ROOT / "eval" / "out" / "literary").glob("*.pro.txt"))
    ai_rows = check_files.check([str(p) for p in ai], "literary", 0.6)
    pro_rows = check_files.check([str(p) for p in pro], "literary", 0.6)
    # humanized output must never be flagged at the default gate
    assert pro_rows and not any(r["flagged"] for r in pro_rows), "humanized output should pass"
    # raw AI scores clearly higher and the majority flags (some are borderline by design)
    ai_mean = sum(r["distance"] for r in ai_rows) / len(ai_rows)
    pro_mean = sum(r["distance"] for r in pro_rows) / len(pro_rows)
    assert ai_mean > pro_mean, "AI text should sit further from the human band than humanized text"
    assert sum(r["flagged"] for r in ai_rows) >= len(ai_rows) / 2, "most raw AI should be flagged"


def test_expand_dedups_and_keeps_files_only():
    g = str(ROOT / "eval" / "out" / "literary" / "*.pro.txt")
    files = check_files._expand([g, g])  # duplicate glob
    assert files
    assert len(files) == len(set(files)), "globs must de-dup"
    assert all(pathlib.Path(f).is_file() for f in files)


def test_main_exit_codes():
    pro = str(ROOT / "eval" / "out" / "literary" / "04-noir.pro.txt")
    ai = str(ROOT / "eval" / "ai_samples" / "literary" / "01-rain.txt")
    assert check_files.main(["--files", pro, "--register", "literary", "--max-distance", "0.6"]) == 0
    assert check_files.main(["--files", ai, "--register", "literary", "--max-distance", "0.6",
                             "--fail-on-flag", "true"]) == 1
    # fail-on-flag=false must not fail the build even when a file is flagged
    assert check_files.main(["--files", ai, "--register", "literary", "--max-distance", "0.6",
                             "--fail-on-flag", "false"]) == 0


def test_no_match_is_not_a_failure():
    assert check_files.main(["--files", "no/such/path/*.md", "--register", "literary"]) == 0
