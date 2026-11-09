"""Rebuild the Earth textures from the NASA Blue Marble equirectangular image (public domain).

    python scripts/build_earth_textures.py path/to/earth-blue-marble-4096x2048.jpg

Writes `earth-mercator.jpg` (web mercator, for the MapLibre globe) and `earth-equirect.jpg` (home hero) into
src/exchange_info/static/assets/partner-map/, then update manifest.json with their hashes.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "src/exchange_info/static/assets/partner-map"


def mercator(source: Image.Image, size: int = 3072) -> Image.Image:
    a = np.asarray(source.convert("RGB"), dtype=np.float32)
    h0, w0, _ = a.shape
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * (np.arange(size) + 0.5) / size))))
    lon = ((np.arange(size) + 0.5) / size) * 360 - 180
    v, u = (90 - lat) / 180 * h0 - 0.5, (lon + 180) / 360 * w0 - 0.5
    v0 = np.clip(np.floor(v).astype(int), 0, h0 - 2)
    u0 = np.clip(np.floor(u).astype(int), 0, w0 - 2)
    fv, fu = (v - v0)[:, None, None], (u - u0)[None, :, None]
    top = a[v0][:, u0] * (1 - fu) + a[v0][:, u0 + 1] * fu
    bottom = a[v0 + 1][:, u0] * (1 - fu) + a[v0 + 1][:, u0 + 1] * fu
    return Image.fromarray(np.clip(top * (1 - fv) + bottom * fv, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    source = Image.open(sys.argv[1])
    mercator(source).save(OUT / "earth-mercator.jpg", quality=78, optimize=True, progressive=True)
    source.convert("RGB").resize((2048, 1024), Image.LANCZOS).save(OUT / "earth-equirect.jpg", quality=80, optimize=True, progressive=True)
