#!/usr/bin/env python3
"""Static regression checks for 0.0.4-exp7-r2 About-link legibility."""
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
theme = (PACKAGE / "widgets/rico_theme.py").read_text(encoding="utf-8")
about = (PACKAGE / "widgets/about_dialog.py").read_text(encoding="utf-8")

errors = []

for required in (
    'palette.setColor(QPalette.ColorRole.Link, QColor("#0068A6"))',
    'palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#0068A6"))',
):
    if required not in theme:
        errors.append(f"Explicit Light palette missing: {required}")

for source_name, source in (("AboutDialog", about),):
    for required in (
        'details_palette.setColor(QPalette.ColorRole.Link, about_link_blue)',
        'details_palette.setColor(QPalette.ColorRole.LinkVisited, about_link_blue)',
        'details.setPalette(details_palette)',
        'details.setText(',
    ):
        if required not in source:
            errors.append(f"{source_name} missing: {required}")
    palette_pos = source.find('details.setPalette(details_palette)')
    text_pos = source.find('details.setText(')
    if not (0 <= palette_pos < text_pos):
        errors.append(f"{source_name} does not apply the link palette before RichText HTML is parsed")

if errors:
    for error in errors:
        print(f"FAIL: {error}")
    raise SystemExit(1)

print("PASS: exp7-r2 About-link palette contract")
