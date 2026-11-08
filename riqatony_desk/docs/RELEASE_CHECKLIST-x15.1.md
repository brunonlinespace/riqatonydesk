# RiqatonyDesk 1.0.0-x15.1 — Release checklist

## Scope

- [x] Start from the immutable x15.0 source edition; retain successful-shutdown optimisation.
- [x] Change only Dashboard List/Grid geometry calculation and notifications.
- [x] Do not alter Dashboard cards, search/sort semantics, document engines, scanner or preferences.
- [x] Keep all historical QA and x15.0 release records unchanged.

## Verification

- [x] New headless x15.1 geometry contracts (cache reuse, invalidation, viewport width, one geometry signal).
- [x] Complete x15.0 predecessor digest comparison with explicit changed-file allowance.
- [x] Desk Health Check 2.1 embedded-manifest schema and file digests updated.
- [x] Static Python syntax and release gate.
- [ ] Live Fedora KDE/Wayland List/Grid performance and navigation smoke test.
- [ ] Detailed 700-document benchmark comparison with x15.0.
