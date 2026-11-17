"""Reading order and layout for text blocks and pictures on a page.

The page is cut recursively at its widest empty gap (XY-cut): across into bands read top to
bottom, or down into columns read left to right (right to left for 縦書き). The cuts form a tree,
and on horizontal pages column cuts are kept as side-by-side columns in the document, so sidebars,
multi-column text and headers beside text keep their arrangement.

Vertical pages are flattened into one column: once 縦書き is turned horizontal, its columns are just
lines. A single picture beside text is not made a column either; it floats on its side and the text
wraps around it.

Text found inside a picture (a sign in a photo, a label) is kept and placed right after it.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.services.ocr.base import Align, Box, TextBlock

# A picture wider than this share of its column is centred; narrower ones float to a side.
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
    width_ratio: float  # share of the width of the column (or page) it sits in
    align: Align


@dataclass(frozen=True)
class Column:
    width_ratio: float  # share of the row's width
    children: list["Node"]


@dataclass(frozen=True)
class Columns:
    columns: list[Column]


Node = TextBlock | PlacedFigure | Columns


@dataclass(frozen=True)
class _Picture:
    """A picture during cutting, before it knows which column it will be placed in."""

    box: Box
    captions: tuple[TextBlock, ...] = ()


_Element = TextBlock | _Picture


def is_vertical_page(blocks: list[TextBlock]) -> bool:
    vertical = sum(b.box.area for b in blocks if b.vertical)
    horizontal = sum(b.box.area for b in blocks if not b.vertical)
    return vertical > 0 and vertical >= horizontal


def _split(
    blocks: list[_Element], span: Callable[[_Element], tuple[float, float]]
) -> tuple[list[list[_Element]], float]:
    """Cut blocks in two at the widest empty gap along one axis. Returns the pieces in axis
    order and the gap's width; one piece and 0 if there is no gap.

    Cutting only at the widest gap (not at every gap) lets a wide gutter, such as the one before
    a sidebar, be cut first, so narrower gaps inside the main column are judged on their own."""
    groups: list[list[_Element]] = []
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


def _extent(elements: list[_Element]) -> Box:
    return Box.union([e.box for e in elements])


def place_figure(box: Box, container: Box, side: Align | None = None) -> PlacedFigure:
    """Size a picture relative to its container; float it to `side`, or the side it is on."""
    ratio = min(1.0, max(MIN_WIDTH_RATIO, box.width / container.width)) if container.width else 1.0
    if side is None:
        if ratio > CENTER_ABOVE_RATIO:
            side = "center"
        else:
            side = "left" if box.center[0] < container.center[0] else "right"
    return PlacedFigure(box=box, width_ratio=round(ratio, 3), align=side)


def _build(elements: list[_Element], vertical: bool, container: Box) -> list[Node]:
    """Recursive XY-cut. `container` is the column (or page) the elements are placed in."""
    if len(elements) == 1:
        return _emit(elements[0], vertical, container)

    bands, band_gap = _split(elements, lambda b: (b.box.y1, b.box.y2))
    columns, column_gap = _split(elements, lambda b: (b.box.x1, b.box.x2))
    if vertical:
        columns.reverse()

    width = _extent(elements).width
    narrow_gutter = column_gap < MIN_GUTTER_RATIO * width
    # A column of pictures beside a column of text is a list of rows: each picture belongs to
    # the text next to it (how-to steps, product listings), so read row by row.
    pictures_beside_text = len(columns) > 1 and any(
        all(isinstance(b, _Picture) for b in piece) for piece in columns
    )
    if len(bands) > 1 and (narrow_gutter or pictures_beside_text or band_gap * BAND_PREFERENCE >= column_gap):
        return [node for band in bands for node in _build(band, vertical, container)]

    if len(columns) <= 1:
        # Overlapping blocks with no clean gap: fall back to plain reading direction.
        key = (lambda b: -b.box.x2) if vertical else (lambda b: b.box.y1)
        return [node for e in sorted(elements, key=key) for node in _emit(e, vertical, container)]

    if vertical:
        return [node for piece in columns for node in _build(piece, vertical, container)]

    # One picture beside text: float it on its side and let the text wrap.
    for index, piece in enumerate(columns):
        if len(piece) == 1 and isinstance(piece[0], _Picture):
            side: Align = "left" if index == 0 else "right"
            other = columns[1 - index]
            picture = piece[0]
            return [
                place_figure(picture.box, container, side),
                *_captions(picture, vertical, container),
                *_build(other, vertical, container),
            ]

    return [_row(columns, vertical)]


def _row(pieces: list[list[_Element]], vertical: bool) -> Columns:
    widths = [_extent(piece).width for piece in pieces]
    total = sum(widths) or 1.0
    columns: list[Column] = []
    for piece, width in zip(pieces, widths, strict=True):
        share = width / total
        children = _build(piece, vertical, _extent(piece))
        # A column that is itself just a row of columns joins this row.
        if len(children) == 1 and isinstance(children[0], Columns):
            columns.extend(Column(round(share * c.width_ratio, 3), c.children) for c in children[0].columns)
        else:
            columns.append(Column(round(share, 3), children))
    return Columns(columns)


def _captions(picture: _Picture, vertical: bool, container: Box) -> list[Node]:
    if not picture.captions:
        return []
    inner = list(picture.captions)
    return _flatten(_build(inner, is_vertical_page(inner), container))


def _emit(element: _Element, vertical: bool, container: Box) -> list[Node]:
    if isinstance(element, TextBlock):
        return [element]
    return [place_figure(element.box, container), *_captions(element, vertical, container)]


def _flatten(nodes: list[Node]) -> list[Node]:
    flat: list[Node] = []
    for node in nodes:
        if isinstance(node, Columns):
            flat.extend(n for column in node.columns for n in _flatten(column.children))
        else:
            flat.append(node)
    return flat


def arrange(blocks: list[TextBlock], figures: list[Box]) -> list[Node]:
    """The page as a tree of text blocks, placed pictures and rows of columns, in reading order."""
    if not blocks and not figures:
        return []
    captions: dict[int, list[TextBlock]] = {i: [] for i in range(len(figures))}
    outside: list[TextBlock] = []
    for block in blocks:
        owner = next((i for i, f in enumerate(figures) if f.contains(block.box.center)), None)
        (outside if owner is None else captions[owner]).append(block)

    pictures = [_Picture(box, tuple(captions[i])) for i, box in enumerate(figures)]
    elements: list[_Element] = [*outside, *pictures]
    vertical = is_vertical_page(blocks)
    return _build(elements, vertical, _extent(elements))
