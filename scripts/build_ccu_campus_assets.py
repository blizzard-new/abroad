"""Build CCU-only assets after explicit identity, licence and visual decisions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
STATIC = ROOT / "src/exchange_info/static/assets/ccu/campuses"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    candidates = json.loads((BUNDLE / "campus-assets-candidates.json").read_text())["schools"]
    review = json.loads((BUNDLE / "campus-photo-review.json").read_text())["selected"]
    location_review_path = BUNDLE / "campus-coordinate-review.json"
    location_review = json.loads(location_review_path.read_text())["schools"] if location_review_path.exists() else {}
    final = []
    for original in candidates:
        row = {key: original[key] for key in ["ccu_page", "school_name", "country", "mother_identity_source_url", "source_pages"]}
        page = str(row["ccu_page"])
        row["coordinates"] = original["coordinates"]
        point = location_review.get(page)
        if point and point["decision"] == "accepted":
            row["coordinates"] = point["field"]
        selected = review.get(page)
        if not selected or selected.get("decision") != "accepted":
            row["photo"] = {"status": "missing", "value": None, "reason": (selected or {}).get("reason") or original["photo"]["reason"], "evidence": original["photo"].get("evidence", [])}
            final.append(row)
            continue
        photo = json.loads((BUNDLE / selected["reviewed_photo_record"]).read_text())
        required = ["artist", "license_name", "license_url", "source_page_url", "image_source_url", "campus_caption", "checked_at"]
        if not all(photo.get(key) for key in required):
            raise ValueError(f"Incomplete attribution / campus identity: p{page}")
        raw = BUNDLE / photo["candidate_file"]
        if sha(raw) != photo["sha256"]:
            raise ValueError(f"Image changed after visual review: p{page}")
        with Image.open(raw) as image:
            image.verify()
        with Image.open(raw) as image:
            image_format, width, height = image.format, image.width, image.height
        suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(image_format)
        if not suffix:
            raise ValueError(f"Unsupported photograph format: p{page}")
        STATIC.mkdir(parents=True, exist_ok=True)
        filename = f"p{page}-{photo['sha256'][:12]}{suffix}"
        destination = STATIC / filename
        shutil.copyfile(raw, destination)
        row["photo"] = {
            "status": "verified_current", "value": {
                **{key: photo[key] for key in required},
                "local_path": "/static/assets/ccu/campuses/" + filename,
                "sha256": sha(destination), "width": width, "height": height,
                "modifications": "原樣保存Commons所提供影像；Commons縮圖尺寸依來源URL，不另裁切或用AI修改。",
                "applicability": "真實校園照片；攝影時間依原頁，查核日不是拍攝日，不保證2027校園外觀或個人分配校區。",
            },
            "reason": selected["identity_note"], "evidence": photo["evidence"],
        }
        final.append(row)
    result = {
        "checked_at": "2026-10-11", "scope": "CCU exchange-list identities; general campus assets, not incoming eligibility",
        "schools": final,
    }
    (BUNDLE / "campus-assets.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("photographs", sum(row["photo"]["status"] == "verified_current" for row in final), "/", len(final))
    print("coordinates", sum(row["coordinates"]["status"] == "verified_current" for row in final), "/", len(final))


if __name__ == "__main__":
    main()
