#!/usr/bin/env python3
# RicopadEditorWidget editor formatting implementation — extraction only.
# GPLv3-or-later
# The original method bodies are copied without modification from 1.0.0-x1.0.

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QKeySequence, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextFormat, QTextListFormat
from PyQt6.QtWidgets import QColorDialog, QComboBox, QDialog, QDialogButtonBox, QFontDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout
from riqatony_desk.rtf_codec import _qt_brush_colour, RTF_AUTOMATIC_CONTRAST_PROPERTY

FONT_SIZE_STEPS = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20,
    22, 24, 26, 28, 32, 36, 40, 44, 48, 54, 60, 66, 72, 80, 88,
    96, 108, 120, 144, 168, 192, 216, 240, 288, 320, 384, 448, 512,
)


class EditorFormattingMixin:
    def merge_character_format(self, char_format):
        """Apply character formatting to selection, current word, or future typing.

        WordPad-style editing should not force a precise drag-selection for a
        single word.  When there is no selection and the caret touches a word,
        format that word while leaving the caret where it was.  In whitespace
        or an empty paragraph, change only the typing format for future text.
        """
        if not self.visual_editing_available():
            return
        editor=self.visual_editor; cursor=editor.textCursor()
        original_position=cursor.position(); original_anchor=cursor.anchor()
        target=QTextCursor(cursor)
        if not target.hasSelection():
            word=self._word_cursor_at_caret(cursor)
            if word is not None:
                target=word
        if target.hasSelection():
            target.mergeCharFormat(char_format)
            restored=QTextCursor(editor.document()); restored.setPosition(original_anchor)
            if original_position!=original_anchor:
                restored.setPosition(original_position,QTextCursor.MoveMode.KeepAnchor)
            editor.setTextCursor(restored)
        else:
            editor.mergeCurrentCharFormat(char_format)
        editor.setFocus(); self.update_formatting_state()

    def _effective_character_format(self):
        """Return the format that a no-selection character command will toggle."""
        editor=self.visual_editor; cursor=editor.textCursor()
        if not cursor.hasSelection():
            word=self._word_cursor_at_caret(cursor)
            if word is not None:
                return word.charFormat()
        return cursor.charFormat() if cursor.hasSelection() else editor.currentCharFormat()

    def _reset_font_face_display(self, _text=""):
        """Keep the collapsed font-family field pinned to the start of its name."""
        line_edit = self.font_combo.lineEdit() if hasattr(self, "font_combo") else None
        if line_edit is None:
            return
        line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        line_edit.deselect()
        line_edit.setCursorPosition(0)

    def set_selected_font(self, font):
        if not self.visual_editing_available(False):
            return
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self.merge_character_format(fmt)

    def set_selected_font_size(self, value):
        if not self.visual_editing_available(False):
            return
        try:
            size = float(str(value).strip())
        except ValueError:
            return
        if not 1 <= size <= 512:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.merge_character_format(fmt)

    def apply_font_weight_from_combo(self, _index):
        if self.font_weight_combo.signalsBlocked():
            return
        weight = self.font_weight_combo.currentData()
        if weight is None:
            return
        self.set_selected_font_weight(int(weight))

    def set_selected_font_weight(self, weight):
        if not self.visual_editing_available(False):
            return
        try:
            value = max(1, min(1000, int(weight)))
        except (TypeError, ValueError):
            return
        fmt = QTextCharFormat()
        fmt.setFontWeight(value)
        self.merge_character_format(fmt)

    @staticmethod
    def _adjacent_font_size(current_size, direction):
        """Return the next standard point size in the requested direction."""
        current = max(float(FONT_SIZE_STEPS[0]), min(float(FONT_SIZE_STEPS[-1]), float(current_size)))
        if direction > 0:
            return next(
                (size for size in FONT_SIZE_STEPS if size > current + 0.01),
                FONT_SIZE_STEPS[-1],
            )
        return next(
            (size for size in reversed(FONT_SIZE_STEPS) if size < current - 0.01),
            FONT_SIZE_STEPS[0],
        )

    def _word_cursor_at_caret(self, cursor):
        """Return WordUnderCursor when the caret touches real word text."""
        probe=QTextCursor(cursor)
        probe.select(QTextCursor.SelectionType.WordUnderCursor)
        if probe.hasSelection() and probe.selectedText().strip():
            return probe
        if cursor.position()>cursor.block().position():
            probe=QTextCursor(cursor); probe.movePosition(QTextCursor.MoveOperation.Left); probe.select(QTextCursor.SelectionType.WordUnderCursor)
            if probe.hasSelection() and probe.selectedText().strip():
                return probe
        return None

    def _step_selected_font_size(self, direction):
        """Step selected runs, or the word under the caret when there is one."""
        if not self.visual_editing_available():
            return
        editor=self.visual_editor; cursor=editor.textCursor()
        if not cursor.hasSelection():
            word=self._word_cursor_at_caret(cursor)
            if word is not None:
                current=self._logical_char_size(word.charFormat())
                target=self._adjacent_font_size(current,direction)
                fmt=QTextCharFormat(); fmt.setFontPointSize(float(target)); word.mergeCharFormat(fmt)
                editor.setTextCursor(cursor); editor.setFocus(); self.update_formatting_state(); return
            current=self._logical_char_size(editor.currentCharFormat())
            target=self._adjacent_font_size(current,direction)
            fmt=QTextCharFormat(); fmt.setFontPointSize(float(target)); editor.mergeCurrentCharFormat(fmt)
            self.font_size_combo.blockSignals(True); self.font_size_combo.setEditText(f"{target:g}"); self.font_size_combo.blockSignals(False)
            editor.setFocus(); self.update_formatting_state(); return
        start_pos=min(cursor.selectionStart(),cursor.selectionEnd()); end_pos=max(cursor.selectionStart(),cursor.selectionEnd())
        document=editor.document(); probe=QTextCursor(document); runs=[]; pos=start_pos
        while pos<end_pos:
            probe.setPosition(pos)
            fmt=probe.charFormat(); size=self._logical_char_size(fmt)
            # Grow a run while the effective point size is the same.
            run_end=pos+1
            while run_end<end_pos:
                q=QTextCursor(document); q.setPosition(run_end)
                if abs(self._logical_char_size(q.charFormat())-size)>0.01:
                    break
                run_end+=1
            runs.append((pos,run_end,self._adjacent_font_size(size,direction))); pos=run_end
        cursor.beginEditBlock()
        try:
            for run_start,run_end,target in runs:
                run=QTextCursor(document); run.setPosition(run_start); run.setPosition(run_end,QTextCursor.MoveMode.KeepAnchor)
                fmt=QTextCharFormat(); fmt.setFontPointSize(float(target)); run.mergeCharFormat(fmt)
        finally:
            cursor.endEditBlock()
        editor.setTextCursor(cursor); self.update_formatting_state()

    def increase_font_size(self, _checked=False):
        self._step_selected_font_size(1)

    def decrease_font_size(self, _checked=False):
        self._step_selected_font_size(-1)

    def choose_selection_font(self):
        if not self.visual_editing_available():
            return
        effective=self._effective_character_format()
        current = effective.font()
        current_size = self._logical_char_size(effective)
        current.setPointSizeF(current_size)
        selected, accepted = QFontDialog.getFont(current, self, "Font")
        if not accepted:
            return
        logical_size = selected.pointSizeF()
        if logical_size <= 0:
            logical_size = current_size
        fmt = QTextCharFormat()
        fmt.setFontFamily(selected.family())
        fmt.setFontWeight(selected.weight())
        fmt.setFontItalic(selected.italic())
        fmt.setFontUnderline(selected.underline())
        fmt.setFontStrikeOut(selected.strikeOut())
        fmt.setFontPointSize(logical_size)
        self.merge_character_format(fmt)

    def toggle_bold(self, _checked=False):
        if not self.visual_editing_available(): return
        current=self._effective_character_format().fontWeight(); fmt=QTextCharFormat(); fmt.setFontWeight(QFont.Weight.Normal if int(current)>=int(QFont.Weight.Bold) else QFont.Weight.Bold); self.merge_character_format(fmt)

    def toggle_italic(self, _checked=False):
        if not self.visual_editing_available(): return
        fmt=QTextCharFormat(); fmt.setFontItalic(not self._effective_character_format().fontItalic()); self.merge_character_format(fmt)

    def toggle_underline(self, _checked=False):
        if not self.visual_editing_available():
            return
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self._effective_character_format().fontUnderline())
        self.merge_character_format(fmt)

    def toggle_strikethrough(self, _checked=False):
        if not self.visual_editing_available(): return
        fmt=QTextCharFormat(); fmt.setFontStrikeOut(not self._effective_character_format().fontStrikeOut()); self.merge_character_format(fmt)

    def _toggle_vertical_alignment(self, alignment):
        """Toggle superscript or subscript without changing the logical font size."""
        if not self.visual_editing_available():
            return
        current = self._effective_character_format().verticalAlignment()
        target = (
            QTextCharFormat.VerticalAlignment.AlignNormal
            if current == alignment
            else alignment
        )
        fmt = QTextCharFormat()
        fmt.setVerticalAlignment(target)
        self.merge_character_format(fmt)

    def toggle_superscript(self, _checked=False):
        self._toggle_vertical_alignment(
            QTextCharFormat.VerticalAlignment.AlignSuperScript
        )

    def toggle_subscript(self, _checked=False):
        self._toggle_vertical_alignment(
            QTextCharFormat.VerticalAlignment.AlignSubScript
        )

    @staticmethod
    def _highlight_contrast_colour(colour):
        luminance=(299*colour.red()+587*colour.green()+114*colour.blue())/1000.0
        return QColor(Qt.GlobalColor.black if luminance>=145 else Qt.GlobalColor.white)

    @staticmethod
    def _character_format_at_position(document, position):
        """Return the format of the character at ``position`` exactly.

        QTextCursor.charFormat() on an unselected cursor describes the character
        immediately to the left at ordinary in-block positions. Highlight
        processing needs the character being changed, especially at the first
        character of a selection, so select exactly that one character before
        reading its format.
        """
        probe=QTextCursor(document); probe.setPosition(position)
        if position < document.characterCount()-1:
            probe.setPosition(position+1,QTextCursor.MoveMode.KeepAnchor)
        return probe.charFormat()

    def _apply_highlight(self, colour=None, clear=False):
        editor=self.visual_editor; original=editor.textCursor(); cursor=QTextCursor(original); document=editor.document()
        if not cursor.hasSelection():
            word=self._word_cursor_at_caret(cursor)
            if word is not None:
                cursor=word
        start=min(cursor.selectionStart(),cursor.selectionEnd()); end=max(cursor.selectionStart(),cursor.selectionEnd())
        ranges=[]
        if cursor.hasSelection():
            position=start
            while position<end:
                current=QTextCharFormat(self._character_format_at_position(document,position))
                run_end=position+1
                while run_end<end:
                    qfmt=self._character_format_at_position(document,run_end)
                    if qfmt!=current:
                        break
                    run_end+=1
                ranges.append((position,run_end,current)); position=run_end
        else:
            ranges=[(None,None,QTextCharFormat(editor.currentCharFormat()))]
        original.beginEditBlock()
        try:
            for run_start,run_end,current in ranges:
                replacement=QTextCharFormat(current)
                tagged=bool(current.property(RTF_AUTOMATIC_CONTRAST_PROPERTY))
                if clear:
                    replacement.clearProperty(QTextFormat.Property.BackgroundBrush)
                    if tagged:
                        replacement.clearProperty(QTextFormat.Property.ForegroundBrush)
                        replacement.clearProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY)
                else:
                    explicit=_qt_brush_colour(current.foreground()) is not None and not tagged
                    replacement.setBackground(colour)
                    if not explicit:
                        replacement.setForeground(self._highlight_contrast_colour(colour))
                        replacement.setProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY,True)
                if run_start is None:
                    editor.setCurrentCharFormat(replacement)
                else:
                    run=QTextCursor(document); run.setPosition(run_start); run.setPosition(run_end,QTextCursor.MoveMode.KeepAnchor); run.setCharFormat(replacement)
        finally:
            original.endEditBlock()
        editor.setTextCursor(original); editor.setFocus(); self.update_formatting_state()

    def choose_text_colour(self, _checked=False):
        if not self.visual_editing_available(): return
        current=_qt_brush_colour(self._effective_character_format().foreground()) or QColor(Qt.GlobalColor.black)
        colour=QColorDialog.getColor(current,self,"Text Colour")
        if colour.isValid():
            fmt=QTextCharFormat(); fmt.setForeground(colour); fmt.setProperty(RTF_AUTOMATIC_CONTRAST_PROPERTY,False); self.merge_character_format(fmt)

    def choose_highlight_colour(self, _checked=False):
        if not self.visual_editing_available():
            return
        dialog=QDialog(self); dialog.setWindowTitle("Highlight Colour — RiqatonyDesk")
        outer=QVBoxLayout(dialog)
        label=QLabel("Standard highlight colours",dialog); outer.addWidget(label)
        grid=QGridLayout(); outer.addLayout(grid)
        palette=(
            ("Yellow", "#fff200", "Y"), ("Green", "#92d050", "G"),
            ("Blue", "#5b9bd5", "B"), ("Cyan", "#66ffff", "C"),
            ("Pink", "#ff99cc", "P"), ("Red", "#ff6666", "R"),
            ("Orange", "#f4b183", "O"), ("Noir", "#000000", "N"),
        )
        chosen={"colour":None,"clear":False}
        def choose(hex_colour):
            chosen["colour"]=QColor(hex_colour); dialog.accept()
        def clear(_checked=False):
            chosen["clear"]=True; dialog.accept()
        for index,(name,hex_colour,key) in enumerate(palette):
            button=QPushButton(f"{name} ({key})",dialog); button.setMinimumWidth(92)
            colour=QColor(hex_colour); text="#ffffff" if colour.lightness()<110 else "#000000"
            button.setStyleSheet(f"QPushButton {{ background:{hex_colour}; color:{text}; padding:6px; }}")
            button.clicked.connect(lambda _checked=False,value=hex_colour:choose(value))
            shortcut=QAction(dialog); shortcut.setShortcut(QKeySequence(key)); shortcut.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut); shortcut.triggered.connect(lambda _checked=False,value=hex_colour:choose(value)); dialog.addAction(shortcut)
            grid.addWidget(button,index//4,index%4)
        row=QHBoxLayout(); outer.addLayout(row)
        clear_button=QPushButton("Clear Highlight (Backspace)",dialog); clear_button.clicked.connect(clear); row.addWidget(clear_button)
        clear_shortcut=QAction(dialog); clear_shortcut.setShortcut(QKeySequence("Backspace")); clear_shortcut.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut); clear_shortcut.triggered.connect(clear); dialog.addAction(clear_shortcut)
        custom_button=QPushButton("Custom…",dialog)
        def custom():
            current=_qt_brush_colour(self.visual_editor.currentCharFormat().background()) or QColor(Qt.GlobalColor.yellow)
            colour=QColorDialog.getColor(current,self,"Custom Highlight Colour")
            if colour.isValid(): chosen["colour"]=colour; dialog.accept()
        custom_button.clicked.connect(custom); row.addWidget(custom_button); row.addStretch(1)
        cancel=QPushButton("Cancel",dialog); cancel.clicked.connect(dialog.reject); row.addWidget(cancel)
        if dialog.exec()!=QDialog.DialogCode.Accepted:
            return
        if chosen["clear"]:
            self.clear_highlight(); return
        colour=chosen["colour"]
        if isinstance(colour,QColor) and colour.isValid():
            self._apply_highlight(colour=colour)

    def clear_highlight(self, _checked=False):
        if not self.visual_editing_available():
            return
        self._apply_highlight(clear=True)

    def _blocks_touched_by_cursor(self, cursor):
        """Return each QTextBlock touched by a selection exactly once."""
        document=self.visual_editor.document()
        if cursor.hasSelection():
            start=min(cursor.selectionStart(),cursor.selectionEnd())
            end=max(cursor.selectionStart(),cursor.selectionEnd())
            probe_end=max(start,end-1)
        else:
            start=cursor.position(); end=start; probe_end=start
        block=document.findBlock(start)
        last=document.findBlock(probe_end)
        blocks=[]
        while block.isValid():
            blocks.append(block)
            if block==last:
                break
            block=block.next()
        return blocks,start,end

    def _document_plain_char_format(self):
        """Return the open document's plain-text baseline, never an app preference."""
        font=self.visual_editor.document().defaultFont()
        plain=QTextCharFormat()
        try:
            families=font.families()
            if families:
                plain.setFontFamilies(families)
            elif font.family():
                plain.setFontFamily(font.family())
        except Exception:
            if font.family():
                plain.setFontFamily(font.family())
        size=float(font.pointSizeF() or 0.0)
        if size>0:
            plain.setFontPointSize(size)
        plain.setFontWeight(font.weight())
        plain.setFontItalic(font.italic())
        plain.setFontUnderline(font.underline())
        plain.setFontStrikeOut(font.strikeOut())
        try:
            plain.setFontOverline(False)
        except Exception:
            pass
        plain.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        plain.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        return plain

    def clear_formatting(self, _checked=False):
        """Reset selected text/paragraph formatting while preserving document objects.

        Links keep their targets; images/inline objects and table structure are not
        destroyed. Paragraph alignment, indents, tabs, spacing, line spacing,
        heading state and list membership are reset to the open document's plain
        baseline. The application New Document Defaults preference is never imposed
        on an existing RTF.
        """
        if not self.visual_editing_available(): return
        editor=self.visual_editor; cursor=editor.textCursor(); blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks: return
        if not cursor.hasSelection():
            start=blocks[0].position(); end=start+max(0,blocks[0].length()-1)
        document=editor.document(); cursor.beginEditBlock()
        try:
            # Clear direct character formatting only over the selected text. An
            # empty QTextCharFormat inherits the document's own RTF default.
            for block in blocks:
                iterator=block.begin()
                while not iterator.atEnd():
                    fragment=iterator.fragment(); iterator+=1
                    if not fragment.isValid(): continue
                    frag_start=fragment.position(); frag_end=frag_start+fragment.length()
                    sel_start=max(start,frag_start); sel_end=min(end,frag_end)
                    if sel_start>=sel_end: continue
                    original=fragment.charFormat()
                    try:
                        if original.isImageFormat() or int(original.objectType())!=0:
                            continue
                    except (TypeError,ValueError):
                        if original.isImageFormat(): continue
                    plain=self._document_plain_char_format()
                    if original.isAnchor():
                        plain.setAnchor(True); plain.setAnchorHref(original.anchorHref()); plain.setAnchorNames(original.anchorNames())
                    run_cursor=QTextCursor(document); run_cursor.setPosition(sel_start); run_cursor.setPosition(sel_end,QTextCursor.MoveMode.KeepAnchor); run_cursor.setCharFormat(plain)
            # Paragraph formatting is block-scoped, so every touched paragraph
            # is reset even when the user selected only part of its text.
            for block in blocks:
                old=block.blockFormat()
                try:
                    if old.property(QTextFormat.Property.BlockTrailingHorizontalRulerWidth):
                        continue
                except Exception:
                    pass
                block_cursor=QTextCursor(block)
                plain_block=QTextBlockFormat()
                try:
                    plain_block.setPageBreakPolicy(old.pageBreakPolicy())
                except Exception:
                    pass
                block_cursor.setBlockFormat(plain_block)
                block_cursor.setBlockCharFormat(self._document_plain_char_format())
        finally:
            cursor.endEditBlock()
        restored=QTextCursor(document); restored.setPosition(start)
        if end>start: restored.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus(); self.update_formatting_state()

    def _mutate_touched_block_formats(self, mutator):
        """Change only requested properties on each selected paragraph's own format."""
        editor=self.visual_editor; cursor=editor.textCursor(); blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks:
            return
        cursor.beginEditBlock()
        try:
            for block in blocks:
                block_cursor=QTextCursor(block); block_format=QTextBlockFormat(block.blockFormat())
                mutator(block_format,block)
                block_cursor.setBlockFormat(block_format)
        finally:
            cursor.endEditBlock()
        restored=QTextCursor(editor.document()); restored.setPosition(start)
        if end>start:
            restored.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus(); self.update_formatting_state()

    def set_alignment(self, alignment):
        if not self.visual_editing_available():
            return
        self._mutate_touched_block_formats(lambda fmt,_block: fmt.setAlignment(alignment))

    def apply_heading_from_combo(self, _index):
        if self.heading_combo.signalsBlocked():
            return
        self.apply_heading(int(self.heading_combo.currentData() or 0))

    def apply_heading(self, level):
        """Apply a paragraph style immediately to every paragraph touched by the selection."""
        level=max(0,min(6,int(level)))
        if not self.visual_editing_available(): return
        editor=self.visual_editor; cursor=editor.textCursor(); blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks: return
        normal_size=float(editor.document().defaultFont().pointSizeF() or 11.0)
        sizes={0:normal_size,1:24,2:20,3:17,4:15,5:13,6:12}
        default_font=editor.document().defaultFont()
        char_format=QTextCharFormat(); char_format.setFontPointSize(float(sizes[level]))
        char_format.setFontWeight(default_font.weight() if level==0 else QFont.Weight.Bold)
        char_format.setFontItalic(default_font.italic() if level==0 else False)
        cursor.beginEditBlock()
        try:
            for block in blocks:
                block_cursor=QTextCursor(block); block_format=QTextBlockFormat(block.blockFormat())
                if hasattr(block_format,"setHeadingLevel"): block_format.setHeadingLevel(level)
                block_cursor.setBlockFormat(block_format)
                block_cursor.setBlockCharFormat(char_format)
                text_length=max(0,block.length()-1)
                if text_length:
                    text_cursor=QTextCursor(editor.document()); text_cursor.setPosition(block.position()); text_cursor.setPosition(block.position()+text_length,QTextCursor.MoveMode.KeepAnchor); text_cursor.mergeCharFormat(char_format)
        finally:
            cursor.endEditBlock()
        restored=QTextCursor(editor.document()); restored.setPosition(start)
        if end>start: restored.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus(); self.update_formatting_state()

    def _remove_list_from_blocks(self, blocks):
        for block in blocks:
            block_cursor=QTextCursor(block); block_format=QTextBlockFormat(block.blockFormat())
            block_format.setObjectIndex(-1); block_format.setIndent(0); block_format.setLeftMargin(0.0); block_format.setTextIndent(0.0)
            block_cursor.setBlockFormat(block_format)

    def _sync_list_marker_format(self, block):
        """Make Qt's list marker use the paragraph's first real text formatting."""
        iterator=block.begin()
        while not iterator.atEnd():
            fragment=iterator.fragment(); iterator+=1
            if not fragment.isValid() or not fragment.text():
                continue
            try:
                if fragment.charFormat().isImageFormat():
                    continue
            except Exception:
                pass
            QTextCursor(block).setBlockCharFormat(fragment.charFormat())
            return
        QTextCursor(block).setBlockCharFormat(self._document_plain_char_format())

    def _toggle_list_style(self, style):
        if not self.visual_editing_available(): return
        editor=self.visual_editor; cursor=editor.textCursor(); blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks: return
        already=all(block.textList() is not None and block.textList().format().style()==style for block in blocks)
        cursor.beginEditBlock()
        try:
            self._remove_list_from_blocks(blocks)
            if not already:
                fmt=QTextListFormat(); fmt.setStyle(style); fmt.setIndent(1)
                for block in blocks:
                    self._sync_list_marker_format(block)
                first_cursor=QTextCursor(blocks[0]); text_list=first_cursor.createList(fmt)
                for block in blocks[1:]: text_list.add(block)
        finally:
            cursor.endEditBlock()
        restored=QTextCursor(editor.document()); restored.setPosition(start)
        if end>start: restored.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus(); self.update_formatting_state()

    def _remove_current_list(self, cursor):
        blocks,_,_=self._blocks_touched_by_cursor(cursor); self._remove_list_from_blocks(blocks)

    def toggle_bullet_list(self, _checked=False):
        self._toggle_list_style(QTextListFormat.Style.ListDisc)

    def change_indent(self, amount):
        if not self.visual_editing_available():
            return
        delta=int(amount)
        if not delta:
            return
        editor=self.visual_editor; cursor=editor.textCursor(); blocks,start,end=self._blocks_touched_by_cursor(cursor)
        if not blocks:
            return

        try:
            indent_width=float(editor.document().indentWidth() or 40.0)
        except Exception:
            indent_width=40.0

        selected_positions={block.position() for block in blocks}
        entries=[]
        for block in blocks:
            block_format=QTextBlockFormat(block.blockFormat()); text_list=block.textList()
            if text_list is None:
                visual_left=float(block_format.leftMargin())+max(0,int(block_format.indent()))*indent_width
                entries.append({"block":block,"format":block_format,"list":None,"left":max(0.0,visual_left+delta*indent_width)})
                continue
            list_format=QTextListFormat(text_list.format())
            current_level=max(1,int(list_format.indent() or 1))
            legacy_block_indent=max(0,int(block_format.indent()))
            target_level=max(1,min(9,current_level+legacy_block_indent+delta))
            entries.append({
                "block":block,
                "format":block_format,
                "list":text_list,
                "list_index":text_list.objectIndex(),
                "list_format":list_format,
                "current_level":current_level,
                "target_level":target_level,
                "legacy_block_indent":legacy_block_indent,
            })

        def compatible_list(text_list, source_format, target_level):
            if text_list is None:
                return False
            candidate=text_list.format()
            return (
                int(candidate.indent() or 1)==target_level
                and candidate.style()==source_format.style()
                and candidate.numberPrefix()==source_format.numberPrefix()
                and candidate.numberSuffix()==source_format.numberSuffix()
                and candidate.start()==source_format.start()
            )

        cursor.beginEditBlock()
        try:
            for entry in entries:
                if entry["list"] is not None:
                    continue
                block_format=entry["format"]
                block_format.setIndent(0)
                block_format.setLeftMargin(entry["left"])
                QTextCursor(entry["block"]).setBlockFormat(block_format)

            index=0
            while index<len(entries):
                entry=entries[index]
                if entry["list"] is None:
                    index+=1
                    continue
                group=[entry]; following=index+1
                while following<len(entries):
                    candidate=entries[following]
                    if (
                        candidate["list"] is None
                        or candidate["list_index"]!=entry["list_index"]
                        or candidate["target_level"]!=entry["target_level"]
                        or group[-1]["block"].next()!=candidate["block"]
                    ):
                        break
                    group.append(candidate); following+=1

                unchanged=(
                    entry["target_level"]==entry["current_level"]
                    and all(item["legacy_block_indent"]==0 for item in group)
                )
                if not unchanged:
                    for item in group:
                        block_format=item["format"]
                        block_format.setIndent(0)
                        QTextCursor(item["block"]).setBlockFormat(block_format)

                    target_format=QTextListFormat(entry["list_format"])
                    target_format.setIndent(entry["target_level"])
                    target_list=None
                    previous=group[0]["block"].previous()
                    if previous.isValid() and previous.position() not in selected_positions:
                        candidate=previous.textList()
                        if compatible_list(candidate,target_format,entry["target_level"]):
                            target_list=candidate
                    if target_list is None:
                        next_block=group[-1]["block"].next()
                        if next_block.isValid() and next_block.position() not in selected_positions:
                            candidate=next_block.textList()
                            if compatible_list(candidate,target_format,entry["target_level"]):
                                target_list=candidate
                    if target_list is None:
                        target_list=QTextCursor(group[0]["block"]).createList(target_format)
                    else:
                        target_list.add(group[0]["block"])
                    for item in group[1:]:
                        target_list.add(item["block"])
                index=following
        finally:
            cursor.endEditBlock()
        restored=QTextCursor(editor.document()); restored.setPosition(start)
        if end>start:
            restored.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(restored); editor.setFocus(); self.update_formatting_state()

    def apply_line_spacing_from_combo(self, _index):
        if self.line_spacing_combo.signalsBlocked():
            return
        self.set_line_spacing(int(self.line_spacing_combo.currentData() or 100))

    def set_line_spacing(self, percent):
        if not self.visual_editing_available():
            return
        percent=max(50,min(400,int(percent)))
        self._mutate_touched_block_formats(
            lambda fmt,_block: fmt.setLineHeight(float(percent),QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        )

    def show_paragraph_dialog(self):
        if not self.visual_editing_available():
            return
        current = self.visual_editor.textCursor().blockFormat()
        dialog = QDialog(self)
        dialog.setWindowTitle("Paragraph")
        form = QFormLayout(dialog)
        alignment = QComboBox(dialog)
        for label, value in (
            ("Left", Qt.AlignmentFlag.AlignLeft),
            ("Centre", Qt.AlignmentFlag.AlignHCenter),
            ("Right", Qt.AlignmentFlag.AlignRight),
            ("Justify", Qt.AlignmentFlag.AlignJustify),
        ):
            alignment.addItem(label, value)
        current_alignment = current.alignment()
        for idx in range(alignment.count()):
            if current_alignment & alignment.itemData(idx):
                alignment.setCurrentIndex(idx)
                break
        # Qt stores paragraph margins/indents in layout pixels, while RTF and
        # this dialog present document measurements in points.  Convert at the
        # boundary instead of relabelling raw pixels as points.
        px_to_pt = lambda value: float(value) * 72.0 / 96.0
        pt_to_px = lambda value: float(value) * 96.0 / 72.0
        left = QSpinBox(dialog); left.setRange(0, 1000); left.setValue(round(px_to_pt(current.leftMargin())))
        right = QSpinBox(dialog); right.setRange(0, 1000); right.setValue(round(px_to_pt(current.rightMargin())))
        first = QSpinBox(dialog); first.setRange(-500, 1000); first.setValue(round(px_to_pt(current.textIndent())))
        before = QSpinBox(dialog); before.setRange(0, 500); before.setValue(round(px_to_pt(current.topMargin())))
        after = QSpinBox(dialog); after.setRange(0, 500); after.setValue(round(px_to_pt(current.bottomMargin())))
        spacing = QComboBox(dialog)
        for label, value in (("1.0", 100), ("1.15", 115), ("1.5", 150), ("2.0", 200)):
            spacing.addItem(label, value)
        current_spacing=round(current.lineHeight()) if current.lineHeight() else 100
        spacing.setCurrentIndex(min(range(spacing.count()),key=lambda i:abs(int(spacing.itemData(i))-current_spacing)))
        form.addRow("Alignment:", alignment)
        form.addRow("Left indent (pt):", left)
        form.addRow("Right indent (pt):", right)
        form.addRow("First line (pt):", first)
        form.addRow("Space before (pt):", before)
        form.addRow("Space after (pt):", after)
        form.addRow("Line spacing:", spacing)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        def apply_paragraph(fmt,_block):
            fmt.setAlignment(alignment.currentData())
            fmt.setLeftMargin(pt_to_px(left.value()))
            fmt.setRightMargin(pt_to_px(right.value()))
            fmt.setTextIndent(pt_to_px(first.value()))
            fmt.setTopMargin(pt_to_px(before.value()))
            fmt.setBottomMargin(pt_to_px(after.value()))
            fmt.setLineHeight(float(spacing.currentData()), QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        self._mutate_touched_block_formats(apply_paragraph)

    def update_formatting_state(self, _format=None):
        if not hasattr(self, "visual_editor"):
            return
        fmt = self.visual_editor.currentCharFormat()
        block = self.visual_editor.textCursor().blockFormat()
        controls = [
            self.font_combo, self.font_size_combo, self.font_weight_combo, self.heading_combo,
            self.line_spacing_combo, self.bold_button, self.italic_button,
            self.underline_button, self.strike_button, self.align_left_button,
            self.align_center_button, self.align_right_button,
            self.align_justify_button, self.bullet_button,
        ]
        for control in controls:
            control.blockSignals(True)
        try:
            self.font_combo.setCurrentFont(fmt.font())
            self._reset_font_face_display()
            size = self._logical_char_size(fmt)
            self.font_size_combo.setEditText(f"{size:g}")
            current_weight = int(fmt.fontWeight())
            weight_idx = min(
                range(self.font_weight_combo.count()),
                key=lambda i: abs(int(self.font_weight_combo.itemData(i)) - current_weight),
            )
            self.font_weight_combo.setCurrentIndex(weight_idx)
            level = block.headingLevel() if hasattr(block, "headingLevel") else 0
            idx = self.heading_combo.findData(level)
            self.heading_combo.setCurrentIndex(max(0, idx))
            bold = int(fmt.fontWeight()) >= int(QFont.Weight.Bold)
            self.bold_button.setChecked(bold)
            self.italic_button.setChecked(fmt.fontItalic())
            self.underline_button.setChecked(fmt.fontUnderline())
            self.strike_button.setChecked(fmt.fontStrikeOut())
            alignment = block.alignment()
            self.align_left_button.setChecked(bool(alignment & Qt.AlignmentFlag.AlignLeft))
            self.align_center_button.setChecked(bool(alignment & Qt.AlignmentFlag.AlignHCenter))
            self.align_right_button.setChecked(bool(alignment & Qt.AlignmentFlag.AlignRight))
            self.align_justify_button.setChecked(bool(alignment & Qt.AlignmentFlag.AlignJustify))
            current_list = self.visual_editor.textCursor().currentList()
            style = current_list.format().style() if current_list else None
            self.bullet_button.setChecked(style == QTextListFormat.Style.ListDisc)
            line_height = round(block.lineHeight()) if block.lineHeight() else 100
            spacing_idx = min(
                range(self.line_spacing_combo.count()),
                key=lambda i: abs(
                    int(self.line_spacing_combo.itemData(i)) - line_height
                ),
            )
            self.line_spacing_combo.setCurrentIndex(spacing_idx)
        finally:
            for control in controls:
                control.blockSignals(False)
        self._reset_font_face_display()
        QTimer.singleShot(0, self._reset_font_face_display)
        for action, checked in (
            (getattr(self, "bold_action", None), int(fmt.fontWeight()) >= int(QFont.Weight.Bold)),
            (getattr(self, "italic_action", None), fmt.fontItalic()),
            (getattr(self, "underline_action", None), fmt.fontUnderline()),
            (getattr(self, "strike_action", None), fmt.fontStrikeOut()),
            (
                getattr(self, "superscript_action", None),
                fmt.verticalAlignment()
                == QTextCharFormat.VerticalAlignment.AlignSuperScript,
            ),
            (
                getattr(self, "subscript_action", None),
                fmt.verticalAlignment()
                == QTextCharFormat.VerticalAlignment.AlignSubScript,
            ),
        ):
            if action is not None:
                action.blockSignals(True)
                action.setChecked(checked)
                action.blockSignals(False)
        current_list = self.visual_editor.textCursor().currentList()
        list_style = current_list.format().style() if current_list else None
        for action, checked in (
            (getattr(self, "bulleted_list_action", None), list_style == QTextListFormat.Style.ListDisc),
            (getattr(self, "alignment_left_action", None), bool(block.alignment() & Qt.AlignmentFlag.AlignLeft)),
            (getattr(self, "alignment_center_action", None), bool(block.alignment() & Qt.AlignmentFlag.AlignHCenter)),
            (getattr(self, "alignment_right_action", None), bool(block.alignment() & Qt.AlignmentFlag.AlignRight)),
            (getattr(self, "alignment_justify_action", None), bool(block.alignment() & Qt.AlignmentFlag.AlignJustify)),
        ):
            if action is not None:
                action.blockSignals(True)
                action.setChecked(checked)
                action.blockSignals(False)
        current_level = (
            block.headingLevel() if hasattr(block, "headingLevel") else 0
        )
        for level, action in getattr(self, "heading_actions", {}).items():
            action.blockSignals(True)
            action.setChecked(level == current_level)
            action.blockSignals(False)
        if hasattr(self, "table_edit_actions"):
            in_table = (
                not self.view_only
                and self.visual_editor.textCursor().currentTable() is not None
            )
            for action in self.table_edit_actions:
                action.setEnabled(in_table)
        if hasattr(self, "edit_link_action"):
            in_link = (not self.view_only and self._visual_anchor_cursor() is not None)
            self.edit_link_action.setEnabled(in_link)
            self.remove_link_action.setEnabled(in_link)
