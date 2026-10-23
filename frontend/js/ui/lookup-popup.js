// The box that appears beside highlighted text: readings, and actions on them.

import { getMeaning, getReadings } from "../api.js";
import { FURIGANA_OCCURRENCES, POPUP_GAP } from "../config.js";
import { insertFurigana, removeFurigana } from "../editor/furigana.js";
import { getSelectionInfo } from "../editor/selection.js";
import { el } from "./dom.js";
import { renderMeaning } from "./meaning-view.js";

const GROUP_LABELS = { word: "読み READING", on: "音 ON", kun: "訓 KUN" };

export function setupLookupPopup({ editor, scroller, status }) {
  const popup = el("div", "popup");
  popup.hidden = true;
  popup.setAttribute("role", "dialog");
  document.body.append(popup);

  // { info, ruby, readings, chosen, meaning: null | "loading" | response }
  let current = null;
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
    render(body, ...renderMeaningSection(), renderActions());
  }

  function renderMeaningSection() {
    if (current.meaning === "loading") return [el("div", "popup__body popup__loading", "LOOKING UP…")];
    if (current.meaning) return [renderMeaning(current.meaning)];
    return [];
  }

  async function onMeaning() {
    if (current.meaning) {
      current.meaning = null; // toggle off
      return renderReadings();
    }
    const id = requestId;
    current.meaning = "loading";
    renderReadings();
    try {
      const meaning = await getMeaning(current.info.text);
      if (id !== requestId) return;
      current.meaning = meaning;
      renderReadings();
    } catch (error) {
      if (id !== requestId) return;
      current.meaning = null;
      renderReadings();
      status.set(`Error: ${error.message}`);
    }
  }

  function renderActions() {
    const actions = el("div", "popup__actions");
    const insert = actionButton(
      "Insert",
      `Add this reading under the next ${FURIGANA_OCCURRENCES} occurrences`,
      onInsert,
    );
    // Furigana that just repeats kana text adds nothing.
    insert.disabled = !current.chosen || current.chosen.kana === current.info.text;
    const meaning = actionButton("Meaning", "Look up the dictionary meaning", onMeaning);
    meaning.setAttribute("aria-pressed", String(Boolean(current.meaning)));
    actions.append(insert, meaning);

    if (current.ruby) {
      actions.append(
        actionButton("Remove", "Remove this furigana", () => onRemove(false)),
        actionButton("Remove all", "Remove this reading from every occurrence", () => onRemove(true)),
      );
    }
    return actions;
  }

  function actionButton(label, title, onClick) {
    const button = el("button", "btn", label);
    button.type = "button";
    button.title = title;
    button.addEventListener("click", onClick);
    return button;
  }

  function onRemove(everywhere) {
    const text = current.info.text;
    const removed = removeFurigana(editor.el, current.ruby, { everywhere });
    editor.changed();
    close();
    window.getSelection().removeAllRanges();
    status.set(`Removed furigana from ${removed} × ${text}`);
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

  async function open(info, ruby = null) {
    const id = ++requestId;
    current = { info, ruby, readings: [], chosen: null, meaning: null };
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

  // A plain click on furigana selects its word and opens the popup with Remove options.
  function onClick(event) {
    const ruby = event.target.closest("ruby");
    if (!ruby || !window.getSelection().isCollapsed) return onSelectionDone();
    const range = document.createRange();
    range.selectNodeContents(ruby);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    const info = getSelectionInfo(editor.el);
    if (info) open(info, ruby);
  }

  editor.el.addEventListener("mouseup", (event) => setTimeout(() => onClick(event)));
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
