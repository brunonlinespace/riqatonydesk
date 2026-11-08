# RiqatonyDesk 1.0.0 — Final source edition (2026-11-01)

The existing `1.0.0-x19.9` source is promoted directly to final `1.0.0`. The only changes are application/packaging version metadata, release-specific verification assertions and documentation of the version promotion. The previously approved Find/Replace behavior and AppImage desktop-entry validator are retained exactly, as are all earlier RTF, file-safety, workspace, theme, and icon implementations.

The independently protected GitHub-root README is preserved with only its approved current-release field changed. Historical source fingerprints and previous release notes are retained. This promotion does not certify a native Fedora AppImage build or interactive GUI testing; those require a native test run.

---

# RiqatonyDesk 1.0.0-x19.9 — Find/Replace and AppImage build correction (2026-11-01)

- Find/Replace commands in the Desk shell were already routed to `toggle_find_panel`; the embedded editor was not. Both editor actions now use the toggle and the editor records the selected mode so repeat clicks close regardless of focus, matching Riqatony Pad x16.9.
- The root GitHub README removes exactly the previously identified blank line 2 and `Current source edition` line 3. The original user-authoritative README fixture and SHA-256 remain untouched. Current release is x19.9.
- Fedora build failed in AppDir assembly because its checker demanded lowercase `riqatonydesk` when the official desktop entry contains `StartupWMClass=RiqatonyDesk`. Correct checker casing and run desktop/AppStream checks before PyInstaller as well as after AppDir assembly.
- Scope: three requested changes plus dedicated QA, source manifests and release metadata only; untouched historical QA remains archived.
- QA performed: headless behavior harness against the actual editor methods, real builder validation with positive/negative desktop-metadata cases, source QA, complete archive manifest check. Full PyQt6/Fedora AppImage execution remains for the Fedora host.

---

# RiqatonyDesk 1.0.0-x19.8 — AppImage QA compatibility hotfix (2026-11-01)

- Correct the current Qt workspace integration runner to expect **Edit** on the Dashboard document card; the application renamed the action from Open in x19.2.
- Preserve the historical x13.3 workspace-integration QA file, its original x13.4 import adapter and the x19.7 migration check unchanged. Apply only the approved import-path and Dashboard-label substitutions in memory for current Qt execution.
- Make the current x19.8 adapter run in the AppImage builder's PyQt6 release gate, and validate its exact transformation statically even when Qt is unavailable.
- No changes to runtime/editor code, dashboard behavior, icons, file safety, or the protected GitHub README outside its two permitted current-version fields.

---

# RiqatonyDesk 1.0.0-x19.7 — QA directory consolidation (2026-11-01)

- Move `release_check.py`, `shutdown_check.py`, and their package initializer from `tools/` into `qa/`, removing the empty `tools/` directory.
- Update the active static-release runner, AppImage builder and current developer documentation to the new QA paths.
- Preserve historical QA scripts and version-pinned fingerprint JSON records without modifying their contents.
- Keep runtime/editor source and all icon assets unchanged. Protect the GitHub README, changing only its two designated current-version fields.

---

# RiqatonyDesk 1.0.0-x19.6 — Protected README and Halcyon asset correction (2026-11-01)

- Replace the GitHub README with the user-approved updated copy, changing only current-version metadata. Save the supplied bytes as the independently pinned README authority.
- Rename dark Halcyon `impport-file.png` to `import-file.png` without modifying the PNG contents. Validate that both Halcyon themes contain the exact same 144 filenames.
- Preserve all other icon families, command wiring, configuration and editor functionality.

---

# RiqatonyDesk 1.0.0-x19.5 — Halcyon icon family and GitHub README protection (2026-11-01)

- Add Riqa Icons Halcyon to Settings → App Icons, using `assets/ribbon-icons-aero`. The new radio choice has no icon or toolbar command.
- Preserve the previous icon families, family settings, toolbar controls, editor and file-handling behavior.
- Restore the root GitHub README to its protected wording, allowing only the current-version field(s) to change. Archive recovered historical README changes in `docs/history/`; add a mandatory reference-checksum QA gate.
- Static source gates passed; live KDE/PyQt6 GUI behavior remains unverified.

---

## Earlier release notes (x19.4)

## 1.0.0-x19.4 — App Sidebar parent icon correction (2026-10-31)

