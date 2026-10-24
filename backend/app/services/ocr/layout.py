"""Reading order for text blocks and pictures on a page.

Vertical pages (縦書き) read in tiers from top to bottom, and within a tier from right to left.
Horizontal pages (横書き) read in columns from left to right, and within a column top to bottom.
The page's orientation is whichever text orientation covers more block area.

Pictures take part in the ordering like text blocks. Text found inside a picture (a sign in a
photo, a label) is kept and placed right after that picture.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from app.services.ocr.base import Align, Box, TextBlock

# A picture wider than this share of the content is centred; narrower ones float to a side.
CENTER_ABOVE_RATIO = 0.6
MIN_WIDTH_RATIO = 0.25


@dataclass(frozen=True)
class PlacedFigure:
    box: Box
    width_ratio: float
    align: Align


Element = TextBlock | PlacedFigure
T = TypeVar("T", TextBlock, PlacedFigure, Element)


def is_vertical_page(blocks: list[TextBlock]) -> bool:
    vertical = sum(b.box.area for b in blocks if b.vertical)
    horizontal = sum(b.box.area for b in blocks if not b.vertical)
    return vertical > 0 and vertical >= horizontal


def _group_by_overlap(blocks: list[T], span: Callable[[T], tuple[float, float]]) -> list[list[T]]:
    """Merge blocks whose spans (on one axis) overlap into groups, ordered by span start."""
    groups: list[list[T]] = []
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


def order_blocks(blocks: list[T], vertical: bool) -> list[T]:
    if vertical:
        tiers = _group_by_overlap(blocks, lambda b: (b.box.y1, b.box.y2))
        return [b for tier in tiers for b in sorted(tier, key=lambda b: -b.box.x2)]

    columns = _group_by_overlap(blocks, lambda b: (b.box.x1, b.box.x2))
    return [b for column in columns for b in sorted(column, key=lambda b: b.box.y1)]


def place_figure(box: Box, content: Box) -> PlacedFigure:
    ratio = min(1.0, max(MIN_WIDTH_RATIO, box.width / content.width)) if content.width else 1.0
    if ratio > CENTER_ABOVE_RATIO:
        align: Align = "center"
    else:
        align = "left" if box.center[0] < content.center[0] else "right"
    return PlacedFigure(box=box, width_ratio=round(ratio, 3), align=align)


def _content_box(boxes: list[Box]) -> Box:
    return Box(
        min(b.x1 for b in boxes),
        min(b.y1 for b in boxes),
        max(b.x2 for b in boxes),
        max(b.y2 for b in boxes),
    )


def arrange(blocks: list[TextBlock], figures: list[Box]) -> list[Element]:
    """Text blocks and pictures in reading order, with placement info for each picture."""
    if not figures:
        return list(order_blocks(blocks, is_vertical_page(blocks)))

    content = _content_box([b.box for b in blocks] + figures)
    placed = [place_figure(box, content) for box in figures]

    inside: dict[int, list[TextBlock]] = {i: [] for i in range(len(placed))}
    outside: list[TextBlock] = []
    for block in blocks:
        owner = next((i for i, f in enumerate(placed) if f.box.contains(block.box.center)), None)
        (outside if owner is None else inside[owner]).append(block)

    vertical = is_vertical_page(blocks)
    arranged: list[Element] = []
    for element in order_blocks([*outside, *placed], vertical):
        arranged.append(element)
        if isinstance(element, PlacedFigure):
            caption_blocks = inside[placed.index(element)]
            arranged.extend(order_blocks(caption_blocks, is_vertical_page(caption_blocks)))
    return arranged
