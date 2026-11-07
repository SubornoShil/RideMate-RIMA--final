import { clamp } from './env.js';

const FIELDS = [
  { text: 'id_start_location', lat: 'id_start_latitude', lng: 'id_start_longitude' },
  { text: 'id_end_location', lat: 'id_end_latitude', lng: 'id_end_longitude' },
];
const LOAD_TIMEOUT_MS = 8000;

function loadScript(key) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    const query = new URLSearchParams({ key, v: 'weekly', loading: 'async', region: 'BD' });
    script.src = `https://maps.googleapis.com/maps/api/js?${query}`;
    script.async = true;
    script.addEventListener('load', resolve, { once: true });
    script.addEventListener('error', () => reject(new Error('maps script blocked')), { once: true });
    document.head.append(script);
    window.setTimeout(() => reject(new Error('maps script timed out')), LOAD_TIMEOUT_MS);
  });
}

function enhance(form, spec, PlaceAutocompleteElement) {
  const input = document.getElementById(spec.text);
  const lat = document.getElementById(spec.lat);
  const lng = document.getElementById(spec.lng);
  if (!input || !lat || !lng) return;

  const limit = input.maxLength > 0 ? input.maxLength : 120;
  const label = form.querySelector(`label[for="${spec.text}"]`)?.textContent.trim() || 'Place';
  const element = new PlaceAutocompleteElement({ includedRegionCodes: ['bd'] });
  element.setAttribute('aria-label', label);
  element.classList.add('places');
  if (input.value && 'value' in element) element.value = input.value;

  const clearCoordinates = () => {
    lat.value = '';
    lng.value = '';
  };

  // Typing without picking a suggestion keeps the text and drops stale coordinates.
  element.addEventListener('input', () => {
    if (typeof element.value === 'string') input.value = element.value.slice(0, limit);
    clearCoordinates();
  });

  const onSelect = async (event) => {
    try {
      const place = event.placePrediction.toPlace();
      await place.fetchFields({ fields: ['displayName', 'formattedAddress', 'location'] });
      input.value = (place.displayName || place.formattedAddress || input.value).slice(0, limit);
      if (place.location) {
        lat.value = clamp(place.location.lat(), -90, 90).toFixed(6);
        lng.value = clamp(place.location.lng(), -180, 180).toFixed(6);
      }
    } catch {
      // The typed text is still in the field, so the form works without coordinates.
    }
  };
  element.addEventListener('gmp-select', onSelect);
  element.addEventListener('gmp-placeselect', onSelect);

  input.after(element);
  input.hidden = true;
}

export async function initMaps() {
  const form = document.querySelector('form[data-ride-form]');
  const key = form?.dataset.mapsKey?.trim();
  if (!form || !key) return;

  try {
    await loadScript(key);
    const { PlaceAutocompleteElement } = await window.google.maps.importLibrary('places');
    if (!PlaceAutocompleteElement) return;
    FIELDS.forEach((spec) => enhance(form, spec, PlaceAutocompleteElement));
  } catch {
    // Blocked, offline, or a bad key: the plain inputs and the area list stay in place.
  }
}