- In the Settings AppMenu, the **App Sidebar** submenu parent uses the dedicated `sidebar-settings.png` icon from the selected Riqa family and current theme, not the Show Sidebar dock-side icon.
- The shared **Show Sidebar** QAction remains dynamic: `show-sidebar.png` when docked left, `show-sidebar-right.png` when docked right. This shared action serves both the Ribbon toggle and the AppMenu's checked Show Sidebar entry; its checked/visibility state is unchanged.
- No icon artwork, other action bindings, sidebar position/visibility behavior, RTF editor, or file operations are modified. Live KDE GUI confirmation remains outstanding.

## 1.0.0-x19.3 — Heritage icon corrective patch (2026-10-31)

- Replace only `ribbon-icons-original/{dark,light}/external-editor.png` and `launch-last-file.png` with the four PNGs supplied in `ribbon-icons-original-patch.zip`.
- Harmony, Humility, all other Heritage icons, editor and workspace behavior remain unchanged. Family selectors and command wiring remain as in x19.2.
- Historical x19.2 asset checks stay archived; x19.3 QA checks the exact four replacements and all other icon hashes against x19.2. Live GUI validation remains outstanding.

## 1.0.0-x19.2 — Desk icon inventory and command wiring (2026-10-31)

- The three user-provided icon ZIPs are authoritative: Harmony, Humility and Heritage each contain exactly 144 dark and 144 light PNG files. Removed legacy, unmatched files from x19.1; no fallback copies survive in these families.
- Dashboard document-card **Open** becomes **Edit** with `file-launch.png` (list and grid modes; view-only action unchanged).
- Dock to Left and Dock to Right use `dock-left.png` and `dock-right.png` on their shared Ribbon/AppMenu actions. Show Sidebar uses the left/right-specific `show-sidebar.png` or `show-sidebar-right.png` as the configured docking side changes.
- Import File uses `import-file.png`. AppMenu groups App Dashboard, App Launch Screen and App File Launch use their dedicated `app-dashboard.png`, `app-launch-screen.png` and `file-launch.png`, rather than mirroring the currently selected submenu command.
- Tabs Enabled and Tabs Disabled use `tabs-enabled.png` / `tabs-disabled.png`, including the Ribbon state toggle. The three icon families and earlier x19.1 heading/link/Find/unsaved policy wiring remain unchanged.
- Ribbon/Retro toolbar-layout icons remain deferred. No RTF editor, Word Wrap or horizontal-rule behavior is changed.

## 1.0.0-x19.2 — Desk icon inventory and command wiring (2026-10-31)

- The three user-provided icon ZIPs are authoritative: Harmony, Humility and Heritage each contain exactly 144 dark and 144 light PNG files. Removed legacy, unmatched files from x19.1; no fallback copies survive in these families.
- Dashboard document-card **Open** becomes **Edit** with `file-launch.png` (list and grid modes; view-only action unchanged).
- Dock to Left and Dock to Right use `dock-left.png` and `dock-right.png` on their shared Ribbon/AppMenu actions. Show Sidebar uses the left/right-specific `show-sidebar.png` or `show-sidebar-right.png` as the configured docking side changes.
- Import File uses `import-file.png`. AppMenu groups App Dashboard, App Launch Screen and App File Launch use their dedicated `app-dashboard.png`, `app-launch-screen.png` and `file-launch.png`, rather than mirroring the currently selected submenu command.
- Tabs Enabled and Tabs Disabled use `tabs-enabled.png` / `tabs-disabled.png`, including the Ribbon state toggle. The three icon families and earlier x19.1 heading/link/Find/unsaved policy wiring remain unchanged.
- Ribbon/Retro toolbar-layout icons remain deferred. No RTF editor, Word Wrap or horizontal-rule behavior is changed.

# RiqatonyDesk 1.0.0-x19.1 — Riqa icon-family re-patch (2026-10-31)

