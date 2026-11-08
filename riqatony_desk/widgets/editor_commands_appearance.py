#!/usr/bin/env python3
# ==============================================================================
# RiqatonyDesk - workspace RTF editor command and appearance methods
# Copyright (C) 2026 Bruno Machado
#
# GPLv3-or-later
#
# Version: 1.0.0-x11.2
# ==============================================================================

import base64
import html
import json
import hashlib
import locale
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import (
    QBuffer, QByteArray, QDateTime, QEvent, QIODevice, QLocale, QMimeData, QRect, QRectF,
    QRegularExpression, QSize, QSizeF, Qt, QTimer, QUrl, pyqtSignal,
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QBrush, QColor, QDesktopServices, QFont, QFontDatabase, QIcon,
    QImage, QImageReader, QKeySequence, QPainter, QPalette, QPixmap, QTextBlockFormat, QTextCharFormat,
    QTextCursor, QTextDocument, QTextDocumentFragment, QTextFormat, QTextImageFormat, QTextListFormat, QTextTableFormat,
)
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontComboBox,
    QFontDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
)

from riqatony_desk.rich_text_support import is_safe_link_target, sanitise_qt_html
from riqatony_desk.widgets.rwpyn.editor_preferences import EditorPreferencesMixin, MAX_CONFIG_FILE_SIZE, preference_bool, preference_text, resource_path
from riqatony_desk.widgets.rwpyn.editor_printing import EditorPrintingMixin, APP_NAME, fsync_directory, count_words
from riqatony_desk.widgets.rwpyn.editor_search_view import EditorSearchViewMixin, MAX_SEARCH_MATCHES
from riqatony_desk.widgets.rwpyn.editor_insertion import EditorInsertionMixin, read_bounded_bytes, host_process_environment, MAX_EMBEDDED_IMAGE_SIZE, MAX_IMAGE_SOURCE_SIZE, MAX_IMAGE_PIXELS
from riqatony_desk.widgets.rwpyn.editor_formatting import EditorFormattingMixin, FONT_SIZE_STEPS
from riqatony_desk.widgets.rwpyn.editor_widgets import (SafeTextDocument, RichTextEdit,
    MAX_PASTE_CHARACTERS, MAX_DOCUMENT_CHARACTERS,
    MAX_CLIPBOARD_HTML_CHARACTERS, RICOPAD_INLINE_RICH_MIME)
from riqatony_desk.services.rtf_new_document import (
    NewDocumentDefaults, build_new_document_rtf_payload,
)
from riqatony_desk.rtf_codec import (
    _qt_brush_colour, _rtf_clear_automatic_foreground,
    decode_rtf, document_to_rtf_with_properties, populate_qtextdocument_from_rtf_model,
    RTF_SYNTHETIC_STRUCTURE_BLOCK, RTF_TABLE_AUTOFIT_PROPERTY,
    RTF_AUTOMATIC_CONTRAST_PROPERTY,
    MAX_RTF_TABLE_ROWS, MAX_RTF_TABLE_COLUMNS, MAX_RTF_TABLE_CELLS,
)



