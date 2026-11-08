# RiqatonyDesk 1.0.0-x16.7 — release validation

## Approved scope

- Extended grapheme cluster counting, reusing the RiqatonyPad 2.0.0-x13.5 RTF document counter; no changes to RTF safety limits or status-bar layout.
- Consistent page-owned backing-file notifications for repository and monitor events, deduplicated by backing state, with selective critical-warning clearing.
- Remove 642 SVG icon assets, preserving 652 PNGs byte-for-byte.

## Verified static checks

- Current x16.7 focused Unicode, caching, notification and predecessor source/PNG integrity test: passed with Qt protocol doubles.
- Three PNG icon families: passed.
- RTF fidelity corpus, LibreOffice interoperability, command convergence and file-action convergence: passed separately.
- Python syntax and AppStream XML parsing: passed.

## Qualifications

- Full historical release-checker execution did not complete within the execution limit; do not represent it as passing.
- Historical security QA requires removed pre-refactoring `widgets/editor_lifecycle.py`; the identical script fails on the untouched x16.6 source. It was not changed.
- Qt/PyQt6 is unavailable; GUI event routing, Qt grapheme segmentation, display behavior and performance remain unverified in a live desktop session.
- Historical version-specific QA and source hashes remain intact; the current gate invokes the x16.7 test in place of the version-pinned x16.6 test.
