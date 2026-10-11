"""Preserve the explicitly identified TKU asset already present at the fixed base.

This is a school-specific provenance join, not a shared name-matching change.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '59a20f27fcee00fb597abc79e75ec11778317422'


def existing_ritsumeikan_photo():
    records = json.loads((ROOT/'src/exchange_info/static/assets/school-images.json').read_text())['schools']
    candidates = [r for r in records if r['school_name']=='立命館大學' and r['country']=='日本' and r.get('artist') and r.get('license_url')]
    assert len(candidates)==1
    original = candidates[0]
    path = ROOT/'src/exchange_info'/original['local_path'].split('?')[0].removeprefix('/')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==original['content_hash'] and original['status']=='verified'
    return dict(id='tku-sister-111',school_name='立命館大學',country='日本',
        source_url=original['official_page_url'],image_source_url=original['image_source_url'],
        author=original['artist'],license=original['license_name'],license_url=original['license_url'],
        license_capture_url=original['official_page_url']+'#Licensing',
        caption='立命館衣笠校區存心館（2016照片；沿用既有素材）',photo_date='2016-09-10',
        identity_quote=original['description'],identity_source_url='https://sister.tku.edu.tw/school-detail.asp?id=111',
        checked_at=original['checked_at'],applicable_year='2016 campus photograph; not current exchange-campus allocation',
        transformations='Existing repository derivative cropped to 16:9; bytes retained without further modification',
        review_status='verified_asset',local_path=original['local_path'],sha256=digest,bytes=path.stat().st_size,
        width=original['width'],height=original['height'],acquisition_status='reused_baseline_asset',baseline_commit=BASE,
        visual_review=dict(sha256=digest,checked_at='2026-10-11',result='pass',
            method='Existing downloaded derivative viewed with view_image; preserve prior licensed identity and author metadata.',
            note='Clock tower and courtyard match the retained Kinugasa campus description; crop explicitly retained.'))


def existing_ritsumeikan_location():
    records = [json.loads(l) for l in (ROOT/'src/exchange_info/official_data/university_locations.jsonl').read_text().splitlines()]
    candidates = [r for r in records if r['school_name']=='立命館大學' and r['country']=='日本']
    assert len(candidates)==1
    original = candidates[0]
    assert original['geocode_status']=='verified' and original['precision']=='representative'
    return dict(id='tku-sister-111',verification_status='verified_asset',acquisition_status='reused_baseline_asset',baseline_commit=BASE,
        location={k:v for k,v in original.items() if k not in {'school_name','country'}},
        evidence=dict(source_url=original['source_url'],identity_source_url=original['identity_source_url'],
            checked_at=original['geocoded_at'],applicable_year='general university representative point; campus allocation unverified',
            role='retained_baseline_representative_location',locator='Fixed-base university_locations.jsonl: 立命館大學 / 日本',
            quote=original['note']))
