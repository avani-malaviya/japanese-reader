from app.services.ocr.base import Box
from app.services.ocr.layout import Columns, PlacedFigure, arrange, is_vertical_page
from app.services.ocr.structure import build_units
from app.services.regions.base import picture_boxes
from tests.factories import block, block_of, line, load_page


def labels(nodes: list) -> list[str]:
    """Reading order, with rows of columns read column by column."""
    out: list[str] = []
    for node in nodes:
        if isinstance(node, Columns):
            out.extend(label for column in node.columns for label in labels(column.children))
        else:
            out.append("[図]" if isinstance(node, PlacedFigure) else node.text)
    return out


def figures(nodes: list) -> list[PlacedFigure]:
    found: list[PlacedFigure] = []
    for node in nodes:
        if isinstance(node, Columns):
            found.extend(f for column in node.columns for f in figures(column.children))
        elif isinstance(node, PlacedFigure):
            found.append(node)
    return found


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
    vertical = block_of([line("日本語を", 5, 0, 10, 10, True), line("読む。", 0, 0, 5, 10, True)], True)
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


def test_how_to_page_pairs_each_photo_with_its_step_and_keeps_sidebar_together() -> None:
    # Shaped like a gardening how-to page: header across the top, steps of photo + text
    # (the text starting a few px above its photo), a sidebar, and a full-width chart below.
    blocks = [
        block("見出し", 0, 0, 1000, 60, vertical=False),
        block("手順1", 360, 95, 700, 160, vertical=False),
        block("手順2", 360, 345, 700, 420, vertical=False),
        block("豆知識", 760, 330, 1000, 600, vertical=False),
    ]
    photo1, photo2, chart = Box(0, 100, 340, 300), Box(0, 350, 340, 550), Box(0, 700, 1000, 900)
    assert labels(arrange(blocks, [photo1, photo2, chart])) == [
        "見出し",
        "[図]",
        "手順1",
        "[図]",
        "手順2",
        "豆知識",
        "[図]",
    ]


def test_skewed_phone_photo_of_a_how_to_page() -> None:
    # Recorded from a real phone photo (slightly skewed) of a gardening book page: five step
    # photos, each with its text to the right, and two sidebars further right.
    blocks, regions = load_page("howto_page_photo.json")
    order = labels(arrange(blocks, picture_boxes(regions)))
    steps = ["ラッカセイは肥料が", "１ヶ所に対して", "本葉が２枚程度", "花が咲きはじめたら"]
    for step in steps:
        index = next(i for i, text in enumerate(order) if text.startswith(step))
        assert order[index - 1] == "[図]", f"{step} should follow its photo"
    tips = next(i for i, text in enumerate(order) if "豆知識" in text)
    assert tips > next(i for i, text in enumerate(order) if text.startswith("本葉が"))


def test_after_structure_photos_still_pair_with_their_steps() -> None:
    # Same page after headings are split out and margin tabs dropped (the real pipeline).
    blocks, regions = load_page("howto_page_photo.json")
    order = labels(arrange(build_units(blocks, regions), picture_boxes(regions)))
    for step in ["ラッカセイは肥料が", "１ヶ所に対して", "本葉が２枚程度", "花が咲きはじめたら"]:
        index = next(i for i, text in enumerate(order) if text.startswith(step))
        assert order[index - 1] == "[図]", f"{step} should follow its photo"


def test_wide_pictures_are_centred_and_narrow_ones_float_to_their_side() -> None:
    text = block("本文", 0, 0, 1000, 50, vertical=False)
    wide, left, right = Box(0, 100, 900, 400), Box(0, 500, 400, 800), Box(600, 900, 1000, 1200)
    assert [(f.align, f.width_ratio) for f in figures(arrange([text], [wide, left, right]))] == [
        ("center", 0.9),
        ("left", 0.4),
        ("right", 0.4),
    ]


def test_two_text_columns_become_a_row_of_columns() -> None:
    blocks = [
        block("見出し", 0, 0, 1000, 60, vertical=False),
        block("左上", 0, 100, 600, 300, vertical=False),
        block("左下", 0, 320, 600, 500, vertical=False),
        block("右", 700, 100, 1000, 500, vertical=False),
    ]
    heading, row = arrange(blocks, [])
    assert heading.text == "見出し"
    assert isinstance(row, Columns)
    assert [labels(c.children) for c in row.columns] == [["左上", "左下"], ["右"]]
    assert [c.width_ratio for c in row.columns] == [round(600 / 900, 3), round(300 / 900, 3)]


def test_picture_beside_text_floats_instead_of_making_columns() -> None:
    blocks = [block("説明", 500, 0, 1000, 200, vertical=False)]
    nodes = arrange(blocks, [Box(0, 0, 400, 300)])
    assert not any(isinstance(n, Columns) for n in nodes)
    assert [(f.align) for f in figures(nodes)] == ["left"]


def test_vertical_pages_stay_one_column() -> None:
    blocks = [
        block("右の段", 700, 0, 760, 500, vertical=True),
        block("左の段", 0, 0, 60, 500, vertical=True),
    ]
    nodes = arrange(blocks, [])
    assert labels(nodes) == ["右の段", "左の段"]
    assert not any(isinstance(n, Columns) for n in nodes)


def test_how_to_page_keeps_the_tips_sidebar_as_a_column() -> None:
    blocks, regions = load_page("howto_page_photo.json")
    nodes = arrange(build_units(blocks, regions), picture_boxes(regions))
    rows = [n for n in nodes if isinstance(n, Columns)]
    sidebar_columns = [
        c for row in rows for c in row.columns if any("豆知識" in label for label in labels(c.children))
    ]
    assert sidebar_columns, "栽培の豆知識 should sit in its own column"
