#!/usr/bin/env python3
"""Audit RiqatonyDesk's complete Heritage/Humility/Harmony command-icon families."""

from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "new": ROOT / "assets" / "ribbon-icons",
    "classic": ROOT / "assets" / "ribbon-icons-classic",
    "original": ROOT / "assets" / "ribbon-icons-original",
}
VARIANTS = ("light", "dark")

REQUIRED_CORE = {
    "about", "bold", "bullet-list", "copy", "cut", "documentation",
    "exit", "find", "new", "open-folder", "save", "save-as",
    "save-exit", "shortcuts", "view-only",
}

def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])

inventories: dict[tuple[str, str], set[str]] = {}
for family, base in FAMILIES.items():
    for variant in VARIANTS:
        pngs = {path.stem for path in (base / variant).glob("*.png")}
        assert not list(base.rglob("*.svg")), (family, "SVG assets remain")
        assert REQUIRED_CORE <= pngs, (family, variant, "missing core icons", sorted(REQUIRED_CORE - pngs))
        assert "layout-retro" not in pngs, "Retired Retro icon remains"
        expected = 144
        assert len(pngs) == expected, (family, variant, len(pngs), expected)
        for name in pngs:
            assert png_dimensions(base / variant / f"{name}.png") == (64, 64), (family, variant, name)
        inventories[(family, variant)] = pngs

reference = inventories[("new", "light")]
assert inventories[("new", "dark")] == reference, "Harmony light/dark command inventories differ"
for family in ("classic", "original"):
    assert inventories[(family, "light")] == inventories[(family, "dark")], (family, "light/dark mismatch")
    assert inventories[(family, "light")] <= reference, (family, "commands missing from Harmony")
assert inventories[("classic", "light")] == inventories[("original", "light")], "Humility/Heritage core inventory changed"

for variant in VARIANTS:
    for left, right in (("new", "classic"), ("new", "original"), ("classic", "original")):
        changed = sum(
            (FAMILIES[left] / variant / f"{name}.png").read_bytes()
            != (FAMILIES[right] / variant / f"{name}.png").read_bytes()
            for name in inventories[(left, variant)] & inventories[(right, variant)]
        )
        assert changed >= 80, (variant, left, right, "families are not visually distinct", changed)

print(
    "PASS: RiqatonyDesk triple icon families "
    f"({len(reference)} commands x light/dark x Heritage/Humility/Harmony)"
)
