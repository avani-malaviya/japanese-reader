// The reader's own notes, in red. Two shapes, chosen from the selection:
// - under a word: a short selection on one line gets the note right beneath it, like furigana
//   (<ruby class="note-word">word<rt>note</rt></ruby>)
// - under a line: a longer selection is underlined and the note follows its paragraph
//   (<span class="noted"> + <p class="note-line">)
// Both carry the same data-note id, so a note can be found from either part.

import { TEXT_BLOCKS } from "./selection.js";

// Longer than this, a note under the word would stretch the line; it goes under the line.
const WORD_NOTE_MAX_CHARS = 12;
export const NOTE_PARTS = ".note-word, .noted, .note-line";

function newId() {
  return `n${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

function fitsUnderWord(range) {
  const text = range.toString().trim();
  const tops = new Set([...range.getClientRects()].map((r) => Math.round(r.top)));
  const crossesFurigana = range.cloneContents().querySelector("ruby, rt") !== null;
  return text.length <= WORD_NOTE_MAX_CHARS && tops.size <= 1 && !crossesFurigana;
}

/** Adds a note for the text in `range`. Returns the note id. */
export function addNote(range, text) {
  const id = newId();
  if (fitsUnderWord(range)) {
    const ruby = document.createElement("ruby");
    ruby.className = "note-word";
    ruby.dataset.note = id;
    const rt = document.createElement("rt");
    rt.contentEditable = "false";
    rt.textContent = text;
    ruby.append(range.extractContents(), rt);
    range.insertNode(ruby);
    return id;
  }
  const mark = document.createElement("span");
  mark.className = "noted";
  mark.dataset.note = id;
  mark.append(range.extractContents());
  range.insertNode(mark);
  const line = document.createElement("p");
  line.className = "note-line";
  line.dataset.note = id;
  line.contentEditable = "false";
  line.textContent = text;
  // After the paragraph, and after any notes already under it, so they stay in order.
  let after = mark.closest(TEXT_BLOCKS);
  while (after.nextElementSibling?.classList.contains("note-line")) after = after.nextElementSibling;
  after.after(line);
  return id;
}

/** The note an element belongs to: { id, text, anchor } (anchor = the noted text), or null. */
export function findNote(root, element) {
  const part = element.closest(NOTE_PARTS);
  if (!part || !root.contains(part)) return null;
  const { note: id } = part.dataset;
  const word = root.querySelector(`.note-word[data-note="${id}"]`);
  if (word) return { id, text: word.querySelector("rt").textContent, anchor: word };
  const line = root.querySelector(`.note-line[data-note="${id}"]`);
  const anchor = root.querySelector(`.noted[data-note="${id}"]`) ?? line;
  return { id, text: line?.textContent ?? "", anchor };
}

export function updateNote(root, id, text) {
  root.querySelectorAll(`[data-note="${id}"]`).forEach((part) => {
    if (part.classList.contains("note-word")) part.querySelector("rt").textContent = text;
    if (part.classList.contains("note-line")) part.textContent = text;
  });
}

export function removeNote(root, id) {
  root.querySelectorAll(`[data-note="${id}"]`).forEach((part) => {
    if (part.classList.contains("note-line")) return part.remove();
    if (part.classList.contains("note-word")) part.querySelector("rt").remove();
    part.replaceWith(...part.childNodes); // keep the noted text itself
  });
  root.normalize();
}
