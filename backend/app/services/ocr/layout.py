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
# Cut into bands unless the column gutter is clearly wider: the gap between a photo and the
# text beside it is often as narrow as the gap between steps, and those must stay paired.
BAND_PREFERENCE = 2.0
# A gutter narrower than this share of the content width is the gap between a picture and its
# text, not between columns.
MIN_GUTTER_RATIO = 0.015
# Phone photos are skewed, so neighbouring blocks overlap slightly; an overlap smaller than this
# share of a block's length still counts as a gap.
OVERLAP_TOLERANCE = 0.15


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


def _split(blocks: list[T], span: Callable[[T], tuple[float, float]]) -> tuple[list[list[T]], float]:
    """Cut blocks in two at the widest empty gap along one axis. Returns the pieces in axis
    order and the gap's width; one piece and 0 if there is no gap.

    Cutting only at the widest gap (not at every gap) lets a wide gutter, such as the one before
    a sidebar, be cut first, so narrower gaps inside the main column are judged on their own."""
    groups: list[list[T]] = []
    gaps: list[float] = []
    group_end = float("-inf")
    for block in sorted(blocks, key=lambda b: span(b)[0]):
        start, end = span(block)
        if groups and start < group_end - OVERLAP_TOLERANCE * (end - start):
            groups[-1].append(block)
            group_end = max(group_end, end)
        else:
            if groups:
                gaps.append(max(0.0, start - group_end))
            groups.append([block])
            group_end = end
    if not gaps:
        return groups, 0.0
    cut = max(range(len(gaps)), key=gaps.__getitem__) + 1
    flatten = lambda part: [b for group in part for b in group]  # noqa: E731
    return [flatten(groups[:cut]), flatten(groups[cut:])], gaps[cut - 1]


def order_blocks(blocks: list[T], vertical: bool) -> list[T]:
    """Recursive XY-cut: split the page at its widest empty gap, across or down, and read the
    pieces in order (bands top to bottom; columns left to right, or right to left for 縦書き).
    Headers spanning several columns, sidebars and pictures beside text each stay together."""
    if len(blocks) <= 1:
        return list(blocks)

    bands, band_gap = _split(blocks, lambda b: (b.box.y1, b.box.y2))
    columns, column_gap = _split(blocks, lambda b: (b.box.x1, b.box.x2))
    if vertical:
        columns.reverse()

    width = max(b.box.x2 for b in blocks) - min(b.box.x1 for b in blocks)
    narrow_gutter = column_gap < MIN_GUTTER_RATIO * width
    # A column of pictures beside a column of text is a list of rows: each picture belongs to
    # the text next to it (how-to steps, product listings), so read row by row.
    pictures_beside_text = len(columns) > 1 and any(
        all(isinstance(b, PlacedFigure) for b in piece) for piece in columns
    )
    if len(bands) > 1 and (
        narrow_gutter or pictures_beside_text or band_gap * BAND_PREFERENCE >= column_gap
    ):
        pieces = bands
    elif len(columns) > 1:
        pieces = columns
    else:
        # Overlapping blocks with no clean gap: fall back to plain reading direction.
        key = (lambda b: -b.box.x2) if vertical else (lambda b: b.box.y1)
        return sorted(blocks, key=key)
    return [b for piece in pieces for b in order_blocks(piece, vertical)]


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
