# Design Rules

Rules every change should follow. If a change needs to break one, update this file in the same commit
and say why.

## 1. Visual

The app has **two surfaces**, each with its own palette:

- **Desktop** (the library, `#/`): a pastel retro PC desktop, after a 2000s OS. Folders, programs,
  windows, dialogs.
- **Document** (the editor, `#/doc/<id>`): **a Kindle crossed with a 2000s desktop application.**
  Calm paper page in the middle, plain utilitarian chrome around it.

Never mix them: no pastel in the editor, no plain black-and-white chrome on the desktop.

### Desktop colour
- Surfaces: mint `--desk-mint` / `--desk-mint-light` (desktop, dithered together), cream
  `--desk-cream` (window bodies, menu bar, labels), pinks `--desk-pink-light` / `--desk-pink` /
  `--desk-pink-deep` (title-bar stripes, toolbars, folder icons, inputs).
- Ink: `--desk-ink` (blue) for every line and all text; `--desk-ink-soft` for secondary text.
- Accents: `--desk-lavender` / `--desk-purple`, only inside pixel icons (shading, stands).
- Selection = blue label with cream text (`--desk-ink` on `--desk-cream`), like an old OS.
- Borders 2px ink; hard offset shadow `--desk-shadow`; square corners; no animation; patterns are
  hard-stop (1-bit style) like the document surface.
- Icons are 16×16 pixel drawings (`js/desktop/icons.js`) coloured only through `.px-*` classes.

### Document colour
- Only `--ink` (`#000`) and `--paper` (`#fff`), plus **one exception: `--note` red, used only for
  the reader's own notes** (note text, the underline of noted text, the note line's rule), so
  what the reader wrote never looks like the page. One grey, `--muted` (`#808080`), for disabled
  or secondary text only.
- No other colours, no smooth gradients, no transparency effects, no blur.
- 1-bit patterns are fine (striped title bar, dithered desktop) — built with hard-stop CSS
  gradients so they stay pure black and white.
- Pictures from uploaded pages are shown **1-bit dithered** (Floyd–Steinberg), never in grey
  or colour, framed with a 1px border.
- Emphasis = **inversion** (white on black), never colour. Hover, active, selected, focused all invert.

### Shape
- Square corners everywhere (`border-radius: 0`).
- Borders are 1px solid ink. Double borders (`3px double`) for window/dialog frames.
- The only shadow allowed is a hard offset: `box-shadow: 3px 3px 0 var(--ink)`, for floating boxes.

### Type
- **UI chrome:** monospace (`--font-ui`), small, often uppercase labels. Buttons look like `[ Open Image… ]`.
- **Document:** Mincho serif (`--font-doc`), large, high line-height — leaves room for furigana
  under the line and reads like an e-reader.
- Furigana (`<rt>`) sits **under** the text (`ruby-position: under`), smaller, same ink colour.

### Document house style
Every page, whatever it looked like, is recreated with the same small set of styles:
- **h1** page title: large bold Mincho, `3px double` rule under it.
- **h2** subtitle: bold Mincho, `1px` rule under it.
- **caption**: small UI font.
- **body**: Mincho, as the page.
- **columns**: side by side with a gap, no borders. Pictures float within their column.
- **page break** between uploaded pages: a dashed rule.
Don't add per-document fonts, sizes or colours; structure is what carries over from the page.

### Layout
- One window: title bar → toolbar → page → status bar.
- The page is centred, ~40em wide max, generous margins. Nothing competes with it.
- Popups float beside the selection, never cover it.
- Editing controls (picture frame, handles, toolbars) are overlays outside the editable page,
  so they can never end up saved in a document.

### Motion & feedback
- No animations or transitions. State changes are instant.
- Progress and loading use text: `READING PAGE [■■■□□□□]`, status bar messages. No spinners.
- Errors show in the status bar or a plain dialog, in words.

### Tokens
All colours, fonts and sizes live in `frontend/css/tokens.css` as CSS custom properties.
No literal colour or font values anywhere else.

## 2. Code

### Architecture
- **Backend:** `api/` (HTTP) depends on `services/` (domain). Services never import FastAPI.
- Each model or dataset is wrapped behind a small interface (`Protocol`) in `services/`.
  Heavy models are loaded lazily, once, on first use.
- **Frontend:** `api.js` is the only module that calls `fetch`. `editor/` owns the document DOM.
  `ui/` owns everything around it. `main.js` only wires modules together.
- Config values (e.g. how many occurrences get furigana) live in one place per side:
  `backend/app/config.py`, `frontend/js/config.js`.

### Style
- Python: type hints everywhere, dataclasses for domain objects, pydantic models only at the API edge.
- JS: ES modules, named exports, no globals, no frameworks, no build step.
- Small modules with one job. If a file needs a section header comment, it probably wants splitting.
- Comments explain *why*, not *what*.

### Tests
- Services get unit tests that do not load heavy models (fakes for OCR engines).
- API gets tests via FastAPI's `TestClient`.

### Commits
- One small, working feature or change per commit. The app should run at every commit.
- Conventional commits: `feat(scope): …`, `fix(scope): …`, `chore: …`, `docs: …`, `test: …`, `refactor: …`.
- Significant technical choices get a short ADR in `docs/decisions/NNNN-title.md`.
