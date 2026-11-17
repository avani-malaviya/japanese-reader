"""Readings (yomikata) for a highlighted piece of text.

- A single kanji: every on/kun reading, plus the in-context reading if the kanji is a word by itself.
- Anything else: the in-context reading from the analyzer, plus other dictionary readings of the word.
"""

from dataclasses import dataclass
from typing import Literal

from app.services import analyzer, dictionary
from app.services.kana import has_kanji, is_kanji, to_hiragana

ReadingKind = Literal["on", "kun", "word"]


@dataclass(frozen=True)
class Reading:
    kana: str  # what goes into furigana
    label: str  # what the popup shows, e.g. "い(きる)"
    kind: ReadingKind
    contextual: bool = False


def get_readings(text: str, context: str | None = None, offset: int | None = None) -> list[Reading]:
    if not has_kanji(text):
        kana = to_hiragana(text)
        return [Reading(kana=kana, label=kana, kind="word", contextual=True)]

    in_context = analyzer.reading_of(text, context, offset)

    if len(text) == 1 and is_kanji(text):
        return _kanji_readings(text, in_context, standalone=_is_own_word(text, context, offset))

    known = dictionary.word_readings(text)
    if in_context not in known:
        known = [in_context, *known]
    return [Reading(kana=k, label=k, kind="word", contextual=k == in_context) for k in known]


def _kanji_readings(kanji: str, in_context: str, standalone: bool) -> list[Reading]:
    found = dictionary.kanji_readings(kanji)
    readings = [Reading(kana=r, label=r, kind="on") for r in found.on]
    # Affix markers are stripped, so "なま" and "なま-" collapse into one reading.
    kun = {r.label: r for r in map(_kun_reading, found.kun)}
    readings += kun.values()
    if not standalone:
        return readings
    # The kanji is a whole word here (e.g. 生 read as なま), so mark the reading that fits.
    marked = [
        Reading(r.kana, r.label, r.kind, contextual=True) if r.kana == in_context else r for r in readings
    ]
    if not any(r.contextual for r in marked):
        marked.insert(0, Reading(kana=in_context, label=in_context, kind="word", contextual=True))
    return marked


def _kun_reading(raw: str) -> Reading:
    # KANJIDIC marks okurigana with "." and affix use with "-", e.g. "い.きる", "なま-".
    stem, _, okurigana = raw.strip("-").partition(".")
    label = f"{stem}({okurigana})" if okurigana else stem
    return Reading(kana=stem, label=label, kind="kun")


def _is_own_word(text: str, context: str | None, offset: int | None) -> bool:
    if context is None or offset is None:
        return True
    end = offset + len(text)
    return any(t.start == offset and t.end == end for t in analyzer.tokenize(context))
