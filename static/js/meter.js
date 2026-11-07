import { clamp, reducedMotion } from './env.js';
import { tick } from './sound.js';

const HOLD_MS = 1200;
const HASH = /^#split=(\d{1,4}):([1-7])$/;
const money = new Intl.NumberFormat('en-BD');

export function initMeter() {
  const root = document.querySelector('details[data-meter]');
  if (!root) return;
  const fixed = root.querySelector('[data-meter-static]');
  const live = root.querySelector('[data-meter-live]');
  const secret = root.querySelector('[data-meter-secret]');
  const fare = root.querySelector('#meter-fare');
  const seats = root.querySelector('#meter-seats');
  const out = root.querySelector('#meter-out');
  const summary = root.querySelector('summary');
  const peopleOut = root.querySelector('#meter-people');
  const pill = root.querySelector('[data-meter-pill]');
  const figures = root.querySelector('[data-meter-figures]');
  if (!fixed || !live || !secret || !fare || !seats || !out || !summary) return;

  fixed.hidden = true;
  live.hidden = false;

  const values = () => {
    const wholeFare = Number.parseInt(fare.value, 10);
    const people = Number.parseInt(seats.value, 10);
    return {
      fare: clamp(Number.isFinite(wholeFare) ? wholeFare : 0, 0, 5000),
      seats: clamp(Number.isFinite(people) ? people : 1, 1, 7),
    };
  };

  const splitLink = () => {
    const { fare: total, seats: people } = values();
    return `${window.location.origin}${window.location.pathname}${window.location.search}#split=${total}:${people}`;
  };

  const renderSecret = () => {
    const { fare: total, seats: people } = values();
    const link = document.createElement('a');
    link.href = splitLink();
    link.textContent = link.href;
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'btn btn--ghost btn--small';
    copy.textContent = 'Copy link';
    if (navigator.clipboard?.writeText) {
      copy.addEventListener('click', () => {
        navigator.clipboard.writeText(link.href).then(
          () => {
            copy.textContent = 'Copied';
          },
          () => {
            copy.textContent = 'Select the link and copy it';
          },
        );
      });
    } else {
      copy.hidden = true;
    }
    const lead = document.createElement('span');
    lead.textContent = `Tk ${money.format(total)} between ${people}. Send this split to the others: `;
    secret.replaceChildren(lead, link, document.createTextNode(' '), copy);
  };

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const person = () => {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 20 30');
    svg.setAttribute('class', 'meter__figure');
    svg.setAttribute('focusable', 'false');
    const head = document.createElementNS(SVG_NS, 'circle');
    head.setAttribute('cx', '10');
    head.setAttribute('cy', '7');
    head.setAttribute('r', '5.5');
    const body = document.createElementNS(SVG_NS, 'path');
    body.setAttribute('d', 'M1 29c0-9 4-14 9-14s9 5 9 14z');
    svg.append(head, body);
    svg.querySelectorAll('circle, path').forEach((node) => node.setAttribute('fill', 'currentColor'));
    return svg;
  };
  const showPeople = (people) => {
    const label = `${people} ${people === 1 ? 'person' : 'people'}`;
    if (peopleOut) peopleOut.textContent = label;
    if (pill) {
      pill.hidden = false;
      pill.textContent = label;
    }
    if (figures) {
      // Only add or drop the difference, so the new person pops in instead of the row redrawing.
      while (figures.childElementCount < people) figures.append(person());
      while (figures.childElementCount > people) figures.lastElementChild.remove();
    }
  };

  let lastSeats = values().seats;
  const update = () => {
    const { fare: total, seats: people } = values();
    out.textContent = `Tk ${money.format(Math.round(total / people))} each`;
    showPeople(people);
    if (!secret.hidden) renderSecret();
    if (people !== lastSeats) {
      lastSeats = people;
      tick(500 + people * 40, 40);
    }
  };
  fare.addEventListener('input', update);
  seats.addEventListener('input', update);

  const applyHash = () => {
    const match = HASH.exec(window.location.hash);
    if (!match) return;
    fare.value = match[1];
    seats.value = match[2];
    root.open = true;
    update();
    root.scrollIntoView({ block: 'center', behavior: reducedMotion.matches ? 'auto' : 'smooth' });
  };
  window.addEventListener('hashchange', applyHash);
  applyHash();
  update();

  // Hold the summary (pointer or Enter/Space) to open the split layer.
  let timer = 0;
  let held = false;
  const cancel = () => {
    window.clearTimeout(timer);
    timer = 0;
  };
  const begin = () => {
    cancel();
    timer = window.setTimeout(() => {
      held = true;
      root.open = true;
      secret.hidden = false;
      renderSecret();
      tick(880, 120);
    }, HOLD_MS);
  };

  summary.addEventListener('pointerdown', (event) => {
    if (event.button === 0) begin();
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach((name) => summary.addEventListener(name, cancel));
  summary.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    if (event.repeat) {
      // A held Enter would otherwise keep toggling the panel open and shut.
      event.preventDefault();
      return;
    }
    begin();
  });
  summary.addEventListener('keyup', cancel);
  summary.addEventListener('click', (event) => {
    if (held) {
      held = false;
      event.preventDefault();
    }
  });
}
