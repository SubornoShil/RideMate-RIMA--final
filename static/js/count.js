import { reducedMotion } from './env.js';

const DURATION = 900;

function countUp(element, target, decimals, finalText) {
  const start = performance.now();
  const step = (now) => {
    const t = Math.min(1, (now - start) / DURATION);
    const eased = 1 - (1 - t) ** 3;
    element.textContent = (target * eased).toFixed(decimals);
    if (t < 1) {
      requestAnimationFrame(step);
    } else {
      element.textContent = finalText;
    }
  };
  requestAnimationFrame(step);
}

export function initCount() {
  const nodes = document.querySelectorAll('[data-count]');
  if (!nodes.length || reducedMotion.matches || !('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const element = entry.target;
      observer.unobserve(element);
      const finalText = element.textContent.trim();
      const raw = finalText.replace(/,/g, '');
      const target = Number.parseFloat(raw);
      if (!Number.isFinite(target) || target === 0) continue;
      const decimals = (raw.split('.')[1] || '').length;
      countUp(element, target, decimals, finalText);
    }
  });
  nodes.forEach((node) => observer.observe(node));
}