- Install the supplied light/dark PNG artwork for **Riqa Icons Harmony** (`ribbon-icons`), **Riqa Icons Humility** (`ribbon-icons-classic`), and **Riqa Icons Heritage** (`ribbon-icons-original`). Existing asset names absent from the supplied packs are retained for command compatibility. The saved icon-family keys (`new`, `classic`, `original`) and default `new` remain unchanged.
- Align AppMenu, Ribbon/Retro family-selector labels and tooltips; `icons-legacy.png` now identifies the Heritage selector, with the corresponding Harmony/Humility selector icons.
- Re-wire `find.png` to Find; `heading-group.png` to the Paragraph Style AppMenu group; `heading-0.png` through `heading-6.png` to Normal Paragraph/Heading 1–6; and `link-group.png` to the Link AppMenu submenu.
- Re-wire `dirty-duplicate-policy.png` and `dirty-external-policy.png` to their respective unsaved-changes policy submenus.
- **Not in this pass:** `toolbar-tabbed.png` / `toolbar-classic.png` wiring, other mismatched icons, changes to editing, file operations, or toolbar behavior.
- Static source/icon QA only; live Fedora KDE GUI validation is still required.

## 1.0.0-x19.0 — Harmony default Ribbon icons

- Replace the default `assets/ribbon-icons` PNG collection with the 296 supplied Harmony images (148 per light/dark variant).
- Rename the user-facing default family from Rico Icons Modern to Rico Icons Harmony, while retaining stored selection key `new` to preserve existing preferences.
- Preserve all Classic and Legacy PNGs, app icons, command routing, Ribbon layout, editor mechanics, save behavior, grapheme counter and backing-warning handling.
- No SVG assets are introduced. Verify complete image coverage and archived source preservation. Live Qt visual validation remains outstanding.

## 1.0.0-x16.7 — Unicode characters, backing notifications and PNG-only icons

- Count extended grapheme clusters in visible RTF document content using the RiqatonyPad x13.5 per-block revision cache; preserve insert/overwrite, zoom, document safety limits and layout.
- Both repository and direct file-monitor events now report only genuine backing-state transitions through the EditorPage, with explicit backing-file warning identity and selective resolution.
- Remove 642 packaged SVG icon sources. Preserve all 652 PNG assets byte-for-byte; active icon QA now validates PNG-only assets.
- Preserve RTF codec, save/Save As, existing monitoring/scanning, drag/drop, application commands and unrelated functionality.
- Static verification and Qt protocol-double testing do not substitute for live Fedora KDE/PyQt6 testing.

## 1.0.0-x16.6 — Critical-message recovery and filename-suggestion correction

- Correct the embedded RTF editor critical-message latch on backing-file recovery and explicit clearing. Change both managed and embedded protected Save Version As suggestions from `- Rico Version` to `- Desk Version` while preserving numbering, extension and collision avoidance.
- Preserve existing document operations, message wording/durations, banners, drop handling, layout and workspace behavior.

## 1.0.0-x16.5 — Desk message-conventions convergence

Shared four-second transient status convention and persistent unresolved warnings; filenames on saves, action-specific duplicate/delete/rename wording, sentence-final punctuation, product identity and duplicate-message correction. No changes to routing, editor features, geometry or drag-and-drop.

### 1.0.0-x16.4 — Drop-highlight stylesheet guard (2026-10-24)

- Carry over MaqaronyDesk x18.5's verified fix to RiqatonyDesk's main Dashboard and Folder Dashboard only.
- `_set_drop_highlight()` applies the same original stylesheet only if it differs from `self.styleSheet()`. Repeated drag-move events do not cause redundant Qt stylesheet repolishing; highlight colour, border width, and clearing remain unchanged.
- Drag/drop acceptance, RTF paths, copy action, destination routing, sidebar, layouts, editor, file operations, and messaging remain unchanged.
- Exact x16.3 production-preservation comparison and Qt-free repeated-event regression tests. Live KDE/Wayland confirmation still required.

### 1.0.0-x16.3 — Editor message cross-pollination (2026-10-24)

- Add local `Loaded {filename}` feedback after successful RTF loading (3000 ms), retaining the existing compatibility-warning priority without duplicating it.
- Add `Clipboard does not contain text that can be pasted.` (3500 ms) when Paste as Plain Text receives no text, following RiqatonyPad x13.2.
- Report actual editor Insert/Overwrite key toggles locally (2500 ms), following RiqatonyPad x13.2; leave indicator updates unchanged.
- Add once-per-transition local notifications when the targeted workspace file monitor detects an externally missing or changed backing file, following RiqatonyPad x13.2. Preserve persistent banners and exclude in-app file-action checks.
- No change to existing messages, editor/layout geometry, RTF semantics, workspace messages or document safety.
- Source-level and mocked-runtime QA; Fedora KDE/PyQt6 live verification remains outstanding.

