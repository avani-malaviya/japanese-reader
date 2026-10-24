from app.services.ocr.base import Ruby
from app.services.ocr.furigana import extract
from tests.factories import block, block_of, line

# Horizontal base line: 10 characters, 40 px each, from x=0 to x=400, y=100..140.
BASE_H = "昨日は友達と映画を見"  # 昨日 0-2, 友達 3-5, 映画 6-8, 見 9


def test_horizontal_furigana_above_attach_to_the_kanji_below() -> None:
    blocks = [
        block(BASE_H, 0, 100, 400, 140, vertical=False),
        block("きのう", 10, 78, 70, 98, vertical=False),  # over 昨日 (x 0-80)
        block("えいが", 250, 78, 310, 98, vertical=False),  # over 映画 (x 240-320)
    ]
    [result] = extract(blocks)
    assert result.text == BASE_H
    assert result.ruby == (Ruby(0, 2, "きのう"), Ruby(6, 8, "えいが"))


def test_vertical_furigana_right_of_the_column() -> None:
    # Column x=100..140, characters 40 px tall from y=0: 友達 is y 120-200.
    base = line("昨日は友達と", 100, 0, 140, 240, vertical=True)
    ruby = line("ともだち", 142, 125, 162, 195, vertical=True)
    [result] = extract([block_of([ruby, base], vertical=True)])
    assert result.text == "昨日は友達と"
    assert result.ruby == (Ruby(3, 5, "ともだち"),)


def test_furigana_over_kana_is_dropped() -> None:
    blocks = [
        block(BASE_H, 0, 100, 400, 140, vertical=False),
        block("はは", 85, 78, 115, 98, vertical=False),  # over は (x 80-120)
    ]
    [result] = extract(blocks)
    assert result.ruby == ()


def test_ordinary_kana_lines_are_kept() -> None:
    blocks = [
        block(BASE_H, 0, 100, 400, 140, vertical=False),
        block("ありがとう", 0, 160, 200, 200, vertical=False),  # same size, below: just text
    ]
    assert [b.text for b in extract(blocks)] == [BASE_H, "ありがとう"]


def test_ruby_offsets_follow_line_joins() -> None:
    first = line("今日は", 0, 0, 120, 40)
    second = line("映画を", 0, 50, 120, 90)
    ruby = line("えいが", 5, 30, 75, 48)  # above 映画 on the second line
    [result] = extract([block_of([first, second, ruby], vertical=False)])
    assert result.text == "今日は映画を"
    assert result.ruby == (Ruby(3, 5, "えいが"),)
