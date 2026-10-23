// The only module that talks to the backend.

async function request(path, options) {
  const response = await fetch(`/api${path}`, options);
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

export function ocrImage(file) {
  const body = new FormData();
  body.append("image", file);
  return request("/ocr", { method: "POST", body });
}
