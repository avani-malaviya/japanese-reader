// A folder window on the desktop: the documents in one folder (a book, "Pamphlets", ...).

import {
  createDocument,
  deleteDocument,
  deleteFolder,
  listDocuments,
  renameDocument,
  renameFolder,
} from "../api.js";
import { documentPath, go } from "../router.js";
import { el } from "../ui/dom.js";
import { confirmDialog, promptDialog } from "./dialogs.js";
import { documentIcon } from "./icons.js";

const DATE = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function button(label, title, onClick) {
  const node = el("button", "desk-btn", label);
  node.type = "button";
  node.title = title;
  node.addEventListener("click", onClick);
  return node;
}

/**
 * Opens a window for `folder` inside `layer`. `onFolderChanged()` is called after the folder is
 * renamed or deleted, `onClose()` when the window closes.
 */
export function openFolderWindow({ folder, layer, position, onFolderChanged, onClose }) {
  const win = el("section", "dwin folder-window");
  win.tabIndex = -1; // focusable, so its keyboard shortcuts apply while it's in front
  win.style.left = `${position.x}px`;
  win.style.top = `${position.y}px`;

  const titleBar = el("div", "dwin__title");
  const name = el("span", "dwin__name", folder.name);
  const closeButton = el("button", "dwin__close", "×");
  closeButton.type = "button";
  closeButton.title = "Close";
  titleBar.append(name, closeButton);

  const toolbar = el("div", "folder-window__toolbar");
  const info = el("span", "folder-window__info");
  toolbar.append(
    button("New document", "A new pamphlet, chapter or reading session", newDocument),
    button("Rename", "Rename the selected document, or the folder (F2)", rename),
    button("Delete", "Delete the selected document, or the folder (Delete)", remove),
    info,
  );

  const list = el("div", "folder-window__list");
  list.setAttribute("role", "listbox");
  win.append(titleBar, toolbar, list);
  layer.append(win);

  let documents = [];
  let selected = null; // the selected document's icon

  function select(icon) {
    selected?.setAttribute("aria-selected", "false");
    selected = icon;
    icon?.setAttribute("aria-selected", "true");
  }

  function render() {
    name.textContent = folder.name;
    info.textContent = plural(documents.length, "document");
    selected = null;
    if (!documents.length) {
      list.replaceChildren(
        el("p", "folder-window__empty", "Empty. Click NEW DOCUMENT to start a pamphlet or a chapter."),
      );
      return;
    }
    list.replaceChildren(
      ...documents.map((doc) => {
        const icon = el("button", "desk-icon file-icon");
        icon.type = "button";
        icon.setAttribute("role", "option");
        icon.setAttribute("aria-selected", "false");
        icon.innerHTML = documentIcon();
        icon.append(
          el("span", "desk-icon__label", doc.title),
          el("span", "file-icon__date", DATE.format(new Date(doc.updated_at)).toUpperCase()),
        );
        icon.doc = doc;
        icon.addEventListener("click", () => select(icon));
        icon.addEventListener("dblclick", () => go(documentPath(doc.id)));
        return icon;
      }),
    );
  }

  async function refresh() {
    documents = await listDocuments(folder.id);
    render();
  }

  async function newDocument() {
    const title = await promptDialog({ title: "New document", label: `Title (in ${folder.name})` });
    if (!title) return;
    const doc = await createDocument(folder.id, title);
    go(documentPath(doc.id));
  }

  async function rename() {
    const doc = selected?.doc;
    if (doc) {
      const title = await promptDialog({ title: "Rename document", label: "Title", value: doc.title });
      if (title && title !== doc.title) {
        await renameDocument(doc.id, title);
        await refresh();
      }
      return;
    }
    const newName = await promptDialog({ title: "Rename folder", label: "Name", value: folder.name });
    if (newName && newName !== folder.name) {
      folder = await renameFolder(folder.id, newName);
      render();
      onFolderChanged();
    }
  }

  async function remove() {
    const doc = selected?.doc;
    if (doc) {
      const ok = await confirmDialog({
        title: "Delete document",
        message: `Delete “${doc.title}”? This can't be undone.`,
      });
      if (ok) {
        await deleteDocument(doc.id);
        await refresh();
        onFolderChanged();
      }
      return;
    }
    const contents = documents.length ? ` and its ${plural(documents.length, "document")}` : "";
    const ok = await confirmDialog({
      title: "Delete folder",
      message: `Delete “${folder.name}”${contents}? This can't be undone.`,
    });
    if (ok) {
      await deleteFolder(folder.id);
      close();
      onFolderChanged();
    }
  }

  function close() {
    win.remove();
    onClose();
  }

  // Drag by the title bar.
  titleBar.addEventListener("pointerdown", (event) => {
    if (event.target === closeButton) return;
    event.preventDefault();
    const startX = event.clientX - win.offsetLeft;
    const startY = event.clientY - win.offsetTop;
    const move = (e) => {
      win.style.left = `${Math.max(0, e.clientX - startX)}px`;
      win.style.top = `${Math.max(0, e.clientY - startY)}px`;
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  });

  closeButton.addEventListener("click", close);
  list.addEventListener("click", (event) => {
    if (event.target === list) select(null);
  });
  win.addEventListener("keydown", (event) => {
    // Shortcuts here are for this window, not the desktop behind it.
    event.stopPropagation();
    if (event.key === "Enter" && selected) go(documentPath(selected.doc.id));
    if (event.key === "F2") rename();
    if (event.key === "Delete" || event.key === "Backspace") remove();
  });

  refresh();
  return {
    folderId: folder.id,
    el: win,
    refresh,
    rename(updated) {
      folder = updated;
      render();
    },
  };
}
