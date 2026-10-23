// Renders a /api/meaning response as a compact dictionary listing.

import { el } from "./dom.js";

const MAX_SENSES = 3;

export function renderMeaning({ text, looked_up, entries }) {
  const section = el("div", "popup__body meaning");
  section.append(el("div", "popup__group", "意味 MEANING"));

  if (looked_up !== text) {
    section.append(el("div", "meaning__note", `Dictionary form: ${looked_up}`));
  }
  if (!entries.length) {
    section.append(el("div", "meaning__note", "Not in the dictionary."));
    return section;
  }

  for (const entry of entries) {
    const head = el("div", "meaning__head");
    head.append(el("span", "meaning__word", entry.headword));
    if (entry.readings.length && entry.readings[0] !== entry.headword) {
      head.append(el("span", "meaning__reading", `【${entry.readings.join("・")}】`));
    }

    const senses = el("ol", "meaning__senses");
    for (const sense of entry.senses.slice(0, MAX_SENSES)) {
      const item = el("li", null, sense.glosses.join("; "));
      if (sense.pos.length) item.append(el("span", "meaning__pos", ` ${sense.pos.join(", ")}`));
      senses.append(item);
    }
    section.append(head, senses);
  }
  return section;
}
