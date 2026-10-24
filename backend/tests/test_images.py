import io

from PIL import Image

from app.services.images import crop, to_dithered_png
from app.services.ocr.base import Box


def gradient(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height))
    image.putdata([(x * 255 // width, 100, 200) for _ in range(height) for x in range(width)])
    return image


def test_crop_pads_and_stays_inside_the_image() -> None:
    image = Image.new("RGB", (100, 100))
    assert crop(image, Box(10, 10, 50, 50), padding=4).size == (48, 48)
    assert crop(image, Box(0, 0, 100, 100), padding=4).size == (100, 100)


def test_dithered_png_is_pure_black_and_white() -> None:
    png = to_dithered_png(gradient(1200, 300), Box(0, 0, 1200, 300))
    result = Image.open(io.BytesIO(png))
    assert result.mode == "1"
    assert result.width <= 800
    assert set(result.convert("L").get_flattened_data()) == {0, 255}
