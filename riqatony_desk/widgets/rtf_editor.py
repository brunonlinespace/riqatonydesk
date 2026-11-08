#!/usr/bin/env python3
# ==============================================================================
# RiqatonyDesk - workspace RTF editor
# Copyright (C) 2026 Bruno Machado
#
# GPLv3-or-later
#
# Version: 1.0.0-x12.1
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
from riqatony_desk.widgets.rwpyn.editor_lifecycle import EditorFileLifecycleMixin, MAX_FILE_SIZE, RTF_EXTENSIONS, DOCUMENT_EXTENSIONS
from riqatony_desk.widgets.editor_commands_appearance import EditorCommandsAppearanceMixin
from riqatony_desk.widgets.rwpyn.editor_printing import EditorPrintingMixin, APP_NAME, fsync_directory, count_words
from riqatony_desk.widgets.rwpyn.editor_search_view import EditorSearchViewMixin, MAX_SEARCH_MATCHES
from riqatony_desk.widgets.rwpyn.editor_insertion import EditorInsertionMixin, read_bounded_bytes, host_process_environment, MAX_EMBEDDED_IMAGE_SIZE, MAX_IMAGE_SOURCE_SIZE, MAX_IMAGE_PIXELS
from riqatony_desk.widgets.rwpyn.editor_formatting import EditorFormattingMixin, FONT_SIZE_STEPS
from riqatony_desk.widgets.rwpyn.character_count import count_visible_characters
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

APP_VERSION = "1.0.0-x12.1"
RIBBON_BUTTON_SIZE = 52
RIBBON_ICON_SIZE = 32
RIBBON_FONT_FAMILY_WIDTH = RIBBON_BUTTON_SIZE * 2

IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
GITHUB_URL = "https://github.com/brunonlinespace/riqatonydesk"
ISSUES_URL = GITHUB_URL + "/issues"

















def normalise_windows_organisation_directory(appdata):
    """Migrate the earlier organisation directory spelling without data loss."""
    desired_name = "brunonlinespace"
    desired_path = os.path.join(appdata, desired_name)
    legacy_names = ("BrunoOnlineSpace", "brunoonlinespace")

    try:
        entries = list(os.scandir(appdata))
    except OSError:
        return desired_path

    if any(
        entry.is_dir(follow_symlinks=False) and entry.name == desired_name
        for entry in entries
    ):
        return desired_path

    legacy_entry = next(
        (
            entry for entry in entries
            if entry.is_dir(follow_symlinks=False) and entry.name in legacy_names
        ),
        None,
    )
    if legacy_entry is None:
        return desired_path

    temporary_path = None
    for counter in range(100):
        candidate = os.path.join(
            appdata,
            f".ricopad-org-migration-{os.getpid()}-{counter}",
        )
        if not os.path.exists(candidate):
            temporary_path = candidate
            break
    if temporary_path is None:
        return desired_path

    try:
        os.rename(legacy_entry.path, temporary_path)
        os.rename(temporary_path, desired_path)
    except OSError:
        try:
            if os.path.exists(temporary_path) and not os.path.exists(legacy_entry.path):
                os.rename(temporary_path, legacy_entry.path)
        except OSError:
            pass
    return desired_path


def platform_config_locations():
    """Return RiqatonyDesk's private editor-preference location."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming"
        )
        organisation_directory = normalise_windows_organisation_directory(appdata)
        return os.path.join(organisation_directory, "RiqatonyDesk"), ()

    config_directory = os.path.expanduser(
        "~/.config/brunonlinespace/riqatonydesk"
    )
    return config_directory, ()


def configure_platform_identity():
    """Apply a stable Windows shell identity while remaining cross-platform."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "brunonlinespace.RiqatonyDesk"
        )
    except (AttributeError, OSError):
        pass




