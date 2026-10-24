"""Reading order for text blocks on a page.

Vertical pages (縦書き) read in tiers from top to bottom, and within a tier from right to left.
Horizontal pages (横書き) read in columns from left to right, and within a column top to bottom.
The page's orientation is whichever orientation covers more block area.
"""

from collections.abc import Callable

from app.services.ocr.base import OcrResult, Paragraph, TextBlock


def is_vertical_page(blocks: list[TextBlock]) -> bool:
    vertical = sum(b.box.area for b in blocks if b.vertical)
    horizontal = sum(b.box.area for b in blocks if not b.vertical)
    return vertical >= horizontal


def _group_by_overlap(
    blocks: list[TextBlock], span: Callable[[TextBlock], tuple[float, float]]
) -> list[list[TextBlock]]:
    """Merge blocks whose spans (on one axis) overlap into groups, ordered by span start."""
    groups: list[list[TextBlock]] = []
    group_end = float("-inf")
    for block in sorted(blocks, key=lambda b: span(b)[0]):
        start, end = span(block)
        if groups and start < group_end:
            groups[-1].append(block)
            group_end = max(group_end, end)
        else:
            groups.append([block])
            group_end = end
    return groups


def order_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    if is_vertical_page(blocks):
        tiers = _group_by_overlap(blocks, lambda b: (b.box.y1, b.box.y2))
        return [b for tier in tiers for b in sorted(tier, key=lambda b: -b.box.x2)]

    columns = _group_by_overlap(blocks, lambda b: (b.box.x1, b.box.x2))
    return [b for column in columns for b in sorted(column, key=lambda b: b.box.y1)]


def to_result(blocks: list[TextBlock]) -> OcrResult:
    return OcrResult(items=[Paragraph(b.text) for b in order_blocks(blocks) if b.text])
