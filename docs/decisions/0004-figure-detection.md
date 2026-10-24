# 0004 — Pictures: DocLayout-YOLO detection, 1-bit dithering, flow placement

**Status:** accepted · 2026-10-24

## Context
Pages often contain photos and illustrations (pamphlets, magazines). The text detector
(ADR 0001) ignores them, so they were silently dropped. We want them back, in the app's
black-and-white style, roughly where they were on the page.

## Decision
- **Detection:** DocLayout-YOLO (`juliozhao/DocLayout-YOLO-DocStructBench`, ~40 MB), a
  document-layout model trained on varied documents. We keep only its `figure` class
  (score ≥ 0.4, ignoring specks under 0.5% of the page). It sits behind the `LayoutDetector`
  interface (`services/regions/base.py`).
- **Rendering:** crop → grayscale → autocontrast → ≤ 800 px wide → Floyd–Steinberg 1-bit PNG
  (`services/images.py`). Sent to the browser as data URIs and stored inside the document.
- **Placement:** a flow approximation, not pixel positions, because the text is reflowed anyway.
  Pictures take part in reading order like text blocks. Pictures wider than 60% of the content
  are centred; narrower ones float to the side they were on, and text wraps around them.
- **Text inside pictures** (signs, labels, speech bubbles) stays as editable paragraphs placed
  right after the picture, so nothing readable is lost.

## Consequences
- One more model to load (~3 s on first use). OCR and detection run one after the other.
- DocLayout-YOLO is AGPL-3.0. Fine for a personal local tool; revisit before distribution.
- Its other classes (title, plain text, caption) could later fix how book pages split into
  short paragraphs (ADR 0001 consequence).
- Data-URI pictures count against the browser's ~5 MB localStorage quota. The status bar warns
  when a save fails; server-side document storage is the real fix.
