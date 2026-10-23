// Owns the document element: one <p> per paragraph.

export function createEditor(el) {
  function setParagraphs(paragraphs) {
    el.replaceChildren(
      ...paragraphs.map((text) => {
        const p = document.createElement("p");
        p.textContent = text;
        return p;
      }),
    );
  }

  return {
    el,
    setParagraphs,

    // Plain text without furigana (<rt>), for counting and lookups.
    getText() {
      const clone = el.cloneNode(true);
      clone.querySelectorAll("rt").forEach((rt) => rt.remove());
      return clone.innerText.trim();
    },

    isEmpty() {
      return this.getText().length === 0;
    },
  };
}
