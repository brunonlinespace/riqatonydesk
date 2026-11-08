"""Unchanged embedded rich-text editor widgets extracted for x1.0."""
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import (QImage, QPixmap, QTextBlockFormat, QTextCharFormat,
    QTextCursor, QTextDocument, QTextDocumentFragment)
from PyQt6.QtWidgets import QApplication, QTextEdit

from riqatony_desk.rich_text_support import sanitise_qt_html

MAX_PASTE_CHARACTERS = 5_000_000
MAX_DOCUMENT_CHARACTERS = 25_000_000
MAX_CLIPBOARD_HTML_CHARACTERS = 10_000_000
RICOPAD_INLINE_RICH_MIME = "application/x-ricopad-inline-richtext"


class SafeTextDocument(QTextDocument):
    """QTextDocument that never auto-loads external document resources."""

    def loadResource(self, resource_type, name):
        if resource_type in (
            QTextDocument.ResourceType.ImageResource,
            QTextDocument.ResourceType.StyleSheetResource,
        ):
            url = QUrl(name)
            if url.scheme().lower() != "data":
                return None
        return super().loadResource(resource_type, name)


class RichTextEdit(QTextEdit):
    """Visual editor with bounded clipboard/drop handling and safe resources."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocument(SafeTextDocument(self))
        self.setAcceptDrops(False)
        # Keep ordinary rich-text/text drag interactions on the editor viewport,
        # but local-file drops are rejected by the event handlers below.
        self.viewport().setAcceptDrops(True)
        self.setUndoRedoEnabled(True)
        self._pending_full_paste = None
        self._full_paste_generation = 0

    def _reject_paste(self, message):
        owner = self.parentWidget()
        if owner is not None and hasattr(owner, "_show_status_message"):
            owner._show_status_message(message, 4000)
        QApplication.beep()

    def _resulting_character_count(self, inserted_text_length):
        cursor = self.textCursor()
        current = max(0, self.document().characterCount() - 1)
        selected = abs(cursor.selectionEnd() - cursor.selectionStart())
        return current - selected + max(0, int(inserted_text_length))

    def _selection_is_full_document(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        document_length = max(0, self.document().characterCount() - 1)
        return min(cursor.selectionStart(), cursor.selectionEnd()) == 0 and max(cursor.selectionStart(), cursor.selectionEnd()) >= document_length

    def _schedule_full_paste(self, kind, payload):
        self._full_paste_generation += 1
        generation = self._full_paste_generation
        self._pending_full_paste = (str(kind), str(payload))
        QTimer.singleShot(0, lambda: self._apply_pending_full_paste(generation))

    def _apply_pending_full_paste(self, generation):
        if generation != self._full_paste_generation or self.isReadOnly():
            return
        pending = self._pending_full_paste
        self._pending_full_paste = None
        if not pending:
            return
        kind, payload = pending
        if kind == "html":
            self.setHtml(payload)
        else:
            self.setPlainText(payload)
        self.document().setModified(True)
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.setFocus()

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.ignore()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.ignore()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.ignore()
            return
        super().dropEvent(event)

    def _insert_inline_rich_html(self, safe_html):
        """Insert one RiqatonyDesk-copied paragraph selection without its HTML block wrapper."""
        fragment = QTextDocumentFragment.fromHtml(safe_html)
        temporary = QTextDocument()
        temporary_cursor = QTextCursor(temporary)
        temporary_cursor.insertFragment(fragment)
        block = temporary.begin()
        target = self.textCursor()
        target.beginEditBlock()
        iterator = block.begin()
        while not iterator.atEnd():
            source_fragment = iterator.fragment()
            if source_fragment.isValid():
                fmt = source_fragment.charFormat()
                if fmt.isImageFormat():
                    target.insertImage(fmt.toImageFormat())
                else:
                    target.insertText(source_fragment.text().replace("\u2029", ""), fmt)
            iterator += 1
        target.endEditBlock()
        self.setTextCursor(target)

    def insertFromMimeData(self, source):
        if self.isReadOnly():
            window = self.window()
            if hasattr(window, "explain_view_only_block"):
                window.explain_view_only_block()
            return
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QPixmap):
                image = image.toImage()
            if isinstance(image, QImage) and not image.isNull():
                window = self.window()
                if hasattr(window, "insert_image_data"):
                    window.insert_image_data(image)
                    return
        if source.hasHtml():
            try:
                raw_html = source.html()
            except Exception as exc:
                self._reject_paste(f"Clipboard HTML could not be read: {exc}")
                return
            if len(raw_html) > MAX_CLIPBOARD_HTML_CHARACTERS:
                self._reject_paste("Clipboard rich text is too large to paste safely.")
                return
            safe_html = sanitise_qt_html(raw_html)
            fragment = QTextDocumentFragment.fromHtml(safe_html)
            plain_length = len(fragment.toPlainText().replace("\x00", ""))
            if plain_length > MAX_PASTE_CHARACTERS or self._resulting_character_count(plain_length) > MAX_DOCUMENT_CHARACTERS:
                self._reject_paste("The rich-text paste would exceed RiqatonyDesk's document safety limit.")
                return
            if self._selection_is_full_document():
                self._schedule_full_paste("html", safe_html)
                return
            if source.hasFormat(RICOPAD_INLINE_RICH_MIME):
                self._insert_inline_rich_html(safe_html)
                return
            self.textCursor().insertFragment(fragment)
            return
        if source.hasText():
            try:
                text = source.text().replace("\x00", "")
            except Exception as exc:
                self._reject_paste(f"Clipboard text could not be read: {exc}")
                return
            if len(text) > MAX_PASTE_CHARACTERS or self._resulting_character_count(len(text)) > MAX_DOCUMENT_CHARACTERS:
                self._reject_paste("The paste would exceed RiqatonyDesk's document safety limit.")
                return
            if self._selection_is_full_document():
                self._schedule_full_paste("text", text)
                return
            self.textCursor().insertText(text)
            return
        self._reject_paste("Clipboard content could not be inserted safely.")

    def keyPressEvent(self, event):
        # WordPad-style visual shortcut: type three underscores and press Enter.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            block = cursor.block()
            if (
                not self.isReadOnly()
                and not cursor.hasSelection()
                and cursor.positionInBlock() == len(block.text())
                and block.text().strip() == "___"
            ):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
                window = self.window()
                if hasattr(window, "insert_horizontal_rule"):
                    window.insert_horizontal_rule()
                    event.accept()
                    return
        was_return=(event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        previous_block=self.textCursor().block() if was_return else None
        previous_heading=(previous_block.headingLevel() if previous_block is not None and hasattr(previous_block,"headingLevel") else 0)
        previous_line_height=0.0
        previous_line_type=None
        previous_was_list=False
        previous_had_text=False
        if previous_block is not None:
            previous_format=previous_block.blockFormat()
            previous_was_list=previous_block.textList() is not None
            previous_had_text=bool(previous_block.text())
            try:
                previous_line_height=float(previous_format.lineHeight() or 0.0)
                previous_line_type=int(previous_format.lineHeightType())
            except Exception:
                pass
        super().keyPressEvent(event)
        if was_return and not self.isReadOnly() and previous_line_height>0 and previous_line_type is not None:
            # Qt normally inherits paragraph spacing on Return.  Only repair it
            # when inheritance actually changed.  In particular, do not rewrite
            # every newly-created *empty* body paragraph: repeated Return on a
            # clean document must stay native QTextEdit behaviour.  The repair
            # remains available for populated paragraphs and list transitions,
            # the cases that originally exposed spacing loss.
            cursor=self.textCursor(); current_format=cursor.blockFormat()
            try:
                current_line_height=float(current_format.lineHeight() or 0.0)
                current_line_type=int(current_format.lineHeightType())
            except Exception:
                current_line_height=0.0; current_line_type=None
            spacing_changed=(
                abs(current_line_height-previous_line_height)>0.01
                or current_line_type!=previous_line_type
            )
            if spacing_changed and (previous_had_text or previous_was_list):
                spacing=QTextBlockFormat()
                spacing.setLineHeight(previous_line_height, previous_line_type)
                cursor.mergeBlockFormat(spacing); self.setTextCursor(cursor)
        if was_return and previous_heading>0 and not self.isReadOnly():
            # Heading paragraphs end in Normal, WordPad-style. Qt can clear the
            # heading level while still inheriting the heading's block character
            # baseline; explicitly restore the document baseline so a second
            # Enter cannot resurrect 24 pt heading text.
            cursor=self.textCursor(); block_format=QTextBlockFormat(cursor.blockFormat())
            if hasattr(block_format,"setHeadingLevel"):
                block_format.setHeadingLevel(0)
            cursor.setBlockFormat(block_format)
            font=self.document().defaultFont(); plain=QTextCharFormat()
            try:
                families=font.families()
                if families: plain.setFontFamilies(families)
                elif font.family(): plain.setFontFamily(font.family())
            except Exception:
                if font.family(): plain.setFontFamily(font.family())
            if font.pointSizeF()>0: plain.setFontPointSize(font.pointSizeF())
            plain.setFontWeight(font.weight()); plain.setFontItalic(font.italic()); plain.setFontUnderline(font.underline()); plain.setFontStrikeOut(font.strikeOut())
            cursor.setBlockCharFormat(plain); self.setCurrentCharFormat(plain); self.setTextCursor(cursor)
        if was_return and not self.isReadOnly():
            # Block formatting can trigger another layout after QTextEdit has already
            # scrolled for Enter. Keep trailing empty paragraphs/caret visible.
            self.ensureCursorVisible()
            QTimer.singleShot(0, self.ensureCursorVisible)

    def mouseReleaseEvent(self, event):
        href = ""
        try:
            href = self.anchorAt(event.position().toPoint())
        except Exception:
            href = ""
        follow = bool(href) and (
            self.isReadOnly()
            or bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        )
        if follow:
            window = self.window()
            if hasattr(window, "open_document_link") and window.open_document_link(href):
                event.accept()
                self.setFocus()
                return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        window = self.window()
        if (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and hasattr(window, "adjust_zoom_from_wheel")
        ):
            window.adjust_zoom_from_wheel(event.angleDelta().y())
            event.accept()
            return
        super().wheelEvent(event)
