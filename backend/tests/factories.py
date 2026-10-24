from app.services.ocr.base import Box, TextBlock, TextLine


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
        box=Box.union([l.box for l in lines]), vertical=vertical, lines=lines, font_size=font_size
    )
