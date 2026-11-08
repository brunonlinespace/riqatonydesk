# RiqatonyDesk

RiqatonyDesk 0.1.7 is a Ribbon-based RTF editor with workspace navigation,
folder dashboards, background discovery, and conservative file handling. It
stores ordinary `.rtf` files and does not introduce a private document format.

## Highlights

- Registered workspaces with a recursive sidebar and fast switching
- Dynamic Workspace(s) quick selector; inactive roots are never scanned
- Workspace and folder dashboards in List or Grid view
- Exactly two card actions: **Open** and **View Only**
- One rich-text Ribbon with File, Home, Insert, View, and Help tabs
- Full-width Ribbon above the sidebar and document/dashboard surface
- Riqa Icons Harmony (default), Humility, and Heritage, each with light and dark variants; all three are available from Settings → App Icons and Configure
- Searchable shortcuts with case-insensitive, modifier-order-independent matching
- Safe create, duplicate, rename, move, import, and removal operations
- Dirty Duplicate and External Editor choices distinguish the current unsaved document from the last saved disk version, with remembered policies under Settings
- F2 renames either the active RTF file or the selected Workspace subfolder
- Atomic RTF saving, external-change detection, and bounded file loading
- Save, Save As, Save and New, Save and Dashboard, and Save and Exit
- Standards-based RTF lists plus curated LibreOffice interoperability coverage

## Run from source

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r riqatony_desk/requirements.txt
python main.py
```

Useful launch forms:

```bash
python main.py --version
python main.py --setup
python main.py document.rtf
python main.py --open-file document.rtf
```

Starting without a file opens the Dashboard and creates no document. **New RTF
File** asks the editor layer to create a complete, valid RTF document; RiqatonyDesk
never uses an empty placeholder file.

## Workspaces and OS file opening

Only the active workspace is scanned. An RTF opened by the operating system
inside that workspace uses its normal workspace entry. An RTF outside the
workspace opens as a transient external session: it is not copied, imported,
or added to workspace navigation or dashboards.

External RTF mouse drops are import-only. Drop onto the workspace/root target, a sidebar folder, a Folder Dashboard, or the application surface to copy the file into that target; the imported file is not opened automatically and does not create a tab or window. Internal managed-document mouse drag-to-move remains separate.

`Ctrl+O` opens workspace management. RiqatonyDesk has no separate **Open RTF
Document** command; desktop file associations and workspace navigation cover
that workflow.

## AppImage

```bash
./riqatony_desk/packaging/fedora/install-build-deps.sh
./riqatony_desk/packaging/fedora/build-appimage.sh
chmod +x riqatony_desk/dist/RiqatonyDesk-0.1.7-x86_64.AppImage
./riqatony_desk/dist/RiqatonyDesk-0.1.7-x86_64.AppImage
```

The desktop launcher accepts one RTF path through `%f`. Files outside the active workspace open as transient external sessions; AppImage mode keeps configuration and documents outside the read-only bundle.

## Configuration and diagnostics

Configuration uses Qt's per-user application-config location under the Rico
Plus application identity. Optional shutdown timing is enabled with:

```bash
RIQATONYDESK_PROFILE_SHUTDOWN=1 python main.py
```

## Validation

```bash
python -m riqatony_desk.qa.release_check
```

See `QA.md`, `BUILDING.md`, and `RELEASE_CHECKLIST.md` for the complete gates.

## Documentation command

**Help → Documentation** opens the bundled `Documentation.rtf` as a transient external RiqatonyDesk document in its own window. The source-tree Markdown files in `docs/` remain developer/release documentation and are not the user-facing Help document.

## License and links

RiqatonyDesk is GPL-3.0-or-later. See `LICENSE`.

- Repository: https://github.com/brunonlinespace/riqatonydesk
- Issues: https://github.com/brunonlinespace/riqatonydesk/issues
