# RiqatonyDesk 1.0.0-x15.0 — Shutdown and Health Check release checklist

- [ ] Portable `python main.py --version` prints `RiqatonyDesk 1.0.0-x15.0`.
- [ ] Close a fully loaded 700-file workspace without rebuilding Dashboard List/Grid cards.
- [ ] Cancel an unsaved-document exit and verify all state and editor contents remain intact.
- [ ] Exercise scanner-stop timeout: abort close, restore Dashboard, allow retry.
- [ ] Close with active scanning, verify cancellation and no unexpected data loss.
- [ ] Confirm original x14.0 palette/Folder Dashboard display remains unchanged.
- [ ] Validate embedded desk-health-check.json and suite-pythoine-component.json using Desk Health Check 2.0.
- [ ] Static QA, source manifest and extracted ZIP checks pass; live KDE/AppImage regression tests still required.

