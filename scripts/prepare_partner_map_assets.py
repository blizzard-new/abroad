"""Fetch pinned public map assets. Run only when intentionally updating vendors."""
from pathlib import Path
import hashlib
import io
import json
import tarfile
import argparse

import requests

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/exchange_info/static"


def download(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def compact_coordinates(value):
    if isinstance(value, list):
        return [compact_coordinates(part) for part in value]
    return round(value, 4) if isinstance(value, float) else value


def prepare_basemap(assets):
    base = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/"
    for filename, source in [
        ("countries", "ne_50m_admin_0_countries"),
        ("lakes", "ne_50m_lakes"),
        ("rivers", "ne_50m_rivers_lake_centerlines"),
    ]:
        collection = json.loads(download(base + source + ".geojson"))
        features = []
        for feature in collection["features"]:
            p = feature["properties"]
            # Keep the major waterways; smaller tributaries would obscure school points.
            if filename != "countries" and p.get("scalerank", 0) > 4:
                continue
            properties = {"name": p.get("NAME_EN") or p.get("name_en") or p.get("name") or ""}
            if filename == "countries":
                properties.update(label_lon=p["LABEL_X"], label_lat=p["LABEL_Y"], continent=p["CONTINENT"], tone=p["MAPCOLOR7"])
            geometry = feature["geometry"]
            geometry["coordinates"] = compact_coordinates(geometry["coordinates"])
            features.append({"type": "Feature", "properties": properties, "geometry": geometry})
        (assets / (filename + ".geojson")).write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basemap-only", action="store_true")
    args = parser.parse_args()
    vendor = STATIC / "vendor/maplibre/5.24.0"
    vendor.mkdir(parents=True, exist_ok=True)
    if not args.basemap_only:
        archive = tarfile.open(fileobj=io.BytesIO(download("https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-5.24.0.tgz")))
        for source, target in [("dist/maplibre-gl-csp.js", "maplibre-gl-csp.js"), ("dist/maplibre-gl-csp-worker.js", "maplibre-gl-csp-worker.js"), ("dist/maplibre-gl.css", "maplibre-gl.css"), ("LICENSE.txt", "LICENSE.txt")]:
            (vendor / target).write_bytes(archive.extractfile("package/" + source).read())
    assets = STATIC / "assets/partner-map"
    assets.mkdir(parents=True, exist_ok=True)
    prepare_basemap(assets)
    font = assets / "fonts/Open Sans Semibold"
    font.mkdir(parents=True, exist_ok=True)
    if not args.basemap_only:
        (font / "0-255.pbf").write_bytes(download("https://demotiles.maplibre.org/font/Open%20Sans%20Semibold/0-255.pbf"))
        (font / "LICENSE.txt").write_bytes(download("https://raw.githubusercontent.com/googlefonts/opensans/main/OFL.txt"))
    files = list(vendor.iterdir()) + list(assets.rglob("*"))
    manifest = {str(p.relative_to(STATIC)).replace('\\', '/'): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p.is_file() and p.name != "manifest.json"}
    (assets / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
