export function setupNewDocument({ button, editor, status }) {
  button.addEventListener("click", () => {
    if (editor.hasContent() && !confirm("Start a new document? The current one will be cleared.")) {
      return;
    }
    editor.clear();
    status.set("New document");
  });
}
