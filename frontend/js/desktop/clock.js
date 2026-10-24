// The menu bar clock: "SAT 24 OCT  15:42".

const DAY = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short" });
const TIME = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

export function startClock(el) {
  const tick = () => {
    const now = new Date();
    el.textContent = `${DAY.format(now).replace(",", "")}  ${TIME.format(now)}`.toUpperCase();
  };
  tick();
  setInterval(tick, 15_000);
}
