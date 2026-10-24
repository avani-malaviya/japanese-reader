// Owns the document element: one <p> per paragraph, editable, autosaved.

import { AUTOSAVE_DELAY_MS } from "../config.js";
import { loadDocument, saveDocument } from "./storage.js";

function renderItem(item) {
  const p = document.createElement("p");
  p.textContent = item.text;
  return p;
}

export function createEditor(el, { onChange } = {}) {
  let saveTimer = null;

  function changed() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => saveDocument(el.innerHTML), AUTOSAVE_DELAY_MS);
    onChange?.();
  }

  // Replaces the document with OCR items: [{ type: "paragraph", text }, ...].
  function setItems(items) {
    el.replaceChildren(...items.map(renderItem));
    changed();
  }

  el.contentEditable = "true";
  el.spellcheck = false;
  el.addEventListener("input", changed);

  // Keep the document clean: pasted content arrives as plain text, never foreign HTML.
  el.addEventListener("paste", (event) => {
    event.preventDefault();
    const text = event.clipboardData.getData("text/plain");
    document.execCommand("insertText", false, text);
  });

  // Typing into an empty page should start a paragraph, not loose text.
  el.addEventListener("focus", () => {
    if (el.childElementCount === 0) {
      el.innerHTML = "<p><br></p>";
    }
  });

  const saved = loadDocument();
  if (saved) el.innerHTML = saved;

  return {
    el,
    setItems,
    changed,

    // Plain text without furigana (<rt>), for counting and lookups.
    getText() {
      const clone = el.cloneNode(true);
      clone.querySelectorAll("rt").forEach((rt) => rt.remove());
      return clone.innerText.trim();
    },

    isEmpty() {
      return this.getText().length === 0;
    },
  };
}
