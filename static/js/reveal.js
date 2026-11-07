import { reducedMotion } from './env.js';

// CSS decides how each kind of reveal looks (slide, clip, scale, draw). This only says when.
export function initReveal() {
  const items = document.querySelectorAll('[data-reveal]');
  if (!items.length) return;

  if (!('IntersectionObserver' in window) || reducedMotion.matches) {
    items.forEach((item) => item.classList.add('is-in'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      let order = 0;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        // Items that arrive together step in one after another instead of as a block.
        entry.target.style.transitionDelay = `${Math.min(order, 5) * 70}ms`;
        entry.target.classList.add('is-in');
        observer.unobserve(entry.target);
        order += 1;
      }
    },
    { threshold: 0.01, rootMargin: '0px 0px -6% 0px' },
  );
  items.forEach((item) => observer.observe(item));
}
