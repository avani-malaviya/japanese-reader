import { ocrImage } from "../api.js";

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function summary(name, items) {
  const pictures = items.filter((item) => item.type === "figure").length;
  const paragraphs = items.length - pictures;
  const parts = [plural(paragraphs, "paragraph")];
  if (pictures) parts.push(plural(pictures, "picture"));
  return `Read ${name}: ${parts.join(", ")}`;
}

export function setupUpload({ button, input, editor, status }) {
  button.addEventListener("click", () => input.click());

  input.addEventListener("change", async () => {
    const file = input.files[0];
    input.value = ""; // allow picking the same file again
    if (!file) return;

    if (!editor.isEmpty() && !confirm("Replace the current document with this image's text?")) {
      return;
    }

    button.disabled = true;
    status.progress(`Reading ${file.name}`);
    try {
      const { items } = await ocrImage(file);
      if (!Array.isArray(items)) {
        throw new Error("Unexpected reply from server. Reload the page and try again");
      }
      editor.setItems(items);
      status.set(items.length ? summary(file.name, items) : `Nothing found in ${file.name}`);
    } catch (error) {
      status.set(`Error: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  });
}