### 1.0.0-x16.2 — Embedded editor message ownership (2026-10-23)

- Route clipboard rejection to the originating RTF editor rather than Qt's central status bar; preserve existing text, 5000 ms timeout, and beep.
- Show existing Save and Save Version As confirmations in the originating editor and add successful ordinary Save As confirmation; do not duplicate central feedback.
- Remove managed-page Locked Mode synchronization notices: the embedded editor already announces user-triggered Locked Mode changes locally.
- Preserve central workspace messages, status-bar geometry, indicator layout, editor algorithms, document lifecycle, and all historical QA.
- Static release verification only; Fedora KDE/PyQt6 live routing checks remain outstanding.

### 1.0.0-x16.1 — Embedded editor status-bar correction (2026-10-23)

- Two visible editor widgets: existing expanding message label on the left and a single permanent indicator on the right.
- Right-hand indicator: `Insert · Chars 1,240 · 100%` (illustrative), with Zoom anchored last and existing number formatting unchanged.
- No independent field-width calculations; message timer, tooltip and signal forwarding are unchanged.
- Status-bar styling, height, host editor layout and Desk workspace status bar are untouched.
- Runtime Qt/Fedora KDE geometry validation remains outstanding.

### 1.0.0-x16.0 — Embedded editor status-bar order (2026-10-23)

- Reorder existing embedded editor-status widgets to Insert/Overwrite → total Chars → numerical Zoom % → independent Message. No added or removed widgets.
- Retain fixed measurements, existing embedded status-bar height, spacing, character grouping, update mechanics and independent status-message routing.
- No changes to the Desk workspace status bar, parent-window geometry, editor methods, RTF support or Dashboard.
- Static release gate only; live Fedora KDE/PyQt6 geometry testing remains outstanding.

### 1.0.0-x15.3 — Corrective Dashboard visibility batching (performance only)

- Batch retained-card hide/show transitions with both Dashboard layouts temporarily suspended and host repainting disabled. Restore each layout and host to its previous enabled state using a `finally` block, then use the existing geometry invalidation once.
- Targets the measured x15.2 startup/scan-completion and search-reset regressions without changing x15.2 ordered-grid retention, widget membership, filtering semantics, sort keys, file management, or x15.0/x15.1 improvements.
- Historical x15.2 QA and releases are preserved. Current-edition headless QA validates batched visibility, search reset, unchanged sort, exception-safe restoration, full source preservation and embedded Health Check manifest.
- This source-only environment cannot validate the actual Fedora KDE/Wayland performance recovery; compare x15.2 and x15.3 with Desk Health Check 2.1 before accepting the performance objective.

### 1.0.0-x15.2 — Dashboard search and sort layout optimisation (performance only)

- Search changes hide or reveal retained cards in-place instead of removing and reinserting both complete List/Grid collections.
- Keep widget layouts in repository sort order independently of the current search. Reorder only when the actual document order or membership changes; a no-op sort does not rebuild layouts. Preserve the historical full-detach method as an unused compatibility hook for Desk Health Check 2.1.
- Reuse grid layout items while reordering; exclude hidden cards from grid wrapping and minimum-size geometry, matching native QVBoxLayout visibility semantics.
- Preserve all x15.1 geometry caching and x15.0 shutdown behaviour, Dashboard actions, file lifecycles, folder dashboards and loading/scanning policy.
- Qt runtime performance still requires Fedora KDE testing through Desk Health Check 2.1.

### 1.0.0-x15.1 — Dashboard List/Grid geometry (performance only)

- Cache active Dashboard page geometry hints by viewport width. Invalidate when Qt requests a layout/style change and after filtering/sorting the cards.
- Remove duplicate geometry notifications when switching List/Grid, retaining the existing QWidget collections and QStackedWidget behaviour.
- Keep x15.0 shutdown optimisation and all file/RTF/Markdown lifecycle behaviour unchanged. No new Dashboard scope or lazy cards.
- Static validation only here; actual Fedora KDE performance requires measurements.

# RiqatonyDesk 1.0.0-x15.0 — Shutdown Dashboard rebuild avoidance (2026-10-21)

