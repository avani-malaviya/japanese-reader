# Japanese Reader

Read real Japanese — pamphlets, book pages, signs — **with assistance instead of translation**.

Take a photo of a page, get it back as an editable typed document, and look things up only
when you need to: highlight a word or kanji to see its reading (yomikata), stamp furigana
under its next few occurrences, or peek at its dictionary meaning.

Everything runs locally and uses only open-source models and open data.

---

## Status

**v0 — done.** One screen: open an image, edit the text, look things up. See [Roadmap](#roadmap).

## Features (v0)

| Feature | What it does |
|---|---|
| **Library desktop** | The app opens on a pastel retro desktop. Make a folder per book, or one for pamphlets (**[ NEW FOLDER ]**); open it to see its documents; **New document** starts a pamphlet or a chapter. Rename (F2) and delete (Delete) folders and documents. Everything is saved on your machine (SQLite), so documents and pictures are no longer limited by browser storage. |
| **Open image** | Upload a photo/scan from your computer. Each new page is **added at the cursor** (after a dashed page break), so press Enter at the end and open the next page. **[ NEW ]** starts over. |
| **OCR** | Detects text (vertical *or* horizontal) and recognises it. Vertical text is converted to horizontal so every document reads the same way. |
| **Page structure** | The page is recreated in one house style: the page title becomes a heading, subtitles become subheadings, captions are styled as captions, and **columns and sidebars stay side by side**. Page furniture (page numbers, margin tabs, running headers) is left out. |
| **Printed furigana** | Furigana printed on the page become real furigana on the right kanji, instead of stray lines of kana. |
| **Pictures** | Photos and illustrations are cut out, dithered to pure black and white, and placed where they sat: wide ones centred, narrow ones floated beside their text. Click a picture to **align** it (◧ ▣ ◨), **resize** it (corner handle), **move** it (drag; a bar shows where it lands, columns included) or **delete** it. Text inside a picture follows it as normal paragraphs. |
| **Editor** | The OCR result lands in a simple word-processor page. Fix mistakes, delete noise, type freely. Paste is always plain text. Autosaved in the browser. |
| **Reading** | Highlight text → a box appears beside it with the reading in hiragana. A single kanji shows *all* its readings (音 / 訓); a word shows its dictionary readings with the one that fits the sentence marked `◆ in context`. |
| **Insert** | Adds the chosen reading as furigana *below* the selected text and the occurrences after it (5 in total). |
| **Remove** | Click any furigana → **Remove** (just that one) or **Remove all** (same word + reading everywhere). |
| **Meaning** | Shows dictionary entries (part of speech + glosses) for the selection. Inflected words (話しました) are looked up by dictionary form (話す). Word-level only — no sentence translation, on purpose. |
| **Notes** | Highlight a word or line → **[ NOTE ]** and type your own note. It appears in **red**: right under a word for short selections, or on a red line under the paragraph (with the text underlined) for longer ones. Click a note to edit or delete it. Notes are saved with the document and never get furigana. |
| **Ask AI** | Sends the highlighted text and its sentence to **your own ChatGPT or Claude account** with a saved grammar template: dictionary form and meaning, conjugation type and rules, the pattern and how it attaches to nouns / i-adjectives / na-adjectives / verbs, examples. Edit the template once (**Save as default**), or add a note per question. The answer opens in a floating window over the app; **[ AI CHAT ]** brings it back. No API keys; nothing is sent until you press Send. |

## Using it

0. On the desktop, double-click a folder (or make one with **[ NEW FOLDER ]**), then **New document**
   (or double-click an existing one). **[ ◂ DESKTOP ]** in the editor goes back; work is autosaved.
1. **[ OPEN IMAGE… ]** → pick a photo. The status bar shows progress; the first read of a session
   takes ~30 s while models load, then a few seconds per page. For a multi-page text, put the
   cursor at the end (or press Enter there) and open the next page.
2. Fix anything the OCR got wrong directly on the page.
3. Highlight a word or a single kanji. In the box beside it:
   - click a reading to choose it, then **[ INSERT ]** to add it as furigana;
   - **[ MEANING ]** toggles dictionary entries.
4. `Esc` or clicking elsewhere closes the box.
5. **[ ASK AI ]** in the box opens the Ask AI panel: add an optional note, pick ChatGPT or Claude,
   **[ SEND ]**. The first time, Chrome may ask you to allow pop-ups for `localhost`. You need to be
   logged in to that service in this browser. **[ AI CHAT ]** in the toolbar shows the chat again.
   For the floating window, don't use full screen: in full screen Chrome opens pop-ups as tabs.
   To fill the screen and keep the floating window, maximise instead (double-click the window's
   title bar, or ⌥-click the green button).

Settings worth knowing: the number of occurrences that get furigana is `FURIGANA_OCCURRENCES`
in [frontend/js/config.js](frontend/js/config.js); backend limits are in
[backend/app/config.py](backend/app/config.py).

## Architecture

```
 Browser (vanilla JS, no build)              Python backend (FastAPI, localhost:8000)
 ┌───────────────────────────┐               ┌──────────────────────────────────────────────┐
 │ ui/upload.js ───────┐     │ POST /api/ocr │ api/ocr.py ─► services/ocr/service.py        │
 │ ui/lookup-popup.js ─┤     │ ─────────────►│                 ├ mokuro_engine.py           │
 │ ui/meaning-view.js  │     │               │                 │   comic-text-detector      │
 │ ui/statusbar.js     ▼     │               │                 │   + manga-ocr              │
 │               js/api.js   │               │                 ├ regions/doclayout_detector │
 │                           │               │                 │   DocLayout-YOLO (pictures)│
 │                           │               │                 ├ layout.py  (reading order) │
 │                           │               │                 └ images.py  (1-bit dither)  │
 │                           │ POST          │                                              │
 │ editor/editor.js          │  /api/reading │ api/lookup.py ─► services/reading.py         │
 │ editor/selection.js       │ ─────────────►│                 services/meaning.py          │
 │ editor/furigana.js        │  /api/meaning │                   ├ analyzer.py   fugashi    │
 │ editor/storage.js         │               │                   └ dictionary.py JMdict,    │
 │   (localStorage)          │               │                                   KANJIDIC2  │
 │                           │◄──────────────│ static files: frontend/                      │
 └───────────────────────────┘               └──────────────────────────────────────────────┘
```

**Layering**

- `backend/app/api/` — HTTP only: routing, request/response schemas, error mapping.
- `backend/app/services/` — domain logic. Knows nothing about HTTP. Each external model or
  dataset sits behind a small interface so it can be swapped (e.g. a different OCR engine).
- `frontend/js/api.js` — the *only* place the frontend talks to the backend.
- `frontend/js/editor/` — the document: content, furigana, persistence.
- `frontend/js/ui/` — chrome around the document: toolbar, popups, status bar.

Dependencies point inward: `api → services`, `ui → editor`, `ui/editor → api.js`. Never the reverse.

### Models & data (all open)

| Purpose | Component | License |
|---|---|---|
| Text detection | [comic-text-detector](https://github.com/dmMaze/comic-text-detector) (via [mokuro](https://github.com/kha-white/mokuro)) | GPL-3.0 |
| Picture detection | [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO) (DocStructBench weights) | AGPL-3.0 |
| Line OCR | [manga-ocr](https://github.com/kha-white/manga-ocr) (`kha-white/manga-ocr-base`) | Apache-2.0 |
| Contextual reading | [fugashi](https://github.com/polm/fugashi) (MeCab) + UniDic | MIT / BSD |
| Kanji readings | [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) | CC BY-SA 4.0 |
| Meanings | [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via [jamdict](https://github.com/neocl/jamdict) | CC BY-SA 4.0 / MIT |

Why these: see [docs/decisions/](docs/decisions/).

## Repository layout

```
README.md                    this file — design, plan, how to run
docs/DESIGN_RULES.md         visual + code rules every change should follow
docs/decisions/              short architecture decision records (ADRs)

backend/                     uv project (Python 3.12)
  app/main.py                create_app(): API routers + static frontend
  app/config.py              limits and settings
  app/api/                   HTTP layer: ocr.py, lookup.py, schemas.py, health.py
  app/services/ocr/          base.py (OcrEngine interface), mokuro_engine.py, service.py (pipeline),
                             furigana.py (printed ruby), structure.py (headings, captions, furniture),
                             layout.py (XY-cut reading order → columns tree)
  app/services/regions/      base.py (LayoutDetector interface), doclayout_detector.py
  app/services/images.py     crop + 1-bit dither pictures
  app/services/reading.py    readings for a selection
  app/services/meaning.py    dictionary meanings for a selection
  app/services/analyzer.py   fugashi/UniDic tokenizer
  app/services/dictionary.py JMdict + KANJIDIC2
  app/services/kana.py       kana helpers
  app/services/library.py    folders + documents in SQLite (backend/data/library.sqlite)
  app/api/library.py         /api/folders, /api/documents
  tests/                     pytest; OCR API tests use a fake engine

frontend/                    served as-is, no build
  index.html
  css/tokens.css             every colour, font and size
  css/base.css, components.css
  js/main.js                 wiring only
  js/api.js                  every backend call
  js/config.js               frontend settings
  js/editor/                 the document: editor, selection, furigana, storage
  js/ui/                     around the document: upload, lookup popup, meaning view, status bar,
                             picture controls, Ask AI box
  js/ai/                     Ask AI: prompt template, handoff to ChatGPT / Claude
  js/desktop/                the library desktop: icons, folder windows, dialogs, clock
  js/screens/                the editor screen (open / autosave a library document)
  js/router.js               #/ desktop · #/folder/<id> · #/doc/<id>
```

## Running locally ("deployment")

The app is a single local process: the backend serves both the API and the frontend.

**Requirements:** macOS/Linux, ~3 GB free disk (≈1.5 GB Python env incl. PyTorch, ≈0.9 GB
models), internet for the first run only. Runs on Apple Silicon GPU (MPS) when available.

```sh
# 1. one-time: install uv (Python package/runtime manager), then open a new shell
#    (or: source $HOME/.local/bin/env)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. install dependencies (uv fetches Python 3.12 automatically)
cd backend
uv sync

# 3. run
uv run uvicorn app.main:app --reload --port 8000

# 4. open
open http://localhost:8000
```

The first OCR request downloads the text-detector and manga-ocr weights into the local
Hugging Face / mokuro caches; after that the app works fully offline. The dictionaries
(JMdict, KANJIDIC2, UniDic-lite) ship inside Python packages, so lookups never need the network.

**Tests:** `cd backend && uv run pytest`

## Known limitations (v0)

- The text detector is tuned for manga; dense book pages can come out as many short paragraphs,
  and very small print may be missed. The engine is swappable (see ADR 0001).
- Selections must stay within one paragraph and be ≤ 50 characters.
- The analyzer's contextual pick is occasionally debatable (日本 → にっぽん); all dictionary
  readings are always listed so you can choose.
- The library lives in one file, `backend/data/library.sqlite`. Back it up by copying that file
  (with the server stopped). Folders are one level deep.
- Layout is a structural recreation (order, headings, columns, picture size and side), not exact
  positions. Heading detection relies on the layout model plus text size; unusual designs can
  produce a missed or extra heading, which you can retype as normal text.
- Printed furigana are only recovered when the OCR reads them; very small ruby is sometimes missed.
- Columns are recreated on horizontal pages only; vertical pages become a single column.
- Ask AI answers live in the ChatGPT/Claude window, not in the document. Pre-filling relies on
  their `?q=` links; if that ever stops working, the prompt is on your clipboard to paste.

## Roadmap

**v0 (done)** — one commit each, see `git log`:

- [x] Repo, README, design rules, ADRs
- [x] Backend scaffold (FastAPI, health endpoint, static hosting)
- [x] Frontend shell in the B/W retro style
- [x] OCR interfaces + reading-order layout
- [x] OCR engine (detector + manga-ocr) and `/api/ocr`
- [x] Upload image → text in editor
- [x] Editable document with autosave
- [x] Reading service and `/api/reading`
- [x] Selection popup with readings
- [x] Insert furigana under the next 5 occurrences; click to remove
- [x] Meaning lookup and `/api/meaning`

**v0.2 (done)**

- [x] Pictures: detect, dither, place; select, align, resize, move
- [x] Multi-page documents: new pages added at the cursor
- [x] Printed furigana → ruby
- [x] Page structure: headings, captions, page furniture, columns
- [x] Ask AI: grammar template handed to your ChatGPT / Claude account

**v0.3 (done)**

- [x] Library: folders and documents saved on the server (SQLite)
- [x] Retro pastel desktop landing page, folder windows, dialogs

**Going public** (accounts, hosting, phone app, camera): see [docs/PRODUCTION_PLAN.md](docs/PRODUCTION_PLAN.md).

**Next on the desktop**: writing tool, kanji tool, opening several documents as windows.

**Later ideas**

- Show the source image side-by-side, click a paragraph to see its crop
- Save multiple documents (SQLite), library screen
- Vocabulary list from looked-up words, export to Anki
- Context-aware explanation with a local open-weight LLM (e.g. via Ollama)
- Book-page-tuned OCR engine (e.g. NDLOCR) as an alternative to the manga detector
- Vertical reading mode (`writing-mode: vertical-rl`) as a view option
