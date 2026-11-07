#!/usr/bin/env python3
"""Build the hero map partial and its pin CSS from real latitude/longitude.

Run from the project root:  python tools/build_maps.py

Writes
  rides/templates/partials/routemap.html   the two map views (Inside Dhaka, Across Bangladesh)
  static/css/mapdata.css             pin positions (the CSP blocks inline style attributes)

Everything is projected with the same equirectangular formula, scaled by cos(latitude),
so distances between places keep their real proportions.

The Bangladesh outline below is a hand-traced border (about 100 points). To use an
official outline instead, put a GeoJSON polygon in tools/bangladesh.geojson
(Natural Earth "admin_0_countries" works) and re-run: it is picked up automatically.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 640, 800  # shared viewBox, so both views fit the same frame
PAD = 34

# --------------------------------------------------------------------------- geometry


class Frame:
    """Equirectangular projection of a lat/lon box into the W x H viewBox."""

    def __init__(self, lat0, lat1, lon0, lon1):
        self.lat0, self.lat1, self.lon0, self.lon1 = lat0, lat1, lon0, lon1
        k = math.cos(math.radians((lat0 + lat1) / 2))
        self.k = k
        span_x = (lon1 - lon0) * k
        span_y = lat1 - lat0
        self.scale = min((W - 2 * PAD) / span_x, (H - 2 * PAD) / span_y)
        self.ox = (W - span_x * self.scale) / 2
        self.oy = (H - span_y * self.scale) / 2

    def xy(self, lat, lon):
        x = self.ox + (lon - self.lon0) * self.k * self.scale
        y = self.oy + (self.lat1 - lat) * self.scale
        return round(x, 1), round(y, 1)

    def pct(self, lat, lon):
        x, y = self.xy(lat, lon)
        return round(x / W * 100, 1), round(y / H * 100, 1)


def smooth(points, tension=0.5):
    """Catmull-Rom through the points, written as cubic Beziers."""
    if len(points) < 3:
        return "M" + "L".join(f"{x} {y}" for x, y in points)
    d = [f"M{points[0][0]} {points[0][1]}"]
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3 * 2 / 2, p1[1] + (p2[1] - p0[1]) * tension / 3 * 2 / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3 * 2 / 2, p2[1] - (p3[1] - p1[1]) * tension / 3 * 2 / 2)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]} {p2[1]}")
    return "".join(d)


def polygon(points):
    return "M" + "L".join(f"{x} {y}" for x, y in points) + "Z"


# --------------------------------------------------------------------------- Bangladesh

# (lat, lon), clockwise from the north-west corner.
BORDER = [
    (26.32, 88.10), (26.55, 88.22), (26.63, 88.45), (26.46, 88.65), (26.30, 88.72),
    (26.28, 88.92), (26.38, 89.03), (26.27, 89.20), (26.15, 89.45), (26.12, 89.70),
    (25.95, 89.82), (25.80, 89.78), (25.60, 89.85), (25.35, 89.87), (25.20, 90.05),
    (25.18, 90.35), (25.20, 90.65), (25.15, 90.95), (25.20, 91.25), (25.20, 91.55),
    (25.17, 91.85), (25.12, 92.05), (24.95, 92.15), (24.85, 92.30), (24.60, 92.22),
    (24.35, 92.20), (24.20, 92.00), (24.05, 91.82), (24.00, 91.55), (23.85, 91.25),
    (23.60, 91.20), (23.40, 91.28), (23.25, 91.40), (23.05, 91.47), (22.95, 91.65),
    (23.15, 91.92), (23.45, 91.95), (23.30, 92.25), (22.95, 92.40), (22.65, 92.50),
    (22.30, 92.58), (21.98, 92.68), (21.70, 92.58), (21.40, 92.42), (21.10, 92.30),
    (20.88, 92.25), (20.59, 92.32), (20.74, 92.28), (20.95, 92.18), (21.10, 92.08),
    (21.25, 92.02), (21.43, 91.97), (21.65, 91.95), (21.80, 91.90), (22.05, 91.85),
    (22.20, 91.80), (22.33, 91.79), (22.50, 91.72), (22.70, 91.60), (22.85, 91.45),
    (22.80, 91.20), (22.65, 91.00), (22.45, 90.85), (22.15, 90.75), (22.00, 90.50),
    (21.95, 90.30), (21.80, 90.12), (21.78, 89.90), (21.75, 89.65), (21.72, 89.40),
    (21.68, 89.15), (21.85, 89.05), (22.15, 88.95), (22.40, 88.92), (22.65, 88.95),
    (23.04, 88.89), (23.30, 88.72), (23.55, 88.65), (23.85, 88.68), (24.00, 88.80),
    (24.20, 88.66), (24.31, 88.57), (24.42, 88.36), (24.56, 88.18), (24.68, 88.03), (24.78, 88.02), (25.00, 88.15),
    (25.20, 88.38), (25.45, 88.40), (25.70, 88.45), (26.00, 88.20),
]

COUNTRY_PLACES = [
    # key, label, lat, lon, label side
    ("dhaka", "Dhaka", 23.8103, 90.4125, "right"),
    ("ctg", "Chattogram", 22.3569, 91.7832, "right"),
    ("sylhet", "Sylhet", 24.8949, 91.8687, "right"),
    ("rajshahi", "Rajshahi", 24.3745, 88.6042, "right"),
    ("khulna", "Khulna", 22.8456, 89.5403, "left"),
    ("rangpur", "Rangpur", 25.7439, 89.2752, "right"),
    ("barishal", "Barishal", 22.7010, 90.3535, "right"),
    ("cox", "Cox's Bazar", 21.4272, 91.9806, "left"),
    ("mymensingh", "Mymensingh", 24.7471, 90.4203, "right"),
]
COUNTRY_ROUTES = [
    # id, from, to, vehicle, speed, offset, via (lat, lon) list
    ("c-ctg", "dhaka", "ctg", "car", 0.045, 0.10, [(23.52, 91.10)]),
    ("c-syl", "dhaka", "sylhet", "car", 0.035, 0.45, [(24.25, 91.15)]),
    ("c-raj", "dhaka", "rajshahi", "bike", 0.040, 0.70, [(24.05, 89.55)]),
    ("c-khl", "dhaka", "khulna", "cng", 0.050, 0.25, [(23.25, 89.95)]),
    ("c-rng", "dhaka", "rangpur", "car", 0.038, 0.55, [(24.85, 89.85)]),
    ("c-cox", "ctg", "cox", "cng", 0.060, 0.35, []),
    ("c-brs", "dhaka", "barishal", "rickshaw", 0.070, 0.80, []),
    ("c-mym", "dhaka", "mymensingh", "bike", 0.080, 0.30, []),
]


def load_border():
    geo = ROOT / "tools" / "bangladesh.geojson"
    if not geo.exists():
        return BORDER
    data = json.loads(geo.read_text())
    feat = data["features"][0]["geometry"] if "features" in data else data
    ring = feat["coordinates"][0] if feat["type"] == "Polygon" else max(
        (poly[0] for poly in feat["coordinates"]), key=len)
    return [(lat, lon) for lon, lat in ring]


# --------------------------------------------------------------------------- Dhaka city

CITY_PLACES = [
    ("uttara", "Uttara", 23.8700, 90.3900, "left"),
    ("airport", "Airport", 23.8470, 90.4010, "right"),
    ("mirpur", "Mirpur 10", 23.8069, 90.3687, "left"),
    ("gabtoli", "Gabtoli", 23.7786, 90.3445, "right"),
    ("banani", "Banani", 23.7937, 90.4066, "left"),
    ("gulshan", "Gulshan", 23.7925, 90.4143, "right"),
    ("bashundhara", "Bashundhara", 23.8193, 90.4526, "left"),
    ("farmgate", "Farmgate", 23.7580, 90.3890, "right"),
    ("dhanmondi", "Dhanmondi", 23.7461, 90.3742, "left"),
    ("motijheel", "Motijheel", 23.7330, 90.4172, "right"),
    ("sadarghat", "Old Dhaka", 23.7090, 90.4070, "left"),
    ("jatrabari", "Jatrabari", 23.7096, 90.4337, "right"),
]
# Rivers that frame the city: Turag and Buriganga on the west and south, Balu on the east.
TURAG_BURIGANGA = [
    (23.890, 90.395), (23.860, 90.365), (23.830, 90.345), (23.800, 90.335), (23.775, 90.331),
    (23.750, 90.334), (23.730, 90.346), (23.715, 90.372), (23.706, 90.405), (23.701, 90.440),
    (23.704, 90.466),
]
BALU = [
    (23.886, 90.455), (23.850, 90.465), (23.810, 90.468), (23.770, 90.462), (23.730, 90.466),
    (23.704, 90.466),
]
CITY_ROUTES = [
    ("d-mirpur", "Mirpur 10 to Motijheel", "cng", 0.060, 0.10, [
        (23.8069, 90.3687), (23.7960, 90.3728), (23.7777, 90.3797), (23.7580, 90.3890),
        (23.7510, 90.3930), (23.7389, 90.3957), (23.7335, 90.4115), (23.7330, 90.4172)]),
    ("d-airport", "Uttara to Dhanmondi", "bike", 0.050, 0.55, [
        (23.8700, 90.3900), (23.8470, 90.4010), (23.8190, 90.3985), (23.7955, 90.4005),
        (23.7787, 90.4005), (23.7640, 90.3940), (23.7580, 90.3890), (23.7530, 90.3830),
        (23.7461, 90.3742)]),
    ("d-gulshan", "Gulshan to Bashundhara", "car", 0.055, 0.30, [
        (23.7925, 90.4143), (23.7975, 90.4240), (23.8060, 90.4380), (23.8193, 90.4526)]),
    ("d-gabtoli", "Gabtoli to Old Dhaka", "rickshaw", 0.070, 0.75, [
        (23.7786, 90.3445), (23.7650, 90.3600), (23.7610, 90.3735), (23.7390, 90.3830),
        (23.7240, 90.4130), (23.7090, 90.4070)]),
    ("d-mirpur12", "Mirpur 12 to Gulshan", "car", 0.045, 0.90, [
        (23.8280, 90.3640), (23.8185, 90.3745), (23.8080, 90.3880), (23.7937, 90.4066),
        (23.7925, 90.4143)]),
    ("d-jatra", "Jatrabari to Motijheel", "cng", 0.090, 0.40, [
        (23.7096, 90.4337), (23.7160, 90.4250), (23.7330, 90.4172)]),
]


# --------------------------------------------------------------------------- output


def vehicle(route_id, kind, speed, offset, scale):
    return (
        f'<g class="vehicle" data-track="{route_id}" data-speed="{speed}" data-offset="{offset}" '
        f'data-scale="{scale}" data-anchor="center" data-rotate="0">'
        f'{{% include "partials/marker.html" with kind="{kind}" %}}</g>'
    )


def build():
    # ---- Bangladesh
    border = load_border()
    lats = [p[0] for p in border]
    lons = [p[1] for p in border]
    cf = Frame(min(lats), max(lats), min(lons), max(lons))
    land = polygon([cf.xy(la, lo) for la, lo in border])
    places = {k: (la, lo) for k, _, la, lo, _ in COUNTRY_PLACES}

    country_paths, country_vehicles = [], []
    for rid, a, b, kind, speed, offset, via in COUNTRY_ROUTES:
        pts = [cf.xy(*places[a]), *[cf.xy(*v) for v in via], cf.xy(*places[b])]
        cls = "map__route map__route--main" if rid == "c-ctg" else "map__route"
        country_paths.append(f'<path class="{cls}" id="{rid}" d="{smooth(pts)}"/>')
        country_vehicles.append(vehicle(rid, kind, speed, offset, 0.9))
    country_dots = "".join(
        f'<circle class="map__city{" map__city--hub" if k == "dhaka" else ""}" '
        f'cx="{cf.xy(la, lo)[0]}" cy="{cf.xy(la, lo)[1]}" r="{9 if k == "dhaka" else 5.5}"/>'
        for k, _, la, lo, _ in COUNTRY_PLACES
    )

    # ---- Dhaka
    city = Frame(23.695, 23.885, 90.325, 90.470)
    river_w = [city.xy(*p) for p in TURAG_BURIGANGA]
    river_e = [city.xy(*p) for p in BALU]
    city_land = polygon(river_w + list(reversed(river_e)))
    cplaces = {k: (la, lo) for k, _, la, lo, _ in CITY_PLACES}

    city_paths, city_vehicles = [], []
    for rid, _title, kind, speed, offset, via in CITY_ROUTES:
        pts = [city.xy(*p) for p in via]
        city_paths.append(f'<path class="map__route map__route--city" id="{rid}" d="{smooth(pts)}"/>')
        city_vehicles.append(vehicle(rid, kind, speed, offset, 0.62))
    city_dots = "".join(
        f'<circle class="map__city map__city--small" cx="{city.xy(la, lo)[0]}" '
        f'cy="{city.xy(la, lo)[1]}" r="4.5"/>'
        for _, _, la, lo, _ in CITY_PLACES
    )
    river_paths = (
        f'<path class="map__river" d="{smooth(river_w)}"/>'
        f'<path class="map__river" d="{smooth(river_e)}"/>'
    )

    def pins(items, frame, prefix):
        out, css = [], []
        for key, label, la, lo, side in items:
            x, y = frame.pct(la, lo)
            name = f"pin--{prefix}-{key}"
            extra = " pin--left" if side == "left" else ""
            hub = " pin--dhaka" if (prefix == "c" and key == "dhaka") else ""
            out.append(f'<li class="pin {name}{extra}{hub}">{label}</li>')
            css.append(f".{name} {{ left: {x}%; top: {y}%; }}")
        return "\n    ".join(out), css

    country_pins, css_c = pins(COUNTRY_PLACES, cf, "c")
    city_pins, css_d = pins(CITY_PLACES, city, "d")

    html = f"""{{# Generated by tools/build_maps.py. Edit the script, not this file. #}}
<div class="mapbox" data-mapview>
  <div class="mapbox__tabs" role="group" aria-label="Map view">
    <button class="mapbox__tab is-active" type="button" aria-pressed="true" data-view-tab="city">Inside Dhaka</button>
    <button class="mapbox__tab" type="button" aria-pressed="false" data-view-tab="country">Across Bangladesh</button>
  </div>
  <div class="map" aria-hidden="true">
    <div class="map__view is-active" data-view="city" data-lane="time">
      <svg class="map__svg" viewBox="0 0 {W} {H}" focusable="false">
        <path class="map__land map__land--city" d="{city_land}"/>
        {river_paths}
        {"".join(city_paths)}
        {city_dots}
        {"".join(city_vehicles)}
      </svg>
      <ul class="map__pins">
    {city_pins}
      </ul>
    </div>
    <div class="map__view" data-view="country" data-lane="time">
      <svg class="map__svg" viewBox="0 0 {W} {H}" focusable="false">
        <path class="map__land" d="{land}"/>
        {"".join(country_paths)}
        {country_dots}
        {"".join(country_vehicles)}
      </svg>
      <ul class="map__pins">
    {country_pins}
      </ul>
    </div>
  </div>
  <p class="mapbox__caption">Most shared rides happen inside one city. Longer trips fill the empty seats of a car already going that way.</p>
</div>
"""
    (ROOT / "rides/templates/partials/routemap.html").write_text(html)
    css = "/* Generated by tools/build_maps.py */\n" + "\n".join(css_c + css_d) + "\n"
    (ROOT / "static/css/mapdata.css").write_text(css)
    print("routemap.html and mapdata.css written;", len(border), "border points")


if __name__ == "__main__":
    build()
