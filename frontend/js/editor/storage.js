// v0 persistence: one document in this browser's localStorage.

const KEY = "japanese-reader:document";

export function loadDocument() {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function saveDocument(html) {
  try {
    localStorage.setItem(KEY, html);
    return true;
  } catch {
    return false;
  }
}
