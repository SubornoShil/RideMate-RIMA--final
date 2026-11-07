import { clamp, reducedMotion } from './env.js';

// Vehicles ride along SVG paths. "time" lanes loop on their own; "scroll" lanes follow the page.

function collect(root) {
  const svg = root.querySelector('svg');
  if (!svg) return [];
  return [...root.querySelectorAll('.vehicle')]
    .map((node) => {
      const path = svg.querySelector(`#${CSS.escape(node.dataset.track || '')}`);
      if (!path || typeof path.getTotalLength !== 'function') return null;
      return {
        node,
        path,
        length: path.getTotalLength(),
        speed: Number.parseFloat(node.dataset.speed) || 0.05,
        offset: Number.parseFloat(node.dataset.offset) || 0,
        scale: Number.parseFloat(node.dataset.scale) || 1,
        centered: node.dataset.anchor === 'center',
        lean: node.dataset.rotate === '0' ? 0 : 0.35,
      };
    })
    .filter(Boolean);
}

function place(rider, progress, seconds) {
  const { path, length, node, scale, centered, lean } = rider;
  const at = progress * length;
  const here = path.getPointAtLength(at);
  const behind = path.getPointAtLength(Math.max(0, at - 5));
  const ahead = path.getPointAtLength(Math.min(length, at + 5));
  // Lean into the road, but less than the road leans: a CNG does not nose-dive.
  const tilt = Math.atan2(ahead.y - behind.y, ahead.x - behind.x) * (180 / Math.PI) * lean;
  const bump = reducedMotion.matches || centered ? 0 : Math.sin(seconds * 11 + rider.offset * 30) * 1.1;
  node.setAttribute(
    'transform',
    `translate(${here.x.toFixed(1)} ${(here.y + bump).toFixed(1)}) rotate(${tilt.toFixed(1)}) scale(${scale})${centered ? '' : ' translate(-60 -77)'}`,
  );
  const fade = clamp(Math.min(progress, 1 - progress) / 0.06, 0, 1);
  node.setAttribute('opacity', fade.toFixed(2));
}

export function initLanes() {
  const roots = [...document.querySelectorAll('[data-lane]')];
  if (!roots.length) return;

  const lanes = roots.map((root) => ({
    root,
    mode: root.dataset.lane === 'scroll' ? 'scroll' : 'time',
    riders: collect(root),
    visible: false,
  })).filter((lane) => lane.riders.length);

  const scrollProgress = (root) => {
    const box = root.getBoundingClientRect();
    const view = window.innerHeight;
    return clamp((view - box.top) / (view + box.height), 0, 1);
  };

  const paintStill = () => {
    for (const lane of lanes) {
      for (const rider of lane.riders) {
        const progress = lane.mode === 'scroll' ? 0.12 + scrollProgress(lane.root) * 0.76 : 0.3 + rider.offset * 0.5;
        place(rider, progress, 0);
      }
    }
  };

  const paintScroll = () => {
    for (const lane of lanes) {
      if (lane.mode !== 'scroll' || !lane.visible) continue;
      const progress = 0.06 + scrollProgress(lane.root) * 0.88;
      lane.riders.forEach((rider) => place(rider, progress, 0));
    }
  };

  paintStill();
  if (reducedMotion.matches || !('IntersectionObserver' in window)) return;

  let frame = 0;
  let scrollQueued = false;
  const anyTimeLane = () => lanes.some((lane) => lane.mode === 'time' && lane.visible);

  const loop = (now) => {
    const seconds = now / 1000;
    for (const lane of lanes) {
      if (lane.mode !== 'time' || !lane.visible) continue;
      for (const rider of lane.riders) {
        place(rider, (seconds * rider.speed + rider.offset) % 1, seconds);
      }
    }
    frame = anyTimeLane() && !document.hidden ? requestAnimationFrame(loop) : 0;
  };
  const wake = () => {
    if (!frame && anyTimeLane() && !document.hidden) frame = requestAnimationFrame(loop);
  };

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const lane = lanes.find((item) => item.root === entry.target);
      if (lane) lane.visible = entry.isIntersecting;
    }
    paintScroll();
    wake();
  });
  lanes.forEach((lane) => observer.observe(lane.root));

  window.addEventListener(
    'scroll',
    () => {
      if (scrollQueued) return;
      scrollQueued = true;
      requestAnimationFrame(() => {
        scrollQueued = false;
        paintScroll();
      });
    },
    { passive: true },
  );
  document.addEventListener('visibilitychange', wake);
  reducedMotion.addEventListener('change', () => window.location.reload());
}
