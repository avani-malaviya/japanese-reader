// Furigana: <ruby>漢字<rt>かんじ</rt></ruby>, shown under the text (see css).

// Already annotated, or the reader's own note text: never gets furigana.
function isAnnotated(node) {
  return Boolean(node.parentElement.closest("ruby, .note-line"));
}

// Occurrences of `text` that sit inside one text node, in document order.
function* occurrences(root, text) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (isAnnotated(node)) continue;
    let index = node.data.indexOf(text);
    while (index !== -1) {
      yield { node, index };
      index = node.data.indexOf(text, index + text.length);
    }
  }
}

export function createRuby(base, kana) {
  const ruby = document.createElement("ruby");
  const rt = document.createElement("rt");
  rt.contentEditable = "false";
  rt.textContent = kana;
  ruby.append(base, rt);
  return ruby;
}

/**
 * Adds `kana` as furigana to `text` at the selection (`from`, a Range) and the occurrences
 * after it, up to `count` in total. Already-annotated occurrences are skipped.
 * Returns how many were added.
 */
export function insertFurigana(root, { text, kana, from, count }) {
  root.normalize(); // merge split text nodes so words aren't missed
  const targets = [];
  for (const hit of occurrences(root, text)) {
    if (from.comparePoint(hit.node, hit.index) < 0) continue; // before the selection
    targets.push(hit);
    if (targets.length === count) break;
  }

  // Last first, so splitting a text node doesn't shift the offsets of earlier hits.
  for (const { node, index } of targets.reverse()) {
    const word = node.splitText(index);
    word.splitText(text.length);
    word.replaceWith(createRuby(word.cloneNode(), kana));
  }
  return targets.length;
}

function unwrap(ruby) {
  ruby.querySelectorAll("rt").forEach((rt) => rt.remove());
  ruby.replaceWith(...ruby.childNodes);
}

export function baseText(ruby) {
  const clone = ruby.cloneNode(true);
  clone.querySelectorAll("rt").forEach((rt) => rt.remove());
  return clone.textContent;
}

function readingOf(ruby) {
  return ruby.querySelector("rt")?.textContent ?? "";
}

/** Removes furigana from `ruby`, or with `everywhere`, from every same word + reading. */
export function removeFurigana(root, ruby, { everywhere = false } = {}) {
  const matches = everywhere
    ? [...root.querySelectorAll("ruby:not(.note-word)")].filter(
        (other) => baseText(other) === baseText(ruby) && readingOf(other) === readingOf(ruby),
      )
    : [ruby];
  matches.forEach(unwrap);
  root.normalize();
  return matches.length;
}
