#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
main = (ROOT/'widgets/main_window.py').read_text(encoding='utf-8')

def require(fragment, label):
    if fragment not in main:
        raise SystemExit(f'FAIL: {label}')

def forbid(fragment, label):
    if fragment in main:
        raise SystemExit(f'FAIL: {label}')

for fragment,label in [
('def _window_launch_command(self, open_path: Path | None = None) -> list[str]:','window launch helper'),
('def _launch_new_window(self, open_path: Path | None = None) -> bool:','new-window launcher'),
('def _open_external_file(self, _checked=False) -> None:','Open External File action'),
('"Open External File...", self._open_external_file','Open External File label'),
('self._startup_open_requested = True','startup-open suppression'),
('self._apply_external_verification_mode(page)','external verification mode'),
('page.set_view_only(True)','external Locked Mode'),
('self._toggle_collapsed_mode(True)','external Focused Mode'),
('document.path.resolve(strict=False) != self._pending_open_path','defensive pending-open path comparison'),
('for a in (self.duplicate_action,self.rename_file_action,self.delete_file_action): more.addAction(a)','More Actions file-management group'),
('more.addSeparator(); more.addAction(self.external_editor_action); more.addAction(self.open_document_folder_action)','More Actions external/location group'),
('more.addSeparator(); more.addAction(self.properties_action)','More Actions properties group'),
('self.duplicate_action = self._command("Duplicate File…", self._duplicate_current, "Ctrl+Shift+D")','Duplicate ellipsis'),
('self.rename_file_action = self._command("Rename File…", self._rename_current, "F2")','Rename label'),
('self.delete_file_action = self._command("Delete File", self._delete_current_file)','Delete no ellipsis'),
]: require(fragment,label)
for fragment,label in [
('self.workspace_menu.addAction(self.new_window_action)','New Window duplicated in Workspace(s)'),
]: forbid(fragment,label)
print('PASS: RiqatonyDesk 0.1.2 external-file lifecycle convergence contract')
