from dataclasses import dataclass, field
from typing import Protocol

from PIL import Image


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)


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
class OcrResult:
    paragraphs: list[str]

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)


class OcrEngine(Protocol):
    """Finds and recognises text blocks on a page image, in any order."""

    def read_blocks(self, image: Image.Image) -> list[TextBlock]: ...
