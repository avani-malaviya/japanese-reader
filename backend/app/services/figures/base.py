from typing import Protocol

from PIL import Image

from app.services.ocr.base import Box


class FigureDetector(Protocol):
    """Finds pictures (photos, illustrations, diagrams) on a page image."""

    def detect(self, image: Image.Image) -> list[Box]: ...
