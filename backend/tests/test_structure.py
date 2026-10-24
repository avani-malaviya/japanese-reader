from app.services.ocr.base import Box, TextBlock
from app.services.ocr.structure import build_units
from app.services.regions.base import Region
from tests.factories import block, block_of, line, load_page

BODY = "本文の行はこのくらいの長さがあります。"


def roles(units: list[TextBlock]) -> list[tuple[str, str, int]]:
    return [(u.text, u.role, u.level) for u in units]


def test_title_region_splits_a_heading_out_of_its_block() -> None:
    merged = block_of(
        [line("栽培のポイント", 0, 0, 300, 40), line(BODY, 0, 50, 700, 90), line(BODY, 0, 100, 700, 140)],
        vertical=False,
    )
    regions = [Region(Box(0, 0, 320, 45), "title", 0.9)]
    assert roles(build_units([merged], regions)) == [
        ("栽培のポイント", "heading", 2),
        (BODY + BODY, "body", 0),
    ]


def test_page_furniture_is_dropped() -> None:
    blocks = [block(BODY, 100, 0, 800, 40, vertical=False), block("基本編", 0, 0, 40, 200, vertical=True)]
    regions = [Region(Box(0, 0, 50, 1000), "abandon", 0.8)]
    assert [u.text for u in build_units(blocks, regions)] == [BODY]


def test_big_short_text_is_a_heading_and_the_biggest_is_the_title() -> None:
    blocks = [
        block("ラッカセイ", 0, 0, 400, 80, vertical=False),  # 2x body size
        block("保存法", 0, 100, 200, 150, vertical=False),  # 1.25x
        block(BODY, 0, 200, 800, 240, vertical=False),
        block(BODY, 0, 250, 800, 290, vertical=False),
        block(BODY, 0, 300, 800, 340, vertical=False),
    ]
    assert roles(build_units(blocks, []))[:3] == [
        ("ラッカセイ", "heading", 1),
        ("保存法", "heading", 2),
        (BODY, "body", 0),
    ]


def test_long_text_is_never_a_size_heading() -> None:
    blocks = [block(BODY * 2, 0, 0, 800, 120, vertical=False), block(BODY, 0, 200, 800, 240, vertical=False)]
    assert [u.role for u in build_units(blocks, [])] == ["body", "body"]


def test_caption_region() -> None:
    blocks = [block("図１　畑の様子", 0, 500, 300, 530, vertical=False), block(BODY, 0, 0, 800, 40, vertical=False)]
    regions = [Region(Box(0, 490, 320, 540), "caption", 0.7)]
    assert build_units(blocks, regions)[0].role == "caption"


def test_real_how_to_page_structure() -> None:
    units = build_units(*load_page("howto_page_photo.json"))
    headings = {u.text: u.level for u in units if u.role == "heading"}
    assert headings["ラッカセイ（マメ科）"] == 1
    for subtitle in ["裁培のポイント", "ススメ品種", "裁培の豆知識", "味存法", "作業タイミングの目安"]:
        assert headings[subtitle] == 2, subtitle
    texts = [u.text for u in units]
    for tab in ["基本編", "栽培編・春夏", "裁培記録ノート", "その他"]:
        assert tab not in texts
    # The body under 栽培の豆知識 is split away from its heading.
    assert any(t.startswith("土が乾燥している") for t in texts)
