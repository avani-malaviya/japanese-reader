// Owns the document element: blocks (<p>, <figure>, page breaks), editable, autosaved through
// `onSave(html)` (the library), which returns a promise.

import { AUTOSAVE_DELAY_MS } from "../config.js";
import { createRuby } from "./furigana.js";

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

// Text with furigana read off the page ({ start, end, kana }) as <ruby>, like inserted ones.
function renderText(parent, text, ruby = []) {
  let position = 0;
  for (const { start, end, kana } of [...ruby].sort((a, b) => a.start - b.start)) {
    if (start < position) continue; // overlapping furigana: keep the first
    parent.append(text.slice(position, start), createRuby(text.slice(start, end), kana));
    position = end;
  }
  parent.append(text.slice(position));
}

// One house style for structure read off any page: <h1> page title, <h2> subtitles, captions.
function renderParagraph({ text, ruby, role, level }) {
  const tag = role === "heading" ? (level === 1 ? "h1" : "h2") : "p";
  const node = document.createElement(tag);
  if (role === "caption") node.className = "caption";
  renderText(node, text, ruby);
  return node;
}

// Columns side by side, as on the page: { columns: [{ width_ratio, items }] }.
function renderColumns({ columns }) {
  const row = document.createElement("div");
  row.className = "columns";
  for (const { width_ratio, items } of columns) {
    const column = document.createElement("div");
    column.className = "column";
    column.style.flexGrow = String(width_ratio);
    column.append(...items.map(renderItem));
    row.append(column);
  }
  return row;
}

function renderItem(item) {
  if (item.type === "figure") return renderFigure(item);
  if (item.type === "columns") return renderColumns(item);
  return renderParagraph(item);
}

function isEmptyParagraph(node) {
  return ["P", "H1", "H2"].includes(node?.tagName) && node.textContent.trim() === "" && !node.querySelector("img");
}

export function createEditor(el, { onChange, onSave, onDirty }) {
  let saveTimer = null;
  let saving = Promise.resolve(); // saves run one after another, in order
  let inFlight = 0;
  let caret = null; // last caret position inside the document, kept while toolbar buttons have focus

  function save() {
    saveTimer = null;
    const html = el.innerHTML;
    inFlight++;
    saving = saving.then(() => onSave(html)).finally(() => inFlight--);
    return saving;
  }

  function changed() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, AUTOSAVE_DELAY_MS);
    onDirty?.();
    onChange?.();
  }

  // Leaving now would lose an edit: one waiting for the autosave delay, or still being sent.
  window.addEventListener("beforeunload", (event) => {
    if (saveTimer === null && inFlight === 0) return;
    flush();
    event.preventDefault(); // the browser asks "Leave site?"; the save carries on meanwhile
  });

  /** Saves any change still waiting for the autosave delay. */
  function flush() {
    if (saveTimer !== null) {
      clearTimeout(saveTimer);
      return save();
    }
    return saving;
  }

  /** Shows a saved document. Call `flush()` first so the previous one isn't lost. */
  function open(html) {
    clearTimeout(saveTimer);
    saveTimer = null;
    el.innerHTML = html;
    caret = null;
    onChange?.();
  }

  function hasContent() {
    return el.textContent.trim() !== "" || el.querySelector("figure") !== null;
  }

  // The top-level block holding the caret, or null if the caret isn't in the document.
  function caretBlock() {
    if (!caret || !el.contains(caret.startContainer)) return null;
    let node = caret.startContainer;
    // A caret between top-level blocks: the block before it.
    if (node === el) return el.childNodes[caret.startOffset - 1] ?? null;
    while (node && node.parentNode !== el) node = node.parentNode;
    return node;
  }

  /**
   * Adds a page of OCR items, paragraphs ({ type, text }) and pictures
   * ({ type, src, width_ratio, align }), after the block holding the caret, or at the end.
   * An empty paragraph at the caret (the user just pressed Enter) is replaced.
   */
  function insertPage(items) {
    const nodes = items.map(renderItem);
    if (!hasContent()) {
      el.replaceChildren(...nodes);
    } else {
      const pageBreak = document.createElement("hr");
      pageBreak.className = "page-break";
      const anchor = caretBlock();
      if (isEmptyParagraph(anchor)) {
        anchor.replaceWith(pageBreak, ...nodes);
      } else if (anchor) {
        anchor.after(pageBreak, ...nodes);
      } else {
        el.append(pageBreak, ...nodes);
      }
    }
    // The next page goes after this one.
    const last = nodes.at(-1);
    if (last) {
      caret = document.createRange();
      caret.setStartAfter(last);
      last.scrollIntoView({ block: "nearest" });
    }
    changed();
  }

  document.addEventListener("selectionchange", () => {
    const selection = window.getSelection();
    if (selection.rangeCount && el.contains(selection.anchorNode)) {
      caret = selection.getRangeAt(0).cloneRange();
    }
  });

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

  return {
    el,
    insertPage,
    open,
    flush,
    changed,
    hasContent,

    // The page's own text: without furigana or notes (both <rt> or .note-line).
    getText() {
      const clone = el.cloneNode(true);
      clone.querySelectorAll("rt, .note-line").forEach((node) => node.remove());
      return clone.innerText.trim();
    },
  };
}
