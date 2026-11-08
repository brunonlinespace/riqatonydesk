#!/usr/bin/env python3
"""Static regression checks for 0.0.4-exp7-r1 Tour/About polish."""
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
main = (PACKAGE / "widgets/main_window.py").read_text(encoding="utf-8")
about = (PACKAGE / "widgets/about_dialog.py").read_text(encoding="utf-8")

errors = []

for required in (
    'When document tabs are ',
    '<b>enabled</b>, <b>Ctrl+Tab</b> and <b>Ctrl+Shift+Tab</b>',
    '<b>disabled</b>, the same shortcuts move forward and backward through the Ribbon pages instead.',
    '<b>Ctrl+T</b> opens the current navigation context as a tab',
    '<b>Ctrl+W</b> closes the active document tab when tabs are enabled',
    '<b>Focused Mode</b> temporarily clears away surrounding interface elements',
    'Application and editor appearance are controlled independently.',
    'Changing App Theme does not automatically change the editor canvas',
    'changing Dark Editor does not change the application theme',
):
    if required not in main:
        errors.append(f"Tour copy missing: {required}")

for retired in (
    'The editor canvas follows the application <b>System, Dark or Light</b> theme by default',
    'persistent editor-only light/dark override, matching the sibling Plus behavior',
):
    if retired in main:
        errors.append(f"Deprecated theme/canvas Tour copy remains: {retired}")

for source_name, source in (("AboutDialog", about),):
    for required in (
        "https://github.com/59de44955ebd/PyWordpad",
        ">PyWordpad</a>",
        "Microsoft WordPad-inspired document features",
        'QPalette.ColorRole.LinkVisited',
        'QColor("#0068A6")',
    ):
        if required not in source:
            errors.append(f"{source_name} missing: {required}")
    if "Nuxpad 2 and WordPad-inspired" in source:
        errors.append(f"{source_name} retains old WordPad credit")

if about.find("Nuxpad 2") > about.find("PyWordpad") or about.find("PyWordpad") > about.find("Microsoft WordPad"):
    errors.append("About lineage order is not Nuxpad 2 -> PyWordpad -> Microsoft WordPad")

if errors:
    for error in errors:
        print(f"FAIL: {error}")
    raise SystemExit(1)

print("PASS: exp7-r1 Tour/About polish contract")
