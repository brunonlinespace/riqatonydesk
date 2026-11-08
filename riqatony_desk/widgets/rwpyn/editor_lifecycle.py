#!/usr/bin/env python3
# RiqatonyDesk - original editor file lifecycle operations
# GPLv3-or-later
# Version: 1.0.0-x11.2

import os
import hashlib
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from riqatony_desk.widgets.rwpyn.editor_printing import APP_NAME, fsync_directory
from riqatony_desk.widgets.rwpyn.editor_insertion import read_bounded_bytes
from riqatony_desk.rich_text_support import sanitise_qt_html
from riqatony_desk.rtf_codec import decode_rtf, document_to_rtf_with_properties, populate_qtextdocument_from_rtf_model, _rtf_clear_automatic_foreground

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MiB responsiveness limit
RTF_EXTENSIONS = {".rtf"}
DOCUMENT_EXTENSIONS = RTF_EXTENSIONS


class EditorFileLifecycleMixin:
    @staticmethod
    def _content_signature(data):
        """Return a stable signature for the exact encoded file bytes."""
        return (
            len(data),
            hashlib.sha256(data).digest(),
        )


    @classmethod
    def _disk_signature(cls, file_path):
        """Hash a file so same-size or timestamp-preserved edits are found."""
        if not file_path:
            return None

        digest = hashlib.sha256()
        size = 0
        try:
            stat = os.stat(file_path)
            if stat.st_size > MAX_FILE_SIZE:
                return ("oversize", stat.st_size)
            with open(file_path, "rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_FILE_SIZE:
                        return ("oversize", size)
                    digest.update(chunk)
        except OSError:
            return None

        return (
            size,
            digest.digest(),
        )


    def _external_change_action(self):
        """Resolve an external-change conflict without owning Plus UI policy.

        Managed RiqatonyDesk pages install ``external_change_action_provider`` so
        EditorPage is the single conflict-UX owner. The local dialog is retained
        only as a defensive standalone/component fallback and follows the same
        protected Save Version As contract.
        """
        if not self.file_path or self.file_disk_signature is None:
            return "overwrite"

        current_signature = self._disk_signature(self.file_path)
        if current_signature == self.file_disk_signature:
            return "overwrite"

        provider = getattr(self, "external_change_action_provider", None)
        if callable(provider):
            action = provider()
            return action if action in {"reload", "save_version_as", "overwrite", "handled_success", "cancel"} else "cancel"

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("File Changed on Disk")
        dialog.setText(
            "This file has changed on disk since RiqatonyDesk opened or saved it."
        )
        dialog.setInformativeText(
            "Choose Reload to discard the edits currently in RiqatonyDesk and use "
            "the disk copy, Save Version As to preserve both versions, or "
            "Overwrite to explicitly replace the changed disk copy."
        )
        reload_button = dialog.addButton("Reload", QMessageBox.ButtonRole.ActionRole)
        reload_button.setEnabled(current_signature is not None)
        save_version_button = dialog.addButton(
            "Save Version As…", QMessageBox.ButtonRole.ActionRole
        )
        overwrite_button = dialog.addButton(
            "Overwrite", QMessageBox.ButtonRole.DestructiveRole
        )
        cancel_button = dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is reload_button:
            return "reload"
        if clicked is save_version_button:
            return "save_version_as"
        if clicked is overwrite_button:
            return "overwrite"
        return "cancel"


    def _has_external_change(self):
        if not self.file_path or self.file_disk_signature is None:
            return False
        return self._disk_signature(self.file_path) != self.file_disk_signature


    def _save_version_as(self):
        if not self.file_path:
            return self.save_as_file()
        source_path = Path(self.file_path).expanduser().resolve(strict=False)
        suffix = source_path.suffix or ".rtf"
        suggested = source_path.with_name(f"{source_path.stem} - Desk Version{suffix}")
        counter = 2
        while suggested.exists():
            suggested = source_path.with_name(
                f"{source_path.stem} - Desk Version {counter}{suffix}"
            )
            counter += 1
        return bool(
            self.save_as_file(
                initial_path=str(suggested),
                forbidden_paths=(source_path,),
                dialog_title="Save Version As — RiqatonyDesk",
                forbidden_message=(
                    "Choose a different filename. The original file changed "
                    "externally and will be left untouched."
                ),
            )
        )


    def check_save_changes(self):
        if self.content_saved:
            return True
        answer = QMessageBox.question(
            self,
            APP_NAME,
            "Do you want to save changes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        if answer == QMessageBox.StandardButton.Discard:
            return True
        return False


    @staticmethod
    def format_for_path(file_path):
        return "rtf" if Path(file_path).suffix.lower() in RTF_EXTENSIONS else None


    def _document_payload(self, target_format=None):
        if (target_format or self.file_format) != "rtf": raise ValueError("RiqatonyDesk saves RTF documents only.")
        return document_to_rtf_with_properties(self._unzoomed_visual_document(), self.rtf_document_properties)


    def _synchronise_after_save(self, payload, *, semantic_signature=None, preserve_warnings=False):
        self._loading=True
        try: self.visual_editor.document().setModified(False)
        finally: self._loading=False
        self._source_rtf_payload=bytes(payload)
        if semantic_signature is None:
            try:
                semantic_signature=self._content_signature(self._document_payload("rtf"))
            except Exception:
                semantic_signature=None
        self._source_rtf_semantic_signature=semantic_signature
        if not preserve_warnings:
            self.rtf_compatibility_warnings=()
        self._rtf_save_warning_acknowledged=False


    def _write_payload_atomically(self, payload, *, target_path=None):
        destination = os.path.abspath(target_path or self.file_path)
        if os.path.islink(destination):
            with open(destination, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            return

        parent = os.path.dirname(destination) or "."
        basename = os.path.basename(destination)
        try:
            existing_mode = os.stat(destination).st_mode & 0o7777
        except FileNotFoundError:
            existing_mode = self._default_created_file_mode()

        descriptor = None
        temporary = None
        try:
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{basename}.ricopad-", suffix=".tmp", dir=parent
            )
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, existing_mode)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
            temporary = None
            fsync_directory(parent)
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


    def new_file(self):
        if not self.check_save_changes(): return False
        self._loading=True
        try:
            self.clear_search_results(); self.visual_editor.clear(); self.file_path=None; self.file_format="rtf"; self.file_encoding="rtf"; self.file_bom=b""; self.file_newline="\n"; self.file_disk_signature=None; self._source_rtf_payload=None; self._source_rtf_semantic_signature=None; self.content_saved=True; self.rtf_compatibility_warnings=(); self.rtf_document_properties={}; self._rtf_save_warning_acknowledged=False; self._view_only_prompt_shown=False; self._visual_document_zoom_percent=100; self.apply_editor_font(); self._apply_visual_document_zoom(self.zoom_percent); self.visual_editor.document().setModified(False)
        finally: self._loading=False
        self.view_only=bool(self.persist_view_only); self._update_mode_capabilities(); self.update_title(); self.update_status_counts(); self.update_formatting_state(); self.visual_editor.setFocus(); return True


    def save_and_exit(self):
        """Offer save-and-exit, exit-without-saving, or cancel explicitly."""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle("Save and Exit — RiqatonyDesk")
        dialog.setText("Do you want to save the current document before exiting RiqatonyDesk?")
        save_button = dialog.addButton(
            "Yes, save and exit", QMessageBox.ButtonRole.AcceptRole
        )
        discard_button = dialog.addButton(
            "No, exit without saving", QMessageBox.ButtonRole.DestructiveRole
        )
        cancel_button = dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is cancel_button or clicked is None:
            return False
        if clicked is save_button:
            if not self.save_file():
                return False
        elif clicked is not discard_button:
            return False

        self._skip_close_save_prompt = True
        self.close()
        return True


    @staticmethod
    def inspect_text_file(file_path):
        try:
            if not os.path.isfile(file_path): return False,"The selected path is not a regular file."
            size=os.path.getsize(file_path)
            if size>MAX_FILE_SIZE: return False,f"The file is larger than RiqatonyDesk's {MAX_FILE_SIZE//(1024*1024)} MiB safety limit."
        except OSError as exc: return False,f"Could not inspect the file:\n{exc}"
        if Path(file_path).suffix.lower() not in RTF_EXTENSIONS: return False,"RiqatonyDesk edits Rich Text Format (.rtf) documents only."
        return True,""


    def load_file(self, file_path, check_changes=True, show_error=True):
        if check_changes and not self.check_save_changes(): return False
        is_safe,reason=self.inspect_text_file(file_path)
        if not is_safe:
            if show_error: QMessageBox.information(self,"Unsupported File — RiqatonyDesk",f"RiqatonyDesk did not open:\n{os.path.basename(file_path)}\n\n{reason}")
            return False
        try:
            data=read_bounded_bytes(file_path,MAX_FILE_SIZE,label="document"); decoded=decode_rtf(data)
        except (ValueError,MemoryError,OSError) as exc:
            if show_error: QMessageBox.warning(self,"RTF Import Error — RiqatonyDesk",f"The RTF document could not be opened safely:\n{exc}")
            return False
        except Exception as exc:
            if show_error: QMessageBox.critical(self,"RTF Import Error — RiqatonyDesk",f"RiqatonyDesk could not import this RTF document:\n{exc}")
            return False
        self._loading=True
        try:
            self.clear_search_results()
            direct_import = populate_qtextdocument_from_rtf_model(
                self.visual_editor.document(), decoded.model
            )
            if not direct_import:
                # Conservative table fallback.  Ordinary paragraphs, blank blocks,
                # indentation and embedded-image provenance no longer pass through
                # Qt's lossy HTML normalization layer.
                document_html=sanitise_qt_html(decoded.html)
                self.visual_editor.setHtml(document_html)
                if decoded.automatic_foreground:
                    _rtf_clear_automatic_foreground(self.visual_editor.document(),decoded.automatic_foreground)
            self.apply_editor_canvas_theme(update_action=True); self._visual_document_zoom_percent=100; self._apply_visual_document_zoom(self.zoom_percent); self.visual_editor.document().clearUndoRedoStacks(); self.visual_editor.document().setModified(False)
            self.file_path=os.path.abspath(file_path); self.file_format="rtf"; self.file_encoding="rtf"; self.file_bom=b""; self.file_newline="\n"; self.file_disk_signature=self._content_signature(data); self._source_rtf_payload=bytes(data); self.content_saved=True; self.rtf_compatibility_warnings=tuple(decoded.warnings); self.rtf_document_properties=dict(decoded.document_properties); self._rtf_save_warning_acknowledged=False; self.view_only=bool(self.persist_view_only); self._view_only_prompt_shown=False
            try:
                self._source_rtf_semantic_signature=self._content_signature(self._document_payload("rtf"))
            except Exception:
                self._source_rtf_semantic_signature=None
        finally: self._loading=False
        self._update_mode_capabilities(); self.update_title(); self.update_status_counts(); self.update_formatting_state(); self.visual_editor.setFocus()
        if self.rtf_compatibility_warnings: self._show_status_message("RTF opened with compatibility warnings. Review File → Properties before saving.",4000)
        else: self._show_status_message(f"Loaded {os.path.basename(self.file_path)}", 4000)
        return True


    @staticmethod
    def _default_created_file_mode():
        """Return the normal 0666 mode after applying the process umask."""
        current_umask = os.umask(0)
        os.umask(current_umask)
        return 0o666 & ~current_umask


    def save_file(self, check_external_change=True):
        if not self.file_path: return self.save_as_file()
        if check_external_change:
            action=self._external_change_action()
            if action=="reload": self.load_file(self.file_path,check_changes=False,show_error=True); return False
            if action=="save_version_as": return self._save_version_as()
            if action=="handled_success": return True
            if action!="overwrite": return False
        document_dirty = (not self.content_saved) or self.visual_editor.document().isModified()
        canonical_payload = None
        canonical_signature = None
        semantically_clean = False
        if (
            document_dirty
            and self._source_rtf_payload is not None
            and self._source_rtf_semantic_signature is not None
        ):
            try:
                canonical_payload = self._document_payload("rtf")
                canonical_signature = self._content_signature(canonical_payload)
                semantically_clean = canonical_signature == self._source_rtf_semantic_signature
            except (ValueError, RuntimeError, MemoryError):
                canonical_payload = None
                canonical_signature = None
                semantically_clean = False
        clean_source = (
            self._source_rtf_payload is not None
            and ((not document_dirty) or semantically_clean)
        )
        if (
            clean_source
            and self.file_disk_signature == self._content_signature(self._source_rtf_payload)
            and self._disk_signature(self.file_path) == self.file_disk_signature
        ):
            # A plain Save on an unchanged loaded document is deliberately a
            # no-op.  A net-zero edit (type/delete back to the loaded supported
            # semantics) is treated the same way, so foreign RTF scaffolding is
            # not destroyed merely because Qt's modified flag stayed sticky.
            self._synchronise_after_save(
                self._source_rtf_payload,
                semantic_signature=self._source_rtf_semantic_signature,
                preserve_warnings=True,
            )
            self.content_saved=True
            self._update_mode_capabilities(); self.update_title(); self.update_status_counts(); return True
        if (not clean_source) and self.rtf_compatibility_warnings and not self._rtf_save_warning_acknowledged:
            details="\n• ".join(self.rtf_compatibility_warnings)
            box=QMessageBox(self); box.setIcon(QMessageBox.Icon.Warning); box.setWindowTitle("RTF Compatibility Warning — RiqatonyDesk"); box.setText("This document contains RTF constructs that RiqatonyDesk does not fully preserve."); box.setInformativeText("Saving will rewrite the document using RiqatonyDesk's supported RTF subset. The following content may be discarded:\n\n• "+details+"\n\nContinue only if that is acceptable."); save_btn=box.addButton("Save Supported Content",QMessageBox.ButtonRole.AcceptRole); box.addButton(QMessageBox.StandardButton.Cancel); box.exec()
            if box.clickedButton() is not save_btn: return False
            self._rtf_save_warning_acknowledged=True
        try:
            if clean_source:
                payload=bytes(self._source_rtf_payload)
                semantic_signature=self._source_rtf_semantic_signature
            else:
                payload=canonical_payload if canonical_payload is not None else self._document_payload("rtf")
                semantic_signature=canonical_signature or self._content_signature(payload)
            if len(payload)>MAX_FILE_SIZE: raise ValueError(f"The saved document would exceed RiqatonyDesk's {MAX_FILE_SIZE//(1024*1024)} MiB reopen limit.")
            self._write_payload_atomically(payload); self.file_disk_signature=self._content_signature(payload); self._synchronise_after_save(payload, semantic_signature=semantic_signature, preserve_warnings=clean_source); self.content_saved=True; self._update_mode_capabilities(); self.update_title(); self.update_status_counts(); return True
        except MemoryError: QMessageBox.critical(self,"Save Error","The document is too large to encode safely. No changes were written.")
        except (OSError,ValueError,RuntimeError) as exc: QMessageBox.critical(self,"Save Error",f"Could not save the document:\n{exc}")
        except Exception as exc: QMessageBox.critical(self,"Save Error",f"RiqatonyDesk could not serialise this document safely:\n{exc}")
        return False


    def save_as_file(
        self,
        *,
        initial_path=None,
        forbidden_paths=(),
        dialog_title="Save As — RiqatonyDesk",
        forbidden_message=None,
    ):
        # Ordinary Save As must preserve an externally changed source. Only the
        # explicit Overwrite choice from the conflict decision may replace it.
        if not forbidden_paths and self._has_external_change():
            return self._save_version_as()
        initial_path=initial_path or self.file_path or os.path.join(os.path.expanduser("~"),"Untitled.rtf")
        file_path,_=QFileDialog.getSaveFileName(self,dialog_title,initial_path,"Rich Text Format (*.rtf)")
        if not file_path: return False
        if not Path(file_path).suffix: file_path += ".rtf"
        if Path(file_path).suffix.lower() not in RTF_EXTENSIONS:
            QMessageBox.warning(self,"Unsupported Extension — RiqatonyDesk","RiqatonyDesk saves .rtf documents only."); return False
        candidate = Path(file_path).expanduser().resolve(strict=False)
        forbidden = {Path(path).expanduser().resolve(strict=False) for path in forbidden_paths}
        if candidate in forbidden:
            QMessageBox.warning(
                self,
                dialog_title,
                forbidden_message or "Choose a different filename for this version.",
            )
            return False
        validator = getattr(self, "save_as_target_validator", None)
        if callable(validator) and not validator(candidate):
            QMessageBox.warning(
                self,
                dialog_title,
                "That RTF file is already open in another editor page. "
                "Close it before replacing it with Save As.",
            )
            return False
        old_path = os.path.abspath(self.file_path) if self.file_path else ""
        target_path = os.path.abspath(file_path)
        if old_path and target_path == old_path:
            # Re-check after the dialog: the source could have changed while the
            # file picker was open. Route that race to protected Save Version As.
            if self._has_external_change():
                return self._save_version_as()
            return self.save_file(check_external_change=False)

        document_dirty = (not self.content_saved) or self.visual_editor.document().isModified()
        canonical_payload = None
        canonical_signature = None
        semantically_clean = False
        if (
            document_dirty
            and self._source_rtf_payload is not None
            and self._source_rtf_semantic_signature is not None
        ):
            try:
                canonical_payload = self._document_payload("rtf")
                canonical_signature = self._content_signature(canonical_payload)
                semantically_clean = canonical_signature == self._source_rtf_semantic_signature
            except (ValueError, RuntimeError, MemoryError):
                canonical_payload = None
                canonical_signature = None
                semantically_clean = False
        clean_source = (
            self._source_rtf_payload is not None
            and ((not document_dirty) or semantically_clean)
        )
        if (not clean_source) and self.rtf_compatibility_warnings and not self._rtf_save_warning_acknowledged:
            details = "\n• ".join(self.rtf_compatibility_warnings)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("RTF Compatibility Warning — RiqatonyDesk")
            box.setText("This document contains RTF constructs that RiqatonyDesk does not fully preserve.")
            box.setInformativeText(
                "Saving will rewrite the document using RiqatonyDesk's supported RTF subset. "
                "The following content may be discarded:\n\n• " + details +
                "\n\nContinue only if that is acceptable."
            )
            save_btn = box.addButton("Save Supported Content", QMessageBox.ButtonRole.AcceptRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()
            if box.clickedButton() is not save_btn:
                return False
            self._rtf_save_warning_acknowledged = True

        try:
            if clean_source:
                payload = bytes(self._source_rtf_payload)
                semantic_signature = self._source_rtf_semantic_signature
            else:
                payload = canonical_payload if canonical_payload is not None else self._document_payload("rtf")
                semantic_signature = canonical_signature or self._content_signature(payload)
            if len(payload) > MAX_FILE_SIZE:
                raise ValueError(
                    f"The saved document would exceed RiqatonyDesk's {MAX_FILE_SIZE//(1024*1024)} MiB reopen limit."
                )

            # Save As is a transaction: write the target while the current editor
            # still belongs to the source path.  Only a successful independent
            # write is allowed to change the live document identity.
            self._write_payload_atomically(payload, target_path=target_path)

            self.file_path = target_path
            self.file_format = "rtf"
            self.file_encoding = "rtf"
            self.file_bom = b""
            self.file_newline = "\n"
            self.file_disk_signature = self._content_signature(payload)

            # Rebind the managed page synchronously BEFORE marking QTextDocument
            # clean.  modificationChanged(False) must therefore apply to the new
            # repository document, never the original source document.
            if old_path and old_path != target_path:
                self.file_path_changed.emit(old_path, target_path)

            self._synchronise_after_save(
                payload,
                semantic_signature=semantic_signature,
                preserve_warnings=clean_source,
            )
            self.content_saved = True
            self._update_mode_capabilities()
            self.update_title()
            self.update_status_counts()
            return True
        except MemoryError:
            QMessageBox.critical(self, "Save Error", "The document is too large to encode safely. No changes were written.")
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save the document:\n{exc}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"RiqatonyDesk could not serialise this document safely:\n{exc}")
        return False

