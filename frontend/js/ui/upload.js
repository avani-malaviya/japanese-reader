import { ocrImage } from "../api.js";

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
      editor.setItems(items);
      status.set(items.length ? `Read ${file.name}` : `No text found in ${file.name}`);
    } catch (error) {
      status.set(`Error: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  });
}
