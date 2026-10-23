# 0002 — Frontend: vanilla JS modules, served by the backend

**Status:** accepted · 2026-10-23

## Context
The UI is one screen: toolbar, an editable page, a popup. The visual style is deliberately plain.

## Decision
Plain HTML, CSS and native ES modules. No framework, no bundler, no Node. FastAPI serves
`frontend/` as static files, so the whole app is one process on one port.

## Consequences
- Zero toolchain; reload the browser to see changes.
- Structure is enforced by convention (see DESIGN_RULES.md), not by a framework.
- If the UI grows into many screens with shared state, revisit (likely Preact or Svelte + Vite).
