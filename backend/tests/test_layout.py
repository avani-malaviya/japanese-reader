from app.services.ocr.base import Box, TextBlock
from app.services.ocr.layout import PlacedFigure, arrange, is_vertical_page


def block(text: str, x1: float, y1: float, x2: float, y2: float, vertical: bool) -> TextBlock:
    return TextBlock(box=Box(x1, y1, x2, y2), vertical=vertical, lines=[text])


def labels(elements: list) -> list[str]:
    return ["[図]" if isinstance(e, PlacedFigure) else e.text for e in elements]


def test_vertical_page_reads_right_to_left() -> None:
    blocks = [
        block("左", 0, 0, 10, 100, vertical=True),
        block("右", 40, 0, 50, 100, vertical=True),
        block("中", 20, 5, 30, 90, vertical=True),
    ]
    assert labels(arrange(blocks, [])) == ["右", "中", "左"]


def test_vertical_page_reads_top_tier_first() -> None:
    blocks = [
        block("下右", 40, 200, 50, 300, vertical=True),
        block("上左", 0, 0, 10, 100, vertical=True),
        block("上右", 40, 0, 50, 100, vertical=True),
    ]
    assert labels(arrange(blocks, [])) == ["上右", "上左", "下右"]


def test_horizontal_page_reads_columns_left_to_right() -> None:
    blocks = [
        block("右上", 200, 0, 300, 10, vertical=False),
        block("左下", 0, 50, 100, 60, vertical=False),
        block("左上", 0, 0, 100, 10, vertical=False),
    ]
    assert labels(arrange(blocks, [])) == ["左上", "左下", "右上"]


def test_orientation_follows_dominant_area() -> None:
    big_vertical = block("縦", 0, 0, 50, 500, vertical=True)
    small_horizontal = block("横", 0, 0, 100, 10, vertical=False)
    assert is_vertical_page([big_vertical, small_horizontal])
    assert not is_vertical_page([small_horizontal])
    assert not is_vertical_page([])


def test_lines_join_into_one_horizontal_paragraph() -> None:
    vertical = TextBlock(box=Box(0, 0, 10, 10), vertical=True, lines=["日本語を ", "読む。"])
    assert vertical.text == "日本語を読む。"


def test_figure_sits_between_paragraphs_in_reading_order() -> None:
    blocks = [
        block("上", 0, 0, 1000, 50, vertical=False),
        block("下", 0, 700, 1000, 750, vertical=False),
    ]
    figure = Box(0, 100, 1000, 600)
    assert labels(arrange(blocks, [figure])) == ["上", "[図]", "下"]


def test_text_inside_a_figure_follows_it() -> None:
    blocks = [
        block("看板", 400, 300, 600, 350, vertical=False),  # a sign in the photo
        block("本文", 0, 700, 1000, 750, vertical=False),
    ]
    figure = Box(0, 100, 1000, 600)
    assert labels(arrange(blocks, [figure])) == ["[図]", "看板", "本文"]


def test_wide_figures_are_centred_and_narrow_ones_float_to_their_side() -> None:
    text = block("本文", 0, 0, 1000, 50, vertical=False)
    wide, left, right = Box(0, 100, 900, 400), Box(0, 500, 400, 800), Box(600, 900, 1000, 1200)
    figures = [e for e in arrange([text], [wide, left, right]) if isinstance(e, PlacedFigure)]
    assert [(f.align, f.width_ratio) for f in figures] == [
        ("center", 0.9),
        ("left", 0.4),
        ("right", 0.4),
    ]
