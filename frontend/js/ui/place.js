import { POPUP_GAP } from "../config.js";

/** Puts a fixed-position box beside `rect` if there is room, otherwise below it. Never on top. */
export function placeBeside(box, rect) {
  const { innerWidth, innerHeight } = window;
  const width = box.offsetWidth;
  const height = box.offsetHeight;
  let left = rect.right + POPUP_GAP;
  let top = rect.top;
  if (left + width > innerWidth) {
    left = Math.max(POPUP_GAP, Math.min(rect.left, innerWidth - width - POPUP_GAP));
    top = rect.bottom + POPUP_GAP;
  }
  if (top + height > innerHeight) {
    top = Math.max(POPUP_GAP, rect.top - height - POPUP_GAP);
  }
  box.style.left = `${left}px`;
  box.style.top = `${top}px`;
}
