import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.ocr.base import OcrEngine, OcrResult
from app.services.ocr.layout import to_result


class InvalidImageError(ValueError):
    pass


def decode_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise InvalidImageError("Not a readable image") from error
    # Phone photos are often stored sideways with an EXIF rotation flag.
    return ImageOps.exif_transpose(image).convert("RGB")


def read_page(engine: OcrEngine, data: bytes) -> OcrResult:
    image = decode_image(data)
    return to_result(engine.read_blocks(image))
