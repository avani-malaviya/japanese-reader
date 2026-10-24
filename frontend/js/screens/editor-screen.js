// The editor screen: one library document open in the editor, saved as it changes.

import { getDocument, listFolders, saveDocument } from "../api.js";
import { desktopPath, go } from "../router.js";

export function setupEditorScreen({ root, titleEl, backButton, status }) {
  let current = null; // { id, folderId }
  let editor = null;

  async function save(html) {
    if (!current) return;
    status.setSaveState("Saving…");
    try {
      await saveDocument(current.id, html);
      status.setSaveState("Saved ·");
    } catch (error) {
      status.setSaveState("Not saved ·");
      status.set(`Not saved: ${error.message}`);
    }
  }

  async function show(id) {
    await editor.flush();
    try {
      const [document, folders] = await Promise.all([getDocument(id), listFolders()]);
      const folder = folders.find((f) => f.id === document.folder_id);
      current = { id: document.id, folderId: document.folder_id };
      editor.open(document.html);
      titleEl.textContent = `Japanese Reader — ${folder?.name ?? "?"} / ${document.title}`;
      window.document.title = `${document.title} · Japanese Reader`;
      status.setSaveState("Saved ·");
      status.set("Ready");
      root.hidden = false;
    } catch (error) {
      current = null;
      status.set(`Could not open the document: ${error.message}`);
      go(desktopPath());
    }
  }

  async function hide() {
    await editor.flush();
    root.hidden = true;
    current = null;
  }

  backButton.addEventListener("click", async () => {
    const folderId = current?.folderId ?? null;
    await editor.flush();
    go(desktopPath(folderId));
  });

  return {
    show,
    hide,
    save,
    // The editor is created after this screen, because its autosave calls `save`.
    attach(createdEditor) {
      editor = createdEditor;
    },
  };
}
