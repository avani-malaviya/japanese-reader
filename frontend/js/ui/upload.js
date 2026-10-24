import { ocrImage } from "../api.js";

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

// Paragraphs and pictures, counting inside columns too.
function flatten(items) {
  return items.flatMap((item) =>
    item.type === "columns" ? item.columns.flatMap((c) => flatten(c.items)) : [item],
  );
}

function summary(name, items) {
  const all = flatten(items);
  const pictures = all.filter((item) => item.type === "figure").length;
  const parts = [plural(all.length - pictures, "paragraph")];
  if (pictures) parts.push(plural(pictures, "picture"));
  const columns = items.filter((item) => item.type === "columns").length;
  if (columns) parts.push(plural(columns, "column row"));
  return `Read ${name}: ${parts.join(", ")}`;
}

export function setupUpload({ button, input, editor, status }) {
  button.addEventListener("click", () => input.click());

  input.addEventListener("change", async () => {
    const file = input.files[0];
    input.value = ""; // allow picking the same file again
    if (!file) return;

    button.disabled = true;
    status.progress(`Reading ${file.name}`);
    try {
      const { items } = await ocrImage(file);
      if (!Array.isArray(items)) {
        throw new Error("Unexpected reply from server. Reload the page and try again");
      }
      editor.insertPage(items);
      status.set(items.length ? summary(file.name, items) : `Nothing found in ${file.name}`);
    } catch (error) {
      status.set(`Error: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  });
}
