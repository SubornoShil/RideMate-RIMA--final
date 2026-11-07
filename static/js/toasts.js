const LINGER_MS = 6000;
const STAY = ['toast--error', 'toast--warning'];

// Errors and warnings stay until the next page, so nobody misses them.
export function initToasts() {
  document.querySelectorAll('.toasts .toast').forEach((toast) => {
    if (STAY.some((name) => toast.classList.contains(name))) return;
    window.setTimeout(() => {
      toast.hidden = true;
    }, LINGER_MS);
  });
}
