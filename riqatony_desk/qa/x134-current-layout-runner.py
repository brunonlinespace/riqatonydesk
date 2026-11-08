#!/usr/bin/env python3
"""Execute exact x13.3 current-layout QA copies without modifying x11.2 historical QA.

Copies in qa/current_x134/ are byte-identical to the working x13.3 layout-
adapted versions. During execution __file__ is the original QA location,
which preserves the tests' existing relative-path and source-tree assumptions.
Every check retains its original assertions.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

QA = Path(__file__).resolve().parent
PKG = QA.parent
ROOT = PKG.parent
ADAPTERS = QA / "current_x134"
REF = json.loads((QA / "x134-preservation-reference.json").read_text(encoding="utf-8"))


def one(name: str) -> None:
    if name not in REF["active_current_adapter_scripts"]:
        raise ValueError("not an approved current-layout test: " + name)
    original = QA / name
    adapted = ADAPTERS / name
    expected = REF["historic_x133_modified_sha256"][name]
    actual = hashlib.sha256(adapted.read_bytes()).hexdigest()
    if actual != expected:
        raise AssertionError("current-layout adapter changed: " + name)
    # Current x13.3 helper was likewise preserved byte-for-byte as a separate
    # current-layout adapter instead of overwriting the historical helper.
    sys.path.insert(0, str(ADAPTERS))
    sys.path.insert(1, str(QA))
    sys.path.insert(2, str(ROOT))
    namespace = {"__name__": "__main__", "__file__": str(original), "__package__": None}
    exec(compile(adapted.read_bytes(), str(original), "exec"), namespace)


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--single":
        one(sys.argv[2]); return 0
    if len(sys.argv) != 1:
        print("usage: x134-current-layout-runner.py [--single NAME]", file=sys.stderr)
        return 2
    errors = []
    for name in REF["active_current_adapter_scripts"]:
        finished = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--single", name],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True, capture_output=True, timeout=30, check=False,
        )
        if finished.returncode:
            errors.append(f"{name}: {finished.stderr.strip() or finished.stdout.strip()}")
        else:
            print(f"PASS current layout: {name}")
    if errors:
        for error in errors: print("FAIL current layout: " + error)
        return 1
    print(f"PASS x13.4: {len(REF['active_current_adapter_scripts'])} exact x13.3 layout-adapted QA contracts")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
