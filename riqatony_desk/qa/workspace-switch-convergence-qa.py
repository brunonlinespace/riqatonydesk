#!/usr/bin/env python3
"""RiqatonyDesk 0.1.3 workspace-switch convergence contract."""
from pathlib import Path
import ast

PACKAGE = Path(__file__).resolve().parents[1]
PATH = PACKAGE / "widgets" / "main_window.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
method = next((n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == "_switch_project"), None)
if method is None:
    raise SystemExit("FAIL: _switch_project() missing")
lines = SOURCE.splitlines(keepends=True)
body = "".join(lines[method.lineno - 1:method.end_lineno])

def require(fragment: str) -> None:
    if fragment not in body:
        raise SystemExit(f"FAIL: workspace-switch contract missing: {fragment}")

for fragment in (
    "self._update_window_title()",
    "self.runtime_paths.ensure_writable_workspace(project.folder)",
    "self.editor_manager.can_close_application()",
    "self._install_watcher(\n                self.library_root, start=True, retire_current=False",
    "self._pending_open_path = None",
    "self._repair_navigation_after_scan = False",
    "self._update_action_states()",
    'self.show_status(f"Opening Workspace: {project.name}")',
):
    require(fragment)

order = (
    "self.runtime_paths.ensure_writable_workspace(project.folder)",
    "self.editor_manager.can_close_application()",
    "self._save_active_project_state(save=True)",
    "self.watcher.stop(",
    "self._pending_open_path = None",
    "self.library_root = root",
    "self.editor_manager.switch_workspace_root(root)",
    "self.navigation.switch_workspace_root(root)",
    "self.repository.clear()",
    "self.project_registry.set_active(project.project_id)",
    "self._apply_active_project_state()",
    "self._install_watcher(root, start=True, retire_current=True)",
    "self.editor_manager.show_dashboard()",
    "self._update_action_states()",
    'self.show_status(f"Opening Workspace: {project.name}")',
)
cursor = -1
for fragment in order:
    cursor = body.find(fragment, cursor + 1)
    if cursor < 0:
        raise SystemExit(f"FAIL: workspace-switch ordering diverged at: {fragment}")
active = body.split("if project.project_id == self.project_registry.active_project_id:", 1)[1].split("if not project.folder.is_dir():", 1)[0]
if active.find("self._update_window_title()") < 0 or active.find("self.editor_manager.show_dashboard()") < 0:
    raise SystemExit("FAIL: active-workspace refresh branch incomplete")
if active.find("self._update_window_title()") > active.find("self.editor_manager.show_dashboard()"):
    raise SystemExit("FAIL: active-workspace title refresh must precede Dashboard")
print("PASS: RiqatonyDesk 0.1.3 workspace-switch convergence contract")