- Avoid the unconditional Dashboard set_loading(False) call on successful shutdown, because that call rebuilds both Dashboard card layouts immediately before exit.
- Preserve navigation loading cleanup, the closing dialog, saved workspace/preferences, unsaved-document confirmation, scanner cancellation timeout and explicit process exit.
- On scanner-stop failure, restore the normal Dashboard loading state before returning to the interactive window; this retains the previous rollback path.
- Introduce source-root `desk-health-check.json` matching the existing Suite compatibility metadata, using the Desk Health Check 2.0 family adapter contract.
- No card painting, search, sort, scan, editor, folder Dashboard, preferences or document-lifecycle changes. Historical QA and archived notes are unchanged.
- Static source and compatibility tests pass; Fedora KDE/PyQt6 runtime and AppImage performance testing remain required.

---

# RiqatonyDesk 1.0.0-x14.0 — Main Dashboard palette card appearance (20 October 2026)

- Apply Suite Pythoine 0.11.2 palette-based, antialiased Button/Mid rounded panel painting to the main Dashboard List/Grid cards only.
- No selected-card visual highlight; keep existing buttons, commands, layouts, interaction and document lifecycle unchanged.
- Folder Dashboard retains its exact previous card presentation and imports. No theme.py or rich_text_support.py changes.
- Add a current-edition source-preservation and Dashboard-only appearance gate; all historical QA, notes and fingerprints unchanged.
- GUI and AppImage rendering still requires live Fedora KDE verification.

---

# RiqatonyDesk 1.0.0-x13.5 — Theme module naming alignment (20 October 2026)

- Derived directly from RiqatonyDesk 1.0.0-x13.4. The existing `widgets/rico_theme.py` is relocated as `widgets/theme.py` with identical file bytes.
- Only direct theme-module imports, current release identity, active QA and packaging metadata are adjusted. Palette colours, System/Light/Dark choices, settings, editor behaviour and file safety are unchanged.
- `rich_text_support.py`, standalone Pads, Plus sources, and archived QA/release records remain untouched.
- Live Fedora KDE/PyQt6 and AppImage testing is still required.

---

# RiqatonyDesk 1.0.0-x13.4 — QA historical-integrity correction (2026-10-19)

- Corrective QA-only edition derived from unchanged 1.0.0-x13.3 production implementation. No editor, codec, workspace, file-safety, UI, method, or module renames.
- Restored exactly 22 previously modified historical QA scripts byte-for-byte from the authoritative 1.0.0-x11.2 source; original historical fingerprints and assertions are not modernised in place.
- Preserved the working x13.3 current-path test variants as new edition-specific adapters under `qa/current_x134/`. The current gate runs those variants with their original QA source-directory context and leaves restored historical scripts unchanged.
- Added a current-only execution wrapper that corrects the moved shortcuts-dialog import for the PyQt6 workspace integration suite in memory; the historical integration script remains unmodified. The release gate runs that suite when PyQt6 is available, and flags its absence otherwise.
- Added x13.4 frozen-source provenance and current QA checks. Historical notes, previous release checklists and earlier source states remain untouched.
- Live Fedora KDE/PyQt6 and AppImage tests still require validation on the target system.

---

# RiqatonyDesk 1.0.0-x13.3 — Help / Quick Tour extraction (2026-10-19)

- Based directly on 1.0.0-x13.2; extracted exactly five unmodified MainWindow Help methods to `widgets/window_parts/help_actions.py` as `HelpActionsMixin`.
- Existing shortcut catalogue, searchable shortcuts dialog, seven-page Quick Tour and footer settings, bundled RTF documentation and About dialog remain identical. Existing GitHub/Issues actions remain owned by MainWindow.
- MainWindow retains Help actions/menu, Qt/dialog ownership, configured settings, file handling, editor, workspace and layout behaviour; no unrelated code extraction.
- Added current x13.3 provenance, headless Help and earlier-contract replay checks. All historical QA scripts, fingerprints and release records remain untouched.
- Live Qt/Fedora KDE and AppImage behaviour remain to be validated on the target system.

---

# RiqatonyDesk 1.0.0-x13.2 — Layout Controls method extraction (2026-10-19)

