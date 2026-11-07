import { reducedMotion, sessionStore } from './env.js';

const SEEN = 'rt-intro';
const HOLD_MS = 900;

// The page is already painted when this runs. The overlay is cosmetic and leaves on its own.
export function initIntro() {
  if (!document.body.classList.contains('page-home')) return;
  if (reducedMotion.matches || window.location.hash) return;
  if (sessionStore.get(SEEN)) return;
  sessionStore.set(SEEN, '1');

  const overlay = document.createElement('div');
  overlay.className = 'intro';
  const word = document.createElement('p');
  word.className = 'intro__word';
  word.textContent = 'RideMate';
  word.setAttribute('aria-hidden', 'true');
  const skip = document.createElement('button');
  skip.type = 'button';
  skip.className = 'intro__skip';
  skip.textContent = 'Skip intro';
  overlay.append(word, skip);
  document.body.prepend(overlay);

  word.animate(
    [
      { opacity: 0, transform: 'translateY(14px)' },
      { opacity: 1, transform: 'none' },
    ],
    { duration: 420, easing: 'cubic-bezier(.2, .8, .2, 1)', fill: 'both' },
  );

  const controller = new AbortController();
  let leaving = false;
  const remove = () => {
    controller.abort();
    overlay.remove();
  };
  const leave = () => {
    if (leaving) return;
    leaving = true;
    overlay.classList.add('is-leaving');
    overlay.addEventListener('transitionend', remove, { once: true });
    window.setTimeout(remove, 520);
  };

  skip.addEventListener('click', leave, { signal: controller.signal });
  document.addEventListener(
    'keydown',
    (event) => {
      if (event.key === 'Escape') leave();
    },
    { signal: controller.signal },
  );
  window.setTimeout(leave, HOLD_MS);
}
