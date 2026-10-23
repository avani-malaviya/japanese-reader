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
| **Open image** | Upload a photo/scan from your computer. |
| **OCR** | Detects text blocks (vertical *or* horizontal) and recognises them. Vertical text is converted to horizontal so every document reads the same way. One block → one paragraph. |
| **Editor** | The OCR result lands in a simple word-processor page. Fix mistakes, delete noise, type freely. Paste is always plain text. Autosaved in the browser. |
| **Reading** | Highlight text → a box appears beside it with the reading in hiragana. A single kanji shows *all* its readings (音 / 訓); a word shows its dictionary readings with the one that fits the sentence marked `◆ in context`. |
| **Insert** | Adds the chosen reading as furigana *below* the selected text and the occurrences after it (5 in total). |
| **Remove** | Click any furigana → **Remove** (just that one) or **Remove all** (same word + reading everywhere). |
| **Meaning** | Shows dictionary entries (part of speech + glosses) for the selection. Inflected words (話しました) are looked up by dictionary form (話す). Word-level only — no sentence translation, on purpose. |

## Using it

1. **[ OPEN IMAGE… ]** → pick a photo. The status bar shows progress; the first read of a session
   takes ~30 s while models load, then ~1–3 s per page.
2. Fix anything the OCR got wrong directly on the page.
3. Highlight a word or a single kanji. In the box beside it:
   - click a reading to choose it, then **[ INSERT ]** to add it as furigana;
   - **[ MEANING ]** toggles dictionary entries.
4. `Esc` or clicking elsewhere closes the box.

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
 │               js/api.js   │               │                 └ layout.py  (reading order) │
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
  app/services/ocr/          base.py (OcrEngine interface), mokuro_engine.py, layout.py, service.py
  app/services/reading.py    readings for a selection
  app/services/meaning.py    dictionary meanings for a selection
  app/services/analyzer.py   fugashi/UniDic tokenizer
  app/services/dictionary.py JMdict + KANJIDIC2
  app/services/kana.py       kana helpers
  tests/                     pytest; OCR API tests use a fake engine

frontend/                    served as-is, no build
  index.html
  css/tokens.css             every colour, font and size
  css/base.css, components.css
  js/main.js                 wiring only
  js/api.js                  every backend call
  js/config.js               frontend settings
  js/editor/                 the document: editor, selection, furigana, storage
  js/ui/                     around the document: upload, lookup popup, meaning view, status bar
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
- One document at a time, stored in this browser only.

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

**Later ideas**

- Show the source image side-by-side, click a paragraph to see its crop
- Save multiple documents (SQLite), library screen
- Vocabulary list from looked-up words, export to Anki
- Context-aware explanation with a local open-weight LLM (e.g. via Ollama)
- Book-page-tuned OCR engine (e.g. NDLOCR) as an alternative to the manga detector
- Vertical reading mode (`writing-mode: vertical-rl`) as a view option
