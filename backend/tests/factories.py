import json
from pathlib import Path

from app.services.ocr.base import Box, TextBlock, TextLine
from app.services.regions.base import Region

FIXTURES = Path(__file__).parent / "fixtures"


def line(text: str, x1: float, y1: float, x2: float, y2: float, vertical: bool = False) -> TextLine:
    box = Box(x1, y1, x2, y2)
    return TextLine(text=text, box=box, thickness=box.width if vertical else box.height)


def block(
    text: str, x1: float, y1: float, x2: float, y2: float, vertical: bool, font_size: float = 40
) -> TextBlock:
    """A block holding one line that fills it."""
    return TextBlock(
        box=Box(x1, y1, x2, y2),
        vertical=vertical,
        lines=[line(text, x1, y1, x2, y2, vertical)],
        font_size=font_size,
    )


def block_of(lines: list[TextLine], vertical: bool, font_size: float = 40) -> TextBlock:
    return TextBlock(
        box=Box.union([ln.box for ln in lines]), vertical=vertical, lines=lines, font_size=font_size
    )


def load_page(name: str) -> tuple[list[TextBlock], list[Region]]:
    """Engine blocks and layout regions recorded from a real page (tests/fixtures)."""
    data = json.loads((FIXTURES / name).read_text())
    blocks = [
        TextBlock(
            box=Box(*b["box"]),
            vertical=b["vertical"],
            font_size=b["font_size"],
            lines=[TextLine(ln["text"], Box(*ln["box"]), ln["thickness"]) for ln in b["lines"]],
        )
        for b in data["blocks"]
    ]
    regions = [Region(Box(*r["box"]), r["kind"], r["score"]) for r in data["regions"]]
    return blocks, regions
