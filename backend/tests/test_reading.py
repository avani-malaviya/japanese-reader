from app.services.analyzer import reading_of
from app.services.kana import to_hiragana
from app.services.reading import get_readings


def kanas(text: str, **kwargs) -> list[str]:
    return [r.kana for r in get_readings(text, **kwargs)]


def contextual(text: str, **kwargs) -> list[str]:
    return [r.kana for r in get_readings(text, **kwargs) if r.contextual]


def test_to_hiragana() -> None:
    assert to_hiragana("カタカナとひらがな") == "かたかなとひらがな"


def test_single_kanji_lists_all_on_and_kun_readings() -> None:
    readings = get_readings("生")
    on = [r.kana for r in readings if r.kind == "on"]
    kun = [r.label for r in readings if r.kind == "kun"]
    assert {"せい", "しょう"} <= set(on)
    assert {"い(きる)", "なま"} <= set(kun)
    assert len(kun) == len(set(kun))


def test_kanji_inside_a_word_has_no_contextual_reading() -> None:
    sentence = "先生が来た"
    assert contextual("生", context=sentence, offset=1) == []


def test_word_lists_dictionary_readings() -> None:
    assert {"にほん", "にっぽん"} <= set(kanas("日本"))


def test_word_reading_uses_context() -> None:
    sentence = "今日は晴れです"
    assert contextual("今日", context=sentence, offset=0) == ["きょう"]


def test_conjugated_phrase_gets_analyzer_reading() -> None:
    assert kanas("行きます") == ["いきます"]


def test_selection_splitting_a_word_falls_back_to_reading_alone() -> None:
    # "本" inside "日本" is not a word boundary in the context.
    assert reading_of("本", context="日本", offset=1) == reading_of("本")


def test_kana_only_selection_reads_as_itself() -> None:
    assert kanas("コーヒー") == ["こーひー"]
