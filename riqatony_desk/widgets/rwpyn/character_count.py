"""Unicode-aware, cached character count for Qt rich-text documents.

The status indicator counts extended grapheme clusters in the document's visible
text. Each boundary between two QTextBlocks counts as one logical separator;
inline embedded objects (U+FFFC) count as one, RTF markup counts as zero.

Never extract the entire document on cursor movement or per text edit. A
QTextBlock caches its count by revision, and only modified blocks are segmented
again. Summing cached block counts costs O(number of blocks), not O(text size).
Document serialization and text-size safety limits deliberately remain untouched.
"""
from PyQt6.QtCore import QTextBoundaryFinder
from PyQt6.QtGui import QTextBlockUserData


class _GraphemeCountData(QTextBlockUserData):
    def __init__(self, revision: int, count: int):
        super().__init__()
        self.revision = revision
        self.count = count


def _count_graphemes(text: str) -> int:
    if not text:
        return 0
    finder = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Grapheme, text)
    count = 0
    while finder.toNextBoundary() != -1:
        count += 1
    return count


def count_visible_characters(document) -> int:
    """Report user-perceived characters without changing editor content."""
    total = 0
    block = document.begin()
    while block.isValid():
        revision = block.revision()
        cache = block.userData()
        if not isinstance(cache, _GraphemeCountData) or cache.revision != revision:
            cache = _GraphemeCountData(revision, _count_graphemes(block.text()))
            block.setUserData(cache)
        total += cache.count
        next_block = block.next()
        if next_block.isValid():
            # One logical break between paragraphs or adjacent table cells.
            total += 1
        block = next_block
    return total
