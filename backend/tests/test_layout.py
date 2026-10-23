from app.services.ocr.base import Box, TextBlock
from app.services.ocr.layout import is_vertical_page, order_blocks, to_result


def block(text: str, x1: float, y1: float, x2: float, y2: float, vertical: bool) -> TextBlock:
    return TextBlock(box=Box(x1, y1, x2, y2), vertical=vertical, lines=[text])


def texts(blocks: list[TextBlock]) -> list[str]:
    return [b.text for b in blocks]


def test_vertical_page_reads_right_to_left() -> None:
    blocks = [
        block("左", 0, 0, 10, 100, vertical=True),
        block("右", 40, 0, 50, 100, vertical=True),
        block("中", 20, 5, 30, 90, vertical=True),
    ]
    assert texts(order_blocks(blocks)) == ["右", "中", "左"]


def test_vertical_page_reads_top_tier_first() -> None:
    blocks = [
        block("下右", 40, 200, 50, 300, vertical=True),
        block("上左", 0, 0, 10, 100, vertical=True),
        block("上右", 40, 0, 50, 100, vertical=True),
    ]
    assert texts(order_blocks(blocks)) == ["上右", "上左", "下右"]


def test_horizontal_page_reads_columns_left_to_right() -> None:
    blocks = [
        block("右上", 200, 0, 300, 10, vertical=False),
        block("左下", 0, 50, 100, 60, vertical=False),
        block("左上", 0, 0, 100, 10, vertical=False),
    ]
    assert texts(order_blocks(blocks)) == ["左上", "左下", "右上"]


def test_orientation_follows_dominant_area() -> None:
    big_vertical = block("縦", 0, 0, 50, 500, vertical=True)
    small_horizontal = block("横", 0, 0, 100, 10, vertical=False)
    assert is_vertical_page([big_vertical, small_horizontal])
    assert not is_vertical_page([small_horizontal])


def test_lines_join_into_one_horizontal_paragraph() -> None:
    vertical = TextBlock(box=Box(0, 0, 10, 10), vertical=True, lines=["日本語を ", "読む。"])
    empty = TextBlock(box=Box(20, 0, 30, 10), vertical=True, lines=[" "])
    result = to_result([vertical, empty])
    assert result.paragraphs == ["日本語を読む。"]
