import { createStatusbar } from "./ui/statusbar.js";

const status = createStatusbar({
  messageEl: document.getElementById("status-message"),
  countEl: document.getElementById("status-count"),
});

status.set("Ready");
