// Hash routes: "#/" is the desktop, "#/folder/<id>" the desktop with that folder open,
// "#/doc/<id>" a document in the editor.

export function currentRoute() {
  const doc = location.hash.match(/^#\/doc\/(\d+)$/);
  if (doc) return { name: "document", id: Number(doc[1]) };
  const folder = location.hash.match(/^#\/folder\/(\d+)$/);
  return { name: "desktop", folderId: folder ? Number(folder[1]) : null };
}

export function onRouteChange(callback) {
  window.addEventListener("hashchange", () => callback(currentRoute()));
}

export const desktopPath = (folderId = null) => (folderId ? `#/folder/${folderId}` : "#/");
export const documentPath = (id) => `#/doc/${id}`;

export function go(path) {
  location.hash = path;
}
