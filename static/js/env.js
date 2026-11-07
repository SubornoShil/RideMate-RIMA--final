// Shared environment checks and tiny helpers. Nothing here touches the DOM.

export const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
export const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
export const darkScheme = window.matchMedia('(prefers-color-scheme: dark)');

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

/** True on devices that asked to save data or report very little CPU or memory. */
export function lowPower() {
  const saveData = navigator.connection?.saveData === true;
  const fewCores = typeof navigator.hardwareConcurrency === 'number' && navigator.hardwareConcurrency <= 2;
  const lowMemory = typeof navigator.deviceMemory === 'number' && navigator.deviceMemory <= 2;
  return saveData || fewCores || lowMemory;
}

/** Storage can throw (private mode, blocked cookies), so every call is guarded. */
export function makeStore(kind) {
  const area = () => (kind === 'session' ? window.sessionStorage : window.localStorage);
  return {
    get(key) {
      try {
        return area().getItem(key);
      } catch {
        return null;
      }
    },
    set(key, value) {
      try {
        area().setItem(key, value);
      } catch {
        // Nothing to do: the setting simply lasts until the page closes.
      }
    },
  };
}

export const localStore = makeStore('local');
export const sessionStore = makeStore('session');

export function whenIdle(callback) {
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(callback, { timeout: 1500 });
  } else {
    window.setTimeout(callback, 250);
  }
}
