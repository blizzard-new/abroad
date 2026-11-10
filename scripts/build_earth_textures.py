"""Rebuild the Earth textures from the NASA Blue Marble equirectangular image (public domain).

    python scripts/build_earth_textures.py path/to/earth-blue-marble-4096x2048.jpg

Writes `earth-equirect.jpg` (the home hero) into src/exchange_info/static/assets/partner-map/, then update
manifest.json with its hash. (The explore page's globe is drawn from the country shapes, not from a photograph.)
"""
import sys
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "src/exchange_info/static/assets/partner-map"

if __name__ == "__main__":
    source = Image.open(sys.argv[1])
    source.convert("RGB").resize((2048, 1024), Image.LANCZOS).save(OUT / "earth-equirect.jpg", quality=80, optimize=True, progressive=True)
