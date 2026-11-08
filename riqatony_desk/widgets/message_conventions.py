# Shared Desk status-message presentation conventions.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Message punctuation, default duration and unresolved warning policy."""

DEFAULT_MESSAGE_DURATION_MS = 4000

def status_sentence(message: str) -> str:
    """Use a final period, preserving supplied information and file paths."""
    text = str(message).strip()
    if not text:
        return text
    if text.endswith("…") or text.endswith("..."):
        return text.rstrip(". …") + "."
    return text if text.endswith(".") else text + "."

def is_critical_status(message: str) -> bool:
    """Unresolved failures with a persistent warning surface or requiring intervention."""
    text = str(message)
    return text.startswith((
        "Could not load ", "Could not save ", "Workspace scan failed:",
        "Backing file missing;", "File changed outside ",
        "RTF opened with compatibility warnings.",
    ))
