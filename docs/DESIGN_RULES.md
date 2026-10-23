# Design Rules

Rules every change should follow. If a change needs to break one, update this file in the same commit
and say why.

## 1. Visual

The feel: **a Kindle crossed with a 2000s desktop application.** Calm paper page in the middle,
plain utilitarian chrome around it.

### Colour
- Only `--ink` (`#000`) and `--paper` (`#fff`). One grey, `--muted` (`#808080`), for disabled
  or secondary text only.
- No other colours, no smooth gradients, no transparency effects, no blur.
- 1-bit patterns are fine (striped title bar, dithered desktop) — built with hard-stop CSS
  gradients so they stay pure black and white.
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

### Layout
- One window: title bar → toolbar → page → status bar.
- The page is centred, ~40em wide max, generous margins. Nothing competes with it.
- Popups float beside the selection, never cover it.

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
