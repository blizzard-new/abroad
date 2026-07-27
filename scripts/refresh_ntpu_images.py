from __future__ import annotations

from collections import Counter

from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
from exchange_info.partner_research import apply_partner_research
from exchange_info.school_image_collector import (
    DEFAULT_IMAGE_MANIFEST,
    DEFAULT_IMAGE_OUTPUT_DIR,
    collect_school_images,
)
from exchange_info.storage import load_partner_research


NTPU_NAME = "國立臺北大學"


def main() -> int:
    partners = apply_partner_research(
        fetch_ntpu_partner_universities(),
        load_partner_research(),
        home_university=NTPU_NAME,
    )
    rows = collect_school_images(
        output_dir=DEFAULT_IMAGE_OUTPUT_DIR,
        manifest_path=DEFAULT_IMAGE_MANIFEST,
        timeout_seconds=15.0,
        delay_seconds=0.0,
        missing_only=True,
        refresh_overrides=False,
        partners=partners,
        workers=3,
    )
    counts = Counter(row.status for row in rows)
    print(f"Checked {len(rows)} NTPU partner-school images: {dict(counts)}")
    print(DEFAULT_IMAGE_MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
