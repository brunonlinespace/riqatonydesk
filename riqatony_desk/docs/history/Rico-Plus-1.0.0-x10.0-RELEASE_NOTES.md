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
