const RULES = {
  number: (value) => /\d/.test(value),
  case: (value) => /[a-z]/.test(value) && /[A-Z]/.test(value),
  symbol: (value) => /[^A-Za-z0-9]/.test(value),
  length: (value) => value.length >= 12,
};

// These checks only say "stronger". The server's validators decide what is allowed.
export function initStrength() {
  const panel = document.querySelector('[data-strength]');
  const input = document.getElementById('id_password1');
  if (!panel || !input) return;

  const meter = panel.querySelector('meter');
  const items = [...panel.querySelectorAll('li[data-rule]')];
  panel.hidden = false;

  const update = () => {
    let met = 0;
    for (const item of items) {
      const rule = RULES[item.dataset.rule];
      const ok = rule ? rule(input.value) : false;
      item.classList.toggle('is-met', ok);
      if (ok) met += 1;
    }
    if (meter) meter.value = met;
  };

  input.addEventListener('input', update);
  update();
}
