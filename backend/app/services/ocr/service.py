import io

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from app.services.images import to_dithered_png
from app.services.ocr import furigana
from app.services.ocr.base import FigureItem, OcrEngine, OcrResult, PageItem, Paragraph
from app.services.ocr.layout import PlacedFigure, arrange
from app.services.regions.base import LayoutDetector, picture_boxes

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


def read_page(engine: OcrEngine, detector: LayoutDetector, data: bytes) -> OcrResult:
    image = decode_image(data)
    items: list[PageItem] = []
    blocks = furigana.extract(engine.read_blocks(image))
    for element in arrange(blocks, picture_boxes(detector.detect(image))):
        if isinstance(element, PlacedFigure):
            png = to_dithered_png(image, element.box)
            items.append(FigureItem(png=png, width_ratio=element.width_ratio, align=element.align))
        elif element.text:
            items.append(Paragraph(element.text, element.ruby))
    return OcrResult(items=items)
