"""Rebuild every UniWay brand image from the single source logo.

    python scripts/build_brand_assets.py

Reads ``static/assets/brand/uniway-logo.webp`` (the logo on a transparent background) and writes, next to it:

* ``uniway-mark.webp``   square, transparent, shown wherever the brand mark appears in the page;
* ``favicon.ico`` / ``favicon-16.png`` / ``favicon-32.png``   transparent tab icons, so they sit well on light and dark tab bars;
* ``apple-touch-icon.png``   180px square on white for iOS home screens (iOS does not accept transparency).

``uniway-logo-glow.webp`` is the earlier glowing-on-black version of the logo; it is kept for reference and is not used by the site.
Only Pillow is needed. The output is deterministic, so re-running it produces identical files.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

BRAND_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static" / "assets" / "brand"
SOURCE = BRAND_DIR / "uniway-logo.webp"


def mark_box(image: Image.Image, threshold: int = 8) -> tuple[int, int, int, int]:
    """Bounding box of everything visible; faint anti-aliasing below ``threshold`` is ignored."""
    box = image.getchannel("A").point(lambda value: 255 if value > threshold else 0).getbbox()
    if box is None:
        raise SystemExit("The source logo is fully transparent; there is nothing to crop around.")
    return box


def framed(image: Image.Image, box: tuple[int, int, int, int], margin: float) -> Image.Image:
    """The mark centred on a transparent square ``margin`` times its larger side (1.0 = touching the edges)."""
    mark = image.crop(box)
    side = round(max(mark.width, mark.height) * margin)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    return canvas


def resized(tile: Image.Image, size: int) -> Image.Image:
    return tile.resize((size, size), Image.Resampling.LANCZOS)  # Pillow resizes RGBA premultiplied, so edges stay clean


def on_white(tile: Image.Image) -> Image.Image:
    background = Image.new("RGBA", tile.size, (255, 255, 255, 255))
    background.alpha_composite(tile)
    return background.convert("RGB")


def main() -> None:
    logo = Image.open(SOURCE).convert("RGBA")
    box = mark_box(logo)

    mark = resized(framed(logo, box, 1.04), 160)
    mark.save(BRAND_DIR / "uniway-mark.webp", quality=92, alpha_quality=100, method=6)

    icon = framed(logo, box, 1.08)
    resized(icon, 16).save(BRAND_DIR / "favicon-16.png", optimize=True)
    resized(icon, 32).save(BRAND_DIR / "favicon-32.png", optimize=True)
    resized(icon, 256).save(BRAND_DIR / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    on_white(resized(framed(logo, box, 1.5), 180)).save(BRAND_DIR / "apple-touch-icon.png", optimize=True)

    for name in ("uniway-mark.webp", "favicon.ico", "favicon-16.png", "favicon-32.png", "apple-touch-icon.png"):
        print(f"{name:22} {(BRAND_DIR / name).stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
