# RiqatonyDesk 1.0.0-x16.3 Release Checklist

- [x] Build from untouched RiqatonyDesk 1.0.0-x16.2.
- [x] Add the local successful-open message, 3000 ms duration, retaining compatibility-warning precedence.
- [x] Add plain-text empty clipboard message, 3500 ms, with no paste side effects.
- [x] Add Insert/Overwrite message, 2500 ms, only on key toggles.
- [x] Add changed/missing backing-file notifications, 5000/6000 ms, only on monitored state transitions; no repeat or in-app action noise.
- [x] Keep existing text, two-widget status bar, central workspace status, and document operations unchanged.
- [x] Exact x16.2 production preservation except approved message insertions.
- [ ] Fedora KDE/PyQt6 live GUI verification.
