import { loadProvider, showChatWindow } from "../ai/handoff.js";
import { AI_PROVIDERS } from "../config.js";

export function setupAiChatButton({ button, status }) {
  button.addEventListener("click", () => {
    const provider = loadProvider();
    const { label } = AI_PROVIDERS[provider];
    const result = showChatWindow(provider);
    if (result === "blocked") status.set("Pop-up blocked: allow pop-ups for this page");
    else if (result === "reopened") status.set(`Opened your ${label} chats`);
  });
}
