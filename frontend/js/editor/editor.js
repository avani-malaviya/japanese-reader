// Owns the document element: one <p> per paragraph, editable, autosaved.

import { AUTOSAVE_DELAY_MS } from "../config.js";
import { loadDocument, saveDocument } from "./storage.js";

// A picture is one uneditable unit in the text flow: Backspace deletes it whole.
function renderFigure({ src, width_ratio, align }) {
  const figure = document.createElement("figure");
  figure.className = `figure figure--${align}`;
  figure.contentEditable = "false";
  figure.style.width = `${(width_ratio * 100).toFixed(1)}%`;
  const img = document.createElement("img");
  img.src = src;
  img.alt = "";
  figure.append(img);
  return figure;
}

function renderItem(item) {
  if (item.type === "figure") return renderFigure(item);
  const p = document.createElement("p");
  p.textContent = item.text;
  return p;
}

export function createEditor(el, { onChange, onSaveFailed } = {}) {
  let saveTimer = null;

  function changed() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      if (!saveDocument(el.innerHTML)) onSaveFailed?.();
    }, AUTOSAVE_DELAY_MS);
    onChange?.();
  }

  // Replaces the document with OCR items: paragraphs ({ type, text }) and
  // pictures ({ type, src, width_ratio, align }), in reading order.
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
