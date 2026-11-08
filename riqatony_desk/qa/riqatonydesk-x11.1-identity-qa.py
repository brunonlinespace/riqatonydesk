#!/usr/bin/env python3
"""Release x11.1 identity-path validation; original legacy QA remains active."""
from pathlib import Path
import ast
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "riqatony_desk"
IDENTITY = "riqatonydesk"
VERSION = "1.0.0-x11.1"
errors = []
def require(condition, message):
    if not condition:
        errors.append(message)

require(PKG.is_dir() and not (ROOT / "rico_plus").exists(), "master Python folder not migrated")
require(not (PKG / "rwpyn").exists() and not (ROOT / "rwpyn").exists(), "unapproved Rwpyn folder")
require((ROOT / "main.py").is_file(), "source entry point missing")
require((PKG / "rtf_codec.py").is_file(), "original RTF codec moved")
require((PKG / "widgets" / "rtf_editor.py").is_file(), "existing rich-text editor moved")
require((PKG / "docs/history/Rico-Plus-1.0.0-x10.0-RELEASE_NOTES.md").is_file(), "original release notes not archived")

app = (PKG / "app.py").read_text()
paths = (PKG / "services/runtime_paths.py").read_text()
require("app.setApplicationName(APP_DISPLAY_NAME)" in app, "Qt public name not configured")
require("app.setDesktopFileName(APP_RUNTIME_DESKTOP_ID)" in app, "Qt desktop association missing")
require('"brunonlinespace" / "riqatonydesk"' in paths, "config namespace not independent")
require('return self.config_root / "riqatonydesk_config.json"' in paths, "config filename mismatch")
require("QStandardPaths.StandardLocation.AppConfigLocation" not in paths, "legacy Qt config namespace persists")

component = json.loads((ROOT / "suite-pythoine-component.json").read_text())
project = json.loads((PKG / "riqatonydesk.json").read_text())
for model in (component, project):
    for key, value in {"id": IDENTITY, "name":"RiqatonyDesk", "version":VERSION,
                       "desktop_id":IDENTITY, "repository":"https://github.com/brunonlinespace/riqatonydesk"}.items():
        require(model.get(key) == value, f"{key} mismatch in project/Suite metadata")
require(component.get("component_kind")=="extension", "Suite extension classification changed")
require(component.get("capabilities")=={"routing":False,"open":False,"create":False}, "Plus routing contract changed")
require((ROOT / component.get("icon","<missing>")).is_file(), "Suite application icon missing")

desktop=(PKG / "packaging/appimage/riqatonydesk.desktop").read_text()
for fragment in ("Name=RiqatonyDesk", "Exec=riqatonydesk %f", "Icon=riqatonydesk",
                 "StartupWMClass=RiqatonyDesk", "X-AppImage-Version="+VERSION):
    require(fragment in desktop, f"desktop metadata mismatch: {fragment}")
appstream=ET.parse(PKG / "packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml").getroot()
require(appstream.findtext('id')=='io.github.brunonlinespace.riqatonydesk', "AppStream ID mismatch")
require(appstream.findtext('launchable')=='riqatonydesk.desktop', "AppStream desktop ID mismatch")
require(appstream.findtext('name')=='RiqatonyDesk', "AppStream visible name mismatch")
require((appstream.find('releases/release').attrib.get('version'))==VERSION, "AppStream version mismatch")

apprun=(PKG/'packaging/appimage/AppRun').read_text()
builder=(PKG/'packaging/fedora/build-appimage.sh').read_text()
for fragment in ('usr/lib/riqatonydesk','"$BUNDLE/riqatonydesk"'):
    require(fragment in apprun, f"AppRun still has old bundle identity: {fragment}")
for fragment in ('APP_ID="riqatonydesk"', 'APP_NAME="RiqatonyDesk"',
                 'APP_VERSION="'+VERSION+'"',
                 '"$APPDIR/usr/share/doc/riqatonydesk"',
                 '"$APPDIR/usr/lib/riqatonydesk"',
                 '"$PROGRAM_ROOT/assets/icons/riqatonydesk-${icon_size}.png"'):
    require(fragment in builder, f"AppImage assembly contract mismatch: {fragment}")
for size in (16,32,48,64,128,256,512):
    require((PKG/f'assets/icons/riqatonydesk-{size}.png').is_file(), f"missing {size}-pixel icon")
for filename in ('riqatonydesk.png','riqatonydesk.ico','riqatonydesk-master.png','riqatonydesk-about.png'):
    require((PKG/'assets/icons'/filename).is_file(), f"missing application image {filename}")

# Existing private MIME identifiers are interoperability contracts, not branding.
require('application/x-rico-plus-document' in (PKG/'widgets/navigation.py').read_text(), "private document MIME changed")
require('application/x-ricopad-inline-richtext' in (PKG/'widgets/editor_widgets.py').read_text(), "private editor MIME changed")

if errors:
    raise SystemExit("\n".join("FAIL: "+e for e in errors))
print("PASS: x11.1 public identity, paths, AppImage layout and private MIME preservation")
