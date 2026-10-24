// Before the library, the one document lived in this browser's localStorage. Kept only so it can
// be moved into the library once.

const KEY = "japanese-reader:document";

export function loadLegacyDocument() {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function removeLegacyDocument() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // Storage unavailable: nothing to remove.
  }
}
