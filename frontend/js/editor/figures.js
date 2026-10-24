// Pictures in the document: alignment, size and position. DOM operations only.

export const ALIGNMENTS = ["left", "center", "right"];
const MIN_WIDTH_PERCENT = 15;

export function getAlign(figure) {
  return ALIGNMENTS.find((align) => figure.classList.contains(`figure--${align}`)) ?? "center";
}

export function setAlign(figure, align) {
  ALIGNMENTS.forEach((a) => figure.classList.remove(`figure--${a}`));
  figure.classList.add(`figure--${align}`);
}

// Width of the box a percentage width is measured against: the parent's content box.
function containerWidth(figure) {
  const parent = figure.parentElement;
  const style = getComputedStyle(parent);
  return parent.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
}

/** Sets the picture's width in px, stored as a percentage of its container. */
export function setWidthPx(figure, px) {
  const percent = (px / containerWidth(figure)) * 100;
  const clamped = Math.min(100, Math.max(MIN_WIDTH_PERCENT, percent));
  figure.style.width = `${clamped.toFixed(1)}%`;
}

// Blocks a picture can be placed between: children of the page or of a column.
function isBlock(node, root) {
  const parent = node.parentElement;
  return parent === root || parent?.classList.contains("column");
}

/**
 * Where a picture dragged to viewport point (x, y) would land: { block, before }, meaning
 * "before or after `block`". `exclude` is the picture being moved. Null if nowhere sensible.
 */
export function dropTarget(root, x, y, exclude) {
  let node = document.elementFromPoint(x, y);
  while (node && node !== root && !(isBlock(node, root) && node !== exclude)) {
    node = node.parentElement;
  }
  let container = root;
  if (node && node !== root) {
    container = node.parentElement;
  } else if (node !== root) {
    return null; // outside the document
  }
  const blocks = [...container.children].filter((child) => child !== exclude);
  if (!blocks.length) return null;
  // Nearest block by vertical distance; drop above or below its middle.
  let best = blocks[0];
  let bestDistance = Infinity;
  for (const block of blocks) {
    const rect = block.getBoundingClientRect();
    const distance = y < rect.top ? rect.top - y : y > rect.bottom ? y - rect.bottom : 0;
    if (distance < bestDistance) {
      best = block;
      bestDistance = distance;
    }
  }
  const rect = best.getBoundingClientRect();
  return { block: best, before: y < rect.top + rect.height / 2 };
}

export function moveFigure(figure, { block, before }) {
  if (before) block.before(figure);
  else block.after(figure);
}
