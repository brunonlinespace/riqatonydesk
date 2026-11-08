#!/usr/bin/env python3
"""x14.0: main Dashboard palette rendering only, with exact predecessor preservation."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE.parent
SLUG = PACKAGE.name
REF = json.loads((Path(__file__).parent / "x140-dashboard-predecessor.json").read_text(encoding="utf-8"))
PREVIOUS = REF["predecessor_sha256_by_path"]
OLD_VERSION = REF["predecessor_version"]
VERSION = REF["current_version"]
errors: list[str] = []

def check(ok: bool, message: str) -> None:
    if not ok:
        errors.append(message)

def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def from_path(name: str) -> bytes:
    return (SOURCE / name).read_bytes()

actual = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*")
          if p.is_file() and "__pycache__" not in p.parts
          and p.suffix not in {".pyc", ".pyo"}
          and p.relative_to(SOURCE).parts[:2] not in {(SLUG, "build"), (SLUG, "dist")}}

qa_dir = "tools" if SLUG == "maqarony_desk" else "qa"
new_files = {f"{SLUG}/{qa_dir}/x140-dashboard-predecessor.json",
             f"{SLUG}/{qa_dir}/x140_dashboard_palette_qa.py"}
if SLUG == "riqatony_desk":
    new_files.add(f"{SLUG}/docs/RELEASE_CHECKLIST-x14.0.md")
check(actual == set(PREVIOUS) | new_files,
      f"Source inventory diverged: {sorted(actual ^ (set(PREVIOUS) | new_files))[:12]}")

card_path = f"{SLUG}/widgets/workspace/dashboard_card.py"
dash_path = f"{SLUG}/widgets/workspace/dashboard.py"
modified_production = {card_path, dash_path}
current_metadata = {
    "README.md", "suite-pythoine-component.json",
    f"{SLUG}/__init__.py", f"{SLUG}/app_constants.py",
    f"{SLUG}/{SLUG.replace('_', '')}.json",
    f"{SLUG}/packaging/README.md",
    f"{SLUG}/packaging/fedora/build-appimage.sh",
    f"{SLUG}/packaging/fedora/test-appimage.sh",
    f"{SLUG}/packaging/appimage/{SLUG.replace('_', '')}.desktop",
}
if SLUG == "maqarony_desk":
    current_metadata |= {f"{SLUG}/docs/README.md", f"{SLUG}/docs/BUILDING.md"}
appstream = f"{SLUG}/packaging/appimage/io.github.brunonlinespace.{SLUG.replace('_', '')}.metainfo.xml"
changed_current = {
    appstream, f"{SLUG}/SOURCE_MANIFEST.sha256",
    f"{SLUG}/tools/release_check.py",
    f"{SLUG}/docs/CHANGELOG.md", f"{SLUG}/docs/RELEASE_NOTES.md",
}
if SLUG == "maqarony_desk":
    changed_current.add(f"{SLUG}/docs/RELEASE_CHECKLIST.md")
for name, old_digest in PREVIOUS.items():
    p = SOURCE / name
    check(p.is_file(), f"Predecessor file missing: {name}")
    if p.is_file() and name not in modified_production | current_metadata | changed_current:
        check(digest(p.read_bytes()) == old_digest, f"Unapproved or historical file modification: {name}")

# Reverse exactly the approved edits and require perfect predecessor-file hashes.
card = from_path(card_path).decode("utf-8")
paint = """    def paintEvent(self, event) -> None:
        # Only root Dashboard cards opt in. Folder Dashboard cards retain their
        # existing native frame, selection appearance and event handling.
        if not self._palette_surface:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        colors = self.palette()
        painter.setBrush(colors.color(QPalette.ColorRole.Button))
        painter.setPen(QPen(colors.color(QPalette.ColorRole.Mid), 1.0))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 6.0, 6.0)
        painter.end()

