// The Ask AI box: the sentence, an optional note, the (editable) template and the provider.

import { copyPrompt, loadProvider, saveProvider } from "../ai/handoff.js";
import { fillPrompt, loadTemplate, resetTemplate, saveTemplate, sentenceAround } from "../ai/prompt.js";
import { AI_PROVIDERS } from "../config.js";
import { el } from "./dom.js";

function button(className, label, title, onClick) {
  const node = el("button", className, label);
  node.type = "button";
  node.title = title;
  node.addEventListener("click", onClick);
  return node;
}

export function setupAskAiDialog({ status }) {
  const dialog = el("div", "popup ask-ai");
  dialog.hidden = true;
  dialog.setAttribute("role", "dialog");
  document.body.append(dialog);

  let current = null; // { selection, sentence }
  let provider = loadProvider();

  function close() {
    dialog.hidden = true;
    current = null;
  }

  async function send(note, template) {
    const { selection, sentence } = current;
    const prompt = fillPrompt(template, { selection, sentence, note });
    const copied = await copyPrompt(prompt);
    close();
    status.set(copied ? `Prompt about ${selection} copied` : "Could not copy the prompt");
  }

  function render() {
    const title = el("div", "popup__title");
    title.append(el("span", "popup__word", `ASK AI · ${current.selection}`));
    title.append(button("popup__close", "×", "Close (Esc)", close));

    const body = el("div", "popup__body");
    body.append(el("div", "popup__group", "Sentence"), el("div", "ask-ai__sentence", current.sentence));

    body.append(el("div", "popup__group", "Note (optional)"));
    const note = el("textarea", "field");
    note.rows = 2;
    note.placeholder = "e.g. compare with 〜ながら";
    body.append(note);

    const templateBox = el("details", "ask-ai__template");
    templateBox.append(el("summary", "popup__group", "Template"));
    const template = el("textarea", "field");
    template.rows = 12;
    template.value = loadTemplate();
    const templateActions = el("div", "ask-ai__row");
    templateActions.append(
      button("btn", "Save as default", "Use this template for every question", () => {
        status.set(saveTemplate(template.value) ? "Template saved" : "Could not save the template");
      }),
      button("btn", "Reset", "Go back to the built-in template", () => {
        template.value = resetTemplate();
        status.set("Template reset");
      }),
    );
    templateBox.append(template, templateActions);
    body.append(templateBox);

    body.append(el("div", "popup__group", "Ask with"));
    const providers = el("div", "ask-ai__providers");
    for (const [id, { label }] of Object.entries(AI_PROVIDERS)) {
      const option = button("tool", label, `Open in your ${label} account`, () => {
        provider = id;
        saveProvider(id);
        providers.querySelectorAll(".tool").forEach((t) => t.setAttribute("aria-pressed", String(t === option)));
      });
      option.setAttribute("aria-pressed", String(id === provider));
      providers.append(option);
    }
    body.append(providers);

    const actions = el("div", "popup__actions");
    const sendButton = button("btn", "Send", "Send (⌘↵)", () => send(note.value, template.value));
    actions.append(sendButton);
    note.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) sendButton.click();
    });

    dialog.replaceChildren(title, body, actions);
    dialog.hidden = false;
    note.focus();
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !dialog.hidden) close();
  });

  return {
    open({ text, context, offset }) {
      current = { selection: text, sentence: sentenceAround(context, offset) };
      render();
    },
  };
}
