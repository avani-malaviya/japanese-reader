// The desktop: the library's landing page.

import { listDocuments, listFolders } from "../api.js";
import { documentPath } from "../router.js";
import { el } from "../ui/dom.js";

export function setupDesktopScreen({ root }) {
  async function show() {
    const list = el("ul");
    for (const folder of await listFolders()) {
      const item = el("li", null, folder.name);
      const documents = el("ul");
      for (const doc of await listDocuments(folder.id)) {
        const link = el("a", null, doc.title);
        link.href = documentPath(doc.id);
        documents.append(el("li"));
        documents.lastChild.append(link);
      }
      item.append(documents);
      list.append(item);
    }
    root.replaceChildren(el("h1", null, "Library"), list);
    window.document.title = "Japanese Reader";
    root.hidden = false;
  }

  function hide() {
    root.hidden = true;
  }

  return { show, hide };
}
