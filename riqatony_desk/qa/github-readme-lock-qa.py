#!/usr/bin/env python3
"""Immutable GitHub README gate; authoritative original is SHA-256 pinned.
Only current-version field(s) are permitted to vary. Never update this
reference or its fingerprint as part of routine release versioning.
"""
from pathlib import Path
import hashlib, re, sys
root=Path(__file__).resolve().parents[2]
reference=Path(__file__).with_name("github-readme-authority.txt").read_bytes()
assert hashlib.sha256(reference).hexdigest()=="27e17c39d8ccc2e746d013d78d3aa592573c90b9bde6d58cbd71a4ab2051f212", "Protected README authority was changed"
expected=reference.decode("utf-8")
assert expected.count("Current release: **1.0.0-x19.5**")==1
expected=expected.replace("Current release: **1.0.0-x19.5**", "Current release: **1.0.0**")
assert expected.startswith('<p align="center">\n\nCurrent source edition: RiqatonyDesk 1.0.0-x19.5.\n')
expected=expected.replace('<p align="center">\n\nCurrent source edition: RiqatonyDesk 1.0.0-x19.5.\n', '<p align="center">\n', 1)
actual=(root/"README.md").read_bytes()
assert actual==expected.encode("utf-8"), "GitHub README differs outside approved version field(s)"
print("PASS immutable GitHub README (version field(s) only)")
