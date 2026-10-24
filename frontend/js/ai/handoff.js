// Hands a question to the user's own ChatGPT or Claude account. No API: the app never talks to
// an AI service itself; the user's browser opens the provider's site with the prompt filled in.

import { AI_MAX_URL_LENGTH, AI_PROVIDERS, AI_WINDOW } from "../config.js";

const PROVIDER_KEY = "japanese-reader:ai-provider";

export function loadProvider() {
  try {
    const saved = localStorage.getItem(PROVIDER_KEY);
    return saved in AI_PROVIDERS ? saved : "claude";
  } catch {
    return "claude";
  }
}

export function saveProvider(provider) {
  try {
    localStorage.setItem(PROVIDER_KEY, provider);
  } catch {
    // Not remembered next time; nothing else depends on it.
  }
}

export async function copyPrompt(prompt) {
  try {
    await navigator.clipboard.writeText(prompt);
    return true;
  } catch {
    return false;
  }
}

// A dialog-sized window floating over the middle of the app, not a split screen.
function windowFeatures() {
  const { width, height, offsetTop } = AI_WINDOW;
  const left = Math.round(window.screenX + (window.outerWidth - width) / 2);
  const top = Math.round(window.screenY + offsetTop);
  return `popup,width=${width},height=${height},left=${left},top=${top}`;
}

// The one AI window, found again by name for every question, even after this page reloads.
// That lookup needs the window's link back to this tab (window.opener), so it is kept; the only
// pages ever opened in it are ChatGPT and Claude.
function openAiWindow(url) {
  const win = window.open(url, AI_WINDOW.name, windowFeatures());
  win?.focus();
  return win;
}

/**
 * Opens the provider with the prompt filled in. Must be called straight from a click, before
 * any await, or the browser blocks the window. Resolves to { opened, prefilled, copied }.
 */
export async function askInWindow(providerId, prompt) {
  const provider = AI_PROVIDERS[providerId];
  // Copy first: once the new window takes focus, this page may no longer write the clipboard.
  const copying = copyPrompt(prompt);
  const url = provider.ask(prompt);
  const prefilled = url.length <= AI_MAX_URL_LENGTH;
  const win = openAiWindow(prefilled ? url : provider.newChat);
  return { opened: Boolean(win), prefilled, copied: await copying };
}

/**
 * Brings the AI window back, e.g. to scroll through the conversation. Never re-sends a
 * question: an open window is just focused; a closed one reopens on the provider's chat list.
 * Returns "focused", "reopened" or "blocked".
 */
export function showChatWindow(providerId) {
  // With an empty URL, an existing window of this name is returned untouched.
  const win = window.open("", AI_WINDOW.name, windowFeatures());
  if (!win) return "blocked";
  let isBlank;
  try {
    isBlank = win.location.href === "about:blank"; // a fresh window: there was none open
  } catch {
    isBlank = false; // cross-origin: it is showing the chat
  }
  if (isBlank) win.location.href = AI_PROVIDERS[providerId].chats;
  win.focus();
  return isBlank ? "reopened" : "focused";
}
