#!/usr/bin/env python3
"""Existing printing, PDF, page setup and document information methods (x5.0).

Moved without changes from the original editor host.
"""

import os
import re
import tempfile
from PyQt6.QtCore import QDateTime, QLocale, QRectF, QSizeF, Qt
from PyQt6.QtGui import QColor, QPainter, QTextCharFormat, QTextCursor
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QVBoxLayout)
from riqatony_desk.rtf_codec import _qt_brush_colour

APP_NAME = "RiqatonyDesk"

def fsync_directory(path):
    """Best-effort directory sync after an atomic replacement on POSIX."""
    if os.name == "nt":
        return
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        pass

_WORD_COUNT_RE = re.compile(
    r"[^\W_]+(?:[’'][^\W_]+)*(?:-[^\W_]+(?:[’'][^\W_]+)*)*",
    re.UNICODE,
)

def count_words(text):
    """Count Unicode words on demand without adding work to the live edit path."""
    return sum(1 for _match in _WORD_COUNT_RE.finditer(str(text)))


class EditorPrintingMixin:
    def show_page_setup_dialog(self):
        """Configure compact left, centre and right header/footer fields."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Page Setup")
        dialog.setModal(True)
        dialog.setMinimumWidth(590)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(20, 18, 20, 16)
        outer.setSpacing(14)

        explanation = QLabel(
            "Headers and footers are added only when printing.<br>"
            "<b>Placeholders:</b> &amp;F filename, &amp;P page, &amp;N total pages, "
            "&amp;D date, &amp;T time, &amp;A application, &amp;C Confidential.",
            dialog,
        )
        explanation.setWordWrap(True)
        outer.addWidget(explanation)

        def build_section(title, enabled, left_value, center_value, right_value):
            group = QGroupBox(dialog)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(12, 10, 12, 12)
            group_layout.setSpacing(7)

            enabled_check = QCheckBox(f"Enable {title.lower()}", group)
            enabled_check.setChecked(enabled)
            group_layout.addWidget(enabled_check)

            labels_row = QHBoxLayout()
            labels_row.setSpacing(8)
            for label_text in ("Left", "Centre", "Right"):
                label = QLabel(label_text, group)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                labels_row.addWidget(label, 1)
            group_layout.addLayout(labels_row)

            fields_row = QHBoxLayout()
            fields_row.setSpacing(8)
            left_edit = QLineEdit(left_value, group)
            center_edit = QLineEdit(center_value, group)
            right_edit = QLineEdit(right_value, group)
            fields_row.addWidget(left_edit, 1)
            fields_row.addWidget(center_edit, 1)
            fields_row.addWidget(right_edit, 1)
            group_layout.addLayout(fields_row)

            def update_enabled():
                active = enabled_check.isChecked()
                left_edit.setEnabled(active)
                center_edit.setEnabled(active)
                right_edit.setEnabled(active)

            enabled_check.toggled.connect(update_enabled)
            update_enabled()

            return group, enabled_check, left_edit, center_edit, right_edit

        (
            header_group,
            self.page_setup_header_check,
            self.page_setup_header_left,
            self.page_setup_header_center,
            self.page_setup_header_right,
        ) = build_section(
            "Header",
            self.print_header_enabled,
            self.print_header_left,
            self.print_header_center,
            self.print_header_right,
        )
        outer.addWidget(header_group)

        (
            footer_group,
            self.page_setup_footer_check,
            self.page_setup_footer_left,
            self.page_setup_footer_center,
            self.page_setup_footer_right,
        ) = build_section(
            "Footer",
            self.print_footer_enabled,
            self.print_footer_left,
            self.print_footer_center,
            self.print_footer_right,
        )
        outer.addWidget(footer_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        outer.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.print_header_enabled = self.page_setup_header_check.isChecked()
        self.print_header_left = self.page_setup_header_left.text()
        self.print_header_center = self.page_setup_header_center.text()
        self.print_header_right = self.page_setup_header_right.text()
        self.print_footer_enabled = self.page_setup_footer_check.isChecked()
        self.print_footer_left = self.page_setup_footer_left.text()
        self.print_footer_center = self.page_setup_footer_center.text()
        self.print_footer_right = self.page_setup_footer_right.text()
        self.save_preferences()

    def _expand_print_template(self, template, page_number, page_count):
        """Expand the small set of RiqatonyDesk print placeholders."""
        now = QDateTime.currentDateTime()
        system_locale = QLocale.system()
        filename = os.path.basename(self.file_path) if self.file_path else "Untitled"
        replacements = {
            "&F": filename,
            "&P": str(page_number),
            "&N": str(page_count),
            "&D": system_locale.toString(now.date(), QLocale.FormatType.ShortFormat),
            "&T": system_locale.toString(now.time(), QLocale.FormatType.ShortFormat),
            "&A": APP_NAME,
            "&C": "Confidential",
        }
        result = template
        for token, value in replacements.items():
            result = result.replace(token, value)
        return result

    def _draw_print_line(
        self, painter, rect, left_text, center_text, right_text, page_number, page_count
    ):
        """Draw three independently aligned fields within one header/footer line."""
        third = rect.width() / 3.0
        fields = (
            (
                QRectF(rect.left(), rect.top(), third, rect.height()),
                left_text,
                Qt.AlignmentFlag.AlignLeft,
            ),
            (
                QRectF(rect.left() + third, rect.top(), third, rect.height()),
                center_text,
                Qt.AlignmentFlag.AlignCenter,
            ),
            (
                QRectF(rect.left() + third * 2, rect.top(), third, rect.height()),
                right_text,
                Qt.AlignmentFlag.AlignRight,
            ),
        )

        for field_rect, template, horizontal_alignment in fields:
            if not template:
                continue
            text = self._expand_print_template(template, page_number, page_count)
            painter.drawText(
                field_rect,
                int(horizontal_alignment | Qt.AlignmentFlag.AlignVCenter),
                text,
            )

    def current_print_document(self):
        """Return a print clone with only automatic/unset body text normalized black.

        This ports Nuxpad's legibility lesson without flattening explicit RTF
        colours: user-selected foreground colours remain document content.
        """
        document=self._unzoomed_visual_document()
        cursor=QTextCursor(document)
        block=document.begin()
        while block.isValid():
            iterator=block.begin()
            while not iterator.atEnd():
                fragment=iterator.fragment()
                if fragment.isValid() and fragment.length()>0 and _qt_brush_colour(fragment.charFormat().foreground()) is None:
                    cursor.setPosition(fragment.position()); cursor.setPosition(fragment.position()+fragment.length(),QTextCursor.MoveMode.KeepAnchor)
                    fmt=QTextCharFormat(); fmt.setForeground(QColor(Qt.GlobalColor.black)); cursor.mergeCharFormat(fmt)
                iterator+=1
            block=block.next()
        return document

    def export_pdf(self):
        default_name=os.path.splitext(self.file_path)[0]+".pdf" if self.file_path else os.path.join(os.path.expanduser("~"),"Untitled.pdf")
        file_path,_=QFileDialog.getSaveFileName(self,"Export PDF",default_name,"PDF Documents (*.pdf)")
        if not file_path: return False
        if not file_path.lower().endswith(".pdf"): file_path += ".pdf"
        parent=os.path.dirname(os.path.abspath(file_path)) or os.curdir; descriptor=None; temporary=None
        try:
            descriptor,temporary=tempfile.mkstemp(prefix=".ricopad-pdf-",suffix=".pdf.tmp",dir=parent); os.close(descriptor); descriptor=None; os.remove(temporary)
            printer=QPrinter(QPrinter.PrinterMode.ScreenResolution); printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat); printer.setOutputFileName(temporary)
            if not self._print_document_with_header_footer(printer): return False
            if not os.path.isfile(temporary) or os.path.getsize(temporary)<=0: raise RuntimeError("The PDF print engine produced no output.")
            os.replace(temporary,file_path); temporary=None; fsync_directory(parent); self._show_status_message(f"Exported PDF to {file_path}",4000); return True
        except (OSError,RuntimeError) as exc:
            QMessageBox.critical(self,"PDF Export Error",f"Could not export PDF:\n{exc}"); return False
        finally:
            if descriptor is not None:
                try: os.close(descriptor)
                except OSError: pass
            if temporary and os.path.exists(temporary):
                try: os.remove(temporary)
                except OSError: pass

    def _print_document_with_header_footer(self, printer):
        """Paginate the rendered rich document with Nuxpad-style metadata bands."""
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Print Error", "RiqatonyDesk could not start the print or PDF job.")
            return False
        completed = False
        try:
            page_rect = QRectF(printer.pageLayout().paintRectPixels(printer.resolution()))
            if page_rect.width() <= 0 or page_rect.height() <= 0:
                raise RuntimeError("The selected printer returned an invalid page size.")
            dpi_x = max(72, printer.logicalDpiX())
            dpi_y = max(72, printer.logicalDpiY())
            side_margin = dpi_x * 0.25
            vertical_gap = dpi_y * 0.12
            body_padding = dpi_y * 0.10
            painter.setFont(QApplication.font())
            metrics = painter.fontMetrics()
            line_height = max(metrics.height(), int(dpi_y * 0.14))
            header_space = line_height * 2 + vertical_gap + body_padding if self.print_header_enabled else body_padding
            footer_space = line_height * 2 + vertical_gap + body_padding if self.print_footer_enabled else body_padding
            content_width = page_rect.width() - side_margin * 2
            content_height = page_rect.height() - header_space - footer_space
            if content_width <= 1 or content_height <= 1:
                raise RuntimeError("The printable page area is too small for the selected settings.")
            content_rect = QRectF(
                page_rect.left() + side_margin,
                page_rect.top() + header_space,
                content_width,
                content_height,
            )

            document = self.current_print_document()
            document.documentLayout().setPaintDevice(printer)
            document.setDocumentMargin(0)
            document.setPageSize(QSizeF(content_width, content_height))
            page_count = max(1, int(document.pageCount()))

            for page_index in range(page_count):
                if page_index and not printer.newPage():
                    raise RuntimeError("The print engine stopped before all pages were produced.")
                page_number = page_index + 1
                painter.setFont(QApplication.font())
                painter.setPen(QColor(Qt.GlobalColor.black))
                if self.print_header_enabled:
                    header_rect = QRectF(
                        page_rect.left() + side_margin,
                        page_rect.top() + vertical_gap,
                        content_width,
                        line_height,
                    )
                    self._draw_print_line(
                        painter, header_rect,
                        self.print_header_left, self.print_header_center, self.print_header_right,
                        page_number, page_count,
                    )
                if self.print_footer_enabled:
                    footer_rect = QRectF(
                        page_rect.left() + side_margin,
                        page_rect.bottom() - line_height - vertical_gap,
                        content_width,
                        line_height,
                    )
                    self._draw_print_line(
                        painter, footer_rect,
                        self.print_footer_left, self.print_footer_center, self.print_footer_right,
                        page_number, page_count,
                    )
                painter.save()
                painter.setPen(QColor(160, 160, 160))
                if self.print_header_enabled:
                    y = content_rect.top() - body_padding / 2
                    painter.drawLine(int(content_rect.left()), int(y), int(content_rect.right()), int(y))
                if self.print_footer_enabled:
                    y = content_rect.bottom() + body_padding / 2
                    painter.drawLine(int(content_rect.left()), int(y), int(content_rect.right()), int(y))
                painter.restore()
                painter.save()
                painter.translate(content_rect.left(), content_rect.top())
                painter.setClipRect(QRectF(0, 0, content_width, content_height))
                painter.translate(0, -page_index * content_height)
                document.drawContents(
                    painter,
                    QRectF(0, page_index * content_height, content_width, content_height),
                )
                painter.restore()
            completed = True
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Print Error", f"RiqatonyDesk could not complete the output.\n\n{exc}")
            return False
        finally:
            if painter.isActive():
                painter.end()
            if not completed and printer.outputFileName():
                try:
                    output_path = printer.outputFileName()
                    if os.path.isfile(output_path) and os.path.getsize(output_path) == 0:
                        os.remove(output_path)
                except OSError:
                    pass

    def print_document(self):
        # Nuxpad lesson: ScreenResolution keeps QTextDocument pagination/font metrics
        # aligned with Qt's printer/PDF paint engine while remaining vector/searchable.
        printer=QPrinter(QPrinter.PrinterMode.ScreenResolution); dialog=QPrintDialog(printer,self); dialog.setWindowTitle("Print")
        if dialog.exec()!=QDialog.DialogCode.Accepted: return False
        return self._print_document_with_header_footer(printer)

    def _format_file_size(self, size):
        size = int(size)
        if size < 1024:
            return f"{size} byte" if size == 1 else f"{size} bytes"
        value = float(size)
        for unit in ("KiB", "MiB", "GiB", "TiB"):
            value /= 1024.0
            if value < 1024.0 or unit == "TiB":
                return f"{value:.1f} {unit} ({size:,} bytes)"
        return f"{size:,} bytes"

    @staticmethod
    def _format_file_datetime(seconds):
        """Return a locale-aware timestamp across supported PyQt6 releases."""
        date_time = QDateTime.fromSecsSinceEpoch(int(seconds))
        format_type_enum = getattr(QLocale, "FormatType", None)
        long_format = getattr(format_type_enum, "LongFormat", None)
        if long_format is not None:
            try:
                return QLocale.system().toString(date_time, long_format)
            except (AttributeError, TypeError):
                pass
        # Newer Qt 6 bindings removed the old locale date-format member, so
        # use an explicit stable pattern as the final compatibility fallback.
        return date_time.toString("dddd, d MMMM yyyy HH:mm:ss t")

    def show_properties_dialog(self):
        dialog=QDialog(self); dialog.setWindowTitle("Properties — RiqatonyDesk"); dialog.setWindowIcon(self.windowIcon()); dialog.setMinimumWidth(640); layout=QVBoxLayout(dialog); layout.setContentsMargins(18,16,18,14); layout.setSpacing(12)
        def add_group(title,rows):
            box=QGroupBox(title,dialog); form=QFormLayout(box); form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for label,value in rows:
                field=QLineEdit(str(value),box); field.setReadOnly(True); field.setCursorPosition(0); form.addRow(label,field)
            layout.addWidget(box)
        if self.file_path:
            path=os.path.abspath(self.file_path)
            try:
                st=os.stat(path); rows=(("Name",os.path.basename(path)),("Document type","Rich Text Format (.rtf)"),("Location",os.path.dirname(path)),("Full path",path),("Size",self._format_file_size(st.st_size)),("Modified",self._format_file_datetime(st.st_mtime)),("Permissions",oct(st.st_mode&0o777)),("Symbolic link","Yes" if os.path.islink(path) else "No"))
            except OSError as exc: rows=(("File",path),("Status",f"Could not inspect: {exc}"))
        else: rows=(("Name","Untitled.rtf"),("Location","Not saved yet"))
        add_group("File",rows)
        text=self.text_area.toPlainText(); compatibility="Fully supported by RiqatonyDesk's RTF subset" if not self.rtf_compatibility_warnings else "; ".join(self.rtf_compatibility_warnings)
        add_group("Document",(("Format","Rich Text Format (RTF)"),("Lines",max(1,self.text_area.document().blockCount())),("Words",count_words(text)),("Characters",len(text)),("Unsaved changes","No" if self.content_saved else "Yes"),("Locked Mode","Yes" if self.view_only else "No"),("Compatibility",compatibility)))
        if self.rtf_document_properties:
            add_group("Preserved RTF page properties",tuple((k,str(v)) for k,v in sorted(self.rtf_document_properties.items())))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok,dialog); buttons.accepted.connect(dialog.accept); layout.addWidget(buttons); dialog.exec()
