import { createEditor } from "./editor/editor.js";
import { setupLookupPopup } from "./ui/lookup-popup.js";
import { createStatusbar } from "./ui/statusbar.js";
import { setupUpload } from "./ui/upload.js";

const status = createStatusbar({
  messageEl: document.getElementById("status-message"),
  countEl: document.getElementById("status-count"),
});

const editor = createEditor(document.getElementById("document"), {
  onChange: () => updateCount(),
  onSaveFailed: () => status.set("Not saved: document too large for browser storage"),
});

function updateCount() {
  status.setCount(editor.getText().replace(/\s/g, "").length);
}

setupUpload({
  button: document.getElementById("open-image"),
  input: document.getElementById("image-input"),
  editor,
  status,
});

setupLookupPopup({
  editor,
  scroller: document.querySelector(".workspace"),
  status,
});

updateCount();
status.set("Ready");
