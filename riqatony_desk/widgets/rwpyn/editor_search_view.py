#!/usr/bin/env python3
"""Existing editor Find/Replace, zoom, wrap and tab-width methods (x4.0).

These methods are moved unchanged from the original editor host.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QTextCharFormat, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QInputDialog, QTextEdit
from riqatony_desk.widgets.rwpyn.editor_widgets import MAX_DOCUMENT_CHARACTERS

MAX_SEARCH_MATCHES = 10_000


class EditorSearchViewMixin:
    def _logical_char_size(self, char_format):
        displayed = float(char_format.fontPointSize() or 0.0)
        if displayed > 0:
            return displayed
        return float(
            self.visual_editor.document().defaultFont().pointSizeF()
            or self.base_font_size
        )

    @staticmethod
    def _zoom_dots_per_metre(dpi):
        # One inch is exactly 0.0254 metres. Qt's QImage DPI metadata is
        # expressed in integer pixels per metre.
        return max(1, round(float(dpi) / 0.0254))

    def _apply_layout_zoom(self, editor, target_percent, device_attribute):
        """Scale a QTextDocument through layout-device metrics only.

        Unlike rewriting every QTextCharFormat, this does not mutate document
        content, dirty the file, or place display-only changes on the undo stack.
        Explicit font sizes and the editor's base font are laid out against the
        same scaled DPI, so mixed-size rich documents zoom consistently.
        """
        target = max(50, min(300, int(target_percent)))
        layout = editor.document().documentLayout()
        if target == 100:
            layout.setPaintDevice(None)
            device = None
        else:
            device = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
            scale = target / 100.0
            device.setDotsPerMeterX(
                self._zoom_dots_per_metre(editor.logicalDpiX() * scale)
            )
            device.setDotsPerMeterY(
                self._zoom_dots_per_metre(editor.logicalDpiY() * scale)
            )
            layout.setPaintDevice(device)
        # The layout keeps a raw paint-device pointer, so retain the QImage for
        # as long as that document uses it.
        setattr(self, device_attribute, device)
        document = editor.document()
        document.markContentsDirty(0, max(1, document.characterCount()))
        editor.viewport().update()
        return target

    def _apply_visual_document_zoom(self, target_percent):
        self._visual_document_zoom_percent = self._apply_layout_zoom(
            self.visual_editor, target_percent, "_visual_zoom_device"
        )

    def _unzoomed_visual_document(self):
        # The zoom paint device belongs to the live editor layout. A clone gets
        # its own unscaled layout and therefore serialises logical formatting.
        clone = self.visual_editor.document().clone(self)
        clone.documentLayout().setPaintDevice(None)
        return clone

    def toggle_format_bar(self, checked):
        """Compatibility no-op: formatting is permanently part of Home."""
        self.show_format_bar = True

    def apply_zoom_preference(self):
        self._apply_visual_document_zoom(self.zoom_percent)
        self.update_status_counts()

    def set_zoom_percent(self, value, *, persist=True):
        target = max(50, min(300, int(value)))
        if target == self.zoom_percent and self._visual_document_zoom_percent == target:
            return
        self.zoom_percent = target
        self._apply_visual_document_zoom(target)
        self.update_status_counts()
        self.update_formatting_state()
        if persist:
            self.save_preferences()

    def adjust_zoom_from_wheel(self, angle_delta_y):
        if angle_delta_y > 0:
            self.zoom_in()
        elif angle_delta_y < 0:
            self.zoom_out()

    def zoom_in(self):
        self.set_zoom_percent(self.zoom_percent + 10)

    def zoom_out(self):
        self.set_zoom_percent(self.zoom_percent - 10)

    def zoom_reset(self):
        self.set_zoom_percent(100)

    def apply_tab_width(self):
        distance=self.visual_editor.fontMetrics().horizontalAdvance(" ")*self.tab_width_spaces; option=self.visual_editor.document().defaultTextOption(); option.setTabStopDistance(float(distance)); self.visual_editor.document().setDefaultTextOption(option)

    def open_tab_width_dialog(self):
        value, accepted = QInputDialog.getInt(
            self, "Tab Width", "Spaces per tab:", self.tab_width_spaces, 1, 16, 1
        )
        if accepted:
            self.tab_width_spaces = value
            self.apply_tab_width()
            self.save_preferences()

    def toggle_find_panel(self, replace=False):
        """Toggle the requested search field when its own shortcut is pressed again."""
        target = self.replace_entry if replace else self.search_entry
        if self.search_container.isVisible() and (
            target.hasFocus()
            or getattr(self, "_find_panel_requested_replace", None) == bool(replace)
        ):
            self.hide_find_panel()
            return False
        self.show_find_panel(replace)
        return True

    def show_find_panel(self, replace=False):
        """Show the bottom Find/Replace panel and focus the requested row."""
        self._find_panel_requested_replace = bool(replace)
        self.search_container.show()
        self.show_search_bar = True
        selected = self.text_area.textCursor().selectedText().replace("\u2029", "\n")
        if selected and "\n" not in selected:
            self.search_entry.setText(selected)
        self.search_entry.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_entry.selectAll()
        if replace:
            self.replace_entry.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.replace_entry.selectAll()
        self.refresh_search()

    def hide_find_panel(self):
        if not self.search_container.isVisible():
            return
        self._find_panel_requested_replace = None
        self.search_container.hide()
        self.show_search_bar = False
        self.clear_search_results()
        self.text_area.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def show_replace_dialog(self):
        """Compatibility entry point for the shared bottom panel."""
        self.show_find_panel(True)

    def _replace_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.search_case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _selection_matches_replace_query(self, cursor, query):
        if not cursor.hasSelection():
            return False
        selected = cursor.selectedText().replace("\u2029", "\n")
        if self.search_case_checkbox.isChecked():
            return selected == query
        return selected.casefold() == query.casefold()

    def _find_replace_match(self, query, start_cursor=None):
        document = self.text_area.document()
        flags = self._replace_flags()
        start = QTextCursor(start_cursor or self.text_area.textCursor())
        if start.hasSelection():
            start.setPosition(start.selectionEnd())
        match = document.find(query, start, flags)
        if match.isNull():
            match = document.find(query, QTextCursor(document), flags)
        return match

    def replace_next(self):
        """Replace the selected hit, or find-and-replace the next hit."""
        if not self.document_editing_available():
            return False
        query = self.search_entry.text()
        if not query:
            self.search_entry.setFocus()
            return False
        cursor = self.text_area.textCursor()
        if not self._selection_matches_replace_query(cursor, query):
            if not self.find_next():
                return False
            cursor = self.text_area.textCursor()
        if not cursor.hasSelection():
            return False
        replacement = self.replace_entry.text()
        current_length = max(0, self.text_area.document().characterCount() - 1)
        selected_length = abs(cursor.selectionEnd() - cursor.selectionStart())
        if current_length - selected_length + len(replacement) > MAX_DOCUMENT_CHARACTERS:
            self._show_status_message("The replacement would exceed RiqatonyDesk's document safety limit.", 4000)
            return False
        cursor.insertText(replacement)
        self.text_area.setTextCursor(cursor)
        self.refresh_search()
        return True

    def replace_all(self):
        """Replace all matches as one undoable rich-text edit operation."""
        if not self.document_editing_available():
            return 0
        query = self.search_entry.text()
        if not query:
            self.search_entry.setFocus()
            return 0
        replacement = self.replace_entry.text()
        document = self.text_area.document()
        flags = self._replace_flags()

        scan = QTextCursor(document)
        count = 0
        while count <= MAX_SEARCH_MATCHES:
            match = document.find(query, scan, flags)
            if match.isNull():
                break
            count += 1
            scan = QTextCursor(match)
            scan.setPosition(match.selectionEnd())
        if count > MAX_SEARCH_MATCHES:
            self._show_status_message(f"Replace All is limited to {MAX_SEARCH_MATCHES:,} matches.", 4000)
            return 0
        if not count:
            self.refresh_search()
            return 0
        current_length = max(0, document.characterCount() - 1)
        resulting_length = current_length + count * (len(replacement) - len(query))
        if resulting_length > MAX_DOCUMENT_CHARACTERS:
            self._show_status_message("Replace All would exceed RiqatonyDesk's document safety limit.", 4000)
            return 0

        scan = QTextCursor(document)
        edit_cursor = QTextCursor(document)
        replaced = 0
        self._search_refresh_suspended = True
        edit_cursor.beginEditBlock()
        try:
            while replaced < count:
                match = document.find(query, scan, flags)
                if match.isNull():
                    break
                match.insertText(replacement)
                scan = QTextCursor(match)
                replaced += 1
        finally:
            edit_cursor.endEditBlock()
            self._search_refresh_suspended = False
        self._show_status_message(f"Replaced {replaced} occurrence(s).", 4000)
        self.refresh_search()
        return replaced

    def focus_search(self):
        self.show_find_panel(False)

    def active_search_text(self):
        return self.search_entry.text()

    def on_search_text_changed(self, _text):
        self.refresh_search()

    def update_search_counter(self):
        total = len(self.search_matches)
        current = self.current_search_index + 1 if 0 <= self.current_search_index < total else 0
        total_text = f"{total:,}+" if self.search_results_truncated else f"{total:,}"
        self.search_count_label.setText(f"{current:,}/{total_text}")
        self.search_count_label.setToolTip(
            f"Showing the first {MAX_SEARCH_MATCHES:,} matches."
            if self.search_results_truncated else ""
        )
        enabled = total > 0
        self.search_previous_button.setEnabled(enabled)
        self.search_next_button.setEnabled(enabled)

    def find_text_and_refocus(self, _checked=False):
        self.refresh_search()
        self.search_entry.setFocus(Qt.FocusReason.OtherFocusReason)

    def on_document_text_changed(self):
        if self._loading: return
        self.update_status_counts()
        if self._search_refresh_suspended:
            return
        if self.search_container.isVisible():
            self.refresh_search()
        else:
            self.clear_search_results()

    def clear_search_results(self):
        self.search_matches.clear()
        self.search_results_truncated = False
        self.current_search_index = -1
        if hasattr(self, "visual_editor"):
            self.visual_editor.setExtraSelections([])
        if hasattr(self, "search_count_label"):
            self.update_search_counter()

    def refresh_search(self, _value=None):
        """Search using the shared gold-match/real-selection interaction model."""
        if not self.search_container.isVisible():
            return False
        query = self.active_search_text()
        self.search_matches = []
        self.search_results_truncated = False
        self.current_search_index = -1
        self.visual_editor.setExtraSelections([])
        if not query:
            self.update_search_counter()
            return False
        document = self.visual_editor.document()
        cursor = QTextCursor(document)
        flags = self._replace_flags()
        while len(self.search_matches) < MAX_SEARCH_MATCHES:
            found = document.find(query, cursor, flags)
            if found.isNull():
                break
            self.search_matches.append(QTextCursor(found))
            cursor = QTextCursor(found)
            cursor.setPosition(found.selectionEnd())
        if len(self.search_matches) == MAX_SEARCH_MATCHES:
            self.search_results_truncated = not document.find(query, cursor, flags).isNull()
        selections = []
        for match_cursor in self.search_matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = QTextCursor(match_cursor)
            sel.format = QTextCharFormat()
            sel.format.setBackground(QColor("#C9A227"))
            sel.format.setForeground(QColor("#101010"))
            selections.append(sel)
        self.visual_editor.setExtraSelections(selections)
        if self.search_matches:
            self.current_search_index = 0
            active_cursor = QTextCursor(self.search_matches[0])
            self.text_area.setTextCursor(active_cursor)
            self.text_area.ensureCursorVisible()
        self.update_search_counter()
        return bool(self.search_matches)

    def refresh_search_highlights(self):
        return self.refresh_search()

    def find_text(self, show_message=True):
        return self.refresh_search()

    def _ensure_search_matches(self):
        if not self.search_container.isVisible():
            self.show_find_panel(False)
        if not self.active_search_text():
            self.search_entry.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.search_entry.selectAll()
            return False
        if not self.search_matches:
            return self.refresh_search()
        return True

    def _show_search_match(self, index):
        if not self.search_matches:
            return False
        self.current_search_index = index % len(self.search_matches)
        cursor = QTextCursor(self.search_matches[self.current_search_index])
        self.text_area.setTextCursor(cursor)
        self.text_area.ensureCursorVisible()
        self.update_search_counter()
        return True

    def find_next(self):
        if not self._ensure_search_matches():
            return False
        index = 0 if self.current_search_index < 0 else self.current_search_index + 1
        return self._show_search_match(index)

    def find_previous(self):
        if not self._ensure_search_matches():
            return False
        index = len(self.search_matches) - 1 if self.current_search_index < 0 else self.current_search_index - 1
        return self._show_search_match(index)

    def set_word_wrap_mode(self):
        self.visual_editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth if self.word_wrap else QTextEdit.LineWrapMode.NoWrap)
        actual=self.visual_editor.lineWrapMode()!=QTextEdit.LineWrapMode.NoWrap
        self.word_wrap=bool(actual)
        action=getattr(self,"wrap_action",None)
        if action is not None:
            action.blockSignals(True); action.setChecked(self.word_wrap); action.blockSignals(False)

    def toggle_word_wrap(self, checked):
        self.word_wrap = bool(checked)
        self.set_word_wrap_mode()
        self.save_preferences()

    def toggle_search_bar(self, checked=True):
        """Compatibility hook for older callers; Find/Replace is transient UI."""
        if bool(checked):
            self.show_find_panel(False)
        else:
            self.hide_find_panel()
