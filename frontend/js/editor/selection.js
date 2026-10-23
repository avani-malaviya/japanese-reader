// Reads the user's selection in terms of the document's plain text (furigana excluded).

import { MAX_LOOKUP_CHARS } from "../config.js";

function plainTextLength(fragment) {
  fragment.querySelectorAll("rt").forEach((rt) => rt.remove());
  return fragment.textContent.length;
}

// Plain-text offset of a DOM boundary point inside `block`.
function offsetIn(block, container, offset) {
  const range = document.createRange();
  range.setStart(block, 0);
  range.setEnd(container, offset);
  return plainTextLength(range.cloneContents());
}

export function plainText(block) {
  const clone = block.cloneNode(true);
  clone.querySelectorAll("rt").forEach((rt) => rt.remove());
  return clone.textContent;
}

/**
 * The current selection inside `root`, or null if there is nothing usable.
 * Returns { text, context, offset, paragraph, rect }: `context` is the paragraph's
 * plain text and `offset` is where `text` starts in it.
 */
export function getSelectionInfo(root) {
  const selection = window.getSelection();
  if (!selection.rangeCount || selection.isCollapsed) return null;

  const range = selection.getRangeAt(0);
  const node = range.commonAncestorContainer;
  const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  const paragraph = element.closest("p");
  if (!paragraph || !root.contains(paragraph)) return null; // e.g. spans paragraphs

  const context = plainText(paragraph);
  const start = offsetIn(paragraph, range.startContainer, range.startOffset);
  const end = offsetIn(paragraph, range.endContainer, range.endOffset);
  const raw = context.slice(start, end);

  // Ignore surrounding whitespace the user swept up with the mouse.
  const text = raw.trim();
  if (!text || text.length > MAX_LOOKUP_CHARS) return null;
  const offset = start + raw.indexOf(text);

  return { text, context, offset, paragraph, rect: range.getBoundingClientRect() };
}
