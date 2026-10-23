from app.services.meaning import get_meaning


def glosses(text: str) -> list[str]:
    return [g for e in get_meaning(text, limit=5).entries for s in e.senses for g in s.glosses]


def test_word_meaning() -> None:
    assert "Japan" in glosses("日本")


def test_kana_word_meaning() -> None:
    assert "to eat" in glosses("たべる")


def test_inflected_selection_uses_dictionary_form() -> None:
    meaning = get_meaning("食べました", limit=5)
    assert meaning.looked_up == "食べる"
    assert "to eat" in glosses("食べました")


def test_unknown_text_has_no_entries() -> None:
    assert get_meaning("ぬぬぬぬ", limit=5).entries == []
