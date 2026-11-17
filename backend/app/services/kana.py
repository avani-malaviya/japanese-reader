_KATAKANA_START, _KATAKANA_END = ord("ァ"), ord("ヶ")
_KANA_OFFSET = ord("ァ") - ord("ぁ")


def to_hiragana(text: str) -> str:
    return "".join(
        chr(ord(ch) - _KANA_OFFSET) if _KATAKANA_START <= ord(ch) <= _KATAKANA_END else ch for ch in text
    )


def is_kanji(ch: str) -> bool:
    # CJK Unified Ideographs + Extension A, plus the iteration mark 々.
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿" or ch == "々"


def has_kanji(text: str) -> bool:
    return any(is_kanji(ch) for ch in text)
