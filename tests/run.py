#!/usr/bin/env python3
"""Zero-dependency test runner. Discovers and runs every test_* function in
tests/test_*.py. Usage: python3 tests/run.py [name-filter]"""
import importlib.util
import pathlib
import sys
import traceback

TESTS_DIR = pathlib.Path(__file__).parent


def load(modpath):
    spec = importlib.util.spec_from_file_location(modpath.stem, modpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    passed = failed = 0
    fails = []
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        if only and only not in f.name:
            continue
        module = load(f)
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
                print(f"PASS {f.name}::{name}")
            except Exception as exc:  # noqa: BLE001 - test harness reports all
                failed += 1
                fails.append((f.name, name, traceback.format_exc()))
                print(f"FAIL {f.name}::{name}: {exc}")
    print(f"\n{passed} passed, {failed} failed")
    for fname, tname, tb in fails:
        print("\n" + "=" * 60 + f"\n{fname}::{tname}\n{tb}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
