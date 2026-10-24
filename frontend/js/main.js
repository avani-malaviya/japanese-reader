import { startSession } from "./api.js";
import { setupDesktopScreen } from "./desktop/desktop.js";
import { importLegacyDocument } from "./desktop/import-legacy.js";
import { createEditor } from "./editor/editor.js";
import { currentRoute, onRouteChange } from "./router.js";
import { setupEditorScreen } from "./screens/editor-screen.js";
import { setupAiChatButton } from "./ui/ai-chat-button.js";
import { setupAskAiDialog } from "./ui/ask-ai-dialog.js";
import { setupFigureControls } from "./ui/figure-controls.js";
import { setupLookupPopup } from "./ui/lookup-popup.js";
import { setupNotePopup } from "./ui/note-popup.js";
import { createStatusbar } from "./ui/statusbar.js";
import { setupUpload } from "./ui/upload.js";

const status = createStatusbar({
  messageEl: document.getElementById("status-message"),
  countEl: document.getElementById("status-count"),
  saveEl: document.getElementById("status-save"),
});

const editorScreen = setupEditorScreen({
  root: document.getElementById("editor-screen"),
  titleEl: document.getElementById("editor-title"),
  backButton: document.getElementById("to-desktop"),
  status,
});

const editor = createEditor(document.getElementById("document"), {
  onChange: () => updateCount(),
  onSave: (html) => editorScreen.save(html),
});
editorScreen.attach(editor);

function updateCount() {
  status.setCount(editor.getText().replace(/\s/g, "").length);
}

setupUpload({
  button: document.getElementById("open-image"),
  input: document.getElementById("image-input"),
  editor,
  status,
});

const askAi = setupAskAiDialog({ status });
setupAiChatButton({ button: document.getElementById("ai-chat"), status });

const notes = setupNotePopup({ editor, scroller: document.querySelector(".workspace"), status });

const lookup = setupLookupPopup({
  editor,
  scroller: document.querySelector(".workspace"),
  status,
  onAskAI: askAi.open,
  onNote: notes.openNew,
  onOpenNote: notes.openExisting,
});

const figures = setupFigureControls({
  editor,
  scroller: document.querySelector(".workspace"),
  status,
});

const desktop = setupDesktopScreen({ root: document.getElementById("desktop") });

async function showRoute(route) {
  // Floating boxes belong to the editor; don't leave them over the desktop.
  lookup.close();
  notes.close();
  askAi.close();
  figures.deselect();
  if (route.name === "document") {
    desktop.hide();
    await editorScreen.show(route.id);
  } else {
    await editorScreen.hide();
    await desktop.show(route.folderId);
  }
}

async function start() {
  startSession();
  try {
    await importLegacyDocument();
  } catch {
    // The old document stays in the browser and is tried again next time.
  }
  onRouteChange(showRoute);
  showRoute(currentRoute());
}

start();
