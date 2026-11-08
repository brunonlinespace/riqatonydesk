#!/usr/bin/env python3
"""Current PyQt6 workspace-integration QA compatibility entry point.

Execute the original x13.3 workspace test with precisely one import relocation
applied in memory. The original historical QA script is never changed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

QA = Path(__file__).resolve().parent
REF = json.loads((QA / "x134-preservation-reference.json").read_text(encoding="utf-8"))
HISTORIC = QA / "workspace-integration-qa.py"
OLD = "from riqatony_desk.widgets.shortcuts_dialog import ("
NEW = "from riqatony_desk.widgets.dialogs.shortcuts_dialog import ("

def adapted_source() -> str:
    content = HISTORIC.read_bytes()
    relative = "riqatony_desk/qa/workspace-integration-qa.py"
    if hashlib.sha256(content).hexdigest() != REF["baseline_sha256_by_path"][relative]:
        raise AssertionError("Historical workspace integration test changed")
    original = content.decode("utf-8")
    if original.count(OLD) != 1 or NEW in original:
        raise AssertionError("Unexpected historical shortcuts import contract")
    current = original.replace(OLD, NEW, 1)
    if current.replace(NEW, OLD, 1) != original:
        raise AssertionError("Current-path adapter rewrote more than the import")
    compile(current, str(HISTORIC), "exec")
    return current


def main() -> None:
    adapted = adapted_source()
    if "--static" in sys.argv[1:]:
        print("PASS x13.4: current workspace integration test import only; original unchanged")
        return
    sys.path.insert(0, str(QA.parent.parent))
    namespace = {"__name__": "__main__", "__file__": str(HISTORIC), "__package__": None}
    exec(compile(adapted, str(HISTORIC), "exec"), namespace)

if __name__ == "__main__":
    main()
