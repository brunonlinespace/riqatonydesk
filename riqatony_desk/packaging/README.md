# RiqatonyDesk Packaging

Build the Fedora 43/44 AppImage as a normal desktop user on native x86_64 or aarch64:

```bash
./riqatony_desk/packaging/fedora/install-build-deps.sh
./riqatony_desk/packaging/fedora/build-appimage.sh
```

The dependency helper is optional/manual and may invoke `sudo dnf`. The builder itself is deliberately non-privileged and never installs host packages.

Artifacts:

```text
riqatony_desk/dist/RiqatonyDesk-1.0.0-<arch>.AppImage
riqatony_desk/dist/RiqatonyDesk-1.0.0-<arch>.AppImage.sha256
riqatony_desk/dist/RiqatonyDesk-1.0.0-<arch>.build-info.txt
riqatony_desk/dist/RiqatonyDesk-1.0.0-<arch>.build-python-lock.txt
```

Test an artifact with:

```bash
./riqatony_desk/packaging/fedora/test-appimage.sh \
  riqatony_desk/dist/RiqatonyDesk-1.0.0-x86_64.AppImage
```

The builder validates the Suite/component identity, runs the authoritative release gate, creates an isolated Python environment, reruns Qt-backed QA in that environment, freezes with PyInstaller, validates desktop/AppStream metadata, checks the required Qt PrintSupport payload, verifies the AppDir, and then creates and verifies the finished AppImage.

For release builds, set `RIQATONYDESK_RELEASE_BUILD=1` and supply `APPIMAGETOOL_SHA256`.
