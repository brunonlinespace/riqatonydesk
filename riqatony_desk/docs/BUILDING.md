# Building RiqatonyDesk

## Source environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r riqatony_desk/requirements.txt
python main.py
```

## Release validation

```bash
python -m riqatony_desk.qa.release_check
```

The release check validates identity, static architecture, assets, RTF corpus behavior, packaging metadata, and the source manifest. With PyQt6 installed it also runs the Qt round-trip and workspace/runtime suites.

## Fedora 43/44 AppImage

```bash
./riqatony_desk/packaging/fedora/install-build-deps.sh
./riqatony_desk/packaging/fedora/build-appimage.sh
```

Run the builder as the normal desktop user. The dependency helper may invoke `sudo dnf`; the builder itself performs no privilege elevation or system package installation. Native x86_64 and aarch64 builds are supported; cross-building is not.

Expected output:

```text
riqatony_desk/dist/RiqatonyDesk-0.1.7-<arch>.AppImage
riqatony_desk/dist/RiqatonyDesk-0.1.7-<arch>.AppImage.sha256
riqatony_desk/dist/RiqatonyDesk-0.1.7-<arch>.build-info.txt
riqatony_desk/dist/RiqatonyDesk-0.1.7-<arch>.build-python-lock.txt
```

The builder reruns the authoritative release gate inside its isolated build venv so PyQt6 runtime QA executes against the Qt environment that is frozen into the AppImage. It validates the required Qt PrintSupport payload for RiqatonyDesk printing/PDF output; it does not impose a QtPdf-reader requirement.

Validate the final artifact on the intended X11 and Wayland desktop targets.
