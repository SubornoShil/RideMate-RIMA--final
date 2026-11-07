import { clamp, finePointer, reducedMotion } from './env.js';

export function initMagnetic() {
  const buttons = [...document.querySelectorAll('[data-magnetic]')];
  if (!buttons.length) return;

  let controller = null;

  const apply = () => {
    controller?.abort();
    controller = null;
    buttons.forEach((button) => {
      button.style.transform = '';
    });
    if (!finePointer.matches || reducedMotion.matches) return;

    controller = new AbortController();
    const { signal } = controller;

    for (const button of buttons) {
      let queued = false;
      let dx = 0;
      let dy = 0;
      const paint = () => {
        queued = false;
        button.style.transform = dx || dy ? `translate3d(${dx}px, ${dy}px, 0)` : '';
      };
      const schedule = () => {
        if (!queued) {
          queued = true;
          requestAnimationFrame(paint);
        }
      };
      button.addEventListener(
        'pointermove',
        (event) => {
          const box = button.getBoundingClientRect();
          dx = clamp((event.clientX - (box.left + box.width / 2)) * 0.25, -10, 10);
          dy = clamp((event.clientY - (box.top + box.height / 2)) * 0.25, -8, 8);
          schedule();
        },
        { passive: true, signal },
      );
      button.addEventListener(
        'pointerleave',
        () => {
          dx = 0;
          dy = 0;
          schedule();
        },
        { signal },
      );
    }
  };

  finePointer.addEventListener('change', apply);
  reducedMotion.addEventListener('change', apply);
  apply();
}
