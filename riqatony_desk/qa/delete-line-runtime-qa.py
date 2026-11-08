#!/usr/bin/env python3
"""Qt runtime regression tests for RiqatonyDesk Delete Line (0.0.4-exp3)."""
from PyQt6.QtGui import QTextCursor, QTextDocument, QTextListFormat


def delete_current_block(cursor: QTextCursor) -> None:
    block = cursor.block()
    is_last = not block.next().isValid()
    has_previous = block.previous().isValid()
    cursor.beginEditBlock()
    try:
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        if cursor.hasSelection():
            cursor.removeSelectedText()
        elif is_last and has_previous:
            cursor.deletePreviousChar()
        elif not is_last:
            cursor.deleteChar()
    finally:
        cursor.endEditBlock()


def make_doc(lines):
    doc = QTextDocument()
    c = QTextCursor(doc)
    c.insertText(lines[0])
    for line in lines[1:]:
        c.insertBlock()
        c.insertText(line)
    return doc


def cursor_for_block(doc, index):
    block = doc.begin()
    for _ in range(index):
        block = block.next()
    assert block.isValid()
    c = QTextCursor(block)
    # Put cursor in the block, including empty blocks.
    c.setPosition(block.position() + (1 if block.length() > 1 else 0))
    return c


def block_texts(doc):
    out = []
    block = doc.begin()
    while block.isValid():
        out.append(block.text())
        block = block.next()
    return out


def check(lines, index, expected, label):
    doc = make_doc(lines)
    c = cursor_for_block(doc, index)
    delete_current_block(c)
    actual = block_texts(doc)
    assert actual == expected, f"{label}: {actual!r} != {expected!r}"


check(
    ["KEEP ABOVE ABCDE", "CUT THIS MIDDLE LINE", "KEEP BELOW 12345"],
    1,
    ["KEEP ABOVE ABCDE", "KEEP BELOW 12345"],
    "middle non-empty",
)
check(
    ["KEEP ABOVE ABCDE", "", "KEEP BELOW 12345"],
    1,
    ["KEEP ABOVE ABCDE", "KEEP BELOW 12345"],
    "middle empty",
)
check(
    ["KEEP LINE 1 ABCDE", "KEEP LINE 2 VWXYZ", "CUT THIS FINAL LINE"],
    2,
    ["KEEP LINE 1 ABCDE", "KEEP LINE 2 VWXYZ"],
    "final non-empty",
)
check(
    ["KEEP LINE 1 ABCDE", "KEEP LINE 2 VWXYZ", ""],
    2,
    ["KEEP LINE 1 ABCDE", "KEEP LINE 2 VWXYZ"],
    "final empty",
)

# List-item cases: create three list blocks and verify that deleting one does not
# alter neighbouring item text or collapse their remaining block structure.
def make_list_doc(items):
    doc = QTextDocument()
    c = QTextCursor(doc)
    fmt = QTextListFormat()
    fmt.setStyle(QTextListFormat.Style.ListDisc)
    lst = c.createList(fmt)
    c.insertText(items[0])
    for item in items[1:]:
        c.insertBlock()
        lst.add(c.block())
        c.insertText(item)
    return doc


doc = make_list_doc(["KEEP BULLET 1 ABCDE", "CUT BULLET 2", "KEEP BULLET 3 12345"])
delete_current_block(cursor_for_block(doc, 1))
assert block_texts(doc) == ["KEEP BULLET 1 ABCDE", "KEEP BULLET 3 12345"], block_texts(doc)

doc = make_list_doc(["KEEP BULLET 1 ABCDE", "KEEP BULLET 2 VWXYZ", "CUT FINAL BULLET"])
delete_current_block(cursor_for_block(doc, 2))
assert block_texts(doc) == ["KEEP BULLET 1 ABCDE", "KEEP BULLET 2 VWXYZ"], block_texts(doc)

print("delete-line-runtime-qa: PASS")
