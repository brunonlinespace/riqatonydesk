#!/usr/bin/env python3
# RiqatonyDesk editor insertion and clipboard implementation — extraction only.
# GPLv3-or-later
# The 39 method bodies originate unchanged from 1.0.0-x2.0.

import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QDateTime, QIODevice, QLocale, QMimeData, QUrl, Qt
from PyQt6.QtGui import QImageReader, QPalette, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment, QTextFormat, QTextImageFormat, QTextTableFormat
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QInputDialog, QLineEdit, QMessageBox, QPushButton, QSpinBox, QToolButton
from riqatony_desk.rich_text_support import is_safe_link_target
from riqatony_desk.widgets.rwpyn.editor_widgets import MAX_DOCUMENT_CHARACTERS, MAX_PASTE_CHARACTERS, RICOPAD_INLINE_RICH_MIME
from riqatony_desk.rtf_codec import RTF_SYNTHETIC_STRUCTURE_BLOCK, RTF_TABLE_AUTOFIT_PROPERTY

MAX_EMBEDDED_IMAGE_SIZE = 12 * 1024 * 1024


MAX_IMAGE_SOURCE_SIZE = 48 * 1024 * 1024


MAX_IMAGE_PIXELS = 40_000_000


def read_bounded_bytes(file_path, limit, *, label="file"):
    """Read at most ``limit`` bytes and fail if the file grows beyond it."""
    with open(file_path, "rb") as handle:
        data = handle.read(int(limit) + 1)
    if len(data) > int(limit):
        raise ValueError(f"The {label} exceeds RiqatonyDesk's safety limit.")
    return data


def host_process_environment():
    """Return a clean environment for launching host desktop applications."""
    environment = os.environ.copy()

    if sys.platform == "win32":
        return environment

    # Portable source runs should inherit the user's environment unchanged.
    if not (
        environment.get("APPDIR")
        or getattr(sys, "frozen", False)
    ):
        return environment

    appdir = environment.get("APPDIR")
    original_library_path = environment.pop(
        "LD_LIBRARY_PATH_ORIG",
        None,
    )
    if original_library_path is None:
        environment.pop("LD_LIBRARY_PATH", None)
    else:
        environment["LD_LIBRARY_PATH"] = original_library_path

    # Do not leak the bundled application's Qt/plugin configuration into a
    # character-map utility supplied by the host operating system.
    for variable in (
        "APPDIR",
        "APPIMAGE",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "QT_QPA_PLATFORMTHEME",
        "QT_STYLE_OVERRIDE",
        "QML_IMPORT_PATH",
        "QML2_IMPORT_PATH",
    ):
        environment.pop(variable, None)

    if appdir and environment.get("PATH"):
        appdir_real = os.path.realpath(appdir)
        clean_path = []
        for entry in environment["PATH"].split(os.pathsep):
            if not entry:
                continue
            try:
                entry_real = os.path.realpath(entry)
                inside_appdir = os.path.commonpath(
                    (appdir_real, entry_real)
                ) == appdir_real
            except (OSError, ValueError):
                inside_appdir = False
            if not inside_appdir:
                clean_path.append(entry)
        environment["PATH"] = os.pathsep.join(clean_path)

    return environment


