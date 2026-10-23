"""JMdict (words) and KANJIDIC2 (kanji) via jamdict's bundled SQLite database."""

import threading
from dataclasses import dataclass

from app.services.kana import to_hiragana


@dataclass(frozen=True)
class KanjiReadings:
    on: list[str]  # hiragana, e.g. ["せい", "しょう"]
    kun: list[str]  # hiragana, okurigana after a dot, e.g. ["い.きる", "なま"]


# jamdict keeps an SQLite connection that only works in the thread that opened it,
# and FastAPI serves requests from a thread pool, so each thread gets its own instance.
@dataclass(frozen=True)
class Sense:
    pos: list[str]  # parts of speech, e.g. ["Ichidan verb", "transitive verb"]
    glosses: list[str]


@dataclass(frozen=True)
class Entry:
    headword: str  # first kanji form, or kana form for kana-only words
    readings: list[str]
    senses: list[Sense]


_local = threading.local()


def _jamdict():
    if not hasattr(_local, "jamdict"):
        from jamdict import Jamdict

        _local.jamdict = Jamdict()
    return _local.jamdict


def _lookup(text: str, *, chars: bool):
    return _jamdict().lookup(text, lookup_chars=chars, lookup_ne=False)


def kanji_readings(kanji: str) -> KanjiReadings:
    result = _lookup(kanji, chars=True)
    on: list[str] = []
    kun: list[str] = []
    for char in result.chars:
        if char.literal != kanji:
            continue
        for group in char.rm_groups:
            for reading in group.readings:
                if reading.r_type == "ja_on":
                    on.append(to_hiragana(reading.value))
                elif reading.r_type == "ja_kun":
                    kun.append(reading.value)
    return KanjiReadings(on=_unique(on), kun=_unique(kun))


def word_readings(text: str) -> list[str]:
    """Kana readings of JMdict entries written exactly as `text`, most common first."""
    readings: list[str] = []
    for entry in _lookup(text, chars=False).entries:
        if any(form.text == text for form in entry.kanji_forms):
            readings.extend(form.text for form in entry.kana_forms)
    return _unique(readings)


def lookup_entries(text: str, limit: int) -> list[Entry]:
    """JMdict entries written or read exactly as `text`."""
    entries: list[Entry] = []
    for raw in _lookup(text, chars=False).entries[:limit]:
        kanji = [form.text for form in raw.kanji_forms]
        kana = [form.text for form in raw.kana_forms]
        senses = [
            Sense(pos=_unique([_short_pos(p) for p in s.pos]), glosses=[g.text for g in s.gloss])
            for s in raw.senses
        ]
        entries.append(Entry(headword=(kanji or kana)[0], readings=kana, senses=senses))
    return entries


def _short_pos(pos: str) -> str:
    # "noun (common) (futsuumeishi)" → "noun"
    return pos.split(" (")[0]


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
