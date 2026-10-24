const PROGRESS_CELLS = 8;

export function createStatusbar({ messageEl, countEl, saveEl }) {
  let progressTimer = null;

  function stopProgress() {
    clearInterval(progressTimer);
    progressTimer = null;
  }

  return {
    set(message) {
      stopProgress();
      messageEl.textContent = message;
    },

    // Indeterminate text progress: LABEL [■■■□□□□□]
    progress(label) {
      stopProgress();
      let filled = 0;
      const render = () => {
        const bar = "■".repeat(filled) + "□".repeat(PROGRESS_CELLS - filled);
        messageEl.textContent = `${label} [${bar}]`;
        filled = (filled + 1) % (PROGRESS_CELLS + 1);
      };
      render();
      progressTimer = setInterval(render, 250);
    },

    // "Saved", "Saving…" or "Not saved", beside the character count.
    setSaveState(text) {
      saveEl.textContent = text;
    },

    setCount(chars) {
      countEl.textContent = `${chars} chars`;
    },
  };
}
