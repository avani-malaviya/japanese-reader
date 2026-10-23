"""Dictionary meanings for a highlighted piece of text. Word-level only: no sentence translation."""

from dataclasses import dataclass

from app.services import analyzer, dictionary
from app.services.dictionary import Entry


@dataclass(frozen=True)
class Meaning:
    looked_up: str  # what was found in the dictionary; differs from the selection if inflected
    entries: list[Entry]


def get_meaning(text: str, limit: int) -> Meaning:
    entries = dictionary.lookup_entries(text, limit)
    if entries:
        return Meaning(looked_up=text, entries=entries)

    # Inflected or multi-word selection (食べました): look up the first word's dictionary form.
    tokens = analyzer.tokenize(text)
    if tokens and tokens[0].lemma != text:
        lemma = tokens[0].lemma
        return Meaning(looked_up=lemma, entries=dictionary.lookup_entries(lemma, limit))
    return Meaning(looked_up=text, entries=[])
