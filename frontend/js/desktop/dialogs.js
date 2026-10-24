// Retro desktop dialogs: a small window with a striped title bar and YES / NO style buttons.
// Each returns a promise; Enter confirms, Esc cancels.

import { el } from "../ui/dom.js";

function button(label, onClick) {
  const node = el("button", "desk-btn", label);
  node.type = "button";
  node.addEventListener("click", onClick);
  return node;
}

function openDialog(title, buildBody, { confirmLabel, cancelLabel }) {
  return new Promise((resolve) => {
    // An invisible layer: the desktop stays visible but can't be clicked until the dialog closes.
    const blocker = el("div", "desk-blocker");
    const dialog = el("div", "dwin desk-dialog");
    dialog.setAttribute("role", "dialog");
    const titleBar = el("div", "dwin__title");
    titleBar.append(el("span", "dwin__name", title));

    const { body, value, focus } = buildBody();
    const finish = (confirmed) => {
      blocker.remove();
      document.removeEventListener("keydown", onKey, true);
      resolve(confirmed ? value() : null);
    };
    const onKey = (event) => {
      if (event.key === "Escape") finish(false);
      // On a focused button, Enter presses that button (so Enter on "No" never means yes).
      if (event.key === "Enter" && event.target.tagName !== "BUTTON") {
        event.preventDefault();
        finish(true);
      }
      event.stopPropagation(); // the desktop's own shortcuts wait until the dialog is closed
    };

    const close = el("button", "dwin__close", "×");
    close.type = "button";
    close.addEventListener("click", () => finish(false));
    titleBar.append(close);

    const actions = el("div", "desk-dialog__actions");
    actions.append(button(confirmLabel, () => finish(true)));
    if (cancelLabel) actions.append(button(cancelLabel, () => finish(false)));

    dialog.append(titleBar, body, actions);
    blocker.append(dialog);
    document.body.append(blocker);
    document.addEventListener("keydown", onKey, true);
    if (focus) focus();
    else actions.firstChild.focus();
  });
}

/** Asks for a name. Resolves to the trimmed text, or null if cancelled or left empty. */
export async function promptDialog({ title, label, value = "", confirmLabel = "OK" }) {
  const answer = await openDialog(
    title,
    () => {
      const body = el("div", "dwin__body");
      const input = el("input", "desk-input");
      input.value = value;
      input.maxLength = 100;
      body.append(el("label", "desk-dialog__label", label), input);
      return {
        body,
        value: () => input.value.trim(),
        focus: () => {
          input.focus();
          input.select();
        },
      };
    },
    { confirmLabel, cancelLabel: "Cancel" },
  );
  return answer || null;
}

/** Asks a yes/no question. Resolves to true for yes. */
export async function confirmDialog({ title, message, confirmLabel = "Yes", cancelLabel = "No" }) {
  const answer = await openDialog(
    title,
    () => {
      const body = el("div", "dwin__body");
      body.append(el("p", "desk-dialog__message", message));
      return { body, value: () => true };
    },
    { confirmLabel, cancelLabel },
  );
  return answer === true;
}

/** Tells the user something. Resolves when dismissed. */
export function alertDialog({ title, message }) {
  return openDialog(
    title,
    () => {
      const body = el("div", "dwin__body");
      body.append(el("p", "desk-dialog__message", message));
      return { body, value: () => true };
    },
    { confirmLabel: "OK" },
  );
}
