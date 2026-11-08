#!/usr/bin/env python3
# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
"""RiqatonyDesk application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from riqatony_desk import APP_NAME as SUITE_APP_NAME, APP_VERSION
from riqatony_desk.app_constants import (
    APP_DISPLAY_NAME,
    APP_INTERNAL_NAME,
    APP_RUNTIME_DESKTOP_ID,
    RTF_EXTENSIONS,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
)
from riqatony_desk.services.config_service import ConfigService
from riqatony_desk.services.project_registry import ProjectRegistry
from riqatony_desk.services.runtime_paths import RuntimePaths
from riqatony_desk.widgets.dialogs.first_run_dialog import FirstRunWizard
from riqatony_desk.widgets.main_window import MainWindow
from riqatony_desk.widgets.theme import apply_theme

def requested_open_path(arguments: list[str]) -> Path | None:
    """Accept one desktop ``%f`` positional or the internal ``--open-file`` form."""
    supplied: str | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--open-file":
            if index + 1 < len(arguments):
                supplied = arguments[index + 1]
                break
            index += 1
            continue
        if not argument.startswith("-"):
            supplied = argument
            break
        index += 1

    if supplied is None:
        return None
    path = Path(supplied).expanduser().resolve(strict=False)
    if path.is_file() and path.suffix.casefold() in RTF_EXTENSIONS:
        return path
    return None


def main() -> int:
    if "--version" in sys.argv:
        print(f"{SUITE_APP_NAME} {APP_VERSION}")
        return 0

    app = QApplication(sys.argv)
    # Keep the internal identifier separate from the visible caption.
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setDesktopFileName(APP_RUNTIME_DESKTOP_ID)

    runtime = RuntimePaths.detect(Path(__file__).resolve().parents[1] / "main.py")
    if runtime.icon_path.exists():
        app.setWindowIcon(QIcon(str(runtime.icon_path)))

    config_path = runtime.config_path
    config_existed_before_startup = config_path.exists()
    config = ConfigService(config_path)
    apply_theme(app, str(config.get("app_theme", "light")))

    force_setup = "--setup" in sys.argv
    should_show_setup = force_setup or (
        not bool(config.get("setup_completed", False))
        and (
            not config_existed_before_startup
            or bool(config.get("show_setup_assistant", False))
        )
    )

    if should_show_setup:
        assistant = FirstRunWizard(runtime)
        if assistant.exec():
            configured_workspace = str(assistant.selected_workspace)
        else:
            # Cancel remains safe and non-blocking: use the runtime default
            # and do not show the assistant again automatically.
            configured_workspace = str(runtime.default_workspace)

        config.update(
            {
                "workspace_path": configured_workspace,
                "setup_completed": True,
                "show_setup_assistant": False,
            },
            save=True,
        )
    else:
        configured_workspace = config.get("workspace_path")

    raw_projects = config.get("projects", [])
    had_registered_projects = bool(
        isinstance(raw_projects, list)
        and any(isinstance(item, dict) for item in raw_projects)
    )
    requested_workspace = runtime.resolve_workspace(configured_workspace)
    project_registry = ProjectRegistry(config, requested_workspace)
    if should_show_setup:
        selected_project = project_registry.add_folder(requested_workspace)
        project_registry.set_active(selected_project.project_id)
    requested_project = project_registry.active_project
    requested_workspace = requested_project.folder

    if (
        had_registered_projects
        and not should_show_setup
        and not requested_workspace.is_dir()
    ):
        fallback_project = next(
            (
                project
                for project in project_registry.projects
                if project.project_id != requested_project.project_id
                and project.folder.is_dir()
            ),
            None,
        )
        if fallback_project is None:
            fallback = runtime.default_workspace.resolve(strict=False)
            if fallback == requested_workspace:
                fallback = fallback.parent / "RiqatonyDesk Workspace"
            fallback = runtime.ensure_writable_workspace(fallback)
            fallback_project = project_registry.add_folder(
                fallback,
                fallback.name or "RiqatonyDesk Workspace",
            )
        else:
            fallback = fallback_project.folder
        project_registry.set_active(fallback_project.project_id)
        QMessageBox.warning(
            None,
            "Workspace Folder Unavailable",
            f"The Workspace '{requested_project.name}' is still registered, "
            "but its folder is unavailable:\n\n"
            f"{requested_workspace}\n\n"
            f"RiqatonyDesk will open '{fallback_project.name}' instead. Use "
            "File > Workspace(s) > Open / Manage Workspaces to relink it.",
        )
        requested_workspace = fallback

    try:
        library_root = runtime.ensure_writable_workspace(requested_workspace)
    except OSError as error:
        # Do not silently attempt to write inside a read-only AppImage mount.
        # Falling back to the runtime default also repairs stale configurations
        # that point to an unavailable removable drive or deleted directory.
        fallback = runtime.ensure_writable_workspace(runtime.default_workspace)
        library_root = fallback
        fallback_project = project_registry.add_folder(
            fallback,
            fallback.name or "RiqatonyDesk Workspace",
        )
        project_registry.set_active(fallback_project.project_id)
        print(
            f"Workspace '{requested_workspace}' was unavailable ({error}); "
            f"using '{fallback}'.",
            file=sys.stderr,
        )

    window = MainWindow(
        library_root,
        config,
        project_registry,
        runtime,
        icon_path=runtime.icon_path,
    )
    window.show()

    open_path = requested_open_path(app.arguments()[1:])
    if open_path is not None:
        window.queue_open_path(open_path)

    if not bool(config.get("quick_tour_seen", False)):
        QTimer.singleShot(0, window._show_quick_tour)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
