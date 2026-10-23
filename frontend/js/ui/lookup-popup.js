// The box that appears beside highlighted text: readings, and actions on them.

import { getReadings } from "../api.js";
import { FURIGANA_OCCURRENCES, POPUP_GAP } from "../config.js";
import { insertFurigana } from "../editor/furigana.js";
import { getSelectionInfo } from "../editor/selection.js";

const GROUP_LABELS = { word: "読み READING", on: "音 ON", kun: "訓 KUN" };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function setupLookupPopup({ editor, scroller, status }) {
  const popup = el("div", "popup");
  popup.hidden = true;
  popup.setAttribute("role", "dialog");
  document.body.append(popup);

  let current = null; // { info, readings, chosen }
  let requestId = 0;

  function close() {
    popup.hidden = true;
    current = null;
    requestId++;
  }

  // Beside the selection if there is room, otherwise below it. Never on top of it.
  function place(rect) {
    const { innerWidth, innerHeight } = window;
    const width = popup.offsetWidth;
    const height = popup.offsetHeight;
    let left = rect.right + POPUP_GAP;
    let top = rect.top;
    if (left + width > innerWidth) {
      left = Math.max(POPUP_GAP, Math.min(rect.left, innerWidth - width - POPUP_GAP));
      top = rect.bottom + POPUP_GAP;
    }
    if (top + height > innerHeight) {
      top = Math.max(POPUP_GAP, rect.top - height - POPUP_GAP);
    }
    popup.style.left = `${left}px`;
    popup.style.top = `${top}px`;
  }

  function render(...sections) {
    const header = el("div", "popup__title");
    header.append(el("span", "popup__word", current.info.text));
    const closeButton = el("button", "popup__close", "×");
    closeButton.type = "button";
    closeButton.title = "Close (Esc)";
    closeButton.addEventListener("click", close);
    header.append(closeButton);

    popup.replaceChildren(header, ...sections);
    popup.hidden = false;
    place(current.info.rect);
  }

  function renderReadings() {
    const body = el("div", "popup__body");
    for (const kind of ["word", "on", "kun"]) {
      const group = current.readings.filter((r) => r.kind === kind);
      if (!group.length) continue;
      body.append(el("div", "popup__group", GROUP_LABELS[kind]));
      const list = el("ul", "popup__list");
      for (const reading of group) {
        const item = el("li", "popup__reading");
        item.append(el("span", "popup__kana", reading.label));
        if (reading.contextual) item.append(el("span", "popup__tag", "◆ in context"));
        item.setAttribute("aria-selected", String(reading === current.chosen));
        item.addEventListener("click", () => {
          current.chosen = reading;
          renderReadings();
        });
        list.append(item);
      }
      body.append(list);
    }
    render(body, renderActions());
  }

  function renderActions() {
    const actions = el("div", "popup__actions");
    const insert = el("button", "btn", "Insert");
    insert.type = "button";
    insert.title = `Add this reading under the next ${FURIGANA_OCCURRENCES} occurrences`;
    // Furigana that just repeats kana text adds nothing.
    insert.disabled = !current.chosen || current.chosen.kana === current.info.text;
    insert.addEventListener("click", onInsert);
    actions.append(insert);
    return actions;
  }

  function onInsert() {
    const { info, chosen } = current;
    const added = insertFurigana(editor.el, {
      text: info.text,
      kana: chosen.kana,
      from: info.range,
      count: FURIGANA_OCCURRENCES,
    });
    editor.changed();
    close();
    window.getSelection().removeAllRanges();
    status.set(
      added
        ? `Added ${chosen.kana} to ${added} × ${info.text}`
        : `${info.text} already has furigana`,
    );
  }

  async function open(info) {
    const id = ++requestId;
    current = { info, readings: [], chosen: null };
    render(el("div", "popup__body popup__loading", "LOOKING UP…"));
    try {
      const { readings } = await getReadings(info);
      if (id !== requestId) return; // a newer selection replaced this one
      current.readings = readings;
      current.chosen = readings.find((r) => r.contextual) ?? readings[0] ?? null;
      renderReadings();
    } catch (error) {
      if (id !== requestId) return;
      close();
      status.set(`Error: ${error.message}`);
    }
  }

  function onSelectionDone() {
    const info = getSelectionInfo(editor.el);
    if (info) open(info);
  }

  editor.el.addEventListener("mouseup", () => setTimeout(onSelectionDone));
  editor.el.addEventListener("keyup", (event) => {
    if (event.shiftKey) onSelectionDone();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
  document.addEventListener("mousedown", (event) => {
    if (!popup.hidden && !popup.contains(event.target)) close();
  });
  scroller.addEventListener("scroll", close);
  window.addEventListener("resize", close);

  return { close };
}
