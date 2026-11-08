- 0.1.7 is the current managed sidebar-drop hotfix. It extends the 0.1.6/Marko Plus 0.2.4 explicit drop-routing contract so internally managed files use the same sidebar destinations: folder row → folder, file row → containing folder, empty tree → Workspace root; Dashboard-button root moves and same-folder no-op protection remain unchanged. 0.1.6 remains the drag/drop reconciliation baseline.
- 0.1.3 is the current Workspace-switch method-convergence release against Marko Plus 0.2.1. It adopts the stronger common validation order (target directory/writability before dirty-close prompting), refreshes active-Workspace title/context, preserves scanner-stop watcher recovery, and completes successful switches with common action-state refresh plus `Opening Workspace: <name>` feedback. The successful 0.1.2 external-file lifecycle remains unchanged.
- 0.1.2 is the current external-file lifecycle convergence release against Marko Plus 0.2.1. It fixes explicit startup-open bookkeeping so external RTF launches do not create an unwanted Dashboard tab, adopts the defensive resolved pending-open comparison, starts external launches in transient Locked Mode + Focused Mode, adds Open External File... with New Window... below it, and applies the agreed File/More Actions AppMenu alignment. Workspace-switch convergence remains deferred to 0.1.3.
- 0.1.1 is the current Phase 1 closure/alignment release. RiqatonyDesk 0.1.0 remains the substantive Phase 1 convergence baseline against Marko Plus 0.1.10: it hardened root-Dashboard touch, restored import-only external RTF drop routing, backported watcher recovery and Refreshing/Refreshed semantics, and moved desktop association to single-file `%f`. RiqatonyDesk 0.1.1 changes only stale runtime QA plus the agreed View separator and two App Settings policy flyouts; no Phase 1 runtime architecture is otherwise changed.
- 0.0.8 is the prior accepted release and branches directly from 0.0.6. The 0.0.7 experiment is rejected. 0.0.8 adds only the Ricopad-aligned on-demand Words count to Properties; no other runtime behavior is intentionally changed.
- 0.0.5 is the preceding command-convergence release. It aligns the four remaining shared Rico H/P shortcuts with Ricopad 1.0.0, applies those mappings in both the shell and embedded editor, and orders View Control/AppMenu View as Full Screen, Show Status, Show Sidebar.
- 0.0.4-r9 is the preceding external-change convergence/safety correction. It preserves the r8 baseline while making EditorPage the managed conflict-UX authority, protecting Save As during unresolved external-change conflicts, and reserving replacement of the changed source for explicit Overwrite.
- 0.0.4-r8 is the earlier AppStream metadata-only packaging hotfix on the canonical 0.0.4-r2 application baseline. It preserves 0.0.4-r7 production behavior, adds structured developer metadata, and keeps only the current release in AppStream metadata so historical experimental version ordering cannot fail validation; full history remains in CHANGELOG.md.
- 0.0.4-r7 was the AppImage release-gate hotfix on the canonical 0.0.4-r2 application baseline. It preserves 0.0.4-r6 production behavior and changes only source inventory handling so generated `riqatony_desk/build/` and `riqatony_desk/dist/` artifacts are ignored when the authoritative release gate is rerun inside the build venv.
- 0.0.4-r6 is the QA/build-metadata hotfix that corrected the stale workspace-integration Refresh Workspace runtime assertion to the live Ctrl+Shift+F5 contract; production editor/RTF/workspace behavior remained unchanged. r5 was not reused because that identifier already belongs to an earlier historical RiqatonyDesk release.
- 0.0.4-r4 modernized the Suite Pythoine portable/AppImage contract and aligned workspace-integration runtime assertions with the current tabbed shell container; production editor/RTF/workspace behavior remained unchanged.
- 0.0.4-exp7-r2 is based directly on 0.0.4-exp7-r1. It fixes About-link legibility in Light theme by explicitly defining Light `Link`/`LinkVisited` palette roles as `#0068A6` and applying the About link palette before RichText HTML parsing in both Plus and embedded About paths; all exp7-r1 wording and runtime behavior are unchanged.
# RiqatonyDesk Project Memory
- 0.0.4-exp7-r1 is based directly on 0.0.4-exp7. It is a Tour/About-only polish: the Tour documents context-sensitive Ctrl+Tab/Ctrl+Shift+Tab, Ctrl+T and Ctrl+W behavior, explains Focused Mode, and replaces deprecated theme/canvas sync copy with the current independent App Theme/Dark Editor model; About adds linked PyWordpad credit, the full Microsoft WordPad name, and blue new/visited links on light palettes. The exp7 Save As/watcher fix and runtime behavior are unchanged.
- 0.0.4-exp7 is based directly on 0.0.4-exp6-r1. It makes managed Save As transactional: the target is written independently before the editor adopts the new path; the page/repository rebinds to the target before the editor is marked clean; a watcher identity guard prevents transitional path/signature mismatches from becoming false reload warnings. The original source bytes remain untouched. Marko Plus was audited and already uses a safe independent `save_copy_to()` pathway, so no Marko Plus change is required.
- 0.0.4-exp6-r1 is based directly on 0.0.4-exp6. It restores the Ricopad-style dirty `*` in the main window title even when tabs are disabled, remaps Text Colour… to Ctrl+Shift+C, aligns App Theme order to Light/Dark/System, applies the reviewed Insert AppMenu/Ribbon ordering, and adds a persistent “Don't ask again when disabling Locked Mode” option. The exp6 highlight fix and unrelated RTF/workspace/theme/icon behavior remain unchanged.
- 0.0.4-exp6 is based directly on 0.0.4-exp5-r1. It fixes highlight clearing at selection boundaries: character-format state is read from the actual selected character, automatic highlight contrast foreground/tag properties are fully removed on clear, explicit user foreground colours are preserved, and the supplied normal/highlighted/highlight-removed RTF files are retained as the regression corpus. The RTF codec and unrelated UI/workflow code are unchanged.
- 0.0.4-exp5-r1 is based directly on 0.0.4-exp5. It is an AppMenu-only cleanup: View removes duplicate Focused Mode and its redundant separator; Workspace(s) places Open / Manage Workspaces… after the live workspace listing and before New Window…; Format adopts the reviewed grouping and removes only the standalone Clear Highlight entry while retaining Clear Highlight inside Highlight Colour…. The exp5 independent App Theme/editor-canvas model is unchanged.
- 0.0.4-exp5 is based directly on 0.0.4-exp4-r3. It removes editor/app theme synchronization: new profiles default to Light app + Light editor; App Theme controls chrome only; Dark Editor controls canvas only. Existing valid App Theme and explicit canvas boolean choices are preserved, missing/null/malformed canvas values migrate to Light, the legacy `editor_canvas_follows_app_theme` key is removed, and the managed Ricopad component no longer reads/writes its own `editor_canvas_theme` preference.
- 0.0.4-exp4-r3 is based directly on 0.0.4-exp4-r2. It moves Advanced from Home to Insert, returns New Document Defaults… to View → Editor Miscellaneous, puts Focused Mode first in Settings, adopts the reviewed Configure Editor/App Settings layouts, reorders App Icons to Modern/Classic/Legacy, and binds the shared selector actions through the active family (Modern `icons-new`, Classic `icons-classic`, Legacy `app-icons`).