class EditorInsertionMixin:
    def text_area_undo(self):
        if self.document_editing_available():
            self.text_area.undo()


    def text_area_redo(self):
        if self.document_editing_available():
            self.text_area.redo()


    def insert_symbol(self, symbol, popup=None):
        """Insert one symbol at the caret and return focus to the active editor."""
        if not self.document_editing_available():
            if popup is not None:
                popup.reject()
            return False
        cursor = self.text_area.textCursor()
        cursor.insertText(symbol)
        self.text_area.setTextCursor(cursor)
        if popup is not None:
            popup.accept()
        self.text_area.setFocus()
        self.text_area.ensureCursorVisible()


    def open_more_symbols(self, popup=None):
        """Open the operating system's available character-map utility."""
        if popup is not None:
            popup.accept()

        host_environment = host_process_environment()
        host_path = host_environment.get("PATH")

        if sys.platform == "win32":
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            candidates = (
                (os.path.join(system_root, "System32", "charmap.exe"), []),
                ("charmap.exe", []),
            )
            missing_message = (
                "Windows Character Map could not be found on this system."
            )
        else:
            candidates = (
                ("kcharselect", []),
                ("gucharmap", []),
                ("gnome-characters", []),
                ("charmap", []),
            )
            missing_message = (
                "No supported character-map application was found.\n\n"
                "Install KCharSelect, GNOME Characters, or Gucharmap "
                "to use this option."
            )

        for command, arguments in candidates:
            executable = (
                command
                if os.path.isfile(command)
                else shutil.which(command, path=host_path)
            )
            if executable:
                try:
                    subprocess.Popen(
                        [executable, *arguments],
                        env=host_environment,
                        start_new_session=(sys.platform != "win32"),
                    )
                    self.text_area.setFocus()
                    return
                except OSError:
                    continue

        QMessageBox.information(
            self,
            "More Symbols",
            missing_message,
        )
        self.text_area.setFocus()


    def show_symbols_popup(self):
        """Show the curated symbol grid centred on the active screen."""
        if not self.visual_editing_available():
            return
        popup = QDialog(self)
        popup.setWindowTitle("Symbols")
        popup.setModal(True)

        layout = QGridLayout(popup)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(5)

        symbols = (
            "©", "®", "™", "°", "•", "·", "—", "–",
            "…", "→", "←", "↑", "↓", "✓", "✗", "§",
            "£", "€", "$", "¥", "¢", "±", "×", "÷",
            "≠", "≤", "≥", "≈", "∞", "µ", "¶", "№",
            "★", "☆", "♥", "♦", "♣", "♠", "☐", "☑",
        )

        columns = 8
        for index, symbol in enumerate(symbols):
            button = QToolButton(popup)
            button.setText(symbol)
            button.setToolTip(f"Insert {symbol}")
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(34, 30)
            button.clicked.connect(
                lambda _checked=False, value=symbol: self.insert_symbol(value, popup)
            )
            layout.addWidget(button, index // columns, index % columns)

        separator = QFrame(popup)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(
            separator,
            (len(symbols) + columns - 1) // columns,
            0,
            1,
            columns,
        )

        more_button = QPushButton("More Symbols…", popup)
        more_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        more_button.clicked.connect(
            lambda _checked=False: self.open_more_symbols(popup)
        )
        layout.addWidget(
            more_button,
            (len(symbols) + columns - 1) // columns + 1,
            0,
            1,
            columns,
        )

        popup.adjustSize()
        screen=self.screen() or QApplication.primaryScreen()
        if screen is not None:
            geometry=screen.availableGeometry()
            popup.move(
                geometry.center().x()-popup.width()//2,
                geometry.center().y()-popup.height()//2,
            )
        popup.exec()

        # Always restore editor focus after the centred symbol chooser closes.
        self.text_area.setFocus()


    def insert_link(self, _checked=False):
        if not self.visual_editing_available(): return
        cursor=self.visual_editor.textCursor(); selected=cursor.selectedText().replace("\u2029","\n")
        dialog=QDialog(self); dialog.setWindowTitle("Insert Link — RiqatonyDesk"); form=QFormLayout(dialog); text=QLineEdit(selected,dialog); url=QLineEdit("https://",dialog); form.addRow("Text:",text); form.addRow("Address:",url); buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,parent=dialog); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec()!=QDialog.DialogCode.Accepted: return
        label=text.text().strip() or url.text().strip(); target=url.text().strip()
        if not target or not is_safe_link_target(target): QMessageBox.warning(self,"Link — RiqatonyDesk","Use a safe http, https, mailto or local anchor target."); return
        fmt=QTextCharFormat(); fmt.setAnchor(True); fmt.setAnchorHref(target); fmt.setForeground(self.palette().color(QPalette.ColorRole.Link)); fmt.setFontUnderline(True); cursor.insertText(label,fmt); self.visual_editor.setTextCursor(cursor)


    @staticmethod
    def _image_dimensions_safe(image):
        if image.isNull():
            return False
        width = max(0, int(image.width()))
        height = max(0, int(image.height()))
        return width > 0 and height > 0 and width * height <= MAX_IMAGE_PIXELS


    def _image_data_url(self, image):
        if not self._image_dimensions_safe(image):
            return None
        array = QByteArray()
        buffer = QBuffer(array)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            return None
        try:
            if not image.save(buffer, "PNG"):
                return None
        finally:
            buffer.close()
        data = bytes(array)
        if len(data) > MAX_EMBEDDED_IMAGE_SIZE:
            return None
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


    def _insert_image_resource(self, name, image):
        if image.isNull():
            return False
        resource_url = QUrl(name)
        self.visual_editor.document().addResource(
            QTextDocument.ResourceType.ImageResource, resource_url, image
        )
        image_format = QTextImageFormat()
        image_format.setName(name)
        max_width = max(200, self.visual_editor.viewport().width() * 0.9)
        width = image.width()
        height = image.height()
        if width > max_width:
            ratio = max_width / width
            width *= ratio
            height *= ratio
        image_format.setWidth(width)
        image_format.setHeight(height)
        cursor = self.visual_editor.textCursor()
        cursor.insertImage(image_format)
        self.visual_editor.setTextCursor(cursor)
        return True


    def insert_image_data(self, image):
        if not self.visual_editing_available():
            return False
        name = self._image_data_url(image)
        if not name:
            QMessageBox.warning(
                self, "Image Too Large",
                "The image is too large to decode or embed safely."
            )
            return False
        return self._insert_image_resource(name, image)


    def insert_image_path(self, path):
        if not self.visual_editing_available():
            return False
        try:
            if os.path.getsize(path) > MAX_IMAGE_SOURCE_SIZE:
                raise ValueError("The image file is too large to load safely.")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Image Error", f"Could not inspect the image:\n{exc}")
            return False

        reader = QImageReader(path)
        dimensions = reader.size()
        if (
            dimensions.isValid()
            and dimensions.width() > 0
            and dimensions.height() > 0
            and dimensions.width() * dimensions.height() > MAX_IMAGE_PIXELS
        ):
            QMessageBox.warning(
                self, "Image Too Large",
                "The image dimensions are too large to decode safely."
            )
            return False
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            message = reader.errorString() or "Qt could not decode this image format."
            QMessageBox.warning(self, "Image Error", message)
            return False
        # Keep original PNG/JPEG bytes when possible.  RTF can embed both
        # formats natively, so decoding/re-encoding a photograph on every save
        # only discards metadata/colour-profile information and makes repeated
        # save cycles needlessly non-idempotent.  Other raster formats are
        # normalised once to PNG for portable RTF embedding.
        suffix = Path(path).suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg"}:
            try:
                raw = read_bounded_bytes(path, MAX_EMBEDDED_IMAGE_SIZE, label="image")
            except (OSError, ValueError):
                raw = b""
            if raw:
                mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
                name = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
                return self._insert_image_resource(name, image)
        return self.insert_image_data(image)


    def insert_image(self):
        if not self.visual_editing_available():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;All Files (*)",
        )
        if path:
            self.insert_image_path(path)


    def _visual_anchor_cursor(self):
        """Return a cursor selecting the anchor under/adjacent to the caret."""
        document = self.visual_editor.document()
        cursor = self.visual_editor.textCursor()
        probe = QTextCursor(cursor)
        if cursor.hasSelection():
            fmt = cursor.charFormat()
            return cursor if fmt.isAnchor() and fmt.anchorHref() else None
        position = cursor.position()
        candidate_positions = [position]
        if position > 0:
            candidate_positions.append(position - 1)
        href = ""
        anchor_position = None
        for candidate in candidate_positions:
            probe.setPosition(candidate)
            fmt = probe.charFormat()
            if fmt.isAnchor() and fmt.anchorHref():
                href = fmt.anchorHref()
                anchor_position = candidate
                break
        if not href or anchor_position is None:
            return None
        start = anchor_position
        end = anchor_position
        max_position = max(0, document.characterCount() - 1)
        while start > 0:
            probe.setPosition(start - 1)
            fmt = probe.charFormat()
            if not (fmt.isAnchor() and fmt.anchorHref() == href):
                break
            start -= 1
        while end < max_position:
            probe.setPosition(end)
            fmt = probe.charFormat()
            if not (fmt.isAnchor() and fmt.anchorHref() == href):
                break
            end += 1
        if end <= start:
            return None
        result = QTextCursor(document)
        result.setPosition(start)
        result.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        return result


    def edit_link(self):
        if not self.visual_editing_available():
            return
        cursor = self._visual_anchor_cursor()
        if cursor is None:
            self._show_status_message("Place the caret inside a link to edit it.", 4000)
            return
        current = cursor.charFormat().anchorHref()
        url, accepted = QInputDialog.getText(self, "Edit Link", "Address:", text=current)
        if not accepted:
            return
        url = url.strip()
        if not url or not is_safe_link_target(url):
            QMessageBox.warning(
                self, "Unsupported Link — RiqatonyDesk",
                "Use an HTTP, HTTPS, mailto, document-relative, or #fragment link.",
            )
            return
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setForeground(self.palette().color(self.palette().ColorRole.Link))
        fmt.setFontUnderline(True)
        cursor.mergeCharFormat(fmt)
        self.visual_editor.setTextCursor(cursor)


    def remove_link(self):
        if not self.visual_editing_available():
            return
        cursor = self._visual_anchor_cursor()
        if cursor is None:
            self._show_status_message("Place the caret inside a link to remove it.", 4000)
            return
        fmt = QTextCharFormat()
        fmt.setAnchor(False)
        fmt.setAnchorHref("")
        fmt.setFontUnderline(False)
        try:
            fmt.clearForeground()
        except Exception:
            pass
        cursor.mergeCharFormat(fmt)
        self.visual_editor.setTextCursor(cursor)


    def _current_visual_table(self):
        cursor = self.visual_editor.textCursor()
        table = cursor.currentTable()
        if table is None:
            return None, None
        cell = table.cellAt(cursor)
        return table, cell


    def insert_table_row_above(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.insertRows(cell.row(), 1)


    def insert_table_row_below(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.insertRows(cell.row() + 1, 1)


    def delete_table_row(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.removeRows(cell.row(), 1)


    def insert_table_column_left(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.insertColumns(cell.column(), 1)


    def insert_table_column_right(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.insertColumns(cell.column() + 1, 1)


    def delete_table_column(self):
        table, cell = self._current_visual_table()
        if self.visual_editing_available() and table is not None and cell is not None:
            table.removeColumns(cell.column(), 1)


    def delete_table(self):
        table, _cell = self._current_visual_table()
        if not self.visual_editing_available() or table is None:
            return
        table.removeRows(0, table.rows())


    def insert_horizontal_rule(self, _checked=False):
        if not self.visual_editing_available():
            return
        # A QTextCursor.insertBlock() normally inherits the current block format.
        # If the ruler property is left on that format, the paragraph created
        # after the rule inherits it and Qt draws two rules.  Preserve the
        # surrounding paragraph format explicitly, but clear the ruler property
        # on the before/after format so exactly one dedicated rule block exists.
        cursor = self.visual_editor.textCursor()
        base_format = QTextBlockFormat(cursor.blockFormat())
        base_format.clearProperty(QTextFormat.Property.BlockTrailingHorizontalRulerWidth)
        rule_format = QTextBlockFormat(base_format)
        rule_format.setProperty(QTextFormat.Property.BlockTrailingHorizontalRulerWidth, 100)
        cursor.beginEditBlock()
        cursor.insertBlock(base_format)
        cursor.setBlockFormat(rule_format)
        cursor.insertBlock(base_format)
        cursor.endEditBlock()
        self.visual_editor.setTextCursor(cursor)
        self.visual_editor.setFocus()
        self.visual_editor.ensureCursorVisible()


    def insert_table(self, _checked=False):
        if not self.visual_editing_available(): return
        dialog=QDialog(self); dialog.setWindowTitle("Insert Table — RiqatonyDesk"); form=QFormLayout(dialog); rows=QSpinBox(dialog); rows.setRange(1,1000); rows.setValue(2); columns=QSpinBox(dialog); columns.setRange(1,64); columns.setValue(2); form.addRow("Rows:",rows); form.addRow("Columns:",columns); buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel,parent=dialog); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            if rows.value()*columns.value()>20000: QMessageBox.warning(self,"Table — RiqatonyDesk","Tables are limited to 20,000 cells."); return
            cursor = self.visual_editor.textCursor()
            table_format=QTextTableFormat()
            table_format.setProperty(RTF_TABLE_AUTOFIT_PROPERTY, True)
            table = cursor.insertTable(rows.value(),columns.value(),table_format)
            # QTextDocument keeps structural separator blocks around tables.
            # Mark only those generated empties so RTF export does not invent
            # user paragraphs around a table.
            for block in (table.firstCursorPosition().block().previous(), table.lastCursorPosition().block().next()):
                if block.isValid() and not block.text():
                    block_cursor = QTextCursor(block); fmt = QTextBlockFormat(block.blockFormat()); fmt.setProperty(RTF_SYNTHETIC_STRUCTURE_BLOCK, True); block_cursor.setBlockFormat(fmt)


    def _whole_list_selection_cursor(self, cursor):
        """Expand a whole-item list selection so clipboard HTML retains list semantics."""
        if not cursor.hasSelection():
            return None
        blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks or any(block.textList() is None for block in blocks):
            return None
        first,last=blocks[0],blocks[-1]
        text_start=first.position()
        text_end=last.position()+max(0,last.length()-1)
        if start>text_start or end<text_end:
            return None
        expanded=QTextCursor(self.visual_editor.document())
        expanded.setPosition(text_start)
        document_end=max(0,self.visual_editor.document().characterCount()-1)
        expanded.setPosition(min(document_end,last.position()+last.length()),QTextCursor.MoveMode.KeepAnchor)
        return expanded


    def copy_selection(self):
        """Copy rich selections without moving the live cursor; preserve whole list items."""
        editor=self.visual_editor; cursor=editor.textCursor()
        position=cursor.position(); anchor=cursor.anchor()
        expanded=self._whole_list_selection_cursor(cursor)
        if expanded is not None:
            fragment=QTextDocumentFragment(expanded)
            mime=QMimeData(); mime.setText(fragment.toPlainText()); mime.setHtml(fragment.toHtml())
            QApplication.clipboard().setMimeData(mime)
        else:
            start=cursor.selectionStart(); end=cursor.selectionEnd()
            start_cursor=QTextCursor(editor.document()); start_cursor.setPosition(start)
            end_cursor=QTextCursor(editor.document()); end_cursor.setPosition(max(start,end-1))
            if (
                cursor.hasSelection()
                and start_cursor.block()==end_cursor.block()
                and "\ufffc" not in cursor.selectedText()
            ):
                # Text-only selections within one paragraph need their inline
                # formatting but not Qt's outer HTML paragraph wrapper. Keep
                # embedded objects/images on Qt's native clipboard path so their
                # resources remain available to the paste target.
                fragment=QTextDocumentFragment(cursor)
                mime=QMimeData(); mime.setText(fragment.toPlainText()); mime.setHtml(fragment.toHtml())
                mime.setData(RICOPAD_INLINE_RICH_MIME,QByteArray(b"1"))
                QApplication.clipboard().setMimeData(mime)
            else:
                editor.copy()
        restored=QTextCursor(editor.document()); restored.setPosition(anchor)
        if position!=anchor:
            restored.setPosition(position,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus()


    def cut_selection(self):
        if not self.document_editing_available():
            return
        editor=self.visual_editor; cursor=editor.textCursor()
        if not cursor.hasSelection():
            return
        expanded=self._whole_list_selection_cursor(cursor)
        self.copy_selection()
        target=expanded if expanded is not None else cursor
        target.removeSelectedText()
        editor.setTextCursor(target); editor.setFocus(); self.update_formatting_state()


    def paste_plain_text(self):
        if not self.document_editing_available(): return
        text=QApplication.clipboard().text().replace("\x00","")
        if not text:
            self._show_status_message("Clipboard does not contain text that can be pasted.", 4000)
            return
        cursor=self.visual_editor.textCursor(); current=max(0,self.visual_editor.document().characterCount()-1); selected=abs(cursor.selectionEnd()-cursor.selectionStart())
        if len(text)>MAX_PASTE_CHARACTERS or current-selected+len(text)>MAX_DOCUMENT_CHARACTERS: self._show_status_message("The paste would exceed RiqatonyDesk's document safety limit.",4000); QApplication.beep(); return
        cursor.insertText(text)


    def delete_selection(self):
        if not self.document_editing_available():
            return
        cursor = self.text_area.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deleteChar()
        self.text_area.setTextCursor(cursor)


    def duplicate_current_line(self):
        """Duplicate the rich selection, or the current logical paragraph."""
        if not self.document_editing_available():
            return
        editor=self.visual_editor; cursor=editor.textCursor()
        if cursor.hasSelection():
            start=min(cursor.selectionStart(),cursor.selectionEnd()); end=max(cursor.selectionStart(),cursor.selectionEnd())
            source=QTextCursor(editor.document()); source.setPosition(start); source.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
            fragment=QTextDocumentFragment(source); insertion=QTextCursor(editor.document()); insertion.setPosition(end); insertion.beginEditBlock()
            try: insertion.insertFragment(fragment)
            finally: insertion.endEditBlock()
            insertion.setPosition(end); insertion.setPosition(end+(end-start),QTextCursor.MoveMode.KeepAnchor); editor.setTextCursor(insertion); editor.ensureCursorVisible(); return
        block=cursor.block(); start=block.position(); end=start+max(0,block.length()-1); source=QTextCursor(editor.document()); source.setPosition(start); source.setPosition(end,QTextCursor.MoveMode.KeepAnchor); fragment=QTextDocumentFragment(source); insertion=QTextCursor(editor.document()); insertion.setPosition(end); insertion.beginEditBlock()
        try: insertion.insertBlock(block.blockFormat(),block.charFormat()); insertion.insertFragment(fragment)
        finally: insertion.endEditBlock()
        editor.setTextCursor(insertion); editor.ensureCursorVisible()


    def delete_current_line(self):
        """Delete the current logical line/block as one undoable operation.

        For a non-empty block, BlockUnderCursor yields a real selection and
        removing that selection already removes the block cleanly.  Performing
        an additional character deletion afterwards corrupts a neighbour: a
        middle block can merge the surrounding paragraphs, while a final block
        can lose the preceding character.

        An empty block has no selected text, so only that case needs an
        explicit paragraph-separator deletion.  A sole empty document block is
        left in place because QTextDocument always requires one block.
        """
        if not self.document_editing_available():
            return
        cursor = self.text_area.textCursor()
        block = cursor.block()
        is_last = not block.next().isValid()
        has_previous = block.previous().isValid()
        cursor.beginEditBlock()
        try:
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            if cursor.hasSelection():
                cursor.removeSelectedText()
            elif is_last and has_previous:
                cursor.deletePreviousChar()
            elif not is_last:
                cursor.deleteChar()
        finally:
            cursor.endEditBlock()
        self.text_area.setTextCursor(cursor)


    def formatted_system_date(self):
        """Return the current date using the desktop's locale."""
        return QLocale.system().toString(
            QDateTime.currentDateTime().date(),
            QLocale.FormatType.ShortFormat,
        )


    def formatted_system_time(self):
        """Return the current time using the desktop's locale."""
        return QLocale.system().toString(
            QDateTime.currentDateTime().time(),
            QLocale.FormatType.ShortFormat,
        )


    def formatted_system_timestamp(self):
        """Return the current locale-aware date and time."""
        return QLocale.system().toString(
            QDateTime.currentDateTime(),
            QLocale.FormatType.ShortFormat,
        )


    def insert_text_at_cursor(self, text):
        """Insert text at the caret and return focus to the editor."""
        if not self.document_editing_available():
            return False
        cursor = self.text_area.textCursor()
        cursor.insertText(text)
        self.text_area.setTextCursor(cursor)
        self.text_area.setFocus()
        self.text_area.ensureCursorVisible()


    def insert_time_date(self):
        """Insert the current system-local date and time at the caret (F5)."""
        self.insert_text_at_cursor(self.formatted_system_timestamp())


    def insert_date(self):
        """Insert the current system-local date at the caret (Ctrl+;)."""
        self.insert_text_at_cursor(self.formatted_system_date())


    def insert_time(self):
        """Insert the current system-local time at the caret (Ctrl+:)."""
        self.insert_text_at_cursor(self.formatted_system_time())


