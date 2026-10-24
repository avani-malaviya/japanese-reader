from dataclasses import dataclass, field
from typing import Literal, Protocol

from PIL import Image


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def area(self) -> float:
        return self.width * max(0.0, self.y2 - self.y1)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def contains(self, point: tuple[float, float]) -> bool:
        x, y = point
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


@dataclass(frozen=True)
class TextBlock:
    """A region of text as found by an engine. `lines` are already in reading order."""

    box: Box
    vertical: bool
    lines: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        # Japanese has no spaces between words, so wrapped lines join directly.
        return "".join(line.strip() for line in self.lines)


@dataclass(frozen=True)
class Paragraph:
    text: str


Align = Literal["left", "center", "right"]


@dataclass(frozen=True)
class FigureItem:
    png: bytes  # 1-bit dithered
    width_ratio: float  # share of the page's content width, 0–1
    align: Align


PageItem = Paragraph | FigureItem


@dataclass(frozen=True)
class OcrResult:
    """The page as a document: items in reading order."""

    items: list[PageItem]

    @property
    def paragraphs(self) -> list[str]:
        return [item.text for item in self.items if isinstance(item, Paragraph)]

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)


class OcrEngine(Protocol):
    """Finds and recognises text blocks on a page image, in any order."""

    def read_blocks(self, image: Image.Image) -> list[TextBlock]: ...
