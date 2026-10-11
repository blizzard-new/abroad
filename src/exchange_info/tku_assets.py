"""Reviewed TKU assets only; no substitution from another home's catalogue."""
from __future__ import annotations

import json
from functools import lru_cache

from .tku_census import school_audit
from .tku_data import BUNDLE
from .university_locations import UniversityLocation


@lru_cache(maxsize=1)
def campus_photos():
    return {r["id"]:r for r in json.loads((BUNDLE/"campus_asset_manifest.json").read_text())
            if r.get("review_status")=="verified_asset" and r.get("local_path")}


@lru_cache(maxsize=1)
def campus_locations():
    return {r["id"]:r for r in json.loads((BUNDLE/"campus_location_manifest.json").read_text())}


def photo_modification_note(photo):
    return "沿用既有16:9裁切照片，本次未修改" if photo.get('acquisition_status')=='reused_baseline_asset' else "本次未另行修改照片"


def attach_images(dashboard,base_url):
    partners=[]
    for partner in dashboard.partner_universities:
        row=school_audit(partner.school_name)
        photo=campus_photos().get(row["id"]) if row else None
        updates=dict(image_url=None,image_source_url=None,image_page_url=None,image_status="missing")
        if photo:
            reference=dict(partner.reference_data)
            reference.update(campus_photo_author=photo['author'],campus_photo_license=photo['license'],
                campus_photo_license_url=photo['license_url'],campus_photo_caption=photo['caption'],
                campus_photo_transformations=photo['transformations'],
                campus_photo_modification_note=photo_modification_note(photo),
                campus_photo_campus_pair_scope=photo.get('campus_pair_scope') or '',
                campus_photo_campus_pair_mismatch='different_campuses' if photo.get('campus_pair_mismatch') else 'not_established')
            updates.update(image_url=base_url.rstrip("/")+photo["local_path"],
                image_source_url=photo["image_source_url"],image_page_url=photo["source_url"],image_status="verified",reference_data=reference)
        partners.append(partner.model_copy(update=updates))
    return dashboard.model_copy(update={"partner_universities":partners})


def school_location(partner):
    row=school_audit(partner.school_name)
    record=campus_locations().get(row["id"]) if row else None
    if not record:
        return UniversityLocation(school_name=partner.school_name,country=partner.country,
            geocode_status="pending",note="尚未核實實際交換校區座標；不以國家、城市中心或其他母校資料替代。Wikidata批次查詢遇HTTP429已停止，候選與原始錯誤保留於TKU資料。")
    return UniversityLocation(school_name=partner.school_name,country=partner.country,**record["location"])


def complete_profile(profile):
    row=school_audit(profile.school_name)
    photo=campus_photos().get(row["id"]) if row else None
    if not photo:
        return profile
    from .models import StudentGuidePhoto
    images=[p for p in profile.guide_photos if p.source_url!=photo["source_url"]]
    images.append(StudentGuidePhoto(image_url=photo["local_path"],source_url=photo["source_url"],
        alt=photo["caption"],caption=f"{photo['caption']}；{photo['author']}；{photo['license']}（{photo['license_url']}）。{photo_modification_note(photo)}；拍攝期{photo['photo_date']}，不代表本期指定交換校區。{photo.get('campus_pair_scope','') if photo.get('campus_pair_mismatch') else ''}",category="campus"))
    return profile.model_copy(update={"guide_photos":images})
