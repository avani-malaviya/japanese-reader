// Click a picture to select it, then align, resize (corner handle), move (drag) or delete it.
// The controls are an overlay outside the editable page, so nothing of them is ever saved.

import {
  ALIGNMENTS,
  dropTarget,
  getAlign,
  moveFigure,
  setAlign,
  setWidthPx,
} from "../editor/figures.js";
import { el } from "./dom.js";

const ALIGN_LABELS = { left: "◧", center: "▣", right: "◨" };
const ALIGN_TITLES = {
  left: "Float left, text wraps on the right",
  center: "Centre on its own line",
  right: "Float right, text wraps on the left",
};
const DRAG_THRESHOLD = 4;
const AUTOSCROLL_EDGE = 48;
const AUTOSCROLL_STEP = 24;

export function setupFigureControls({ editor, scroller, status }) {
  const overlay = el("div", "figure-overlay");
  const frame = el("div", "figure-overlay__frame");
  frame.title = "Drag to move";
  const handle = el("div", "figure-overlay__handle");
  handle.title = "Drag to resize";
  const toolbar = el("div", "figure-overlay__toolbar");
  overlay.append(frame, handle, toolbar);
  overlay.hidden = true;

  const dropBar = el("div", "drop-bar");
  dropBar.hidden = true;
  document.body.append(overlay, dropBar);

  let selected = null;

  function place() {
    if (!selected) return;
    const rect = selected.getBoundingClientRect();
    Object.assign(overlay.style, {
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
    });
  }

  function renderToolbar() {
    const current = getAlign(selected);
    const buttons = ALIGNMENTS.map((align) => {
      const button = el("button", "tool", ALIGN_LABELS[align]);
      button.type = "button";
      button.title = ALIGN_TITLES[align];
      button.setAttribute("aria-pressed", String(align === current));
      button.addEventListener("click", () => {
        setAlign(selected, align);
        editor.changed();
        renderToolbar();
        place();
      });
      return button;
    });
    const remove = el("button", "tool", "✕");
    remove.type = "button";
    remove.title = "Delete picture";
    remove.addEventListener("click", deleteSelected);
    toolbar.replaceChildren(...buttons, remove);
  }

  function select(figure) {
    selected = figure;
    overlay.hidden = false;
    renderToolbar();
    place();
  }

  function deselect() {
    selected = null;
    overlay.hidden = true;
  }

  function deleteSelected() {
    selected.remove();
    deselect();
    editor.changed();
    status.set("Picture deleted");
  }

  // Shared pointer-drag plumbing: onMove(dx, dy, event), onEnd(moved, event).
  function drag(startEvent, { onMove, onEnd }) {
    startEvent.preventDefault();
    const { clientX: startX, clientY: startY } = startEvent;
    let moved = false;
    const move = (event) => {
      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      if (!moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      moved = true;
      onMove(dx, dy, event);
    };
    const up = (event) => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      onEnd(moved, event);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  // Dragging near the top or bottom edge scrolls, so pictures can move anywhere in a long document.
  function autoScroll(y) {
    const { top, bottom } = scroller.getBoundingClientRect();
    if (y < top + AUTOSCROLL_EDGE) scroller.scrollBy(0, -AUTOSCROLL_STEP);
    else if (y > bottom - AUTOSCROLL_EDGE) scroller.scrollBy(0, AUTOSCROLL_STEP);
  }

  handle.addEventListener("pointerdown", (event) => {
    const startWidth = selected.getBoundingClientRect().width;
    drag(event, {
      // Floats on the right grow towards the left, so drag direction follows the side.
      onMove: (dx) => {
        const sign = getAlign(selected) === "right" ? -1 : 1;
        setWidthPx(selected, startWidth + sign * dx);
        place();
      },
      onEnd: (moved) => moved && editor.changed(),
    });
  });

  frame.addEventListener("pointerdown", (event) => {
    let target = null;
    drag(event, {
      onMove: (_dx, _dy, move) => {
        autoScroll(move.clientY);
        overlay.hidden = true; // don't hide what's under the pointer
        target = dropTarget(editor.el, move.clientX, move.clientY, selected);
        overlay.hidden = false;
        dropBar.hidden = !target;
        if (target) {
          const rect = target.block.getBoundingClientRect();
          Object.assign(dropBar.style, {
            left: `${rect.left}px`,
            width: `${rect.width}px`,
            top: `${target.before ? rect.top - 2 : rect.bottom}px`,
          });
        }
      },
      onEnd: (moved) => {
        dropBar.hidden = true;
        if (!moved || !target) return;
        moveFigure(selected, target);
        editor.changed();
        place();
        status.set("Picture moved");
      },
    });
  });

  editor.el.addEventListener("click", (event) => {
    const figure = event.target.closest("figure");
    if (figure && editor.el.contains(figure)) select(figure);
  });

  // Native image drag would copy the picture as HTML into the document.
  editor.el.addEventListener("dragstart", (event) => {
    if (event.target.closest("figure")) event.preventDefault();
  });

  document.addEventListener("mousedown", (event) => {
    if (!selected || overlay.contains(event.target)) return;
    if (!selected.contains(event.target)) deselect();
  });

  document.addEventListener("keydown", (event) => {
    if (!selected) return;
    if (event.key === "Delete" || event.key === "Backspace") {
      event.preventDefault();
      deleteSelected();
    } else {
      deselect(); // Esc, or the user went back to typing
    }
  });

  scroller.addEventListener("scroll", place);
  window.addEventListener("resize", place);
  editor.el.addEventListener("input", () => {
    if (selected && !editor.el.contains(selected)) deselect();
    else place();
  });

  return { deselect };
}
