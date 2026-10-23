"""Morphological analysis (MeCab via fugashi, UniDic dictionary): splits text into words
and gives each word the reading that fits its context."""

import threading
from dataclasses import dataclass
from functools import cache

from app.services.kana import to_hiragana


@dataclass(frozen=True)
class Token:
    surface: str
    start: int
    end: int
    reading: str  # hiragana
    lemma: str  # dictionary form, e.g. 食べ → 食べる


_lock = threading.Lock()


@cache
def _tagger():
    import fugashi

    return fugashi.Tagger()


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0
    with _lock:
        words = list(_tagger()(text))
    for word in words:
        # MeCab drops whitespace, so locate each surface in the original text.
        start = text.index(word.surface, position)
        end = start + len(word.surface)
        kana = getattr(word.feature, "kana", None)
        # UniDic tags loanword lemmas with their origin, e.g. "コーヒー-coffee".
        lemma = (getattr(word.feature, "lemma", None) or word.surface).split("-")[0]
        tokens.append(Token(word.surface, start, end, to_hiragana(kana or word.surface), lemma))
        position = end
    return tokens


def reading_of(text: str, context: str | None = None, offset: int | None = None) -> str:
    """Reading of `text`, using `context` (the text it sits in, at `offset`) when the
    selection lines up with word boundaries there. Otherwise reads `text` on its own."""
    if context is not None and offset is not None and context[offset : offset + len(text)] == text:
        end = offset + len(text)
        covering = [t for t in tokenize(context) if t.end > offset and t.start < end]
        if covering and covering[0].start == offset and covering[-1].end == end:
            return "".join(t.reading for t in covering)
    return "".join(t.reading for t in tokenize(text))