def appimage_theme_resources():
    """Return RiqatonyDesk's bundled theme-resource locations.

    The historical helper name and packaged QSS resources are retained for
    preference/backward compatibility and AppImage availability detection.
    Dark and Light chrome follow the Plus-family palette-only theme model in
    both Portable/source and AppImage runtimes.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    appdir = os.environ.get("APPDIR")
    if appdir:
        candidates.append(os.path.join(appdir, "usr", "share", "riqatonydesk", "styles"))
    candidates.extend((
        os.path.join(script_dir, "styles"),
        os.path.join(script_dir, "assets", "styles"),
        os.path.join(script_dir, "packaging", "appimage", "styles"),
        os.path.normpath(os.path.join(script_dir, "..", "assets", "styles")),
    ))
    for style_directory in candidates:
        resources = {
            "dark": os.path.join(style_directory, "breeze-dark.qss"),
            "light": os.path.join(style_directory, "breeze-light.qss"),
        }
        if all(os.path.isfile(path) for path in resources.values()):
            return resources
    return {}




# ---------- Rich editor widgets ----------







class _EmbeddedMenuRegistry:
    """Non-widget menu registry used by embedded Ricopad engines.

    RiqatonyDesk owns the only QMenuBar.  Embedded editors still construct their
    QMenus/QActions for command behavior, but never instantiate a child menu
    bar that Plasma can mistake for the application's global menu.
    """

    def __init__(self) -> None:
        self._menus = []

    def addMenu(self, menu):
        self._menus.append(menu)
        return menu

    def clear(self) -> None:
        self._menus.clear()

    def hide(self) -> None:
        return

    def setVisible(self, _visible: bool) -> None:
        return


# The retired standalone/embedded RtfEditorWindow implementation was removed in
# 0.0.3-exp6-r3. RiqatonyDesk has one live rich-text host only:
# MainWindow -> EditorPage -> RicopadEditorWidget(QWidget).


# ============================================================================
# Extracted Ricopad editor component for Plus-family hosting
# ============================================================================

class RicopadEditorWidget(EditorFileLifecycleMixin, EditorCommandsAppearanceMixin, EditorPreferencesMixin, EditorPrintingMixin, EditorSearchViewMixin, EditorFormattingMixin, EditorInsertionMixin, QWidget):
    """Ricopad's rich-text editor hosted as a real QWidget component.

    The component owns document/RTF/editing semantics. RiqatonyDesk owns all
    application chrome (MainWindow, AppMenu, Ribbon, workspace and window title).
    No QMainWindow compatibility API and no hidden Ricopad Ribbon/menu bar are
    constructed on the managed-document path.
    """

    new_requested = pyqtSignal()
    workspace_requested = pyqtSignal()
    dashboard_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    save_and_new_requested = pyqtSignal()
    save_and_dashboard_requested = pyqtSignal()
    save_and_exit_requested = pyqtSignal()
    external_editor_requested = pyqtSignal()
    containing_folder_requested = pyqtSignal()
    rename_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    duplicate_requested = pyqtSignal()
    file_path_changed = pyqtSignal(str, str)
    status_message = pyqtSignal(str)

    def __init__(self, initial_file=None, *, config_directory=None, managed_canvas_light_provider=None, managed_locked_mode_prompt_provider=None, managed_locked_mode_prompt_setter=None, parent=None):
        QWidget.__init__(self, parent)
        self.setObjectName("ricopadEditorWidget")
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAcceptDrops(False)

        self.file_path = None
        self.file_format = "rtf"
        self.file_encoding = "rtf"
        self.file_bom = b""
        self.file_newline = "\n"
        self.file_disk_signature = None
        self._source_rtf_payload = None
        self._source_rtf_semantic_signature = None
        self.content_saved = True
        self._loading = False
        self._syncing_editors = False
        self.view_only = False
        self._view_only_prompt_shown = False
        self.rtf_compatibility_warnings = ()
        self.rtf_document_properties = {}
        self._rtf_save_warning_acknowledged = False
        self.shortcuts_dialog = None
        self.about_dialog = None
        self.tutorial_dialog = None
        self.new_document_defaults_dialog = None
        self.search_matches = []
        self.search_results_truncated = False
        self._search_refresh_suspended = False
        self.current_search_index = -1
        self.icon_bindings = []
        self.format_actions = []
        self.format_widgets = []
        self.visual_insert_actions = []
        self.editing_actions = []
        self.file_dependent_actions = []
        self.zoom_percent = 100
        self._visual_document_zoom_percent = 100
        self._visual_zoom_device = None
        self._skip_close_save_prompt = False
        self.save_as_target_validator = None
        self.external_change_action_provider = None

        default_config_directory, _import_candidates = platform_config_locations()
        self.config_directory = os.fspath(config_directory or default_config_directory)
        self.config_import_candidates = ()
        self.config_file = os.path.join(self.config_directory, "editor.json")
        self.new_document_template_file = os.path.join(self.config_directory, "new-document-template.rtf")

        self.appimage_theme_files = appimage_theme_resources()
        self.appimage_theme_available = bool(self.appimage_theme_files)
        requested_theme = os.environ.get("RIQATONYDESK_APP_THEME", "").strip().lower()
        self.appimage_theme_override = requested_theme if requested_theme in ("system", "dark", "light") else None
        requested_icon_set = os.environ.get("RIQATONYDESK_ICON_SET", "").strip().lower()
        self.appimage_icon_set_override = requested_icon_set if requested_icon_set in ("original", "classic", "new", "aero") else None
        self.managed_canvas_light_provider = managed_canvas_light_provider
        self.managed_locked_mode_prompt_provider = managed_locked_mode_prompt_provider
        self.managed_locked_mode_prompt_setter = managed_locked_mode_prompt_setter

        self.load_preferences()
        self.view_only = bool(self.persist_view_only)
        icon_path = resource_path("icons", "riqatonydesk.png")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.build_ui()
        self.bind_shortcuts()
        self._loading = True
        try:
            self.apply_preferences()
            self.visual_editor.document().setModified(False)
            self.content_saved = True
        finally:
            self._loading = False
        self.apply_native_style()
        self.update_title()
        self.update_status_counts()
        self.update_search_counter()
        self.update_formatting_state()

        if initial_file:
            self.load_file(initial_file, check_changes=False)
        QTimer.singleShot(0, self._focus_editor_after_startup)

    def build_ui(self):
        """Build only Ricopad's editor component; application chrome belongs to RiqatonyDesk."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Construct Ricopad's authoritative QActions/QMenus as command objects only.
        # No QMenuBar, QMainWindow, Ricopad Ribbon or standalone toolbar is created.
        self.app_menu_bar = _EmbeddedMenuRegistry()
        self.make_file_menu(); self.make_edit_menu(); self.make_format_menu()
        self.make_insert_menu(); self.make_view_menu()

        # The authoritative two-row Find/Replace panel is inserted
        # below the editor surface after the editor is constructed.
        self.search_container = QFrame(self)
        self.search_container.setObjectName("searchContainer")
        self.search_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.search_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        search_layout = QGridLayout(self.search_container)
        search_layout.setContentsMargins(8, 6, 8, 6)
        self.search_entry = QLineEdit(self.search_container); self.search_entry.setPlaceholderText("Find")
        self.replace_entry = QLineEdit(self.search_container); self.replace_entry.setPlaceholderText("Replace")
        self.search_case_checkbox = QCheckBox("Match case", self.search_container)
        self.search_count_label = QLabel("", self.search_container); self.search_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_previous_button = QPushButton("Previous", self.search_container)
        self.search_next_button = QPushButton("Next", self.search_container)
        replace_button = QPushButton("Replace", self.search_container)
        replace_all_button = QPushButton("Replace All", self.search_container)
        close_button = QPushButton("Close", self.search_container)
        search_layout.addWidget(self.search_entry, 0, 0, 1, 3)
        search_layout.addWidget(self.search_previous_button, 0, 3)
        search_layout.addWidget(self.search_next_button, 0, 4)
        search_layout.addWidget(self.search_case_checkbox, 0, 5)
        search_layout.addWidget(self.search_count_label, 0, 6)
        search_layout.addWidget(self.replace_entry, 1, 0, 1, 3)
        search_layout.addWidget(replace_button, 1, 3)
        search_layout.addWidget(replace_all_button, 1, 4)
        search_layout.addWidget(close_button, 1, 6)
        self.search_entry.textChanged.connect(self.refresh_search)
        self.search_case_checkbox.toggled.connect(self.refresh_search)
        self.search_entry.returnPressed.connect(self.find_next)
        self.search_previous_button.clicked.connect(self.find_previous)
        self.search_next_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_next)
        replace_all_button.clicked.connect(self.replace_all)
        close_button.clicked.connect(self.hide_find_panel)
        self.replace_find_entry = self.search_entry
        self.replace_with_entry = self.replace_entry
        self.replace_case_checkbox = self.search_case_checkbox
        self.search_container.hide()

        # Ricopad formatting-state widgets are retained as editor state/control objects.
        # They are not a second toolbar: RiqatonyDesk presents them through ShellRibbon.
        self.format_controls = QWidget(self)
        self.format_controls.hide()
        self.format_toolbar = self.format_controls
        self.font_combo = QFontComboBox(self.format_controls); self.font_combo.setEditable(True); self.font_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if self.font_combo.lineEdit() is not None:
            e = self.font_combo.lineEdit(); e.setReadOnly(True); e.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.font_combo.currentTextChanged.connect(self._reset_font_face_display); self.font_combo.currentFontChanged.connect(self.set_selected_font); self.font_combo.currentFontChanged.connect(lambda _font:self._reset_font_face_display())
        self.font_size_combo = QComboBox(self.format_controls); self.font_size_combo.setEditable(True); self.font_size_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.font_size_combo.addItems(["8","9","10","11","12","14","16","18","20","24","28","32","36","48","72"]); self.font_size_combo.currentTextChanged.connect(self.set_selected_font_size)
        self.font_weight_combo = QComboBox(self.format_controls)
        for text, weight in (("Thin",QFont.Weight.Thin),("Extra Light",QFont.Weight.ExtraLight),("Light",QFont.Weight.Light),("Regular",QFont.Weight.Normal),("Medium",QFont.Weight.Medium),("Demi Bold",QFont.Weight.DemiBold),("Bold",QFont.Weight.Bold),("Extra Bold",QFont.Weight.ExtraBold),("Black",QFont.Weight.Black)):
            self.font_weight_combo.addItem(text, int(weight))
        self.font_weight_combo.currentIndexChanged.connect(self.apply_font_weight_from_combo)
        self.heading_combo = QComboBox(self.format_controls)
        for text, level in (("Normal",0),("Heading 1",1),("Heading 2",2),("Heading 3",3),("Heading 4",4),("Heading 5",5),("Heading 6",6)):
            self.heading_combo.addItem(text, level)
        self.heading_combo.currentIndexChanged.connect(self.apply_heading_from_combo)
        self.line_spacing_combo = QComboBox(self.format_controls)
        for label, value in (("1",100),("1.15",115),("1.5",150),("2",200)):
            self.line_spacing_combo.addItem(label, value)
        self.line_spacing_combo.currentIndexChanged.connect(self.apply_line_spacing_from_combo)

        def state_button(callback, *, checkable=False):
            button = QToolButton(self.format_controls); button.setCheckable(checkable); button.clicked.connect(callback); return button
        self.bold_button = state_button(self.toggle_bold, checkable=True)
        self.italic_button = state_button(self.toggle_italic, checkable=True)
        self.underline_button = state_button(self.toggle_underline, checkable=True)
        self.strike_button = state_button(self.toggle_strikethrough, checkable=True)
        self.text_colour_button = state_button(self.choose_text_colour)
        self.highlight_button = state_button(self.choose_highlight_colour)
        self.align_left_button = state_button(lambda:self.set_alignment(Qt.AlignmentFlag.AlignLeft), checkable=True)
        self.align_center_button = state_button(lambda:self.set_alignment(Qt.AlignmentFlag.AlignHCenter), checkable=True)
        self.align_right_button = state_button(lambda:self.set_alignment(Qt.AlignmentFlag.AlignRight), checkable=True)
        self.align_justify_button = state_button(lambda:self.set_alignment(Qt.AlignmentFlag.AlignJustify), checkable=True)
        self.bullet_button = state_button(self.toggle_bullet_list, checkable=True)
        self.symbols_button = state_button(self.show_symbols_popup)
        self.indent_button = state_button(lambda:self.change_indent(1))
        self.outdent_button = state_button(lambda:self.change_indent(-1))
        self.format_widgets.extend([self.font_combo,self.font_size_combo,self.font_weight_combo,self.heading_combo,self.line_spacing_combo,self.text_colour_button,self.highlight_button,self.bold_button,self.italic_button,self.underline_button,self.strike_button,self.align_left_button,self.align_center_button,self.align_right_button,self.align_justify_button,self.bullet_button,self.symbols_button,self.indent_button,self.outdent_button])

        self.visual_editor = RichTextEdit(self)
        self.visual_editor.setObjectName("visualEditor")
        self.visual_editor.setAcceptRichText(True)
        self.visual_editor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoNone)
        self.visual_editor.setFrameShape(QFrame.Shape.NoFrame)
        self.visual_editor.setContentsMargins(0,0,0,0)
        self.visual_editor.setViewportMargins(0,0,0,0)
        self.visual_editor.setMinimumSize(0,0)
        self.visual_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.visual_editor.document().setDocumentMargin(4.0)
        self.visual_editor.viewport().setMinimumSize(0,0)
        self.visual_editor.viewport().installEventFilter(self)
        self.visual_editor.currentCharFormatChanged.connect(self.update_formatting_state)
        self.visual_editor.cursorPositionChanged.connect(self.update_formatting_state)
        self.visual_editor.document().modificationChanged.connect(self.on_modification_changed)
        self.visual_editor.textChanged.connect(self.on_document_text_changed)
        self.visual_editor.installEventFilter(self)
        self.text_area = self.visual_editor
        self.main_layout.addWidget(self.visual_editor, 1)
        self.main_layout.addWidget(self.search_container, 0)

        # Editor-specific information stays a normal child widget, never a nested
        # application status bar/QMainWindow surface.
        self.app_status_bar = QStatusBar(self)
        self.app_status_bar.setObjectName("ricopadEditorStatus")
        self.app_status_bar.setSizeGripEnabled(False)

        # The flexible message occupies the left; the complete editor indicator
        # stays together at the right. No independent field-width reservations.
        self.status_message_label = QLabel("", self.app_status_bar)
        self.status_message_label.setMinimumWidth(0)
        self.status_message_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.status_message_label.setToolTip("")
        self.status_indicators_label = QLabel("Insert · Chars 0 · 100%", self.app_status_bar)
        self.status_indicators_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_indicators_label.setMinimumWidth(0)

        self._status_message_timer = QTimer(self)
        self._status_message_timer.setSingleShot(True)
        self._status_message_timer.timeout.connect(self._clear_status_message)

        self.app_status_bar.addWidget(self.status_message_label, 1)
        self.app_status_bar.addPermanentWidget(self.status_indicators_label)
        self.main_layout.addWidget(self.app_status_bar, 0)

    def _clear_status_message(self, *, warning_kind=None):
        # A resolved backing-file warning must not erase an unrelated critical notice.
        if warning_kind is not None and getattr(self, "_critical_editor_message_kind", None) != warning_kind:
            return
        self._status_message_timer.stop()
        self._critical_editor_message = False
        self._critical_editor_message_kind = None
        self.status_message_label.clear()
        self.status_message_label.setToolTip("")

    def _show_status_message(self, message, timeout=4000, *, warning_kind=None):
        from riqatony_desk.widgets.message_conventions import (
            is_critical_status, status_sentence,
        )
        text = status_sentence(message)
        critical = is_critical_status(text)
        recovering = text.startswith(("Loaded ", "Saved ", "Saved as ", "Saved RiqatonyDesk version as "))
        if getattr(self, "_critical_editor_message", False) and not (critical or recovering):
            return
        self._critical_editor_message = critical
        self._critical_editor_message_kind = warning_kind if critical else None
        if critical:
            timeout = 0
        self.status_message_label.setText(text)
        self.status_message_label.setToolTip(text)
        if int(timeout) > 0:
            self._status_message_timer.start(int(timeout))
        else:
            self._status_message_timer.stop()
        self.status_message.emit(text)


    def update_title(self):
        # Window titles are exclusively owned by RiqatonyDesk MainWindow.
        self.editor_title = os.path.basename(self.file_path) if self.file_path else "Untitled.rtf"
















    def _focus_editor_after_startup(self):
        """Give normal startup focus to the document after Ribbon is shown."""
        if not hasattr(self, "visual_editor") or not self.visual_editor.isEnabled():
            return
        # Do not steal focus from a first-run/tutorial window.
        if self.tutorial_dialog is not None and self.tutorial_dialog.isVisible():
            return
        self.visual_editor.setFocus(Qt.FocusReason.OtherFocusReason)
        self.visual_editor.ensureCursorVisible()

    def toggle_view_only(self, checked):
        checked=bool(checked)
        prompt_provider=getattr(self,"managed_locked_mode_prompt_provider",None)
        should_confirm=True if not callable(prompt_provider) else bool(prompt_provider())
        if not checked and self.view_only and should_confirm:
            dialog=QMessageBox(self); dialog.setWindowTitle("Disable Locked Mode? — RiqatonyDesk"); dialog.setIcon(QMessageBox.Icon.Warning); dialog.setText("Locked Mode protects files from accidental changes."); dialog.setInformativeText("Continue only when you intend to edit the document.")
            dont_ask=QCheckBox("Don't ask again when disabling Locked Mode",dialog); dialog.setCheckBox(dont_ask)
            keep=dialog.addButton("Keep Locked",QMessageBox.ButtonRole.RejectRole); cont=dialog.addButton("Continue",QMessageBox.ButtonRole.AcceptRole); dialog.setDefaultButton(keep); dialog.setEscapeButton(keep); dialog.exec()
            if dialog.clickedButton() is not cont:
                self.view_only_action.blockSignals(True); self.view_only_action.setChecked(True); self.view_only_action.blockSignals(False); return
            if dont_ask.isChecked():
                prompt_setter=getattr(self,"managed_locked_mode_prompt_setter",None)
                if callable(prompt_setter): prompt_setter(False)
        self.view_only=checked; self.persist_view_only=checked; self._view_only_prompt_shown=False; self.view_only_action.blockSignals(True); self.view_only_action.setChecked(checked); self.view_only_action.blockSignals(False); self._update_mode_capabilities(); self.update_title(); self.update_status_counts(); self.save_preferences(); self._show_status_message("Locked Mode enabled." if checked else "Locked Mode disabled.",4000)

    def explain_view_only_block(self):
        self._show_status_message("Editing is disabled while Locked Mode is enabled.",4000)
        if self._view_only_prompt_shown: return
        self._view_only_prompt_shown=True
        QMessageBox.information(self,"Locked Mode — RiqatonyDesk","Editing is disabled because Locked Mode is enabled.\n\nClear View → Locked Mode and confirm Continue to edit the document.")

    def eventFilter(self, watched, event):
        if bool(watched.property("ricopad_instant_tooltip")):
            if event.type()==QEvent.Type.Enter and watched.toolTip(): QToolTip.showText(watched.mapToGlobal(watched.rect().bottomLeft()),watched.toolTip(),watched,watched.rect(),7000)
            elif event.type()==QEvent.Type.Leave: QToolTip.hideText()
        editor=getattr(self,"visual_editor",None)
        viewport=editor.viewport() if editor is not None else None
        if watched is editor and event.type()==QEvent.Type.KeyPress and event.key()==Qt.Key.Key_Insert:
            editor.setOverwriteMode(not editor.overwriteMode()); self.update_status_counts()
            self._show_status_message("Overwrite mode enabled." if editor.overwriteMode() else "Insert mode enabled.", 4000)
            return True
        if self.view_only and watched is editor:
            if event.type()==QEvent.Type.InputMethod and (event.commitString() or event.preeditString()): self.explain_view_only_block(); return True
            if event.type()==QEvent.Type.KeyPress:
                modifiers=event.modifiers(); mutating=event.key() in {Qt.Key.Key_Backspace,Qt.Key.Key_Delete,Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Tab}; printable=bool(event.text()) and not (modifiers&(Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier|Qt.KeyboardModifier.MetaModifier)); standard=any(event.matches(k) for k in (QKeySequence.StandardKey.Cut,QKeySequence.StandardKey.Paste,QKeySequence.StandardKey.Undo,QKeySequence.StandardKey.Redo))
                if mutating or printable or standard: self.explain_view_only_block(); return True
        return QWidget.eventFilter(self, watched, event)












    def _new_document_alignment_flag(self):
        return {
            "left": Qt.AlignmentFlag.AlignLeft,
            "centre": Qt.AlignmentFlag.AlignHCenter,
            "right": Qt.AlignmentFlag.AlignRight,
            "justify": Qt.AlignmentFlag.AlignJustify,
        }.get(self.new_document_alignment, Qt.AlignmentFlag.AlignLeft)














    def document_editing_available(self, show_message=True):
        """Return whether document mutation is allowed in the active window."""
        if not self.view_only:
            return True
        if show_message:
            self.explain_view_only_block()
        return False

    def visual_editing_available(self, show_message=True):
        return self.document_editing_available(show_message)












































































    def toggle_status_bar(self, checked):
        self.show_status_bar = bool(checked)
        self.app_status_bar.setVisible(self.show_status_bar)
        if self.show_status_bar:
            self.update_status_counts()
        self.save_preferences()

    def toggle_menu_style(self, checked):
        """Compatibility hook retained for older configuration imports."""
        self.use_app_menu = False
        self.app_menu_bar.setVisible(False)

    def apply_menu_style(self):
        self.use_app_menu = False
        self.app_menu_bar.setVisible(False)

    def apply_native_style(self):
        """Keep source/portable chrome system-native; editor canvas stays independent."""
        self.setStyleSheet("")
        self.apply_editor_canvas_theme(update_action=True)











    def _open_host_target(self, target, *, local=False):
        """Open a URL/path with the host desktop, outside AppImage Qt/library env."""
        target=str(target)
        environment=host_process_environment(); host_path=environment.get("PATH")
        if sys.platform=="win32":
            try:
                os.startfile(target)
                return True
            except (AttributeError,OSError):
                pass
        candidates=[]
        if sys.platform=="darwin":
            candidates=[("open",[target])]
        elif sys.platform!="win32":
            candidates=[("xdg-open",[target]),("gio",["open",target])]
        for command,args in candidates:
            executable=shutil.which(command,path=host_path)
            if not executable:
                continue
            try:
                subprocess.Popen([executable,*args],env=environment,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
        url=QUrl.fromLocalFile(target) if local else QUrl(target)
        return bool(QDesktopServices.openUrl(url))

    def open_document_link(self, href):
        href=str(href or "").strip()
        if not href or not is_safe_link_target(href):
            return False
        if href.startswith("#"):
            try:
                self.visual_editor.scrollToAnchor(href[1:])
                self.visual_editor.setFocus()
                return True
            except Exception:
                return False
        parsed=QUrl(href)
        if parsed.scheme().lower() in ("http","https","mailto"):
            return self._open_host_target(href)
        if parsed.isLocalFile():
            path=parsed.toLocalFile()
        else:
            base=os.path.dirname(os.path.abspath(self.file_path)) if self.file_path else os.getcwd()
            path=os.path.abspath(os.path.join(base,href))
        if os.path.exists(path):
            return self._open_host_target(path,local=True)
        self._show_status_message("The linked file could not be found.",4000)
        return False

    def show_format_support_dialog(self):
        QMessageBox.information(self,"RTF Support — RiqatonyDesk","RiqatonyDesk edits Rich Text Format (.rtf) only.\n\nSupported core: fonts and character formatting, colours/highlights, paragraphs, lists, hyperlinks, embedded PNG/JPEG images, horizontal rules and bounded simple non-nested tables.\n\nUnsupported or partially supported constructs such as OLE objects, shapes, comments, footnotes, headers/footers and nested tables are reported in Properties and warned before a destructive save.\n\nPrint and Export PDF are output operations; RiqatonyDesk is not a PDF reader.")

    def on_modification_changed(self, _modified):
        if self._loading or self._syncing_editors:
            return
        active_modified = self.text_area.document().isModified()
        self.content_saved = not active_modified
        self.update_title()

    def update_status_counts(self):
        if not hasattr(self, "text_area"):
            return
        mode = "Overwrite" if self.text_area.overwriteMode() else "Insert"
        characters = count_visible_characters(self.text_area.document())
        self.status_indicators_label.setText(
            f"{mode} · Chars {characters:,} · {self.zoom_percent}%"
        )








    def _update_mode_capabilities(self):
        editing=not self.view_only
        self.visual_editor.setAcceptRichText(True); self.visual_editor.setReadOnly(self.view_only)
        self.format_menu.setEnabled(editing)
        for action in self.format_actions: action.setEnabled(editing)
        for widget in self.format_widgets: widget.setEnabled(editing)
        for action in self.visual_insert_actions: action.setEnabled(editing)
        for action in self.editing_actions: action.setEnabled(editing)
        for action in self.file_dependent_actions: action.setEnabled(bool(self.file_path))
        self.copy_action.setEnabled(True); self.select_all_action.setEnabled(True)
        if hasattr(self,"table_edit_actions"):
            in_table=editing and self.visual_editor.textCursor().currentTable() is not None
            for action in self.table_edit_actions: action.setEnabled(in_table)
        if hasattr(self,"edit_link_action"):
            in_link=editing and self._visual_anchor_cursor() is not None; self.edit_link_action.setEnabled(in_link); self.remove_link_action.setEnabled(in_link)
        self.view_only_action.blockSignals(True); self.view_only_action.setChecked(self.view_only); self.view_only_action.blockSignals(False)











    def closeEvent(self, event):
        if self._skip_close_save_prompt:
            self._skip_close_save_prompt = False
            event.accept()
            return
        if self.check_save_changes():
            event.accept()
        else:
            event.ignore()


