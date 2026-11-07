import { initCount } from './count.js';
import { initCountdown } from './countdown.js';
import { initLanes } from './lanes.js';
import { initIntro } from './intro.js';
import { initMagnetic } from './magnetic.js';
import { initMapView } from './mapview.js';
import { initMaps } from './maps.js';
import { initMeter } from './meter.js';
import { initPasswordToggles } from './password.js';
import { initReveal } from './reveal.js';
import { initSound } from './sound.js';
import { initStrength } from './strength.js';
import { initTitle } from './title.js';
import { initToasts } from './toasts.js';

document.documentElement.classList.add('js');
document.documentElement.dataset.ready = '1';

const enhancements = [
  initIntro,
  initReveal,
  initCount,
  initPasswordToggles,
  initStrength,
  initCountdown,
  initMagnetic,
  initToasts,
  initMeter,
  initSound,
  initMaps,
  initMapView,
  initLanes,
  initTitle,
];

for (const enhance of enhancements) {
  try {
    enhance();
  } catch {
    // Every enhancement is optional and independent: one failing must not stop the rest.
  }
}
