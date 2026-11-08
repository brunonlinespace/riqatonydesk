#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.3 Grid/mouse-navigation release gate."""
from __future__ import annotations

import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors: list[str] = []

def req(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)

def src(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")

def sha(relative: str) -> str:
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()

main = src("widgets/main_window.py")
card = src("widgets/dashboard_card.py")
init = src("__init__.py")
constants = src("app_constants.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.3"' in init, "0.2.3 package identity missing")
req('APP_REVISION = "0.2.3"' in constants, "0.2.3 revision identity missing")

for fragment in (
    'QPushButton("" if grid else text)',
    'button.setFixedSize(44, 44)',
    'button.setIconSize(QSize(28, 28))',
    'button.setAccessibleName(text)',
    'minimum_width=None if grid else 96',
):
    req(fragment in card, f"Grid icon-button contract missing: {fragment}")
req('button.setMinimumHeight(32)' not in card, "old Grid minimum-height treatment remains")

for fragment in (
    'app.installEventFilter(self)',
    'event.button() == Qt.MouseButton.BackButton',
    'self._navigation_history: list[str] = []',
    'if len(self._navigation_history) > 64:',
    'self._navigation_pending = target',
    'QTimer.singleShot(0, self._commit_navigation_record)',
    'target.startswith("folder:")',
    'target.startswith("document:")',
):
    req(fragment in main, f"mouse Back navigation contract missing: {fragment}")
req('Qt.Key.Key_Backspace' not in main, "keyboard Backspace navigation was added out of scope")

req('Current release: **0.2.3**' in readme, "root README current release is stale")

protected = {'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999', 'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad', 'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123', 'controllers/editor_manager.py': '82a88e86c1a69a942dd88bc6b09be85a7b54f5f16d24b7f05592d422378b5959', 'widgets/editor_page.py': '6de5e5858f41813f87ce1591bb3966dc797873e2228e284be119a40395d937b2', 'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f', 'widgets/resolve_open_documents_dialog.py': '38657cbfaf21ab286cb58dc2cd8fac43b2b562d270629d98276274d68c17047e', 'widgets/shell_ribbon.py': '4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993', 'services/config_service.py': 'c2741e48d3b1416d365625a8e7e49acf09db833117fa63827e65e5af0a67d131'}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.3 check failed:")
    for error in errors:
        print("- " + error)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.3 Grid/mouse-navigation contract")
