// The desktop: the library's landing page. Folder icons, program icons, a menu bar.

import { createFolder, deleteFolder, listFolders, renameFolder } from "../api.js";
import { loadProvider, showChatWindow } from "../ai/handoff.js";
import { el } from "../ui/dom.js";
import { startClock } from "./clock.js";
import { alertDialog, confirmDialog, promptDialog } from "./dialogs.js";
import { chatIcon, folderIcon } from "./icons.js";

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

export function setupDesktopScreen({ root }) {
  const menubar = el("header", "desk-menubar");
  const brand = el("span", "desk-menubar__brand", "◆ Japanese Reader");
  const newFolderButton = el("button", "desk-btn", "New folder");
  newFolderButton.type = "button";
  const clock = el("span", "desk-menubar__clock");
  menubar.append(brand, newFolderButton, el("span", "desk-menubar__spacer"), clock);

  const icons = el("div", "desk-icons");
  icons.setAttribute("role", "listbox");
  root.replaceChildren(menubar, icons);
  startClock(clock);

  let folders = [];
  let selected = null; // the selected icon element

  function select(icon) {
    selected?.setAttribute("aria-selected", "false");
    selected = icon;
    icon?.setAttribute("aria-selected", "true");
    icon?.focus();
  }

  function iconButton({ svg, label, title, onOpen, folder = null }) {
    const icon = el("button", "desk-icon");
    icon.type = "button";
    icon.title = title;
    icon.setAttribute("role", "option");
    icon.setAttribute("aria-selected", "false");
    icon.innerHTML = svg;
    icon.append(el("span", "desk-icon__label", label));
    icon.folder = folder;
    icon.addEventListener("click", () => select(icon));
    icon.addEventListener("dblclick", onOpen);
    icon.addEventListener("keydown", (event) => {
      if (event.key === "Enter") onOpen();
    });
    return icon;
  }

  async function openChat() {
    const result = showChatWindow(loadProvider());
    if (result === "blocked") {
      await alertDialog({ title: "AI Chat", message: "Pop-up blocked. Allow pop-ups for this page and try again." });
    }
  }

  function render() {
    const folderIcons = folders.map((folder) =>
      iconButton({
        svg: folderIcon(),
        label: folder.name,
        title: `${folder.name} · ${plural(folder.document_count, "document")}`,
        folder,
        onOpen: () => {},
      }),
    );
    const programs = [
      iconButton({ svg: chatIcon(), label: "AI Chat", title: "Show the AI chat window", onOpen: openChat }),
    ];
    icons.replaceChildren(...folderIcons, ...programs);
    selected = null;
  }

  async function refresh() {
    folders = await listFolders();
    render();
  }

  async function newFolder() {
    const name = await promptDialog({ title: "New folder", label: "Name (a book, “Pamphlets”…)" });
    if (!name) return;
    const folder = await createFolder(name);
    await refresh();
    select([...icons.children].find((icon) => icon.folder?.id === folder.id));
  }

  async function renameSelected() {
    const folder = selected?.folder;
    if (!folder) return;
    const name = await promptDialog({ title: "Rename folder", label: "Name", value: folder.name });
    if (!name || name === folder.name) return;
    await renameFolder(folder.id, name);
    await refresh();
  }

  async function deleteSelected() {
    const folder = selected?.folder;
    if (!folder) return;
    const contents = folder.document_count ? ` and its ${plural(folder.document_count, "document")}` : "";
    const ok = await confirmDialog({
      title: "Delete folder",
      message: `Delete “${folder.name}”${contents}? This can't be undone.`,
    });
    if (!ok) return;
    await deleteFolder(folder.id);
    await refresh();
  }

  newFolderButton.addEventListener("click", newFolder);
  icons.addEventListener("click", (event) => {
    if (event.target === icons) select(null); // click on empty desktop
  });
  root.addEventListener("keydown", (event) => {
    if (root.hidden || event.target.closest("input, textarea")) return;
    if (event.key === "F2") renameSelected();
    if (event.key === "Delete" || event.key === "Backspace") deleteSelected();
  });

  return {
    async show() {
      root.hidden = false;
      window.document.title = "Japanese Reader";
      await refresh();
    },
    hide() {
      root.hidden = true;
    },
  };
}
