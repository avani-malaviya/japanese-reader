# 0005 — Page structure: regions + text size → headings, columns, furigana

**Status:** accepted · 2026-10-24

## Context
A flat list of paragraphs loses what makes a page readable: its title and subtitles, its columns
and sidebars. Printed furigana came out as stray lines of kana. We want a close recreation in
one consistent editor style, extracted generically from any page.

## Decision
The pipeline after OCR (`services/ocr/service.py`):

1. **Furigana** (`furigana.py`): an all-kana line much thinner than an adjacent line (above it
   in horizontal text, right of it in vertical text) is furigana. Its position along that line
   picks the kanji run it reads; it becomes ruby there, or is dropped if it sits over kana.
2. **Structure** (`structure.py`): every OCR line is matched to the DocLayout-YOLO region its
   centre is in. Blocks are split where the region changes (OCR often merges a heading with its
   body). `title` regions, or short text ≥ 1.2× the body size, become headings; the biggest is
   the page title. `caption` regions become captions; `abandon` regions (page numbers, tabs,
   running headers) are dropped.
3. **Layout** (`layout.py`): recursive XY-cut at the widest gap (bands preferred over narrow
   gutters, slight overlaps tolerated for skewed photos; a column of pictures beside text is
   read as rows). On horizontal pages, column cuts are kept as a tree of side-by-side columns;
   a single picture beside text floats instead.

The editor renders headings as `h1`/`h2`, captions, columns and ruby with one house style
(DESIGN_RULES), so structure carries over but each page's typography does not.

## Why not a vision-language model?
A VLM could describe structure directly, but it is large, slow and can invent text. The layout
model is already loaded for pictures, and geometric rules are inspectable and testable against
recorded pages (`tests/fixtures/`).

## Consequences
- Thresholds are heuristics tuned on real pages; each one is a named constant with its reason.
  New page types should be added as recorded fixtures with tests before tuning.
- Vertical pages are flattened into one column (their columns are lines once horizontal).
- Columns are plain `div`s inside the editable page; editing across column boundaries is
  possible but crude.
