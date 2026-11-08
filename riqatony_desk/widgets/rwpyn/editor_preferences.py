#!/usr/bin/env python3
"""Original editor preferences and new-document defaults, relocated at x6.0.

The editor method bodies are unchanged; resource lookup retains its old widgets/ base after relocation.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextBlockFormat, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFontComboBox, QFormLayout, QLabel, QMessageBox)
from riqatony_desk.services.rtf_new_document import NewDocumentDefaults, build_new_document_rtf_payload
from riqatony_desk.widgets.rwpyn.editor_insertion import read_bounded_bytes
from riqatony_desk.widgets.rwpyn.editor_printing import fsync_directory

MAX_CONFIG_FILE_SIZE = 1024 * 1024  # 1 MiB; preferences should remain tiny.

def preference_bool(data, key, default):
    value = data.get(key, default)
    return value if isinstance(value, bool) else bool(default)

def preference_text(data, key, default, *, limit=512):
    value = data.get(key, default)
    if not isinstance(value, str):
        return str(default)
    return value[:limit]

def resource_path(*parts):
    """Return an asset path in source, portable, legacy, and AppImage layouts."""
    candidates = []
    appdir = os.environ.get("APPDIR")
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # PyInstaller places bundled data beside the frozen script location.
    candidates.append(os.path.join(script_dir, *parts))

    # Source-portable layout: implementation modules and assets share the
    # RiqatonyDesk package directory.
    candidates.append(os.path.join(script_dir, "assets", *parts))

    # Compatibility with the earlier RC3 source/ subdirectory layout.
    candidates.append(
        os.path.normpath(os.path.join(script_dir, "..", "assets", *parts))
    )

    # Retain compatibility with the unpublished 2.3.x development layout.
    candidates.append(os.path.join(script_dir, "ricopad-assets", *parts))

    if appdir:
        candidates.append(os.path.join(appdir, *parts))
        candidates.append(
            os.path.join(appdir, "usr", "share", "riqatonydesk", *parts)
        )

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


class EditorPreferencesMixin:
    def apply_preferences(self):
        self.apply_editor_font()
        self.set_word_wrap_mode()
        self.search_container.hide()
        self.status_bar_action.blockSignals(True)
        self.status_bar_action.setChecked(bool(self.show_status_bar))
        self.status_bar_action.blockSignals(False)
        self.app_status_bar.setVisible(self.show_status_bar)
        self._update_mode_capabilities()
        self.apply_tab_width()
        self.apply_zoom_preference()

    def load_preferences(self):
        self.word_wrap = True
        self.show_status_bar = True
        self.show_search_bar = False
        self.base_font_family = "Sans Serif"
        self.base_font_size = 12
        self.base_font_weight = "normal"
        self.base_font_slant = "roman"
        self.new_document_line_spacing = 115
        self.new_document_alignment = "left"
        self.appimage_theme = "system"
        self.appimage_icon_set = "new"
        self.editor_canvas_theme = "light"
        self.zoom_percent = 100
        self.tab_width_spaces = 4
        self.persist_view_only = False
        self.print_header_enabled = True
        self.print_header_left = "&F"
        self.print_header_center = ""
        self.print_header_right = ""
        self.print_footer_enabled = True
        self.print_footer_left = ""
        self.print_footer_center = "Page &P of &N"
        self.print_footer_right = ""
        self.tutorial_seen = False

        source_file = self.config_file
        migrating_preferences = False
        if not os.path.isfile(source_file):
            for candidate in self.config_import_candidates:
                if candidate != self.config_file and os.path.isfile(candidate):
                    source_file = candidate
                    migrating_preferences = True
                    break
        try:
            raw = read_bounded_bytes(source_file, MAX_CONFIG_FILE_SIZE, label="preferences file")
            data = json.loads(raw.decode("utf-8", errors="strict"))
            if not isinstance(data, dict):
                raise ValueError("Preferences must contain a JSON object.")
            self.word_wrap = preference_bool(data, "word_wrap", True)
            self.show_search_bar = False
            self.base_font_family = preference_text(data, "font_family", "Sans Serif", limit=256)
            self.base_font_size = max(6, min(72, int(data.get("font_size", 12))))
            self.base_font_weight = preference_text(data, "font_weight", "normal", limit=32)
            self.base_font_slant = preference_text(data, "font_slant", "roman", limit=32)
            self.new_document_line_spacing = max(50, min(400, int(data.get("new_document_line_spacing", 115))))
            saved_alignment = preference_text(data, "new_document_alignment", "left", limit=16).lower()
            if saved_alignment in ("left", "centre", "right", "justify"):
                self.new_document_alignment = saved_alignment
            self.zoom_percent = max(50, min(300, int(data.get("zoom_percent", 100))))
            self.tab_width_spaces = max(1, min(16, int(data.get("tab_width_spaces", 4))))
            # exp5: managed RiqatonyDesk owns the editor canvas preference.
            # Remove the retired embedded canvas key on the next safe rewrite.
            if "editor_canvas_theme" in data:
                migrating_preferences = True
            self.print_header_enabled = preference_bool(data, "print_header_enabled", True)
            old_header = preference_text(data, "print_header_text", "&F")
            self.print_header_left = preference_text(data, "print_header_left", old_header)
            self.print_header_center = preference_text(data, "print_header_center", "")
            self.print_header_right = preference_text(data, "print_header_right", "")
            self.print_footer_enabled = preference_bool(data, "print_footer_enabled", True)
            old_footer = preference_text(data, "print_footer_text", "Page &P of &N")
            self.print_footer_left = preference_text(data, "print_footer_left", "")
            self.print_footer_center = preference_text(data, "print_footer_center", old_footer)
            self.print_footer_right = preference_text(data, "print_footer_right", "")
        except (OSError, UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError):
            migrating_preferences = False
        if migrating_preferences:
            self.save_preferences()

    def save_preferences(self):
        data = {
            "word_wrap": self.word_wrap,
            "show_search_bar": self.show_search_bar,
            "font_family": self.base_font_family,
            "font_size": self.base_font_size,
            "font_weight": self.base_font_weight,
            "font_slant": self.base_font_slant,
            "new_document_line_spacing": int(self.new_document_line_spacing),
            "new_document_alignment": self.new_document_alignment,
            "zoom_percent": self.zoom_percent,
            "tab_width_spaces": self.tab_width_spaces,
            "print_header_enabled": self.print_header_enabled,
            "print_header_left": self.print_header_left,
            "print_header_center": self.print_header_center,
            "print_header_right": self.print_header_right,
            "print_header_text": self.print_header_left,
            "print_footer_enabled": self.print_footer_enabled,
            "print_footer_left": self.print_footer_left,
            "print_footer_center": self.print_footer_center,
            "print_footer_right": self.print_footer_right,
            "print_footer_text": self.print_footer_center,
        }
        temporary = None
        descriptor = None
        try:
            os.makedirs(self.config_directory, mode=0o700, exist_ok=True)
            if os.name != "nt":
                try: os.chmod(self.config_directory, 0o700)
                except OSError: pass
            descriptor, temporary = tempfile.mkstemp(prefix=".ricopad-", suffix=".json.tmp", dir=self.config_directory, text=True)
            os.chmod(temporary, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = None
                json.dump(data, handle, indent=2)
                handle.write("\n")
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, self.config_file); temporary = None
            fsync_directory(self.config_directory)
        except OSError:
            pass
        finally:
            if descriptor is not None:
                try: os.close(descriptor)
                except OSError: pass
            if temporary:
                try: os.remove(temporary)
                except OSError: pass

    def _build_new_document_template_payload(self):
        """Build an interoperable RTF template containing the exact saved defaults."""
        return build_new_document_rtf_payload(
            NewDocumentDefaults(
                font_family=self.base_font_family,
                font_size=self.base_font_size,
                font_weight=self.base_font_weight,
                font_slant=self.base_font_slant,
                line_spacing=self.new_document_line_spacing,
                alignment=self.new_document_alignment,
            )
        )

    def _apply_new_document_defaults_direct(self):
        """Materialise new-document defaults directly in Qt without an RTF re-import."""
        document=self.visual_editor.document()
        document.clear()
        font=QFont()
        try:
            font.setFamilies([self.base_font_family])
        except Exception:
            font.setFamily(self.base_font_family)
        font.setPointSize(int(self.base_font_size))
        font.setBold(self.base_font_weight=="bold")
        font.setItalic(self.base_font_slant=="italic")
        document.setDefaultFont(font)
        document.setDocumentMargin(4.0)
        cursor=QTextCursor(document)
        block=QTextBlockFormat(cursor.blockFormat())
        block.setAlignment(self._new_document_alignment_flag())
        block.setLeftMargin(0.0); block.setRightMargin(0.0); block.setTextIndent(0.0)
        block.setTopMargin(0.0); block.setBottomMargin(0.0)
        block.setLineHeight(float(self.new_document_line_spacing),QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor.setBlockFormat(block)
        plain=QTextCharFormat()
        try:
            plain.setFontFamilies([self.base_font_family])
        except Exception:
            plain.setFontFamily(self.base_font_family)
        plain.setFontPointSize(float(self.base_font_size))
        plain.setFontWeight(QFont.Weight.Bold if self.base_font_weight=="bold" else QFont.Weight.Normal)
        plain.setFontItalic(self.base_font_slant=="italic")
        cursor.setBlockCharFormat(plain)
        self.visual_editor.setTextCursor(cursor)
        self.visual_editor.setCurrentCharFormat(plain)
        self.visual_editor.setCurrentFont(font)
        return True

    def _write_new_document_template(self, payload):
        """Atomically refresh the per-user generated new-document RTF template."""
        os.makedirs(self.config_directory, mode=0o700, exist_ok=True)
        if os.name != "nt":
            try:
                os.chmod(self.config_directory, 0o700)
            except OSError:
                pass
        descriptor = None
        temporary = None
        try:
            descriptor, temporary = tempfile.mkstemp(
                prefix=".new-document-template-", suffix=".rtf.tmp",
                dir=self.config_directory,
            )
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.new_document_template_file)
            temporary = None
            fsync_directory(self.config_directory)
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary:
                try:
                    os.remove(temporary)
                except OSError:
                    pass

    def _ensure_new_document_template(self):
        """Keep the generated RTF template exactly aligned with saved defaults."""
        try:
            expected = self._build_new_document_template_payload()
            current = None
            try:
                current = read_bounded_bytes(
                    self.new_document_template_file,
                    MAX_CONFIG_FILE_SIZE,
                    label="new-document template",
                )
            except OSError:
                pass
            if current != expected:
                self._write_new_document_template(expected)
            return expected
        except (OSError, ValueError, RuntimeError, MemoryError):
            factory = resource_path("templates", "default-document.rtf")
            try:
                return read_bounded_bytes(factory, MAX_CONFIG_FILE_SIZE, label="factory new-document template")
            except OSError:
                return None

    def _apply_new_document_template(self):
        """Apply saved defaults to a brand-new document and refresh its RTF template."""
        self._ensure_new_document_template()
        return self._apply_new_document_defaults_direct()

    def apply_editor_font(self):
        """Compatibility hook: apply the generated template only to a blank untitled document."""
        if self.file_path is not None or max(0, self.visual_editor.document().characterCount() - 1) != 0:
            return
        self._apply_new_document_template()

    def show_new_document_defaults_dialog(self):
        if self.new_document_defaults_dialog is not None:
            self.new_document_defaults_dialog.show()
            self.new_document_defaults_dialog.raise_()
            self.new_document_defaults_dialog.activateWindow()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("New Document Defaults — RiqatonyDesk")
        dialog.setWindowIcon(self.windowIcon())
        dialog.setModal(False)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        form = QFormLayout(dialog)

        family = QFontComboBox(dialog)
        family.setCurrentFont(QFont(self.base_font_family))
        size = QComboBox(dialog)
        size.setEditable(True)
        size.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"])
        size.setEditText(str(self.base_font_size))
        style = QComboBox(dialog)
        for label, weight, slant in (
            ("Normal", "normal", "roman"),
            ("Bold", "bold", "roman"),
            ("Italic", "normal", "italic"),
            ("Bold Italic", "bold", "italic"),
        ):
            style.addItem(label, (weight, slant))
        for index in range(style.count()):
            if style.itemData(index) == (self.base_font_weight, self.base_font_slant):
                style.setCurrentIndex(index)
                break
        spacing = QComboBox(dialog)
        for label, value in (("1.0", 100), ("1.15", 115), ("1.5", 150), ("2.0", 200)):
            spacing.addItem(label, value)
        for index in range(spacing.count()):
            if int(spacing.itemData(index)) == int(self.new_document_line_spacing):
                spacing.setCurrentIndex(index)
                break
        alignment = QComboBox(dialog)
        for label, value in (("Left", "left"), ("Centre", "centre"), ("Right", "right"), ("Justify", "justify")):
            alignment.addItem(label, value)
        for index in range(alignment.count()):
            if alignment.itemData(index) == self.new_document_alignment:
                alignment.setCurrentIndex(index)
                break
        form.addRow("Font family:", family)
        form.addRow("Font size:", size)
        form.addRow("Font style:", style)
        form.addRow("Line spacing:", spacing)
        form.addRow("Alignment:", alignment)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
        form.addRow(buttons)

        def save_defaults():
            try:
                point_size = int(float(size.currentText().strip()))
            except ValueError:
                point_size = self.base_font_size
            point_size = max(6, min(72, point_size))
            weight, slant = style.currentData()
            self.base_font_family = family.currentText().strip() or family.currentFont().family() or "Sans Serif"
            self.base_font_size = point_size
            self.base_font_weight = weight
            self.base_font_slant = slant
            self.new_document_line_spacing = int(spacing.currentData() or 115)
            self.new_document_alignment = str(alignment.currentData() or "left")
            self.save_preferences()
            self._ensure_new_document_template()
            if self.file_path is None and max(0, self.visual_editor.document().characterCount() - 1) == 0:
                self._loading = True
                try:
                    self._apply_new_document_template()
                    self.visual_editor.document().setModified(False)
                    self.content_saved = True
                finally:
                    self._loading = False
                self.apply_editor_canvas_theme(update_action=True)
                self.apply_zoom_preference()
                self.update_formatting_state()
            else:
                self._show_status_message("New-document defaults saved; the open RTF was not reformatted.", 4000)
            dialog.close()

        buttons.accepted.connect(save_defaults)
        buttons.rejected.connect(dialog.close)
        dialog.finished.connect(lambda _result: setattr(self, "new_document_defaults_dialog", None))
        self.new_document_defaults_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def open_font_dialog(self):
        """Compatibility alias retained for older action bindings."""
        self.show_new_document_defaults_dialog()
