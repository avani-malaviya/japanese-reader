// The only module that talks to the backend.

// The server's build when this page loaded. Every response carries the current build; if it
// changed, this page's code is older than the server's and may misread its replies.
let pageBuild = null;

async function request(path, options) {
  const response = await fetch(`/api${path}`, options);
  const build = response.headers.get("X-App-Build");
  if (pageBuild && build && build !== pageBuild) {
    throw new Error("The app was updated. Reload the page (⌘R) to continue");
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      // Body was not JSON; keep the status text.
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export async function startSession() {
  const response = await fetch("/api/health");
  pageBuild = response.headers.get("X-App-Build");
}

function sendJson(method, path, payload) {
  return request(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

const postJson = (path, payload) => sendJson("POST", path, payload);

export function getReadings({ text, context, offset }) {
  return postJson("/reading", { text, context, offset });
}

export function getMeaning(text) {
  return postJson("/meaning", { text });
}

export function ocrImage(file) {
  const body = new FormData();
  body.append("image", file);
  return request("/ocr", { method: "POST", body });
}

// ---- library ----

export const listFolders = () => request("/folders");
export const createFolder = (name) => postJson("/folders", { name });
export const renameFolder = (id, name) => sendJson("PATCH", `/folders/${id}`, { name });
export const deleteFolder = (id) => request(`/folders/${id}`, { method: "DELETE" });

export const listDocuments = (folderId) => request(`/folders/${folderId}/documents`);
export const createDocument = (folderId, title) =>
  postJson(`/folders/${folderId}/documents`, { title });
export const getDocument = (id) => request(`/documents/${id}`);
export const saveDocument = (id, html) => sendJson("PUT", `/documents/${id}`, { html });
export const renameDocument = (id, title) => sendJson("PATCH", `/documents/${id}`, { title });
export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });
