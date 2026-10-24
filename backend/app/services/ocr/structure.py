"""What each piece of text is: heading, caption or body. Page furniture is dropped.

The OCR engine groups lines into blocks by appearance, so a heading and the paragraph under it
often arrive as one block. Each line is matched to the layout region its centre falls in, and a
block is split wherever that region changes. Every resulting unit then gets a role:

- heading: inside a `title` region, or short and clearly bigger than the page's body text
  (catches headings the layout model misses, such as white text on a coloured band)
- caption: inside a `caption` region
- dropped: inside an `abandon` region (page numbers, running headers, margin tabs)
- body: everything else
"""

from dataclasses import replace
from statistics import median

from app.services.ocr.base import Box, TextBlock, TextLine
from app.services.regions.base import Region, RegionKind

# Which region wins when a line's centre is inside several.
PRIORITY: list[RegionKind] = ["title", "caption", "abandon", "figure", "table", "text"]

# Size-based headings: at least this much bigger than body text, and short.
HEADING_SIZE_RATIO = 1.2
HEADING_MAX_CHARS = 20
HEADING_MAX_LINES = 2
# The biggest heading is the page title (level 1) if it is at least this big.
TITLE_SIZE_RATIO = 1.3
# Headings within this factor of the biggest one share its level.
SAME_LEVEL_RATIO = 0.95


def _region_kind(line: TextLine, regions: list[Region]) -> RegionKind | None:
    centre = line.box.center
    inside = [r.kind for r in regions if r.box.contains(centre)]
    return min(inside, key=PRIORITY.index) if inside else None


def _body_size(blocks: list[TextBlock]) -> float:
    """Typical line thickness of body text: the median over all characters on the page."""
    sizes = [line.thickness for b in blocks for line in b.lines for _ in line.text]
    return median(sizes) if sizes else 0.0


def _size(unit: TextBlock) -> float:
    return median(line.thickness for line in unit.lines)


def _split(block: TextBlock, regions: list[Region]) -> list[tuple[RegionKind | None, TextBlock]]:
    runs: list[tuple[RegionKind | None, list[TextLine]]] = []
    for line in block.lines:
        kind = _region_kind(line, regions)
        if runs and runs[-1][0] == kind:
            runs[-1][1].append(line)
        else:
            runs.append((kind, [line]))
    return [
        (kind, replace(block, lines=lines, box=Box.union([l.box for l in lines])))
        for kind, lines in runs
    ]


def _looks_like_heading(unit: TextBlock, body: float) -> bool:
    return (
        body > 0
        and len(unit.text) <= HEADING_MAX_CHARS
        and len(unit.lines) <= HEADING_MAX_LINES
        and _size(unit) >= HEADING_SIZE_RATIO * body
    )


def build_units(blocks: list[TextBlock], regions: list[Region]) -> list[TextBlock]:
    body = _body_size(blocks)
    units: list[TextBlock] = []
    for block in blocks:
        for kind, unit in _split(block, regions):
            if kind == "abandon":
                continue
            if kind == "title" or _looks_like_heading(unit, body):
                units.append(replace(unit, role="heading", level=2))
            elif kind == "caption":
                units.append(replace(unit, role="caption"))
            else:
                units.append(unit)
    return _promote_title(units, body)


def _promote_title(units: list[TextBlock], body: float) -> list[TextBlock]:
    sizes = [_size(u) for u in units if u.role == "heading"]
    if not sizes or max(sizes) < TITLE_SIZE_RATIO * body:
        return units
    threshold = max(sizes) * SAME_LEVEL_RATIO
    return [
        replace(u, level=1) if u.role == "heading" and _size(u) >= threshold else u for u in units
    ]
