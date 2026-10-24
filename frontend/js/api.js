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
  return response.json();
}

export async function startSession() {
  const response = await fetch("/api/health");
  pageBuild = response.headers.get("X-App-Build");
}

function postJson(path, payload) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

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