- Derived exclusively from RiqatonyDesk 1.0.0-x13.1. Moved exactly thirteen existing MainWindow layout-control methods into `widgets/window_parts/layout_controls.py` (`LayoutControlsMixin`), without changing their method bodies.
- MainWindow retains existing splitter/widgets, QAction and Qt-signal ownership and temporary Focused Mode state. Riqatony's sidebar icon synchronisation and RTF status propagation remain unchanged.
- Added current-edition preservation and headless layout QA. Historical QA scripts, method fingerprints, source references, release notes, changelog entries and earlier checklists remain unchanged.
- Navigation History, Help/Quick Tour, editor/RTF codec, file actions, workspace lifecycle and watchers are untouched. Live Fedora KDE and AppImage validation is still required.

---

# RiqatonyDesk 1.0.0-x13.1 — Navigation History method extraction (2026-10-19)

- Derived exclusively from RiqatonyDesk 1.0.0-x13.0. Relocated exactly six existing MainWindow navigation-history methods into `widgets/window_parts/navigation_history.py` (`NavigationHistoryMixin`), with identical method bodies.
- MainWindow retains `eventFilter()`, Mouse Back handling, history state and Qt signal connections. Coalesced history recording, the 64-entry limit, workspace-path validation and document/Back routing retain their current semantics.
- Added new current-edition preservation and headless navigation QA. All earlier source/QA fingerprints, historical records, and previous release checklists are preserved unchanged.
- Layout Controls, Help/Quick Tour, RTF editor, file actions, workspace lifecycle and watchers are untouched. Live Qt/Fedora KDE/AppImage validation remains necessary.

---

# RiqatonyDesk 1.0.0-x13.0 — Document Tabs method extraction (2026-10-19)

- Derived exclusively from RiqatonyDesk 1.0.0-x12.1. Extracted 25 existing Document Tabs methods into `widgets/window_parts/document_tabs.py` (`DocumentTabsMixin`).
- QTabBar construction, signal connections, QAction ownership, settings/action routing and document lifecycle remain with the existing MainWindow. Existing `riqatonydesk://navigation/` tab tokens are unchanged.
- Added a current x13.0 preservation gate and current-path identity/contract checks. Every historical QA file, method fingerprint and earlier release record remains unmodified.
- Navigation History, Layout Controls, Help/Quick Tour and all editor/file-safety mechanisms are outside this release. Live Qt and AppImage checks still require Fedora KDE validation.

---

# RiqatonyDesk 1.0.0-x12.1 — Workspace and dialog folder convergence (2026-10-19)

- Derived exclusively from RiqatonyDesk 1.0.0-x12.0. Four existing workspace widgets moved under `widgets/workspace/`, and six application dialogs under `widgets/dialogs/`.
- Adjusted only production module imports and three Dashboard/card/folder Dashboard asset lookup anchors. The RTF editor, document lifecycle, file safety, workspace services, persisted preferences and all interface behaviours retain their x12.0 implementation.
- Added an x12.1 frozen-source preservation gate and current-path checks. All x12.0 and older QA, previous release notes, changelog entries, historical files and fingerprints remain unmodified.
- Static checks do not substitute for runtime Qt/Fedora KDE/AppImage validation.

---

# RiqatonyDesk 1.0.0-x12.0 — Editor folder convergence (2026-10-19)

Stage 1 of the Desk↔Pad structural convergence moves the seven existing embedded-RTF editor helper modules into `widgets/rwpyn/`, consistent with RiqatonyPad's editorial package. Existing editor methods and lifecycle contracts remain intact; only imports and the resource resolver's module-depth anchor change. Current QA and packaging references are retargeted, with a new x12 preservation gate. Historical changelog and release-note sections below remain unchanged.

Live Qt/GUI and AppImage behaviour requires validation on the intended Fedora KDE host.

---

# RiqatonyDesk 1.0.0-x11.2 — Historical-record and packaging-metadata corrections (2026-10-17)

This correction restores the exact original Rico Plus release history beneath the RiqatonyDesk release entries. The older release names, versions, descriptions and chronology are preserved without modification. The current AppStream release description now identifies the actual x11.2 work. Packaging and QA shell-script executable permissions are restored without changing their content.

Windows configuration-path support is explicitly deferred. No editor, RTF codec, workspace, Ribbon, file handling or runtime architecture is changed.

---

# RiqatonyDesk 1.0.0-x11.1 — Identity migration

