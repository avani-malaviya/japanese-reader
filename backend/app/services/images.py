"""Pictures cut out of a page, rendered in the app's 1-bit black and white."""

import io

from PIL import Image, ImageOps

from app.services.ocr.base import Box

MAX_FIGURE_WIDTH = 800
CROP_PADDING = 4


def crop(image: Image.Image, box: Box, padding: int = CROP_PADDING) -> Image.Image:
    left = max(0, int(box.x1) - padding)
    top = max(0, int(box.y1) - padding)
    right = min(image.width, int(box.x2) + padding)
    bottom = min(image.height, int(box.y2) + padding)
    return image.crop((left, top, right, bottom))


def dither(image: Image.Image, max_width: int = MAX_FIGURE_WIDTH) -> Image.Image:
    gray = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    if gray.width > max_width:
        height = round(gray.height * max_width / gray.width)
        gray = gray.resize((max_width, height), Image.Resampling.LANCZOS)
    # Pillow dithers with Floyd–Steinberg when converting to 1-bit.
    return gray.convert("1")


def to_dithered_png(image: Image.Image, box: Box) -> bytes:
    buffer = io.BytesIO()
    dither(crop(image, box)).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
