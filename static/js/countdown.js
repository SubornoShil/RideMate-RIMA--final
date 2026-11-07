// Shows the wait on the resend button. The server enforces the real 60 second limit.
export function initCountdown() {
  document.querySelectorAll('[data-countdown]').forEach((button) => {
    const seconds = Number.parseInt(button.dataset.countdown, 10);
    if (!Number.isFinite(seconds) || seconds <= 0) return;

    const label = button.textContent.trim();
    const endsAt = performance.now() + seconds * 1000;
    let shown = -1;
    button.disabled = true;

    const tick = (now) => {
      const left = Math.max(0, Math.ceil((endsAt - now) / 1000));
      if (left !== shown) {
        shown = left;
        button.textContent = left > 0 ? `${label} (${left}s)` : label;
      }
      if (left > 0) {
        requestAnimationFrame(tick);
      } else {
        button.disabled = false;
      }
    };
    requestAnimationFrame(tick);
  });
}