"""
check(card.count(paint) == 1, "Suite-style palette paintEvent changed/missing")
check("QPalette.ColorRole.Highlight" not in paint, "Selection highlight must not be painted")
check("setStyleSheet(" not in paint, "Card paint must not affect descendant styles")
check('palette_surface: bool = False' in card, "Folder-compatible default must remain False")
card_original = card.replace(paint, "")
card_original = card_original.replace(
    'self.setFrameShape(QFrame.Shape.NoFrame if self._palette_surface else QFrame.Shape.StyledPanel)',
    'self.setFrameShape(QFrame.Shape.StyledPanel)')
card_original = card_original.replace('        self._palette_surface = bool(palette_surface)\n', '')
card_original = card_original.replace('        palette_surface: bool = False,\n', '')
card_original = card_original.replace('QMimeData, QPoint, QRectF, QSize, Qt, pyqtSignal',
                                      'QMimeData, QPoint, QSize, Qt, pyqtSignal')
card_original = card_original.replace('QDrag, QIcon, QInputDevice, QMouseEvent, QPainter, QPalette, QPen',
                                      'QDrag, QIcon, QInputDevice, QMouseEvent, QPalette')
check(digest(card_original.encode('utf-8')) == PREVIOUS[card_path],
      'DashboardCard changes exceed the approved opt-in paint renderer')

dash = from_path(dash_path).decode("utf-8")
check(dash.count('            palette_surface=True,\n') == 2,
      'Exactly root List and Grid cards should enable palette surface')
check(dash.count('                card.update()  # Repaint palette-based surface without recreating card.\n') == 1,
      'Root theme refresh must repaint existing cards once')
dash_original = dash.replace('            palette_surface=True,\n', '')
dash_original = dash_original.replace('                card.update()  # Repaint palette-based surface without recreating card.\n','')
check(digest(dash_original.encode('utf-8')) == PREVIOUS[dash_path],
      'Main Dashboard changes exceed opt-in cards and theme repaint')

# This is crucial: Folder Dashboard stays byte-for-byte unchanged and does
# not request palette cards or their selected-border changes.
folder_path = f'{SLUG}/widgets/workspace/folder_dashboard.py'
check(digest(from_path(folder_path)) == PREVIOUS[folder_path],
      'Folder Dashboard was changed outside scope')
check('palette_surface' not in from_path(folder_path).decode('utf-8'),
      'Folder Dashboard must continue using native QFrame cards')
# No new card-state selection behavior, layout changes or event replacements.
card_tree = ast.parse(card)
classes = [n for n in card_tree.body if isinstance(n, ast.ClassDef) and n.name == 'DashboardCard']
check(len(classes) == 1, 'DashboardCard class identity must not change')
if classes:
    methods = {m.name: m for m in classes[0].body if isinstance(m, ast.FunctionDef)}
    check('paintEvent' in methods, 'Palette painting entrypoint missing')
    check('set_selected' in methods and len(methods['set_selected'].body) == 4,
          'Existing selection state handler changed')
    check(all(m in methods for m in ('mousePressEvent', 'mouseMoveEvent', 'mouseReleaseEvent', 'mouseDoubleClickEvent')),
          'Existing card pointer interactions changed')

for rel in current_metadata:
    data=from_path(rel)
    check(VERSION.encode() in data, f'Current version missing in metadata: {rel}')
    check(digest(data.replace(VERSION.encode(), OLD_VERSION.encode())) == PREVIOUS[rel],
          f'Unapproved metadata edit: {rel}')
for rel in (f'{SLUG}/docs/RELEASE_NOTES.md', f'{SLUG}/docs/CHANGELOG.md'):
    current=from_path(rel)
    # Historical records must appear verbatim at the end of the new file.
    # We cannot recover historical bytes from a digest; the prior size is saved
    # below in the reference to check the exact original suffix.
    n = REF['predecessor_sizes_by_path'][rel]
    check(digest(current[-n:]) == PREVIOUS[rel], f'Historical release record rewritten: {rel}')
if SLUG == 'maqarony_desk':
    rel=f'{SLUG}/docs/RELEASE_CHECKLIST.md'
    n=REF['predecessor_sizes_by_path'][rel]
    check(digest(from_path(rel)[-n:]) == PREVIOUS[rel], 'Earlier checklist content rewritten')

appstream_text=from_path(appstream).decode('utf-8')
check(appstream_text.count('<release version="'+VERSION+'"') == 1,
      'AppStream must contain exactly one current x14.0 entry')
check(appstream_text.count('<release version=') == 1,
      'AppStream must not accumulate historical release entries')
release_gate=from_path(f'{SLUG}/tools/release_check.py').decode('utf-8')
check('x140_dashboard_palette_qa.py' in release_gate,
      'Active release gate must invoke x14.0 preservation')

if errors:
    for failure in errors:
        print('FAIL:', failure)
    raise SystemExit(1)
print(f'PASS {VERSION} ({SLUG}): palette-only root Dashboard change; full predecessor and Folder Dashboard preserved')
