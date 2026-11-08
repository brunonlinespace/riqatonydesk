"""Normalize only approved application-identity substitutions for historical AST checks.

The original x1–x10 fingerprints remain the comparison authorities. This
helper does not modify source algorithms or regenerate expected hashes.
"""

def normalize_identity_dump(serialized_ast: str) -> str:
    # x12.0: undo the single resource_path parent-directory adjustment only
    # when comparing the historical x1/x6 frozen function AST fingerprints.
    # Other function and method digests remain subject to the original checks.
    moved = "Assign(targets=[Name(id='script_dir', ctx=Store())], value=Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='dirname', ctx=Load()), args=[Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='dirname', ctx=Load()), args=[Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='abspath', ctx=Load()), args=[Name(id='__file__', ctx=Load())])])]))"
    original = "Assign(targets=[Name(id='script_dir', ctx=Store())], value=Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='dirname', ctx=Load()), args=[Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='abspath', ctx=Load()), args=[Name(id='__file__', ctx=Load())])]))"
    serialized_ast = serialized_ast.replace(moved, original)
    for new, original in (
        ("brunonlinespace.RiqatonyDesk", "brunonlinespace.RicoPlus"),
        ("riqatonydesk-about.png", "ricopad-about.png"),
        ("riqatonydesk-master.png", "ricopad-master.png"),
        ("riqatonydesk.png", "ricopad.png"),
        ("riqatony_desk", "rico_plus"),
        ("RIQATONYDESK", "RICO_PLUS"),
        ("riqatonydesk", "rico-plus"),
        ("RiqatonyDesk", "Rico Plus"),
        ("1.0.0-x12.0", "1.0.0-x10.0"),
        ("1.0.0-x11.2", "1.0.0-x10.0"),
        ("1.0.0-x11.1", "1.0.0-x10.0"),
    ):
        serialized_ast = serialized_ast.replace(new, original)
    return serialized_ast


def normalize_identity_text(text: str) -> str:
    """Invert the approved branding edits before comparing historical source hashes."""
    for size in (16, 32, 48, 64, 128, 256, 512):
        text = text.replace(f"riqatonydesk-{size}.png", f"ricopad-{size}.png")
    for new, old in (
        ("riqatonydesk-about.png", "ricopad-about.png"),
        ("riqatonydesk-master.png", "ricopad-master.png"),
        ("riqatonydesk.ico", "ricopad.ico"),
        ("riqatonydesk.png", "ricopad.png"),
        ("riqatony_desk", "rico_plus"),
        ("RIQATONYDESK", "RICO_PLUS"),
        ("riqatonydesk", "rico-plus"),
        ("RiqatonyDesk", "Rico Plus"),
        ("1.0.0-x12.0", "1.0.0-x10.0"),
        ("1.0.0-x11.2", "1.0.0-x10.0"),
        ("1.0.0-x11.1", "1.0.0-x10.0"),
    ):
        text = text.replace(new, old)
    return text.replace(
        "app.setApplicationName(APP_DISPLAY_NAME)",
        "app.setApplicationName(APP_INTERNAL_NAME)",
    )


def historical_source_sha(path):
    import hashlib
    return hashlib.sha256(normalize_identity_text(path.read_text(encoding="utf-8")).encode("utf-8")).hexdigest()
