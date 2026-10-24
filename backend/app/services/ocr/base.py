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
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def contains(self, point: tuple[float, float]) -> bool:
        x, y = point
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    @staticmethod
    def union(boxes: "list[Box]") -> "Box":
        return Box(
            min(b.x1 for b in boxes),
            min(b.y1 for b in boxes),
            max(b.x2 for b in boxes),
            max(b.y2 for b in boxes),
        )


@dataclass(frozen=True)
class Ruby:
    """Furigana over text[start:end]."""

    start: int
    end: int
    kana: str

    def shifted(self, offset: int) -> "Ruby":
        return Ruby(self.start + offset, self.end + offset, self.kana)


@dataclass(frozen=True)
class TextLine:
    text: str
    box: Box
    # Size across the line (height of a horizontal line, width of a vertical one), measured on
    # the engine's rotated quad so skewed photos don't inflate it.
    thickness: float
    ruby: tuple[Ruby, ...] = ()


Role = Literal["body", "heading", "caption"]


@dataclass(frozen=True)
class TextBlock:
    """A region of text as found by an engine. `lines` are already in reading order.
    `role` and `level` are filled in later, from the page's structure."""

    box: Box
    vertical: bool
    lines: list[TextLine] = field(default_factory=list)
    font_size: float = 0.0
    role: Role = "body"
    level: int = 0  # headings: 1 (page title) or 2

    @property
    def text(self) -> str:
        # Japanese has no spaces between words, so wrapped lines join directly.
        return "".join(line.text for line in self.lines)

    @property
    def ruby(self) -> tuple[Ruby, ...]:
        """Each line's furigana, with offsets into `text`."""
        found: list[Ruby] = []
        offset = 0
        for line in self.lines:
            found.extend(r.shifted(offset) for r in line.ruby)
            offset += len(line.text)
        return tuple(found)


@dataclass(frozen=True)
class Paragraph:
    text: str
    ruby: tuple[Ruby, ...] = ()
    role: Role = "body"
    level: int = 0


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
