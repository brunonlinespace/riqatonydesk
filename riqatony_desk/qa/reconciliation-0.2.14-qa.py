#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.14 Audit 26 Ctrl+wheel host-bridge gate."""
from pathlib import Path
import hashlib

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors = []


def req(condition, message):
    if not condition:
        errors.append(message)


def src(relative):
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha(relative):
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()


init = src("__init__.py")
constants = src("app_constants.py")
main = src("widgets/main_window.py")
rtf = src("widgets/rtf_editor.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.14"' in init, "0.2.14 package identity missing")
req('APP_REVISION = "0.2.14"' in constants, "0.2.14 revision identity missing")
req('Current release: **0.2.14**' in readme, "README current release stale")

bridge = '''    def adjust_zoom_from_wheel(self, angle_delta_y) -> None:\n        self._editor_call("adjust_zoom_from_wheel", angle_delta_y)\n\n'''
req(main.count(bridge) == 1, "MainWindow Ctrl+wheel bridge must exist exactly once and use the existing _editor_call path")

# Prove the only MainWindow production delta from 0.2.13 is the exact bridge above.
main_without_bridge = main.replace(bridge, "", 1)
req(
    hashlib.sha256(main_without_bridge.encode("utf-8")).hexdigest()
    == "36997f762355cb6a53b0ffe402ad5cf9323130c83d8102d60ba7822d3dedd3d0",
    "MainWindow changed outside the exact Audit 26 bridge",
)

# Ricopad-authoritative wheel and zoom implementation must remain untouched.
req(
    sha("widgets/rtf_editor.py")
    == "409762cd779547b2e49b0d083175492872c4baee2de9ac5a8298afdcad8e7dd9",
    "Ricopad-derived RTF editor changed; Audit 26 must be host-bridge only",
)
for fragment in (
    "def wheelEvent(self, event):",
    "window = self.window()",
    'hasattr(window, "adjust_zoom_from_wheel")',
    "window.adjust_zoom_from_wheel(event.angleDelta().y())",
    "event.accept()",
    "def adjust_zoom_from_wheel(self, angle_delta_y):",
    "self.zoom_in()",
    "self.zoom_out()",
    "self.set_zoom_percent(self.zoom_percent + 10)",
    "self.set_zoom_percent(self.zoom_percent - 10)",
):
    req(fragment in rtf, f"Ricopad-authoritative Ctrl+wheel/zoom contract missing: {fragment}")

# Audit 26 must not spill into the surrounding editor, shell, lifecycle, or file stack.
protected = {
    "widgets/editor_page.py": "22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e",
    "widgets/shell_ribbon.py": "38ce2f39ea63ec26cb16220268b8cbd337e73f417158a73886144338a2afa570",
    "controllers/file_actions.py": "3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569",
    "controllers/editor_manager.py": "bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894",
    "services/open_document_monitor.py": "25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
    "services/filesystem_watcher.py": "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "services/document_scanner.py": "8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
    "models/document_repository.py": "e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f",
    "services/file_io.py": "96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55",
    "rtf_codec.py": "34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
    "rich_text_support.py": "6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb",
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.14 check failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("PASS: RiqatonyDesk 0.2.14 Audit 26 Ricopad-authoritative Ctrl+wheel host bridge")
