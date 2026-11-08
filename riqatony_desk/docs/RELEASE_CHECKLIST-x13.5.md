# RiqatonyDesk 1.0.0-x13.5 — Theme naming checklist

- [ ] Source identity reports RiqatonyDesk 1.0.0-x13.5.
- [ ] `widgets/theme.py` is byte-identical to the 1.0.0-x13.4 `widgets/rico_theme.py`.
- [ ] The two active production importers refer to `widgets.theme`, and the old file is absent.
- [ ] `rich_text_support.py`, RTF codec, file-safety services and historical QA remain intact.
- [ ] Current source gate and archive extraction verification pass.
- [ ] Confirm Light/Dark/System and icon families on Fedora KDE; AppImage smoke test pending.
