import { reducedMotion } from './env.js';

// The hero map has two views: inside Dhaka (where most shared rides happen) and across Bangladesh.
// It swaps on its own every few seconds until the visitor picks one.
const SWAP_MS = 9000;

export function initMapView() {
  const root = document.querySelector('[data-mapview]');
  if (!root) return;
  const tabs = [...root.querySelectorAll('[data-view-tab]')];
  const views = [...root.querySelectorAll('[data-view]')];
  if (tabs.length < 2 || tabs.length !== views.length) return;

  let current = Math.max(0, views.findIndex((view) => view.classList.contains('is-active')));
  let timer = 0;

  const show = (index) => {
    current = index;
    views.forEach((view, i) => view.classList.toggle('is-active', i === index));
    tabs.forEach((tab, i) => {
      tab.classList.toggle('is-active', i === index);
      tab.setAttribute('aria-pressed', String(i === index));
    });
  };

  const stop = () => {
    window.clearInterval(timer);
    timer = 0;
  };
  const start = () => {
    if (timer || reducedMotion.matches || document.hidden) return;
    timer = window.setInterval(() => show((current + 1) % views.length), SWAP_MS);
  };

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => {
      stop(); // the visitor chose: stop swapping for good
      show(i);
      root.dataset.manual = '1';
    });
  });
  document.addEventListener('visibilitychange', () => {
    if (root.dataset.manual) return;
    if (document.hidden) stop();
    else start();
  });
  start();
}
