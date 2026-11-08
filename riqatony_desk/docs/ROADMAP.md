# Roadmap

### 0.1.2 — External-file lifecycle convergence (completed)
- Marko 0.2.1 external-open lifecycle parity, transient Locked + Focused startup, and AppMenu alignment.

### 0.1.7 — Managed sidebar drop hotfix (current)

- Managed file drops in the sidebar now resolve folder rows, file rows, and empty tree space consistently.

### 0.1.6 — Drag/drop reconciliation

- Port Marko Plus 0.2.4 explicit drag/drop routing: navigation surfaces import, editor opens external, ambiguous chrome rejects.
- Make Main Dashboard and empty sidebar tree explicit Workspace-root import targets.
- Resolve sidebar file rows to their containing folder while retaining folder-row targets and folder-only internal moves.
- Final planned behavioral reconciliation before the joint convergence audit.

### 0.1.5 — Reconciliation and small UX (completed)

- Relabel Find Bar to non-checkable Find while retaining context-sensitive Ctrl+F behavior.
- Add Open External File and Import File into Workspace to Create & Print.
- Replace user-facing Markdown Documentation with bundled RTF Documentation opened through the external-file lifecycle.
- Adopt Marko Plus dirty-status grammar and Workspace-menu QActionGroup rebuild lifecycle.
- Preserve RiqatonyDesk new-document semantics for Duplicate Last Saved Version.

### 0.1.4 — Discoverability and integration metadata (completed)

- Expose existing import behavior through File → Import File into Workspace....
- Align shared File/Workspace(s) AppMenu taxonomy and import discoverability.
- Align AppStream media-type declarations with the existing Desktop Entry RTF contract.

### 0.1.3 — Workspace-switch method convergence
- Adopt the stronger common workspace validation/switch completion sequence.
- Validate target writability before dirty-close prompting.
- Refresh common action/title/status state after a successful switch.


### 0.1.1 — Phase 1 closure/alignment (completed)

- Correct stale single-file startup QA.
- Small AppMenu/Ribbon policy-control alignment only.

### 0.1.0 — Phase 1 convergence

- Explicit main-Dashboard touch-is-scroll / never-touch-QDrag contract.
- External RTF mouse-drop import routing restored without auto-open/tab/window behavior.
- Workspace-switch watcher recovery and manual Refresh semantics converged with Marko Plus.
- Broken multi-file desktop-launch branch removed; desktop association is single-file `%f`.

### 0.0.5 — command convergence (completed)

- Align the remaining shared Rico shortcuts with Ricopad 1.0.0.
- Order Configure → View Control line 1 as Full Screen, Show Status, Show Sidebar.
- Order AppMenu → View as Full Screen, Show Status, Show Sidebar.

### 0.0.8 — Properties word count (accepted prior release)

- Branches directly from 0.0.6.
- Adds only on-demand Words count to Properties.
- 0.0.7 is rejected and not in the accepted lineage.

### 0.0.6 — file-action convergence (accepted baseline)

- Converge dirty Duplicate File semantics with Ricopad.
- Converge dirty Open in External Editor semantics with Ricopad.
- Add remembered policy/settings without weakening external-change protection.

### 0.0.7 — rejected experiment

- Rejected and not part of the accepted release lineage.

### Future — sidebar positioning and Plus-Plus follow-up

- Add sidebar Left/Right positioning if still desired after convergence.
- Continue RiqatonyDesk ↔ Marko Plus implementation convergence only through explicitly reviewed items.
