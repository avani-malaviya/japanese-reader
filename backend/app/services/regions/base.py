from dataclasses import dataclass
from typing import Literal, Protocol

from PIL import Image

from app.services.ocr.base import Box

RegionKind = Literal["title", "text", "caption", "figure", "table", "abandon"]


@dataclass(frozen=True)
class Region:
    """A part of the page and what it is. `abandon` means page furniture: page numbers,
    running headers, margin tabs."""

    box: Box
    kind: RegionKind
    score: float


class LayoutDetector(Protocol):
    """Finds the parts of a page: titles, text, captions, pictures, tables, page furniture."""

    def detect(self, image: Image.Image) -> list[Region]: ...


def picture_boxes(regions: list[Region]) -> list[Box]:
    # Tables are kept as pictures for now; any text OCR'd inside follows them as paragraphs.
    return [r.box for r in regions if r.kind in ("figure", "table")]
