// Hands a question to the user's own ChatGPT or Claude account. No API: the app never talks to
// an AI service itself; the user's browser opens the provider's site with the prompt filled in.

import { AI_PROVIDERS } from "../config.js";

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
