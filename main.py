#!/usr/bin/env python3
"""RiqatonyDesk launcher."""

from __future__ import annotations

import sys

from riqatony_desk import APP_NAME, APP_VERSION


# Packaging tools may probe an extracted portable tree before any build
# environment exists. Keep this path dependency-free and exact.
if "--version" in sys.argv:
    print(f"{APP_NAME} {APP_VERSION}")
    raise SystemExit(0)

from riqatony_desk.app import main


if __name__ == "__main__":
    raise SystemExit(main())
