# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared application identity and metadata."""

from riqatony_desk import (
    APP_ID,
    APP_NAME as SUITE_APP_NAME,
    APP_VERSION,
    DESKTOP_ID,
    PUBLISHER_ID,
)

# Visible product branding and canonical Suite/package identity are RiqatonyDesk.
APP_INTERNAL_NAME = "riqatonydesk"
APP_BRAND_NAME = "RiqatonyDesk"
APP_DISPLAY_NAME = APP_BRAND_NAME
APP_WINDOW_TITLE = APP_DISPLAY_NAME
APP_RUNTIME_DESKTOP_ID = DESKTOP_ID
APP_REVISION = "1.0.0"

ORGANIZATION_NAME = "brunonlinespace"
ORGANIZATION_DOMAIN = "github.com/brunonlinespace"

RTF_EXTENSIONS = frozenset({".rtf"})
RTF_FILE_GLOB = "*.rtf"

GITHUB_URL = "https://github.com/brunonlinespace/riqatonydesk"
ISSUES_URL = f"{GITHUB_URL}/issues"
