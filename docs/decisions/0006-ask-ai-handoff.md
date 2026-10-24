# 0006 — Ask AI: hand off to the user's own ChatGPT / Claude account

**Status:** accepted · 2026-10-24

## Context
Learners want a fuller grammar explanation than a dictionary gives: the dictionary form and
conjugation of a verb, the rules of the pattern, and how it attaches to nouns, adjectives and
verbs. Asking that by hand every time is tedious, so the question should come from a saved,
editable template. The user wants to use their existing ChatGPT or Claude subscription, not
API keys.

## Decision
- **Handoff, not integration.** The app never calls an AI service. **[ ASK AI ]** fills the
  template (`frontend/js/ai/prompt.js`) and opens `chatgpt.com/?q=…` or `claude.ai/new?q=…`
  in the user's browser, where they are already logged in (`frontend/js/ai/handoff.js`).
  OpenAI and Anthropic do not let third-party apps use subscription logins, so this is the only
  account-based route.
- **A floating window, not a bubble.** Both sites refuse to be embedded in another page, so the
  answer can't appear inside the app. A dialog-sized window (560×680) opens centred over the app
  and is reused for every question; **[ AI CHAT ]** brings it back without re-sending anything.
- **Clipboard as a safety net.** The prompt is always copied too. Prompts whose URL would be too
  long (> 7000 chars) open a blank new chat and the user pastes.
- **Window reuse keeps `window.opener`.** Finding the window again by name requires it. The only
  pages opened there are ChatGPT and Claude.

## Consequences
- This is the one place the app sends text off the machine, and only when the user presses
  Send: the highlighted text, its sentence and any note go to the chosen provider. Everything
  else stays local and open source.
- The `?q=` parameters are the providers' own conventions and could change; the clipboard copy
  keeps the feature usable if they do.
- The answer lives in the provider's chat, not in the document. Saving explanations into the
  app would need an API (keys) or a local model.
- The template is stored in this browser (localStorage) with a Reset to the built-in default.
