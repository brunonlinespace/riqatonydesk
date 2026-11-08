#!/usr/bin/env python3
"""Qt runtime regression tests for RiqatonyDesk exp6 highlight clearing."""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QA_STATE = tempfile.TemporaryDirectory(prefix="riqatonydesk-highlight-qa-")
os.environ["XDG_CONFIG_HOME"] = QA_STATE.name
sys.dont_write_bytecode = True

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
PROJECT = PACKAGE.parent
CORPUS = pathlib.Path(__file__).resolve().parent / "highlight-corpus"
sys.path.insert(0, str(PROJECT))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QApplication

from riqatony_desk.rtf_codec import (
    RTF_AUTOMATIC_CONTRAST_PROPERTY,
    _qt_brush_colour,
    _rtf_clear_automatic_foreground,
    decode_rtf,
    document_to_rtf,
    populate_qtextdocument_from_rtf_model,
)
from riqatony_desk.widgets import rtf_editor as rtf_editor_module
from riqatony_desk.widgets.rtf_editor import RicopadEditorWidget

rtf_editor_module.platform_config_locations = lambda: (QA_STATE.name, ())
app = QApplication.instance() or QApplication(["riqatonydesk-highlight-qa"])


def require(value, message):
    if not value:
        raise AssertionError(message)


def set_selection(editor, start, end):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


def format_at(surface, position):
    # Keep the complete Qt format object instead of forcing opaque QVariant
    # properties (for example QMap<QFont::Tag,uint>) through Python. Qt's
    # native QTextCharFormat equality still verifies exact formatting.
    return QTextCharFormat(surface._character_format_at_position(surface.visual_editor.document(), position))


def round_trip_selection(text, start, end, colour):
    surface = RicopadEditorWidget()
    editor = surface.visual_editor
    editor.setPlainText(text)
    before = [format_at(surface, i) for i in range(start, end)]
    set_selection(editor, start, end)
    surface._apply_highlight(colour=QColor(colour))
    for i in range(start, end):
        fmt = surface._character_format_at_position(editor.document(), i)
        require(_qt_brush_colour(fmt.background()) is not None, f"highlight missing at {i}")
        require(bool(fmt.property(RTF_AUTOMATIC_CONTRAST_PROPERTY)), f"automatic contrast tag missing at {i}")
    surface.clear_highlight()
    after = [format_at(surface, i) for i in range(start, end)]
    require(after == before, f"clear highlight did not restore exact character formatting for {text[start:end]!r}")
    payload = document_to_rtf(editor.document())
    require(br"\highlight" not in payload, "cleared highlight serialized back into RTF")
    return surface


# First/middle/final selection boundaries all return to their original exact format.
for text, start, end in (
    ("first middle final", 0, 5),
    ("first middle final", 6, 12),
    ("first middle final", 13, 18),
):
    round_trip_selection(text, start, end, "#fff200")

# Dark highlight uses automatic white contrast; clearing must remove it completely.
surface = round_trip_selection("before fixing after", 7, 13, "#000000")
for i in range(7, 13):
    fmt = surface._character_format_at_position(surface.visual_editor.document(), i)
    require(_qt_brush_colour(fmt.foreground()) is None, "automatic white foreground survived black-highlight clearing")
    require(not fmt.hasProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY), "automatic contrast marker survived clearing")

# An explicit user foreground is never mistaken for Rico's automatic contrast.
surface = RicopadEditorWidget(); editor = surface.visual_editor; editor.setPlainText("before fixing after")
set_selection(editor, 7, 13)
explicit = QTextCharFormat(); explicit.setForeground(QColor("#d00000")); explicit.setProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY, False)
editor.textCursor().mergeCharFormat(explicit)
before = [format_at(surface, i) for i in range(7, 13)]
set_selection(editor, 7, 13); surface._apply_highlight(colour=QColor("#fff200"))
for i in range(7, 13):
    fmt = surface._character_format_at_position(editor.document(), i)
    require(_qt_brush_colour(fmt.foreground()).name().lower() == "#d00000", "explicit foreground was replaced by highlight contrast")
    require(not bool(fmt.property(RTF_AUTOMATIC_CONTRAST_PROPERTY)), "explicit foreground was tagged automatic")
surface.clear_highlight()
require([format_at(surface, i) for i in range(7, 13)] == before, "explicit foreground did not survive highlight/clear exactly")

# Caret-only clear uses WordUnderCursor and must clean the whole touched word.
surface = RicopadEditorWidget(); editor = surface.visual_editor; editor.setPlainText("before fixing after")
set_selection(editor, 7, 13); surface._apply_highlight(colour=QColor("#fff200"))
caret = QTextCursor(editor.document()); caret.setPosition(9); editor.setTextCursor(caret); surface.clear_highlight()
for i in range(7, 13):
    fmt = surface._character_format_at_position(editor.document(), i)
    require(_qt_brush_colour(fmt.background()) is None, "caret clear left highlight inside the word")
    require(_qt_brush_colour(fmt.foreground()) is None, "caret clear left automatic contrast inside the word")
    require(not fmt.hasProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY), "caret clear left automatic marker inside the word")

# Reproduce the user's exact highlighted sample, clear only `fixing`, and verify
# it rejoins the surrounding ordinary run semantically instead of leaving the
# observed f/ixing split.
surface = RicopadEditorWidget(); editor = surface.visual_editor
decoded = decode_rtf((CORPUS / "highlighted.rtf").read_bytes())
if not populate_qtextdocument_from_rtf_model(editor.document(), decoded.model):
    editor.document().setHtml(decoded.html)
    if decoded.automatic_foreground:
        _rtf_clear_automatic_foreground(editor.document(), decoded.automatic_foreground)
plain = editor.toPlainText(); start = plain.index("fixing"); end = start + len("fixing")
set_selection(editor, start, end); surface.clear_highlight()
reference = format_at(surface, start - 1)
for i in range(start, end):
    require(format_at(surface, i) == reference, f"supplied corpus clear left a different format at fixing[{i-start}]")
payload = document_to_rtf(editor.document())
require(br"\highlight" not in payload, "supplied highlighted sample still serializes highlight after clear")
require(br"\red255\green242\blue0;" not in payload, "unused supplied yellow highlight colour survived serialization")
require(br"{\plain\f0\fs24 f}{\plain\f0\fs24 ixing}" not in payload, "supplied regression still serializes the f/ixing split")

print("highlight-runtime-qa: PASS")
