# 0003 — Readings and meanings: morphological analyzer + open dictionaries

**Status:** accepted · 2026-10-23

## Context
Highlighting text should show its reading in hiragana (all readings if ambiguous, e.g. a single
kanji) and, on demand, its meaning. Must be local and open source.

## Decision
- **Contextual reading:** fugashi (MeCab) with UniDic — a statistical analyzer that picks the
  reading that fits the surrounding sentence.
- **All readings of a kanji:** KANJIDIC2 on/kun readings.
- **Alternative word readings and meanings:** JMdict, via `jamdict` + `jamdict-data` (SQLite).

## Why not an LLM?
Dictionaries are exact, instant and never invent readings. A local open-weight LLM is a good
*later* addition for "explain this in context", not for the core lookup.

## Consequences
- JMdict/KANJIDIC2 are CC BY-SA 4.0 — attribution is in the README.
- Lookups are synchronous and fast; no model download needed for this feature.
