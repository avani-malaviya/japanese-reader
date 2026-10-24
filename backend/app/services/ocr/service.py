import io

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from app.services.images import to_dithered_png
from app.services.ocr import furigana, structure
from app.services.ocr.base import (
    ColumnItem,
    ColumnsItem,
    FigureItem,
    OcrEngine,
    OcrResult,
    PageItem,
    Paragraph,
)
from app.services.ocr.layout import Columns, Node, PlacedFigure, arrange
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


def _to_items(nodes: list[Node], image: Image.Image) -> list[PageItem]:
    items: list[PageItem] = []
    for node in nodes:
        if isinstance(node, Columns):
            columns = [ColumnItem(c.width_ratio, _to_items(c.children, image)) for c in node.columns]
            items.append(ColumnsItem(columns))
        elif isinstance(node, PlacedFigure):
            png = to_dithered_png(image, node.box)
            items.append(FigureItem(png=png, width_ratio=node.width_ratio, align=node.align))
        elif node.text:
            items.append(Paragraph(node.text, node.ruby, node.role, node.level))
    return items


def read_page(engine: OcrEngine, detector: LayoutDetector, data: bytes) -> OcrResult:
    image = decode_image(data)
    regions = detector.detect(image)
    units = structure.build_units(furigana.extract(engine.read_blocks(image)), regions)
    return OcrResult(items=_to_items(arrange(units, picture_boxes(regions)), image))
