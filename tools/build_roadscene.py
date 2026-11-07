#!/usr/bin/env python3
"""Build rides/templates/partials/roadscene.html: a looping street scene with a car, a CNG and a
rickshaw that replaces the old red right-to-left ticker.

Run from the project root:  python tools/build_roadscene.py
Colours live in static/css/main.css (the roadway block); this file only draws shapes.
"""
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HALF = 1920  # viewBox width of one repeat; two repeats make the loop

SIGNS = ["Women-only rides", "Verified Circles", "Guardian Mode", "Split the fare"]


def far_layer() -> str:
    """Skyline silhouettes with lit windows. Deterministic, and seamless at the edges."""
    rnd = random.Random(11)
    parts, x = [], 0
    while x < HALF:
        w = rnd.choice([58, 70, 84, 96, 110])
        w = min(w, HALF - x)
        h = rnd.choice([46, 62, 78, 96, 112])
        tone = rnd.choice(["b1", "b2", "b3"])
        y = 140 - h
        parts.append(f'<rect class="sky__b {tone}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
        if rnd.random() < 0.18:  # a water tank or mast on some roofs
            parts.append(f'<rect class="sky__b {tone}" x="{x + w / 2 - 4}" y="{y - 14}" width="8" height="14"/>')
        for wy in range(y + 10, 132, 16):
            for wx in range(x + 8, x + w - 8, 14):
                if rnd.random() < 0.36:
                    parts.append(f'<rect class="sky__win" x="{wx}" y="{wy}" width="5" height="7"/>')
        x += w + rnd.choice([0, 0, 6, 12])
    return f'<svg class="roadway__svg" viewBox="0 0 {HALF} 140" preserveAspectRatio="none" focusable="false">{"".join(parts)}</svg>'


def near_layer() -> str:
    """Trees, lamp posts and the roadside signs that carry the old ticker's words."""
    rnd = random.Random(5)
    parts = []
    x = 70
    sign_i = 0
    while x < HALF - 120:
        kind = rnd.choice(["tree", "tree", "lamp", "sign"])
        if kind == "sign" and sign_i < len(SIGNS) * 2:
            text = SIGNS[sign_i % len(SIGNS)]
            sign_i += 1
            parts.append(
                f'<g transform="translate({x} 0)"><rect class="near__post" x="58" y="56" width="5" height="64"/>'
                f'<rect class="near__sign" x="-14" y="26" width="150" height="34" rx="6"/>'
                f'<text class="near__text" x="61" y="48" text-anchor="middle">{text}</text></g>'
            )
            x += 330
        elif kind == "lamp":
            parts.append(
                f'<g transform="translate({x} 0)"><rect class="near__post" x="0" y="30" width="5" height="90"/>'
                f'<path class="near__post" d="M2 32 Q2 20 22 20 H34 V26 H22 Q9 26 9 36Z"/>'
                f'<circle class="near__lamp" cx="31" cy="30" r="5"/></g>'
            )
            x += 200
        else:
            r = rnd.choice([26, 32, 38])
            parts.append(
                f'<g transform="translate({x} 0)"><rect class="near__trunk" x="-3" y="{120 - r - 20}" width="7" height="{r + 20}"/>'
                f'<circle class="near__leaf" cx="0" cy="{110 - r - 8}" r="{r}"/>'
                f'<circle class="near__leaf near__leaf--lt" cx="{r // 2}" cy="{110 - r - 18}" r="{r * 0.6:.0f}"/></g>'
            )
            x += rnd.choice([150, 210, 260])
    return f'<svg class="roadway__svg" viewBox="0 0 {HALF} 120" preserveAspectRatio="none" focusable="false">{"".join(parts)}</svg>'


def wheel(cx, cy, r, extra=""):
    spokes = "".join(
        f'<line class="wheel__spoke" x1="0" y1="{-r + 4}" x2="0" y2="{r - 4}" transform="rotate({a})"/>'
        for a in (0, 45, 90, 135)
    )
    return (
        f'<g transform="translate({cx} {cy})"><g class="wheel{extra}">'
        f'<circle class="wheel__tire" r="{r}"/><circle class="wheel__rim" r="{r * 0.55:.1f}"/>{spokes}'
        f'<circle class="wheel__hub" r="2.6"/></g></g>'
    )


CAR = f"""
<svg class="rv rv--car" viewBox="0 0 220 90" focusable="false">
  <ellipse class="rv__shadow" cx="110" cy="85" rx="96" ry="5"/>
  <path class="rv__beam" d="M212 48 L292 30 V70 Z"/>
  <g class="rv__bob">
    <path class="car__body" d="M8 64 V50 Q8 42 18 40 L46 35 L64 16 Q68 12 74 12 H138 Q146 12 152 19 L168 36 L200 42 Q212 44 212 54 V64 Q212 68 207 68 H13 Q8 68 8 64Z"/>
    <path class="car__glass" d="M72 19 H132 Q137 19 141 24 L153 36 H58 L68 22 Q69.5 19 72 19Z"/>
    <path class="rv__cloth rv__cloth--a" d="M71 36 Q71 31 82 31 Q93 31 93 36Z"/><circle class="rv__skin rv__skin--a" cx="82" cy="27" r="6"/>
    <path class="rv__cloth rv__cloth--b" d="M105 36 Q105 31 115 31 Q125 31 125 36Z"/><circle class="rv__skin rv__skin--b" cx="115" cy="27" r="6"/>
    <path class="rv__cloth rv__cloth--c" d="M127 36 Q127 31 137 31 Q147 31 147 36Z"/><circle class="rv__skin rv__skin--c" cx="137" cy="27" r="6"/>
    <rect class="car__pillar" x="95" y="18" width="6" height="19"/>
    <rect class="car__stripe" x="14" y="50" width="192" height="3" rx="1.5"/>
    <text class="car__logo" x="104" y="62" text-anchor="middle">RideMate</text>
    <path class="car__arch" d="M37 68 A17 17 0 0 1 71 68Z"/><path class="car__arch" d="M149 68 A17 17 0 0 1 183 68Z"/>
    <rect class="car__light" x="204" y="46" width="8" height="6" rx="2"/>
    <rect class="car__tail" x="8" y="46" width="5" height="7" rx="2"/>
  </g>
  {wheel(54, 68, 15)}{wheel(166, 68, 15)}
</svg>"""

CNG = f"""
<svg class="rv rv--cng" viewBox="0 0 170 100" focusable="false">
  <ellipse class="rv__shadow" cx="85" cy="95" rx="72" ry="5"/>
  <path class="rv__beam" d="M158 56 L228 40 V80 Z"/>
  <g class="rv__bob">
    <path class="cng__roof" d="M24 40 Q24 14 52 12 H108 Q128 12 137 30 L144 42Z"/>
    <path class="cng__body" d="M16 46 H148 Q157 46 158 55 V76 H12 V54 Q12 46 16 46Z"/>
    <path class="cng__glass" d="M28 42 H126 V70 H28Z"/>
    <path class="rv__cloth rv__cloth--a" d="M46 70 Q46 58 58 58 Q70 58 70 70Z"/><circle class="rv__skin rv__skin--a" cx="58" cy="50" r="6"/>
    <path class="rv__cloth rv__cloth--b" d="M78 70 Q78 58 90 58 Q102 58 102 70Z"/><circle class="rv__skin rv__skin--b" cx="90" cy="50" r="6"/>
    <circle class="rv__skin rv__skin--c" cx="136" cy="38" r="6"/>
    <path class="cng__cage" d="M44 42V70M60 42V70M76 42V70M92 42V70M108 42V70"/>
    <rect class="cng__stripe" x="12" y="66" width="146" height="3"/>
    <rect class="cng__light" x="152" y="54" width="7" height="7" rx="2"/>
  </g>
  {wheel(44, 78, 13)}{wheel(138, 80, 11)}
</svg>"""

RICKSHAW = f"""
<svg class="rv rv--rick" viewBox="0 0 160 100" focusable="false">
  <ellipse class="rv__shadow" cx="80" cy="95" rx="66" ry="5"/>
  <g class="rv__bob">
    <path class="rk__hood" d="M18 56 Q16 18 50 18 Q76 20 82 54Z"/>
    <path class="rk__rib" d="M34 20 Q32 40 36 54M50 18 Q50 38 52 55M65 21 Q67 40 69 54"/>
    <path class="rv__cloth rv__cloth--a" d="M42 58 Q42 47 54 47 Q66 47 66 58Z"/><circle class="rv__skin rv__skin--a" cx="54" cy="40" r="6"/>
    <path class="rk__seat" d="M22 56 H86 V64 H22Z"/>
    <path class="rk__frame" d="M86 62 L104 62 L108 44 M104 62 L122 76 M44 62 L44 76"/>
    <circle class="rv__skin rv__skin--b" cx="104" cy="28" r="6"/>
    <path class="rk__rider" d="M104 35 L101 52 L112 66 M101 52 L96 60 M104 38 L120 46 L122 58"/>
  </g>
  {wheel(44, 78, 16)}{wheel(122, 78, 15)}
</svg>"""


def build() -> None:
    far, near = far_layer(), near_layer()
    html = f"""{{# Generated by tools/build_roadscene.py. Edit the script, not this file. #}}
<section class="roadway" aria-hidden="true">
  <svg class="roadway__defs" width="0" height="0" focusable="false">
    <defs><linearGradient id="rv-beam" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#FFE9A8" stop-opacity=".55"/><stop offset="1" stop-color="#FFE9A8" stop-opacity="0"/></linearGradient></defs>
  </svg>
  <div class="roadway__sun"></div>
  <div class="roadway__layer roadway__layer--far"><div class="roadway__track">{far}{far}</div></div>
  <div class="roadway__layer roadway__layer--near"><div class="roadway__track">{near}{near}</div></div>
  <div class="roadway__road"><div class="roadway__edge"></div><div class="roadway__lines"></div></div>
  <div class="roadway__vehicle roadway__vehicle--rick">{RICKSHAW}</div>
  <div class="roadway__vehicle roadway__vehicle--cng">{CNG}</div>
  <div class="roadway__vehicle roadway__vehicle--car">{CAR}</div>
</section>
"""
    (ROOT / "rides/templates/partials/roadscene.html").write_text(html)
    print("roadscene.html written", len(html), "bytes")


if __name__ == "__main__":
    build()
