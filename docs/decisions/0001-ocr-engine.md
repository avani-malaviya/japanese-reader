# 0001 — OCR engine: text detector + manga-ocr

**Status:** accepted · 2026-10-23

## Context
Input is a photo of a page that may contain vertical (縦書き) or horizontal (横書き) Japanese,
often mixed (e.g. pamphlets). We need open-source, local OCR that copes with both and gives us
text in reading order.

## Options considered
- **Local VLM (e.g. Qwen2.5-VL via Ollama)** — reads whole pages well, but large (~6 GB),
  slow, and can hallucinate text that is not on the page.
- **Tesseract `jpn` / `jpn_vert`** — light, but weak on real-world photos.
- **Text detector + manga-ocr** — small models, very accurate per text line in both orientations.

## Decision
Use comic-text-detector (as packaged in `mokuro`) to find text blocks and their orientation,
and `manga-ocr` to recognise each line. Our own `layout.py` decides reading order and joins
lines into horizontal paragraphs.

## Consequences
- The detector is tuned for manga; dense book pages may fragment into many small blocks.
- The engine sits behind the `OcrEngine` interface (`services/ocr/base.py`) so a book-oriented
  engine (e.g. NDLOCR) or a VLM can be added later without touching the API or frontend.
- comic-text-detector is GPL-3.0. Fine for a personal local tool; revisit before any distribution.
