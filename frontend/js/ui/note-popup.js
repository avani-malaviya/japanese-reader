// The box for writing a note: new for a selection, or editing one already on the page.

import { baseText } from "../editor/furigana.js";
import { addNote, findNote, removeNote, updateNote } from "../editor/notes.js";
import { el } from "./dom.js";
import { placeBeside } from "./place.js";

function button(label, title, onClick) {
  const node = el("button", "btn", label);
  node.type = "button";
  node.title = title;
  node.addEventListener("click", onClick);
  return node;
}

export function setupNotePopup({ editor, scroller, status }) {
  const popup = el("div", "popup note-popup");
  popup.hidden = true;
  popup.setAttribute("role", "dialog");
  document.body.append(popup);

  function close() {
    popup.hidden = true;
  }

  function render(heading, rect, initialText, { onSave, onDelete }) {
    const title = el("div", "popup__title");
    title.append(el("span", "popup__word", heading));
    const closeButton = button("×", "Close (Esc)", close);
    closeButton.className = "popup__close";
    title.append(closeButton);

    const body = el("div", "popup__body");
    const field = el("textarea", "field note-popup__field");
    field.rows = 3;
    field.value = initialText;
    field.placeholder = "Your note…";
    body.append(field);

    const actions = el("div", "popup__actions");
    const save = button("Save", "Save (⌘↵)", () => {
      const text = field.value.trim();
      if (!text) return field.focus();
      onSave(text);
      editor.changed();
      close();
    });
    actions.append(save);
    if (onDelete) {
      actions.append(
        button("Delete note", "Remove this note (the text stays)", () => {
          onDelete();
          editor.changed();
          close();
        }),
      );
    }
    field.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) save.click();
    });

    popup.replaceChildren(title, body, actions);
    popup.hidden = false;
    placeBeside(popup, rect);
    field.focus();
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
  document.addEventListener("mousedown", (event) => {
    if (!popup.hidden && !popup.contains(event.target)) close();
  });
  scroller.addEventListener("scroll", close);

  return {
    close,

    /** A new note for the selection in `info` (from getSelectionInfo). */
    openNew(info) {
      const range = info.range.cloneRange();
      render(`NOTE · ${info.text}`, info.rect, "", {
        onSave: (text) => {
          addNote(range, text);
          window.getSelection().removeAllRanges();
          status.set(`Note added to ${info.text}`);
        },
      });
    },

    /** Opens the note that `element` (any part of it) belongs to. Returns false if none. */
    openExisting(element) {
      const note = findNote(editor.el, element);
      if (!note) return false;
      const noted = note.anchor.classList.contains("note-line") ? "" : ` · ${baseText(note.anchor)}`;
      render(`NOTE${noted}`, element.getBoundingClientRect(), note.text, {
        onSave: (text) => {
          updateNote(editor.el, note.id, text);
          status.set("Note updated");
        },
        onDelete: () => {
          removeNote(editor.el, note.id);
          status.set("Note deleted");
        },
      });
      return true;
    },
  };
}
