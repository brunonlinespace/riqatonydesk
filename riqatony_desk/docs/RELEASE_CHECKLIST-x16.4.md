# RiqatonyDesk 1.0.0-x16.4 Release Checklist

- [x] Start from unchanged RiqatonyDesk 1.0.0-x16.3.
- [x] Modify only `DashboardWidget._set_drop_highlight()` and `FolderDashboard._set_drop_highlight()` in production, apart from version identity.
- [x] Match MaqaronyDesk x18.5 guard precisely and preserve the original CSS including palette-driven highlight colour.
- [x] Repeated drag movement does not reapply the existing stylesheet; palette changes and drag leave/drop still apply the needed state once.
- [x] Drag/drop event handlers, RTF import routing, file operations, geometry, message routing, and editor mechanics unchanged.
- [x] All other production code preserved byte-for-byte and edition-specific QA retained as historical evidence.
- [x] Full static release gate and fresh-extraction gate.
- [ ] Live Fedora KDE/Wayland drag-and-drop verification.
