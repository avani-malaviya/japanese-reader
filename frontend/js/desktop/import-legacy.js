// Moves the document saved in this browser before the library existed into the library, once.

import { createDocument, createFolder, listFolders, saveDocument } from "../api.js";
import { loadLegacyDocument, removeLegacyDocument } from "../editor/legacy-storage.js";

const FOLDER = "Imported";
const TITLE = "My first document";

/** Resolves to the new document, or null if there was nothing to import. */
export async function importLegacyDocument() {
  const html = loadLegacyDocument();
  const probe = document.createElement("div");
  probe.innerHTML = html ?? "";
  if (!probe.textContent.trim() && !probe.querySelector("img")) {
    removeLegacyDocument(); // empty leftovers aren't worth a folder
    return null;
  }
  const folders = await listFolders();
  const folder = folders.find((f) => f.name === FOLDER) ?? (await createFolder(FOLDER));
  const doc = await createDocument(folder.id, TITLE);
  await saveDocument(doc.id, html);
  // Only forget the browser copy once the library has it.
  removeLegacyDocument();
  return doc;
}
