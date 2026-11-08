#!/usr/bin/env python3
"""1.0.0-x19.6: dark Halcyon icon filename parity and byte-preserving correction."""
from pathlib import Path
import hashlib
root = Path(__file__).resolve().parents[1]
icons = root / "assets" / "ribbon-icons-aero"
light = {p.name for p in (icons / "light").glob("*.png")}
dark = {p.name for p in (icons / "dark").glob("*.png")}
assert light == dark, (sorted(light-dark),sorted(dark-light))
assert len(light) == 144, len(light)
assert "import-file.png" in dark
assert "impport-file.png" not in dark
png = (icons / "dark" / "import-file.png").read_bytes()
assert png[:8] == b"\x89PNG\r\n\x1a\n"
assert hashlib.sha256(png).hexdigest() == "c6c139452caae0d3df4d003785151a0607a994b94afbb61157abba05e7fa6c61"
print("PASS dark Halcyon Import File filename and light/dark inventory")