## Identity

- Product: RiqatonyDesk 0.1.7
- 0.0.4-exp4-r3 is based directly on 0.0.4-exp4. It renames the displayed icon families Rico Icons New → Rico Icons Modern and Rico Icons Original → Rico Icons Legacy while preserving technical keys/folders and keeping Modern (technical key `new`) as the default. File → This Session gains Previous File/Next File using the established Previous/Next artwork, the sidebar gains Refresh Workspace immediately below Dashboard, and Highlight Colour retains its in-dialog Clear Highlight action. Legacy is now available on the Configure Ribbon alongside Modern and Classic.
- 0.0.4-exp4 is based directly on 0.0.4-exp3. It replaces the Classic/New command-icon assets with the supplied improved sets and adds complete Rico Icons Original assets. Original is selectable from Settings → App Icons only; the Configure Ribbon remains Classic/New-only and New remains the fresh-profile default.
- 0.0.4-exp3 is based on the complete 0.0.4-r5 source and is a RiqatonyDesk-only Delete Line correctness experiment. Non-empty blocks are deleted once; explicit neighbour/separator character deletion is retained only for empty blocks. Ricopad is intentionally untouched.
- 0.0.4-r5 is based strictly on 0.0.4-exp1-r4 and restores only internal workspace RTF drag-and-drop moves (Dashboard/Folder Dashboard/tree → sidebar folder, plus Dashboard/root target), using the existing FileActions.move_document()/repository path. External application-file drops remain retired; App File Launch tabs behavior is unchanged.
- 0.0.4-exp1-r4 adds contextual tab keyboard navigation: Ctrl+T enables tabs if needed and opens/reuses the active file's parent-folder temporary tab (Workspace-root files fall back to Dashboard); Ctrl+W closes the active document with existing unsaved protection and lands in that same folder context when tabs are enabled, while retaining Dashboard behavior when tabs are disabled; Ctrl+Alt+Shift+T disables tabs without closing documents.
- Toolkit: Python 3 and PyQt6
- 0.0.4-exp1-r2 retains the existing `EditorManager`/`QStackedWidget` document-tab architecture and adds one ephemeral navigation tab for Dashboard/folder-dashboard views while Tabs Enabled is active. The navigation tab is rebound between Dashboard/folders and disappears as soon as an RTF document is selected; persistent document tabs remain untouched.
- exp12 restores Ricopad-style touchscreen Ribbon panning through Qt `QScroller.TouchGesture`; stationary taps remain ordinary button/selector taps, while finger drags pan horizontally.
- exp10 softens the explicit Light application palette to the approved neutral-gray reference: Window `#D4D4D4`, editable Base `#F4F4F4`, Button `#E4E4E4`, with the Rico brick accent retained. System and Dark themes are unchanged.
- exp9-r7 restores **F3** to Find Next, maps **Ctrl+Shift+L** to Bullet List, moves unbound **Launch New Window…** between Page Setup and Exit, and makes the Keyboard Shortcuts catalogue recursively complete (including nested formatting shortcuts).
- exp9-r6 assigns **F3** to **New Window**; Find Next remains available from the Find bar without F3.
- exp9-r5 maps **Font…** to **Ctrl+Shift+F**, **Increase Font Size** to **Ctrl+Shift+]**, and **Decrease Font Size** to **Ctrl+Shift+[**.
- exp9-r4 renames **Show File Header** to **File Header** and assigns **Ctrl+Alt+Shift+F** to toggle it; the shortcut is removed from the shell Font action to avoid ambiguity.
- exp9-r2 removes the expensive live word counter, reorders editor status to Insert/Overwrite | percentage | Chars | flexible message, and normalizes runtime/desktop identity to `riqatonydesk`.
- Document format: `.rtf` only
- Repository: https://github.com/brunonlinespace/riqatonydesk
- License: GPL-3.0-or-later
- Accent: Rico brick `#B24A3B`

The official logo uses a lifted white page exposing a Breeze-blue plus beneath
it. The three available command-icon families are Rico Icons Legacy, Rico Icons Classic, and Rico Icons Modern. In 0.0.4-exp4-r3, Legacy is AppMenu-only while Classic/Modern remain on the Configure Ribbon; Modern remains the default (technical key `new`).

## Product boundary

RiqatonyDesk is a workspace-scale rich-text application. It uses the Plus-family
workspace shell and the Ricopad RTF engine. The editor uses the Ribbon only;
there are no transferable document layouts or alternate editor chrome.

## Invariants

- No-argument startup opens the Dashboard and creates no file.
- New document creation belongs to RiqatonyDesk, even when initiated by Suite.
- New files are complete valid RTF payloads, never empty placeholders.
- `Ctrl+O` opens workspace management.
- Dashboard cards offer Open and View Only only.
- External OS-open files remain external and transient.
- External application-file drag-and-drop imports supported RTF files into the targeted Workspace location and stops without opening them; App File Launch controls whether document tabs are enabled.
- Save/reopen must preserve deliberate spaces at formatting and list boundaries.
- Untouched documents remain clean and never cause a save prompt.
- Both Rico icon families remain complete and selectable.
- The Ribbon is a shell-level surface above the whole sidebar/content splitter,
  never an editor-local strip to the right of the sidebar.
- Registered Workspaces are available through a dynamic quick selector and
  only the active Workspace is scanned.
- The repository/sidebar dirty marker follows QTextDocument's modified state
  and must clear immediately after Ribbon Save.
- Shell shortcuts remain enabled while editing; managed editor QAction
  duplicates carry no shortcuts and hidden pages cannot claim document keys.
- There is exactly one shell-owned Ribbon object; no hidden Dashboard editor
  and no editor Ribbon reparenting are permitted.
- The shell owns one stable application menu (`File`, `Edit`, `Format`,
  `Insert`, `View`, `Settings`, `Help`); embedded pages never install or
  advertise a menu bar.
- The shell does not force a non-native `QMenuBar`; desktop global-menu
  integration is allowed to export the authoritative application menu.
- The Settings icon-family submenu is labeled `App Icons`.

- exp6 hosting rule: managed pages use a real `RicopadEditorWidget(QWidget)`; no nested `RtfEditorWindow`, fake QMainWindow compatibility API, dynamic method transplantation, or hidden Ricopad Ribbon/menu bar is permitted.
- exp6-r3 source rule: the retired `RtfEditorWindow` implementation is removed from production source entirely; QA targets the one live `RicopadEditorWidget` instead of retaining dead code as a parity oracle.
- exp7 closing rule: application shutdown follows the authoritative Marko Plus staged `ClosingDialog` sequence: unsaved check → save preferences/state → hide the heavy shell → cancel/stop the workspace scanner responsively → final exit.
- exp8 external-change rule: watcher/repository metadata changes are connected to every open `EditorPage`; the page confirms the disk bytes against Ricopad's exact content signature and shows an independent external-change warning surface that is never tied to File Header or Collapsed Mode visibility. Reload protects unsaved editor changes.
- exp8-r1 preservation rule: the former Keep My Version acknowledgement is removed. **Save Version As…** must save the Rico editor payload to a different path and must never allow the externally changed source path as its target; the external disk copy remains untouched.
- exp8-r2 rename rule: F2 follows Marko Plus semantics—rename the active document when editing, otherwise rename the selected/open Workspace subfolder; the active Workspace root is never renameable.
- exp8-r3 mode rule: user-facing **Lock Editor** is renamed **Locked Mode** and **Collapsed Mode** is renamed **Focused Mode**. The View AppMenu places Focused Mode immediately before Locked Mode, with the separator after Locked Mode. Opening a document while Locked Mode is active resets the editor cursor/viewport to the top. Internal `view_only`/`collapsed_mode` identifiers remain implementation details.
- exp9 editor-status rule: the editor status bar contains **Insert/Overwrite | Chars, Words | percentage | flexible status** only. The filepath is shown only in the file header. Fixed fields reserve their longest supported widths; the right-hand message field is elastic with zero minimum width and must never increase the application minimum width.
- exp6 narrow-window rule: keep sidebar horizontal scrolling and use the proven Plus-family `QToolBar` overflow model for the shell Ribbon.
- The approved empty-paragraph/cell codec fix is treated as a Ricopad upstream bugfix and must be backported to Ricopad rather than maintained as an independent RiqatonyDesk semantic fork.

## Current structure

```text
main.py
  -> RuntimePaths / ConfigService / ProjectRegistry
  -> MainWindow
     -> Repository / StateStore / Scanner / Watcher
     -> Navigation / Dashboards / FileActions / EditorManager
     -> ShellRibbon + shell-owned QAction command model
        -> EditorPage -> private RicopadEditorWidget(QWidget) -> RichTextEdit / rtf_codec
```

## Release policy

Run the source release check, Qt RTF suite, workspace integration suite, and an
extracted-archive check before issuing a version. AppImage publication also
requires host desktop, print/PDF, and file-association testing.

- r8/r9 review: retain the Plus-family file heading; managed editors must never own QApplication theme; editor canvas follows App Theme until explicit Dark Editor override; Classic/New selector icons share the four-square Rico background with C/N target badges; editor focus indication uses the native transient focus-frame primitive rather than an invented permanent border.
