import { localStore } from './env.js';

const KEY = 'rt-sound';
let context = null;
let enabled = false;

function audioContext() {
  if (context) {
    if (context.state === 'suspended') context.resume().catch(() => {});
    return context;
  }
  const Ctor = window.AudioContext || window.webkitAudioContext;
  if (!Ctor) return null;
  context = new Ctor();
  return context;
}

/** One short, quiet click. Does nothing unless the visitor switched sound on. */
export function tick(frequency = 520, length = 70) {
  if (!enabled) return;
  const audio = audioContext();
  if (!audio) return;
  const now = audio.currentTime;
  const end = now + length / 1000;
  const oscillator = audio.createOscillator();
  const gain = audio.createGain();
  oscillator.type = 'triangle';
  oscillator.frequency.setValueAtTime(frequency, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.05, now + 0.008);
  gain.gain.exponentialRampToValueAtTime(0.0001, end);
  oscillator.connect(gain).connect(audio.destination);
  oscillator.start(now);
  oscillator.stop(end + 0.02);
}

export function initSound() {
  const button = document.querySelector('[data-sound-toggle]');
  if (!button || !(window.AudioContext || window.webkitAudioContext)) return;

  // Muted unless the visitor turned it on earlier. The audio context itself only
  // starts on a click, because browsers refuse to play before one.
  enabled = localStore.get(KEY) === 'on';
  button.hidden = false;

  const render = () => {
    button.setAttribute('aria-pressed', String(enabled));
    button.textContent = enabled ? 'Sound on' : 'Sound off';
  };
  render();

  button.addEventListener('click', () => {
    enabled = !enabled;
    localStore.set(KEY, enabled ? 'on' : 'off');
    render();
    tick(660, 90);
  });

  document.addEventListener('click', (event) => {
    if (event.target instanceof Element && event.target.closest('.btn, .nav__link, summary')) {
      tick(440, 50);
    }
  });
}