class EditorCommandsAppearanceMixin:

    def custom_icon_variant(self):
        """Choose icons from the active AppImage theme or the host system palette."""
        if self.appimage_theme_available:
            selected=self.effective_appimage_theme()
            if selected in ("light","dark"):
                return selected
        try:
            application=QApplication.instance()
            palette=application.palette() if application is not None else self.palette()
            colour=palette.color(QPalette.ColorRole.Window)
            return "dark" if colour.lightness()<128 else "light"
        except (AttributeError,RuntimeError):
            return "light"

    def effective_appimage_icon_set(self):
        """Return the one-launch override or saved AppImage icon-family choice."""
        return self.appimage_icon_set_override or self.appimage_icon_set

    def custom_icon(self, icon_name):
        """Load one bundled RiqatonyDesk icon without consulting the host theme."""
        variant = self.custom_icon_variant()
        family = "ribbon-icons"
        if self.appimage_theme_available:
            family = {
                "original": "ribbon-icons-original",
                "classic": "ribbon-icons-classic",
                "aero": "ribbon-icons-aero",
            }.get(self.effective_appimage_icon_set(), "ribbon-icons")
        icon_path = resource_path(family, variant, f"{icon_name}.png")
        if os.path.isfile(icon_path):
            return QIcon(icon_path)
        # A branded application icon is safer than silently falling back to a
        # platform-dependent native glyph if a package is damaged.
        fallback = resource_path("icons", "riqatonydesk.png")
        return QIcon(fallback) if os.path.isfile(fallback) else QIcon()

    def bind_custom_icon(self, target, icon_name):
        """Assign and register a bundled icon for theme-variant refreshes."""
        target.setIcon(self.custom_icon(icon_name))
        self.icon_bindings.append((target, icon_name))

    def refresh_portable_icons(self):
        """Refresh bundled icons after an AppImage theme change or host repaint."""
        for target, icon_name in tuple(self.icon_bindings):
            try:
                target.setIcon(self.custom_icon(icon_name))
            except RuntimeError:
                continue

    def add_menu_action(
        self, menu, label, callback, shortcut=None, *, checkable=False,
    ):
        """Create a shared command action used by the Ribbon."""
        action = QAction(label, self)
        action.setCheckable(bool(checkable))
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        # Register the shared action on the window as well so its shortcut
        # remains active even though the legacy menu bar is hidden.
        self.addAction(action)
        return action

    def make_file_menu(self):
        menu = QMenu("&File", self); self.file_menu = menu; self.app_menu_bar.addMenu(menu)
        self.new_action = self.add_menu_action(
            menu, "New File…", self.new_requested.emit,
            QKeySequence.StandardKey.New,
        )
        self.workspace_action = self.add_menu_action(
            menu, "Open / Manage Workspace…", self.workspace_requested.emit,
            QKeySequence.StandardKey.Open,
        )
        self.dashboard_action = self.add_menu_action(
            menu, "Show Dashboard", self.dashboard_requested.emit,
            QKeySequence("Ctrl+W"),
        )
        menu.addSeparator()
        self.save_action = self.add_menu_action(menu, "Save", self.save_file, QKeySequence.StandardKey.Save)
        self.save_as_action = self.add_menu_action(menu, "Save As…", self.save_as_file, QKeySequence.StandardKey.SaveAs)
        menu.addSeparator()
        self.properties_action = self.add_menu_action(menu, "Properties", self.show_properties_dialog)
        self.more_actions_menu = menu.addMenu("More Actions")
        self.external_editor_action = self.add_menu_action(self.more_actions_menu, "Open in External Editor", self.external_editor_requested.emit, QKeySequence("Ctrl+Shift+E"))
        self.more_actions_menu.addSeparator()
        self.rename_action = self.add_menu_action(self.more_actions_menu, "Rename…", self.rename_requested.emit, QKeySequence("F2"))
        self.delete_file_action = self.add_menu_action(self.more_actions_menu, "Delete File", self.delete_requested.emit)
        self.more_actions_menu.addSeparator()
        self.duplicate_file_action = self.add_menu_action(self.more_actions_menu, "Duplicate File", self.duplicate_requested.emit, QKeySequence("Ctrl+Shift+D"))
        self.open_folder_action = self.add_menu_action(self.more_actions_menu, "Open Containing Folder", self.containing_folder_requested.emit, QKeySequence("Ctrl+Shift+O"))
        self.file_dependent_actions.extend([self.external_editor_action,self.rename_action,self.delete_file_action,self.duplicate_file_action,self.open_folder_action])
        menu.addSeparator()
        self.print_action = self.add_menu_action(menu, "Print…", self.print_document, QKeySequence.StandardKey.Print)
        self.export_pdf_action = self.add_menu_action(menu, "Export PDF…", self.export_pdf, QKeySequence("Ctrl+Alt+Shift+P"))
        self.page_setup_action = self.add_menu_action(menu, "Page Setup…", self.show_page_setup_dialog)
        menu.addSeparator()
        self.save_new_action = self.add_menu_action(
            menu, "Save and New", self.save_and_new_requested.emit,
        )
        self.save_dashboard_action = self.add_menu_action(
            menu, "Save and Dashboard", self.save_and_dashboard_requested.emit,
            QKeySequence("Ctrl+Shift+W"),
        )
        self.save_exit_action = self.add_menu_action(
            menu, "Save and Exit", self.save_and_exit_requested.emit,
            QKeySequence("Ctrl+Shift+Q"),
        )
        self.exit_action = self.add_menu_action(
            menu, "Exit", self.exit_requested.emit,
            QKeySequence.StandardKey.Quit,
        )

    def make_edit_menu(self):
        menu=QMenu("&Edit",self); self.edit_menu=menu; self.app_menu_bar.addMenu(menu)
        self.undo_action=self.add_menu_action(menu,"Undo",self.text_area_undo,QKeySequence.StandardKey.Undo)
        self.redo_action=self.add_menu_action(menu,"Redo",self.text_area_redo,QKeySequence("Ctrl+Y")); menu.addSeparator()
        self.cut_action=self.add_menu_action(menu,"Cut",self.cut_selection,QKeySequence.StandardKey.Cut)
        self.copy_action=self.add_menu_action(menu,"Copy",self.copy_selection,QKeySequence.StandardKey.Copy)
        self.paste_action=self.add_menu_action(menu,"Paste",lambda:self.text_area.paste(),QKeySequence.StandardKey.Paste)
        self.paste_plain_action=self.add_menu_action(menu,"Paste as Plain Text",self.paste_plain_text,QKeySequence("Ctrl+Shift+V")); menu.addSeparator()
        self.delete_text_action=self.add_menu_action(menu,"Delete",self.delete_selection,QKeySequence.StandardKey.Delete); menu.addSeparator()
        self.duplicate_line_action=self.add_menu_action(menu,"Duplicate Line / Selection",self.duplicate_current_line,QKeySequence("Ctrl+D"))
        self.delete_line_action=self.add_menu_action(menu,"Delete Line",self.delete_current_line,QKeySequence("Ctrl+Shift+K")); menu.addSeparator()
        self.select_all_action=self.add_menu_action(menu,"Select All",lambda:self.text_area.selectAll(),QKeySequence.StandardKey.SelectAll); menu.addSeparator()
        self.search_bar_action=QAction("Find",self); self.search_bar_action.setShortcut(QKeySequence.StandardKey.Find); self.search_bar_action.setToolTip("Find"); self.search_bar_action.setStatusTip("Find"); self.search_bar_action.triggered.connect(lambda _checked=False:self.toggle_find_panel(False)); self.addAction(self.search_bar_action)
        self.replace_action=self.add_menu_action(menu,"Find and Replace",lambda:self.toggle_find_panel(True),QKeySequence("Ctrl+H"))
        self.dismiss_find_action=QAction("Close Find/Replace",self); self.dismiss_find_action.setShortcut(QKeySequence("Esc")); self.dismiss_find_action.triggered.connect(self.hide_find_panel); self.addAction(self.dismiss_find_action)
        self.editing_actions.extend([self.undo_action,self.redo_action,self.cut_action,self.paste_action,self.paste_plain_action,self.delete_text_action,self.duplicate_line_action,self.delete_line_action,self.replace_action])

    def make_view_menu(self):
        menu=QMenu("&View",self); self.view_menu=menu; self.app_menu_bar.addMenu(menu)
        self.view_only_action=self.add_menu_action(menu,"Locked Mode",self.toggle_view_only,QKeySequence("F12"),checkable=True)
        self.status_bar_action=self.add_menu_action(menu,"Status Bar",self.toggle_status_bar,QKeySequence("Ctrl+Alt+Shift+S"),checkable=True)
        menu.addSeparator()
        self.wrap_action=self.add_menu_action(menu,"Word Wrap",self.toggle_word_wrap,QKeySequence("Ctrl+Alt+Shift+W"),checkable=True)
        menu.addAction(self.search_bar_action)
        self.editor_canvas_theme_action=self.add_menu_action(menu,"Dark Editor",self.toggle_editor_canvas_light,checkable=True)
        menu.addSeparator()
        zoom_menu=menu.addMenu("Zoom")
        self.zoom_in_action=self.add_menu_action(zoom_menu,"Zoom In",self.zoom_in,QKeySequence.StandardKey.ZoomIn)
        self.zoom_out_action=self.add_menu_action(zoom_menu,"Zoom Out",self.zoom_out,QKeySequence.StandardKey.ZoomOut)
        zoom_menu.addSeparator()
        self.zoom_reset_action=self.add_menu_action(zoom_menu,"Reset Zoom",self.zoom_reset,QKeySequence("Ctrl+0"))
        self.more_settings_menu=menu.addMenu("More Settings")
        self.tab_width_action=self.add_menu_action(self.more_settings_menu,"Tab Width…",self.open_tab_width_dialog)
        self.more_settings_menu.addSeparator()
        self.default_font_action=self.add_menu_action(self.more_settings_menu,"New Document Defaults…",self.show_new_document_defaults_dialog)
        menu.addSeparator()
        self.theme_menu=None; self.appimage_theme_group=None; self.appimage_theme_actions={}; self.appimage_icon_group=None; self.appimage_icon_actions={}
        if self.appimage_theme_available:
            self.theme_menu=menu.addMenu("App Theme")
            self.appimage_theme_group=QActionGroup(self); self.appimage_theme_group.setExclusive(True)
            for theme,label in (("system","System"),("dark","Dark"),("light","Light")):
                action=QAction(label,self,checkable=True)
                action.triggered.connect(lambda _checked=False,selected=theme:self.set_appimage_theme(selected))
                self.appimage_theme_group.addAction(action); self.theme_menu.addAction(action); self.addAction(action); self.appimage_theme_actions[theme]=action
            self.theme_menu.addSeparator()
            self.appimage_icon_group=QActionGroup(self); self.appimage_icon_group.setExclusive(True)
            for icon_set,label in (("original","Riqa Icons Heritage"),("classic","Riqa Icons Humility"),("new","Riqa Icons Harmony"),("aero","Riqa Icons Halcyon")):
                action=QAction(label,self,checkable=True)
                action.triggered.connect(lambda _checked=False,selected=icon_set:self.set_appimage_icon_set(selected))
                self.appimage_icon_group.addAction(action); self.theme_menu.addAction(action); self.addAction(action); self.appimage_icon_actions[icon_set]=action
        self.appimage_dark_mode_action=None

    def make_insert_menu(self):
        menu=QMenu("&Insert",self); self.insert_menu=menu; self.app_menu_bar.addMenu(menu)
        link_menu=menu.addMenu("Link"); self.bind_custom_icon(link_menu.menuAction(),"link-group")
        self.link_action=self.add_menu_action(link_menu,"Insert Link…",self.insert_link,QKeySequence("Ctrl+K"))
        self.edit_link_action=self.add_menu_action(link_menu,"Edit Link…",self.edit_link)
        link_menu.addSeparator()
        self.remove_link_action=self.add_menu_action(link_menu,"Remove Link",self.remove_link)
        menu.addSeparator()
        self.horizontal_rule_action=self.add_menu_action(menu,"Horizontal Rule",self.insert_horizontal_rule,QKeySequence("Ctrl+Alt+Shift+H"))
        self.image_action=self.add_menu_action(menu,"Image…",self.insert_image,QKeySequence("Ctrl+Shift+I"))
        menu.addSeparator()
        self.table_action=self.add_menu_action(menu,"Table…",self.insert_table,QKeySequence("Ctrl+Shift+T"))
        table_edit_menu=menu.addMenu("Table Editing")
        self.table_row_above_action=self.add_menu_action(table_edit_menu,"Insert Row Above",self.insert_table_row_above)
        self.table_row_below_action=self.add_menu_action(table_edit_menu,"Insert Row Below",self.insert_table_row_below)
        self.table_delete_row_action=self.add_menu_action(table_edit_menu,"Delete Row",self.delete_table_row); table_edit_menu.addSeparator()
        self.table_column_left_action=self.add_menu_action(table_edit_menu,"Insert Column Left",self.insert_table_column_left)
        self.table_column_right_action=self.add_menu_action(table_edit_menu,"Insert Column Right",self.insert_table_column_right)
        self.table_delete_column_action=self.add_menu_action(table_edit_menu,"Delete Column",self.delete_table_column); table_edit_menu.addSeparator()
        self.table_delete_action=self.add_menu_action(table_edit_menu,"Delete Table",self.delete_table)
        menu.addSeparator()
        self.insert_date_time_action=self.add_menu_action(menu,"Date and Time",self.insert_time_date,QKeySequence("F5"))
        self.date_action=self.add_menu_action(menu,"Date Only",self.insert_date,QKeySequence("Ctrl+;"))
        self.time_action=self.add_menu_action(menu,"Time Only",self.insert_time,QKeySequence("Ctrl+:"))
        menu.addSeparator()
        self.symbol_action=self.add_menu_action(menu,"Symbol…",self.show_symbols_popup,QKeySequence("Shift+F5"))
        self.table_edit_actions=[self.table_row_above_action,self.table_row_below_action,self.table_delete_row_action,self.table_column_left_action,self.table_column_right_action,self.table_delete_column_action,self.table_delete_action]
        self.visual_insert_actions.extend([self.insert_date_time_action,self.date_action,self.time_action,self.symbol_action,self.image_action,self.link_action,self.edit_link_action,self.remove_link_action,self.horizontal_rule_action,self.table_action,*self.table_edit_actions])

    def make_format_menu(self):
        menu=QMenu("F&ormat",self); self.format_menu=menu; self.app_menu_bar.addMenu(menu)
        def add(label,callback,shortcut=None):
            action=self.add_menu_action(menu,label,callback,shortcut); self.format_actions.append(action); return action
        self.font_dialog_action=add("Font…",self.choose_selection_font,QKeySequence("Ctrl+Shift+F"))
        self.increase_font_size_action=add("Increase Font Size",self.increase_font_size,QKeySequence("Ctrl+Shift+]"))
        self.decrease_font_size_action=add("Decrease Font Size",self.decrease_font_size,QKeySequence("Ctrl+Shift+["))
        self.text_colour_action=add("Text Colour…",self.choose_text_colour,QKeySequence("Ctrl+Shift+C"))
        self.highlight_colour_action=add("Highlight Colour…",self.choose_highlight_colour,QKeySequence("Ctrl+Shift+H"))
        self.clear_highlight_action=add("Clear Highlight",self.clear_highlight)
        menu.addSeparator()
        self.bold_action=add("Bold",self.toggle_bold,QKeySequence.StandardKey.Bold); self.bold_action.setCheckable(True)
        self.italic_action=add("Italic",self.toggle_italic,QKeySequence.StandardKey.Italic); self.italic_action.setCheckable(True)
        self.underline_action=add("Underline",self.toggle_underline,QKeySequence.StandardKey.Underline); self.underline_action.setCheckable(True)
        self.strike_action=add("Strikethrough",self.toggle_strikethrough,QKeySequence("Ctrl+Shift+X")); self.strike_action.setCheckable(True)
        self.superscript_action=add("Superscript",self.toggle_superscript,QKeySequence("Ctrl+.")); self.superscript_action.setCheckable(True)
        self.subscript_action=add("Subscript",self.toggle_subscript,QKeySequence("Ctrl+,")); self.subscript_action.setCheckable(True)
        menu.addSeparator()
        heading_menu=menu.addMenu("Paragraph Style"); self.bind_custom_icon(heading_menu.menuAction(),"heading-group"); self.heading_actions={}
        for label,level,shortcut in (("Normal Paragraph",0,"Ctrl+Shift+0"),("Heading 1",1,"Ctrl+Shift+1"),("Heading 2",2,"Ctrl+Shift+2"),("Heading 3",3,"Ctrl+Shift+3"),("Heading 4",4,"Ctrl+Shift+4"),("Heading 5",5,"Ctrl+Shift+5"),("Heading 6",6,"Ctrl+Shift+6")):
            action=QAction(label,self,checkable=True); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(lambda _checked=False,selected=level:self.apply_heading(selected)); heading_menu.addAction(action); self.addAction(action); self.bind_custom_icon(action,f"heading-{level}"); self.heading_actions[level]=action; self.format_actions.append(action)
        alignment_menu=menu.addMenu("Alignment"); self.alignment_actions={}
        for label,alignment,shortcut in (("Left",Qt.AlignmentFlag.AlignLeft,"Ctrl+L"),("Centre",Qt.AlignmentFlag.AlignHCenter,"Ctrl+E"),("Right",Qt.AlignmentFlag.AlignRight,"Ctrl+R"),("Justify",Qt.AlignmentFlag.AlignJustify,"Ctrl+J")):
            action=QAction(label,self,checkable=True); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(lambda _checked=False,selected=alignment:self.set_alignment(selected)); alignment_menu.addAction(action); self.addAction(action); self.alignment_actions[alignment]=action; self.format_actions.append(action)
        self.alignment_left_action=self.alignment_actions[Qt.AlignmentFlag.AlignLeft]; self.alignment_center_action=self.alignment_actions[Qt.AlignmentFlag.AlignHCenter]; self.alignment_right_action=self.alignment_actions[Qt.AlignmentFlag.AlignRight]; self.alignment_justify_action=self.alignment_actions[Qt.AlignmentFlag.AlignJustify]
        spacing_menu=menu.addMenu("Line Spacing"); self.line_spacing_actions={}
        for label,percent,shortcut in (("1.0",100,"Ctrl+1"),("1.15",115,"Ctrl+2"),("1.5",150,"Ctrl+3"),("2.0",200,"Ctrl+4")):
            action=QAction(label,self,checkable=True); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(lambda _checked=False,selected=percent:self.set_line_spacing(selected)); spacing_menu.addAction(action); self.addAction(action); self.line_spacing_actions[percent]=action; self.format_actions.append(action)
        menu.addSeparator()
        self.bulleted_list_action=add("Bullet List",self.toggle_bullet_list,QKeySequence("Ctrl+Shift+L")); self.bulleted_list_action.setCheckable(True)
        self.increase_indent_action=add("Indent",lambda:self.change_indent(1),QKeySequence("Ctrl+]"))
        self.decrease_indent_action=add("Outdent",lambda:self.change_indent(-1),QKeySequence("Ctrl+[")); menu.addSeparator()
        self.paragraph_action=add("Paragraph…",self.show_paragraph_dialog,QKeySequence("Ctrl+Shift+P"))
        self.clear_formatting_action=add("Clear Formatting",self.clear_formatting,QKeySequence("Ctrl+Space"))

    def bind_shortcuts(self):
        """Shortcuts are owned by the shared actions used by the ribbon."""
        return

    def infer_editor_canvas_theme(self):
        """Infer the existing editor appearance without changing it.

        This is now only a defensive fallback for malformed component state.
        RiqatonyDesk exp5 supplies an explicit editor-canvas preference instead of
        deriving canvas appearance from the application theme.
        """
        if self.appimage_theme_available:
            selected = self.effective_appimage_theme()
            if selected in ("light", "dark"):
                return selected
        colour = self.visual_editor.palette().color(QPalette.ColorRole.Base)
        return "light" if colour.lightness() >= 128 else "dark"

    def update_editor_canvas_theme_action(self):
        action = getattr(self, "editor_canvas_theme_action", None)
        if action is None:
            return
        is_dark = self.editor_canvas_theme == "dark"
        current = "Dark" if is_dark else "Light"
        target = "light" if is_dark else "dark"
        shortcut=action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        tooltip = (
            f"Dark Editor ({shortcut}) — editor canvas: {current}. Click for {target}; "
            "the ribbon and the rest of the interface will not change."
        ) if shortcut else (
            f"Dark Editor — editor canvas: {current}. Click for {target}; "
            "the ribbon and the rest of the interface will not change."
        )
        action.blockSignals(True)
        action.setChecked(is_dark)
        action.setToolTip(tooltip)
        action.setStatusTip(f"Editor canvas appearance: {current}")
        action.blockSignals(False)

    def apply_editor_canvas_theme(self, update_action=True):
        """Apply a display-only light/dark canvas override without rewriting RTF formatting."""
        if not hasattr(self,"visual_editor"): return
        provider = getattr(self, "managed_canvas_light_provider", None)
        if callable(provider):
            # Managed RiqatonyDesk owns one explicit light/dark canvas preference.
            # It is independent of the application System/Dark/Light setting.
            self.editor_canvas_theme = "light" if bool(provider()) else "dark"
        elif self.editor_canvas_theme not in ("light","dark"):
            self.editor_canvas_theme=self.infer_editor_canvas_theme()
        editor=self.visual_editor
        # Exact canonical Ricopad canvas-palette model.  Managed RiqatonyDesk does
        # not add a QSS border here; its persistent frame is rendered separately
        # with Qt's native focus primitive so the system's dimmer treatment is kept.
        palette=QPalette(editor.palette())
        if self.editor_canvas_theme == "light":
            palette.setColor(QPalette.ColorRole.Base,QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Text,QColor("#202124"))
            palette.setColor(QPalette.ColorRole.Highlight,QColor("#B24A3B"))
            palette.setColor(QPalette.ColorRole.HighlightedText,QColor("#FFFFFF"))
        else:
            palette.setColor(QPalette.ColorRole.Base,QColor("#151719"))
            palette.setColor(QPalette.ColorRole.Text,QColor("#F1F3F4"))
            palette.setColor(QPalette.ColorRole.Highlight,QColor("#B24A3B"))
            palette.setColor(QPalette.ColorRole.HighlightedText,QColor("#FFFFFF"))
        editor.setPalette(palette)
        editor.viewport().setPalette(palette)
        editor.setStyleSheet("")
        editor.viewport().setAutoFillBackground(True)
        editor.setContentsMargins(0,0,0,0)
        editor.setViewportMargins(0,0,0,0)
        editor.document().setDocumentMargin(4.0)
        editor.viewport().update()
        if update_action: self.update_editor_canvas_theme_action()

    def toggle_editor_canvas_light(self, checked):
        # The View action is named "Dark Editor": checked means dark.
        self.editor_canvas_theme = "dark" if bool(checked) else "light"
        self.apply_editor_canvas_theme(update_action=True)
        self.save_preferences()
        self._show_status_message(
            "Editor canvas switched to a dark background."
            if self.editor_canvas_theme == "dark"
            else "Editor canvas switched to a light background.",
            4000,
        )

    def effective_appimage_theme(self):
        """Return the explicit launch override or saved AppImage System/Dark/Light choice."""
        return self.appimage_theme_override or self.appimage_theme

    def _portable_rico_palette(self, theme):
        """Return the Plus-family Dark/Light palette with Rico's brick accent."""
        palette=QPalette()
        if theme == "dark":
            palette.setColor(QPalette.ColorRole.Window,QColor("#202326"))
            palette.setColor(QPalette.ColorRole.WindowText,QColor("#F1F3F4"))
            palette.setColor(QPalette.ColorRole.Base,QColor("#151719"))
            palette.setColor(QPalette.ColorRole.AlternateBase,QColor("#202326"))
            palette.setColor(QPalette.ColorRole.ToolTipBase,QColor("#F1F3F4"))
            palette.setColor(QPalette.ColorRole.ToolTipText,QColor("#101214"))
            palette.setColor(QPalette.ColorRole.Text,QColor("#F1F3F4"))
            palette.setColor(QPalette.ColorRole.Button,QColor("#292D31"))
            palette.setColor(QPalette.ColorRole.ButtonText,QColor("#F1F3F4"))
            palette.setColor(QPalette.ColorRole.Highlight,QColor("#B24A3B"))
            palette.setColor(QPalette.ColorRole.HighlightedText,QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.PlaceholderText,QColor("#8E969E"))
        else:
            application=QApplication.instance()
            palette=QPalette(application.style().standardPalette()) if application is not None else QPalette()
            palette.setColor(QPalette.ColorRole.Window,QColor("#D4D4D4"))
            palette.setColor(QPalette.ColorRole.WindowText,QColor("#2A2A2A"))
            palette.setColor(QPalette.ColorRole.Base,QColor("#F4F4F4"))
            palette.setColor(QPalette.ColorRole.AlternateBase,QColor("#E4E4E4"))
            palette.setColor(QPalette.ColorRole.ToolTipBase,QColor("#F4F4F4"))
            palette.setColor(QPalette.ColorRole.ToolTipText,QColor("#2A2A2A"))
            palette.setColor(QPalette.ColorRole.Text,QColor("#2A2A2A"))
            palette.setColor(QPalette.ColorRole.Button,QColor("#E4E4E4"))
            palette.setColor(QPalette.ColorRole.ButtonText,QColor("#2A2A2A"))
            palette.setColor(QPalette.ColorRole.Light,QColor("#F4F4F4"))
            palette.setColor(QPalette.ColorRole.Midlight,QColor("#D0D0D0"))
            palette.setColor(QPalette.ColorRole.Mid,QColor("#B2B2B2"))
            palette.setColor(QPalette.ColorRole.Dark,QColor("#767676"))
            palette.setColor(QPalette.ColorRole.Shadow,QColor("#545454"))
            palette.setColor(QPalette.ColorRole.Highlight,QColor("#B24A3B"))
            palette.setColor(QPalette.ColorRole.HighlightedText,QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.PlaceholderText,QColor("#767676"))
        return palette

    def _appimage_palette(self, theme):
        """Return a complete AppImage palette independent of the host theme."""
        application = QApplication.instance()
        base_palette = QPalette(application.palette()) if application is not None else QPalette()
        if theme == "dark":
            colours = {
                QPalette.ColorRole.Window: QColor("#232629"),
                QPalette.ColorRole.WindowText: QColor("#EFF0F1"),
                QPalette.ColorRole.Base: QColor("#1B1E20"),
                QPalette.ColorRole.AlternateBase: QColor("#252A2E"),
                QPalette.ColorRole.ToolTipBase: QColor("#31363B"),
                QPalette.ColorRole.ToolTipText: QColor("#EFF0F1"),
                QPalette.ColorRole.Text: QColor("#EFF0F1"),
                QPalette.ColorRole.Button: QColor("#31363B"),
                QPalette.ColorRole.ButtonText: QColor("#EFF0F1"),
                QPalette.ColorRole.BrightText: QColor("#FFFFFF"),
                QPalette.ColorRole.Highlight: QColor("#3DAEE9"),
                QPalette.ColorRole.HighlightedText: QColor("#FFFFFF"),
                QPalette.ColorRole.Link: QColor("#3DAEE9"),
                QPalette.ColorRole.LinkVisited: QColor("#9B7BD5"),
                QPalette.ColorRole.PlaceholderText: QColor("#A7AFB7"),
                QPalette.ColorRole.Light: QColor("#555B60"),
                QPalette.ColorRole.Midlight: QColor("#454A4F"),
                QPalette.ColorRole.Mid: QColor("#3D4246"),
                QPalette.ColorRole.Dark: QColor("#202326"),
                QPalette.ColorRole.Shadow: QColor("#111315"),
            }
            disabled = QColor("#70777D")
        else:
            colours = {
                QPalette.ColorRole.Window: QColor("#EFF0F1"),
                QPalette.ColorRole.WindowText: QColor("#232629"),
                QPalette.ColorRole.Base: QColor("#FFFFFF"),
                QPalette.ColorRole.AlternateBase: QColor("#F2F4F6"),
                QPalette.ColorRole.ToolTipBase: QColor("#FFFFDC"),
                QPalette.ColorRole.ToolTipText: QColor("#232629"),
                QPalette.ColorRole.Text: QColor("#232629"),
                QPalette.ColorRole.Button: QColor("#F7F7F8"),
                QPalette.ColorRole.ButtonText: QColor("#232629"),
                QPalette.ColorRole.BrightText: QColor("#FFFFFF"),
                QPalette.ColorRole.Highlight: QColor("#3DAEE9"),
                QPalette.ColorRole.HighlightedText: QColor("#FFFFFF"),
                QPalette.ColorRole.Link: QColor("#0068A6"),
                QPalette.ColorRole.LinkVisited: QColor("#6B4BA3"),
                QPalette.ColorRole.PlaceholderText: QColor("#6C757D"),
                QPalette.ColorRole.Light: QColor("#FFFFFF"),
                QPalette.ColorRole.Midlight: QColor("#E4E7E9"),
                QPalette.ColorRole.Mid: QColor("#B8BDC2"),
                QPalette.ColorRole.Dark: QColor("#92999F"),
                QPalette.ColorRole.Shadow: QColor("#687078"),
            }
            disabled = QColor("#9BA1A6")
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            for role, colour in colours.items():
                base_palette.setColor(group, role, colour)
        for role, colour in colours.items():
            base_palette.setColor(QPalette.ColorGroup.Disabled, role, colour)
        for role in (
            QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText, QPalette.ColorRole.PlaceholderText,
        ):
            base_palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
        return base_palette

    def apply_appimage_theme(self, theme, update_actions=True):
        """Apply System/Dark/Light chrome without touching document formatting."""
        if not self.appimage_theme_available or theme not in ("system","dark","light"):
            return
        application=QApplication.instance()
        if application is None:
            return
        # Plus-family implementation in every runtime: keep the active Qt
        # style, remove application QSS, reset to that style's standard palette,
        # then apply only the Dark/Light palette. Rico changes only the accent.
        application.setStyleSheet("")
        application.setPalette(application.style().standardPalette())
        if theme in ("dark","light"):
            application.setPalette(self._portable_rico_palette(theme))
        if update_actions:
            for selected,action in getattr(self,"appimage_theme_actions",{}).items():
                action.blockSignals(True); action.setChecked(selected==theme); action.blockSignals(False)
            self.refresh_portable_icons()
            self.apply_editor_canvas_theme(update_action=True)

    def set_appimage_theme(self, theme):
        """Persist System/Dark/Light application chrome across shipped runtimes."""
        theme=str(theme).strip().lower()
        if theme not in ("system","dark","light") or not self.appimage_theme_available:
            return
        os.environ.pop("RIQATONYDESK_APP_THEME",None)
        self.appimage_theme=theme
        self.appimage_theme_override=None
        self.apply_appimage_theme(theme)
        self.save_preferences()
        label="System" if theme=="system" else theme.title()
        self._show_status_message(f"Theme: {label}.",4000)

    def set_appimage_icon_set(self, icon_set):
        """Persist the Rico Legacy/Classic/Harmony command-icon family choice."""
        icon_set=str(icon_set).strip().lower()
        if icon_set not in ("original","classic","new","aero") or not self.appimage_theme_available:
            return
        os.environ.pop("RIQATONYDESK_ICON_SET",None)
        self.appimage_icon_set=icon_set
        self.appimage_icon_set_override=None
        for selected,action in getattr(self,"appimage_icon_actions",{}).items():
            action.blockSignals(True); action.setChecked(selected==icon_set); action.blockSignals(False)
        self.refresh_portable_icons()
        self.save_preferences()
        family_label={"new":"Harmony","classic":"Humility","original":"Heritage"}[icon_set]
        self._show_status_message(f"Riqa icons: {family_label}.",4000)

    def toggle_appimage_dark_mode(self, checked):
        """Compatibility hook for older shortcuts/configuration."""
        self.set_appimage_theme("dark" if checked else "light")