This version applies Rebrand Contract v1.1 to the authoritative Rico Plus 1.0.0-x10.0 source.
The public product name, technical application identity, packaging metadata, application artwork and independent configuration namespace are renamed to RiqatonyDesk.
The established Rico Plus RTF codec, editor mixins, workspaces, external-change safety, Ribbon, command icons and x1–x10 extraction architecture are preserved.
No Rwpyn abstraction, wrapper, relocation or engine/codec rewrite is introduced.
The preceding release notes remain archived at `docs/history/Rico-Plus-1.0.0-x10.0-RELEASE_NOTES.md`.

---

## Rico Plus 1.0.0-x10.0 — Editor file-lifecycle extraction only (2026-10-16)

Moved existing editor-owned file I/O, Save/Save As and related lifecycle methods into editor_lifecycle.py, without changing their definitions or operation; full original editor AST parity checked.

## Rico Plus 1.0.0-x8.0 — Embedded-editor commands, icons and appearance extraction only (2026-10-16)

- Relocated the existing 23 embedded-editor command/icon/appearance methods into `widgets/editor_commands_appearance.py` without changing their parsed definitions.
- Retained the workspace-owned shell and menu registry, including different preferences, file lifecycle and appearance contracts.
- No shared-runtime dependency, new functionality or opportunistic fixes. Previous x1–x6 stage method parity preserved; host GUI/build validation remains necessary.

## Rico Plus 1.0.0-x6.0 — Preferences and new-document defaults extraction only

Original preferences and new-document defaults extracted without changes; historical release details retained below.

## Rico Plus 1.0.0-x5.0 — Printing, PDF and document information extraction only (2026-10-16)

Relocated ten existing page setup, print/PDF, file-size/date and Properties methods unchanged into `widgets/editor_printing.py` using the same host method names. Relocated their existing supporting constants and functions without changing ASTs and preserved imports through the editor host. All previous x1–x4 method definitions remain unchanged. No user-visible feature, file lifecycle, RTF codec or runtime sharing changes. Live Qt and actual packaged builds still require host verification.

## Rico Plus 1.0.0-x4.0 — Find/Replace and editor-view extraction only (2026-10-16)

Moved 40 existing Find/Replace, search-state, zoom, word-wrap and tab-width methods into an application-local `widgets/editor_search_view.py` mixin without altering any method definition. The existing search cap moved with those methods; all previous stage method contracts remain intact. No feature, user-facing behaviour, configuration, RTF/file lifecycle or workspace changes. Live Qt and actual packaged builds remain for target-host verification.

## Rico Plus 1.0.0-x3.0 — insertion and clipboard extraction only (2026-10-16)

Moved 39 existing symbols, image/link/table, clipboard, line editing, and date/time insertion methods verbatim to `widgets/editor_insertion.py`. Moved their three exclusively used image safety limits and two unchanged helper functions into that module and imported them back into the host. Workspace controllers, window, editor page, RTF codec and file-lifecycle behaviour remain untouched. No shared runtime dependency or functionality changes. Qt runtime and AppImage/Windows builds remain for host verification.

## Rico Plus 1.0.0-x2.0 — formatting extraction only (2026-10-16)

Relocates 43 existing rich-text formatting methods into an application-local `editor_formatting.py` mixin. No method-body changes, cross-application shared dependency, new functionality, or altered document/file-lifecycle behaviour. Preserves x1.0 widget extraction; updates source packaging and location-aware regression checks. Live Qt runtime and AppImage/Windows builds must be verified on equipped hosts.

# Rico Plus 1.0.0-x1.0 — Editor widget extraction

Based on 0.2.24. Moved `SafeTextDocument` and `RichTextEdit` verbatim to `editor_widgets.py`; retained public import names and application-specific widget behaviour. Updated only required module loading, packaging, release identity and verification wiring. No editor features or file-lifecycle changes.

---

# Rico Plus 0.2.24 — App Settings parent icon synchronization

Rico Plus 0.2.24 is limited to synchronizing three AppMenu parent icons with their currently selected radio options.

- **App Dashboard** mirrors **List View / Grid View**.
- **App Launch Screen** mirrors **Dashboard / Last File**.
- **App File Launch** mirrors **Tabs Enabled / Tabs Disabled**.
- The existing radio actions remain the sole authority for selection, behavior, and persistence.
- Theme/icon-family refreshes reapply the currently selected radio icon to each parent.

No Dashboard behavior, launch behavior, tab/file-launch behavior, workspace/setup wizard, sidebar behavior, RTF/editor, file-lifecycle, formatting, or unrelated logic is changed.
