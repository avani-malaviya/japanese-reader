"""comic-text-detector + manga-ocr, via mokuro's page pipeline. See docs/decisions/0001."""

import io
import math
import threading

from PIL import Image

from app.services.inference import gpu_lock
from app.services.ocr.base import Box, TextBlock, TextLine


class MokuroEngine:
    def __init__(self) -> None:
        # Imported here so the app (and tests) start without loading torch.
        from mokuro.manga_page_ocr import MangaPageOcr

        self._ocr = MangaPageOcr()

    def read_blocks(self, image: Image.Image) -> list[TextBlock]:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        with gpu_lock:
            result = self._ocr(buffer)
        return [
            TextBlock(
                box=Box(*block["box"]),
                vertical=bool(block["vertical"]),
                lines=[_line(text, quad) for text, quad in zip(block["lines"], block["lines_coords"])],
                font_size=float(block["font_size"]),
            )
            for block in result["blocks"]
        ]


def _line(text: str, quad: list[list[float]]) -> TextLine:
    xs = [x for x, _ in quad]
    ys = [y for _, y in quad]
    sides = [math.dist(quad[i], quad[(i + 1) % 4]) for i in range(4)]
    return TextLine(text=text, box=Box(min(xs), min(ys), max(xs), max(ys)), thickness=min(sides))


_engine: MokuroEngine | None = None
_lock = threading.Lock()


def get_engine() -> MokuroEngine:
    """Models take a while to load and ~1 GB of memory, so load once, on first use."""
    global _engine
    with _lock:
        if _engine is None:
            _engine = MokuroEngine()
        return _engine
