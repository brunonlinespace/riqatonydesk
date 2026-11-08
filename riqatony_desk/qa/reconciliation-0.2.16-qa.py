#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.16 Audit 12 preference-ownership gate."""
from pathlib import Path
import ast
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


def function_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    end = getattr(child, "end_lineno", child.lineno)
                    return "\n".join(lines[child.lineno - 1:end])
    raise AssertionError(f"function not found: {name}")


init = src("__init__.py")
constants = src("app_constants.py")
rtf = src("widgets/rtf_editor.py")
page = src("widgets/editor_page.py")
manager = src("controllers/editor_manager.py")
main = src("widgets/main_window.py")
config = src("services/config_service.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.16"' in init, "0.2.16 package identity missing")
req('APP_REVISION = "0.2.16"' in constants, "0.2.16 revision identity missing")
req('Current release: **0.2.16**' in readme, "README current release stale")

load = function_source(src("widgets/editor_preferences.py"), "load_preferences")
save = function_source(src("widgets/editor_preferences.py"), "save_preferences")

# Audit 12 removes only duplicate embedded persistence. Runtime attributes remain.
for fragment in (
    'self.show_status_bar = True',
    'self.appimage_theme = "system"',
    'self.appimage_icon_set = "new"',
    'self.persist_view_only = False',
    'self.tutorial_seen = False',
):
    req(fragment in load, f"embedded runtime default removed or changed: {fragment}")

# Plus-owned/stale values must no longer be sourced from editor.json.
for key in (
    '"show_status_bar"',
    '"show_counters"',
    '"view_only"',
    '"appimage_theme"',
    '"overall_theme"',
    '"appimage_icon_set"',
    '"tutorial_seen"',
):
    req(key not in load, f"embedded preferences still load host-owned/stale key: {key}")

# Nor may save_preferences persist competing copies.
for key in (
    '"show_status_bar"',
    '"show_counters"',
    '"view_only"',
    '"appimage_theme"',
    '"appimage_icon_set"',
    '"tutorial_seen"',
):
    req(key not in save, f"embedded preferences still save host-owned/stale key: {key}")

# Legitimate editor-domain preferences remain owned by editor.json.
for key in (
    '"word_wrap"',
    '"show_search_bar"',
    '"font_family"',
    '"font_size"',
    '"font_weight"',
    '"font_slant"',
    '"new_document_line_spacing"',
    '"new_document_alignment"',
    '"zoom_percent"',
    '"tab_width_spaces"',
    '"print_header_enabled"',
    '"print_header_left"',
    '"print_header_center"',
    '"print_header_right"',
    '"print_footer_enabled"',
    '"print_footer_left"',
    '"print_footer_center"',
    '"print_footer_right"',
):
    req(key in save, f"legitimate editor preference was removed from persistence: {key}")

# Existing Plus authority paths remain unchanged.
for fragment in (
    'self._status_visible = bool(config.get("show_status_bar", True))',
    'theme = str(self.config.get("app_theme", "light"))',
    'icon_set = str(self.config.get("editor_icon_set", "new"))',
    'self._surface.persist_view_only = enabled',
):
    req(fragment in page, f"EditorPage managed preference path changed: {fragment}")
req('self.config.set("lock_editor", enabled, save=True)' in manager,
    "EditorManager Locked Mode ownership changed")
for fragment in (
    'self.config.set("app_theme", theme, save=True)',
    'self.config.set("editor_icon_set", icon_set, save=True)',
    'self.config.set("show_status_bar", visible, save=True)',
):
    req(fragment in main, f"MainWindow Plus preference ownership changed: {fragment}")
for key in ('"app_theme"', '"editor_icon_set"', '"show_status_bar"', '"lock_editor"', '"quick_tour_seen"'):
    req(key in config, f"Plus config default missing: {key}")

# Exact resulting editor hash pins Audit 12 to the approved persistence-only change.
req(
    sha("widgets/rtf_editor.py") == "9017a17b2b17ea87cc85ccf61422f84ab911d1e7b896324fbfee7ff57e561a6c",
    "rtf_editor.py changed outside the approved Audit 12 persistence-only edit",
)

# No surrounding Plus/runtime authority may change.
protected = {
    "widgets/editor_page.py": "22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e",
    "controllers/editor_manager.py": "bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894",
    "widgets/main_window.py": "59d2227e2df86e7dab64bd2caa1d683b13ea8a4cfbdc2f0dc02bab9b194bc4e3",
    "services/config_service.py": "b4d72c5a9ac37d02b537c3fd8b83892b8ba01e22b5e339a14c4f65273e072e7e",
    "controllers/file_actions.py": "3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569",
    "widgets/shell_ribbon.py": "38ce2f39ea63ec26cb16220268b8cbd337e73f417158a73886144338a2afa570",
    "services/open_document_monitor.py": "25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
    "services/filesystem_watcher.py": "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "models/document_repository.py": "e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f",
    "services/file_io.py": "96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55",
    "rtf_codec.py": "34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
    "rich_text_support.py": "6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb",
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.16 check failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("PASS: RiqatonyDesk 0.2.16 Audit 12 duplicate embedded preference persistence removed")
