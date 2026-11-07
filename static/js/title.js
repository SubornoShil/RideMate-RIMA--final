const AWAY_TITLE = 'Still going that way? | RideMate';

// Two threads tied into one knot, in the accent colours. Used as the favicon while the tab is hidden.
const AWAY_ICON = `data:image/svg+xml,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#138553"/>'
  + '<path d="M3 25C12 25 12 7 16 16S22 7 29 7" fill="none" stroke="#3EE29A" stroke-width="3" stroke-linecap="round"/>'
  + '<path d="M3 7C12 7 12 25 16 16S22 25 29 25" fill="none" stroke="#E9F3EC" stroke-width="3" stroke-linecap="round"/>'
  + '<circle cx="16" cy="16" r="4.5" fill="#E9F3EC" stroke="#06110C" stroke-width="1.5"/></svg>',
)}`;

export function initTitle() {
  const icon = document.querySelector('link[rel="icon"]');
  const originalIcon = icon?.getAttribute('href') ?? null;
  let originalTitle = document.title;

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      originalTitle = document.title;
      document.title = AWAY_TITLE;
      if (icon) icon.setAttribute('href', AWAY_ICON);
    } else {
      document.title = originalTitle;
      if (icon && originalIcon) icon.setAttribute('href', originalIcon);
    }
  });
}
