import io

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from app.services.ocr.base import OcrEngine, OcrResult
from app.services.ocr.layout import to_result

# iPhone photos are HEIC by default; teach Pillow to open them.
register_heif_opener()


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
