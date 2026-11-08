#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.1.8 final convergence wording/documentation gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def source(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha256(relative: str) -> str:
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()

init = source("__init__.py")
constants = source("app_constants.py")
main = source("widgets/main_window.py")
editor = source("widgets/rtf_editor.py")
doc = source("docs/Documentation.rtf")
component = json.loads((ROOT / "suite-pythoine-component.json").read_text(encoding="utf-8"))
manifest = json.loads((PACKAGE / "riqatonydesk.json").read_text(encoding="utf-8"))

require('APP_VERSION = "0.1.8"' in init, "0.1.8 package identity missing")
require('APP_REVISION = "0.1.8"' in constants, "0.1.8 revision identity missing")
require(component.get("version") == "0.1.8", "Suite component version mismatch")
require(manifest.get("version") == "0.1.8", "manifest version mismatch")

require('self.quick_start_action=self._command("Quick Tour",self._show_quick_tour,"Shift+F1")' in main,
        "shell Quick Tour action missing")
require('self.quick_start_action=self._command("Tutorial Wizard"' not in main,
        "stale shell Tutorial Wizard label remains")
require('this Quick Tour' in main and 'RiqatonyDesk GitHub Repository' in main,
        "Quick Tour help wording not aligned")
require('menu, "Quick Tour", self.show_tutorial_wizard,' in editor,
        "embedded help Quick Tour action missing")
require('Quick Tour (Shift+F1)' in editor, "embedded Quick Tour tooltip missing")
require('wizard.setWindowTitle("Quick Tour — RiqatonyDesk")' in editor,
        "embedded Quick Tour title missing")
require('RiqatonyDesk GitHub Repository' in editor,
        "embedded help repository wording missing")

require('RiqatonyDesk 0.1.8 is a Ribbon-based RTF editor' in doc,
        "F1 Documentation version is not 0.1.8")
require('RiqatonyDesk-0.1.8-x86_64.AppImage' in doc,
        "F1 Documentation AppImage examples are not 0.1.8")
require('External RTF mouse drops are import-only.' not in doc,
        "stale import-only drop wording remains in F1 Documentation")
for fragment in (
    'empty sidebar tree to import to the Workspace root',
    "sidebar file to import to that file's containing folder",
    "Dropping a supported RTF onto the editor opens it through RiqatonyDesk' external-file lifecycle instead of importing it",
    'Unrelated application chrome rejects drops',
):
    require(fragment in doc, f"F1 Documentation missing current drop contract: {fragment}")

expected = {
    'controllers/file_actions.py': 'a0a8e5e0ee4ab4f4df612e42f22c68b14bb167c1141eecb2bedd63fc26d2dbbd',
    'models/document_repository.py': 'e7e1829d7ee5d71644e5cffdb6fe98b533e44d44b6fe3e4436ad8179e83e6247',
    'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
    'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
    'widgets/navigation.py': '3b7d79ec70ce713cf0cbe2850a7d4fbf5e171a0326bb74449a7ded5e326a1711',
    'widgets/dashboard.py': 'f9c44c01fdc25061f095348a082986eb30f8b6a3576c7d92c4239fed54f46023',
    'widgets/folder_dashboard.py': '66cda277e6113251540f72ba8842b7e9a03ca6fe893e3a921085890f19360b0a',
    'controllers/editor_manager.py': '0b193baa75972318ae2502e3b6ccd6720236800dcd2606aca6a95399a8717151',
    'widgets/editor_page.py': '2908f58d89d039c6ff2c60b7cc843e1c577a56e0a3adca4a66a5444071bc4f11',
    'widgets/shell_ribbon.py': '4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993',
    'rtf_codec.py': '34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
}
for relative, digest in expected.items():
    require(sha256(relative) == digest, f"protected 0.1.7 implementation changed: {relative}")

if errors:
    print("RiqatonyDesk 0.1.8 check failed:")
    for error in errors:
        print("- " + error)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.1.8 final convergence wording/documentation contract")
