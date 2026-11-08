#!/usr/bin/env python3
"""Static/corpus regression checks for the exp6 highlight-boundary fix."""
from __future__ import annotations

import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
CORPUS = Path(__file__).resolve().parent / "highlight-corpus"
EDITOR = PACKAGE / "widgets" / "rtf_editor.py"

EXPECTED_HASHES = {
    "normal.rtf": "328a6e939b8b0b9c7204b8bc61fb3bf9a9db525dad3ef223b08203e8bdc83872",
    "highlighted.rtf": "aefc34667f512330531f47e6c7295a672025ffe7194579c4d5c2265690c236db",
    "cleared-observed-bug.rtf": "20c9f3df8430f6d52ec432ca5125aec034e8192cb87426986d2159365ea5702b",
}


def require(value, message):
    if not value:
        raise AssertionError(message)


for name, expected in EXPECTED_HASHES.items():
    payload = (CORPUS / name).read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    require(actual == expected, f"highlight regression corpus changed: {name}")

normal = (CORPUS / "normal.rtf").read_text(encoding="latin-1")
highlighted = (CORPUS / "highlighted.rtf").read_text(encoding="latin-1")
cleared = (CORPUS / "cleared-observed-bug.rtf").read_text(encoding="latin-1")

require(r"\highlight1 fixing" not in normal, "normal sample unexpectedly contains highlight")
require(r"\red255\green242\blue0;" not in normal, "normal sample unexpectedly contains highlight colour")
require(r"\red255\green242\blue0;" in highlighted, "highlighted sample lost supplied yellow colour")
require(r"\highlight1 fixing" in highlighted, "highlighted sample no longer isolates the highlighted word")
require(r"\highlight1" not in cleared, "observed clear-highlight sample still contains RTF highlight")
require(r"\red255\green242\blue0;" not in cleared, "observed clear-highlight sample still contains yellow colour")
require(r"{\plain\f0\fs24 f}{\plain\f0\fs24 ixing}" in cleared, "observed first-character split is no longer represented by the supplied bug sample")
require(r"{\plain\f0\fs24  needs fixing}" in normal, "normal sample no longer contains the unsplit baseline run")

source = EDITOR.read_text(encoding="utf-8") + "\n" + (EDITOR.parent / "rwpyn" / "editor_formatting.py").read_text(encoding="utf-8")
for fragment in (
    "def _character_format_at_position(document, position):",
    "probe.setPosition(position+1,QTextCursor.MoveMode.KeepAnchor)",
    "current=QTextCharFormat(self._character_format_at_position(document,position))",
    "qfmt=self._character_format_at_position(document,run_end)",
    "replacement.clearProperty(QTextFormat.Property.BackgroundBrush)",
    "replacement.clearProperty(QTextFormat.Property.ForegroundBrush)",
    "replacement.clearProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY)",
    "run.setCharFormat(replacement)",
):
    require(fragment in source, f"exp6 highlight fix contract missing: {fragment}")

require(
    "fmt.setProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY,False)" not in source[source.index("def _apply_highlight"):source.index("def choose_text_colour")],
    "clear-highlight still leaves a false-valued automatic-contrast property behind",
)

print("highlight-boundary-qa: PASS")
