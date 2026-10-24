export const AUTOSAVE_DELAY_MS = 500;

// Keep in sync with MAX_LOOKUP_CHARS in backend/app/config.py.
export const MAX_LOOKUP_CHARS = 50;

// "Insert" adds furigana to the selected occurrence and the ones after it, this many in total.
export const FURIGANA_OCCURRENCES = 5;

// Gap between the selection and the lookup popup, in px.
export const POPUP_GAP = 12;

// "Ask AI" hands the question to the user's own ChatGPT or Claude account in a floating window.
export const AI_PROVIDERS = {
  chatgpt: {
    label: "ChatGPT",
    ask: (prompt) => `https://chatgpt.com/?q=${encodeURIComponent(prompt)}`,
    newChat: "https://chatgpt.com/",
    chats: "https://chatgpt.com/",
  },
  claude: {
    label: "Claude",
    ask: (prompt) => `https://claude.ai/new?q=${encodeURIComponent(prompt)}`,
    newChat: "https://claude.ai/new",
    chats: "https://claude.ai/recents",
  },
};
export const AI_WINDOW = { name: "japanese-reader-ai", width: 560, height: 680, offsetTop: 80 };
// Longer pre-filled URLs risk being refused; the prompt is copied to paste instead.
export const AI_MAX_URL_LENGTH = 7000;
