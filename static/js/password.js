// The server-rendered button is hidden until this runs, so without JavaScript it never shows.
export function initPasswordToggles() {
  document.querySelectorAll('[data-toggle-password]').forEach((button) => {
    const scope = button.closest('[data-password-group]') || button.closest('form');
    if (!scope) return;
    const inputs = [...scope.querySelectorAll('input[type="password"]')];
    if (!inputs.length) return;

    const showLabel = button.textContent.trim();
    const hideLabel = showLabel.replace(/^Show/, 'Hide');
    button.hidden = false;

    const setVisible = (visible) => {
      for (const input of inputs) {
        input.type = visible ? 'text' : 'password';
        input.spellcheck = false;
      }
      button.setAttribute('aria-pressed', String(visible));
      button.textContent = visible ? hideLabel : showLabel;
    };

    button.addEventListener('click', () => {
      setVisible(button.getAttribute('aria-pressed') !== 'true');
    });
    // Put the fields back before submitting so password managers see a password field.
    button.closest('form')?.addEventListener('submit', () => setVisible(false));
  });
}
