const PROGRESS_CELLS = 8;

export function createStatusbar({ messageEl, countEl }) {
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

    setCount(chars) {
      countEl.textContent = `${chars} chars`;
    },
  };
}
