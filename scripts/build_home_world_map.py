"""Build the static world outline used by the home page map preview.

The home page shows a non-interactive map of the partner network. Loading the
1.9 MB country file and the MapLibre engine just to draw a thumbnail would slow
the first screen, so this script flattens the same Natural Earth country shapes
(assets/partner-map/countries.geojson) into one small SVG path in a Natural
Earth projection centred on 20°E. The browser projects partner coordinates with
the same formula (static/platform-home.js) and draws them over the outline.

    python scripts/build_home_world_map.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"
SOURCE = STATIC / "assets" / "partner-map" / "countries.geojson"
TARGET = STATIC / "assets" / "home" / "world-land.json"

CENTER = 20.0  # central meridian: Europe and Asia in the middle, the Pacific cut at 160°W
WIDTH = 1000.0
TOP_LAT, BOTTOM_LAT = 83.0, -57.0
SIMPLIFY_DEGREES = 0.28
MIN_AREA = 0.9  # square degrees; smaller islands are dropped, except the always-kept names
ALWAYS_KEEP = {"Taiwan", "Japan", "Singapore", "Hong Kong", "Macao", "South Korea"}


def natural_earth(lon_deg: float, lat_deg: float) -> tuple[float, float]:
    """d3.geoNaturalEarth1 (Šavrič et al. 2015) in unscaled units."""
    lam, phi = math.radians(lon_deg), math.radians(lat_deg)
    p2 = phi * phi
    p4 = p2 * p2
    x = lam * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y


def unwrap(ring: list[list[float]]) -> list[tuple[float, float]]:
    """Make longitudes continuous so a ring crossing the cut meridian is one run."""
    out: list[tuple[float, float]] = []
    previous = None
    for lon, lat in ring:
        lon = ((lon - CENTER + 540) % 360) - 180
        if previous is not None:
            while lon - previous > 180:
                lon -= 360
            while lon - previous < -180:
                lon += 360
        out.append((lon, lat))
        previous = lon
    return out


def clip_x(points: list[tuple[float, float]], bound: float, keep_greater: bool) -> list[tuple[float, float]]:
    """Sutherland–Hodgman against the vertical line x = bound."""
    inside = (lambda p: p[0] >= bound) if keep_greater else (lambda p: p[0] <= bound)
    result: list[tuple[float, float]] = []
    for index, current in enumerate(points):
        previous = points[index - 1]
        if inside(current) != inside(previous):
            t = (bound - previous[0]) / (current[0] - previous[0])
            result.append((bound, previous[1] + t * (current[1] - previous[1])))
        if inside(current):
            result.append(current)
    return result


def douglas_peucker(points: list[tuple[float, float]], epsilon: float) -> list[tuple[float, float]]:
    if len(points) < 4:
        return points
    first, last = points[0], points[-1]
    dx, dy = last[0] - first[0], last[1] - first[1]
    length = math.hypot(dx, dy)
    index, worst = 0, 0.0
    for i in range(1, len(points) - 1):
        px, py = points[i][0] - first[0], points[i][1] - first[1]
        distance = math.hypot(px, py) if length == 0 else abs(px * dy - py * dx) / length
        if distance > worst:
            index, worst = i, distance
    if worst <= epsilon:
        return [first, last]
    return douglas_peucker(points[: index + 1], epsilon)[:-1] + douglas_peucker(points[index:], epsilon)


def area(points: list[tuple[float, float]]) -> float:
    return abs(sum(points[i - 1][0] * points[i][1] - points[i][0] * points[i - 1][1] for i in range(len(points)))) / 2


def rings_for(feature: dict) -> list[list[tuple[float, float]]]:
    geometry = feature["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    name = feature["properties"]["name"]
    result = []
    for polygon in polygons:
        ring = unwrap(polygon[0])  # holes (inland seas) are not needed at thumbnail size
        pieces = [ring]
        # A ring that leaves [-180, 180] is cut there and the overflow reappears on the other side.
        for shift in (-360, 360):
            moved = [(x + shift, y) for x, y in ring]
            if any(-180 <= x <= 180 for x, _ in moved):
                pieces.append(moved)
        for piece in pieces:
            clipped = clip_x(clip_x(piece, -180.0, True), 180.0, False)
            if len(clipped) < 3:
                continue
            if area(clipped) < MIN_AREA and name not in ALWAYS_KEEP:
                continue
            simple = douglas_peucker(clipped + [clipped[0]], SIMPLIFY_DEGREES)[:-1]
            if len(simple) >= 3:
                result.append(simple)
    return result


def main() -> None:
    features = json.loads(SOURCE.read_text(encoding="utf-8"))["features"]
    x_edge, _ = natural_earth(180.0, 0.0)
    scale = WIDTH / (2 * x_edge)
    _, y_top = natural_earth(0.0, TOP_LAT)
    _, y_bottom = natural_earth(0.0, BOTTOM_LAT)
    height = (y_top - y_bottom) * scale

    def path_for(rings: list[list[tuple[float, float]]]) -> str:
        parts = []
        for ring in rings:
            projected = []
            for lon, lat in ring:
                x, y = natural_earth(lon, lat)
                projected.append((WIDTH / 2 + x * scale, (y_top - y) * scale))
            parts.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in projected) + "Z")
        return "".join(parts)

    land, taiwan = [], []
    for feature in features:
        name = feature["properties"]["name"]
        if name == "Antarctica":
            continue
        (taiwan if name == "Taiwan" else land).extend(rings_for(feature))

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(
            {
                "projection": "naturalEarth1",
                "center": CENTER,
                "width": WIDTH,
                "height": round(height, 1),
                "scale": round(scale, 4),
                "top": round(y_top * scale, 4),
                "land": path_for(land),
                "taiwan": path_for(taiwan),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {TARGET.relative_to(STATIC.parents[2])} ({TARGET.stat().st_size / 1024:.1f} KB), viewBox 0 0 {WIDTH:.0f} {height:.0f}")


if __name__ == "__main__":
    main()
