"""Reconcile all TKU agreements and programme rows, retaining every gap state."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
FIELDS = {
    "home_eligibility": "母校資格", "home_language": "母校語言", "host_eligibility": "接待校資格",
    "host_language": "接待校語言", "quota": "名額", "home_deadline": "校內期限",
    "host_deadline": "外校申請期限", "host_nomination_deadline": "外校提名期限",
    "documents": "母校本期文件", "latest_forms": "接待校本期文件", "study_period": "交換期間",
    "department_scope": "系所及計畫限制", "campus": "交換校區", "course_restrictions": "課程限制",
    "housing": "住宿", "housing_costs": "住宿費用", "costs": "交換费用", "insurance": "保險",
    "living_costs": "生活費", "transport": "生活及交通來源", "coordinates": "地球座標",
    "campus_photo": "可授權校園照片",
}

# These are reviewed institutional identities, never fuzzy/geocoder matches.
# The record's original spelling and country remain in programme evidence.
ALIASES = {
    "法國巴黎西岱大學": "203", "法國高等計算機子及自動化學校": "195",
    "拉脫維亞大學": "318", "斯洛維尼亞盧比安納大學": "309", "荷蘭HZ應用科技大學": "322",
    "美國加州州立大學長堤分校": "85", "美國聖道大學": "94", "澳洲昆士蘭理工大學": "119",
    "澳洲西雪梨大學": "241", "韓國明知大學": "261", "印度SRM大學": "263",
    "印度費爾大學": "212", "印度維洛爾理工大學": "266", "馬來西亞拉曼大學": "163",
    "印尼穆罕默迪亞大學": "183", "墨西哥州立自治大學": "52", "智利國立大學": "10",
    "阿根廷企業大學": "290", "蘭州大學": "125", "澳門大學": "175", "澳門城市大學": "337",
    "金門大學": "186",
}


def normalize(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value).casefold() if c.isalnum())


def read_rows(name):
    return [json.loads(line) for line in (BUNDLE / name).read_text().splitlines() if line.strip()]


def reconcile():
    census = read_rows("partner_census.jsonl")
    programmes = read_rows("partners_current.jsonl") + read_rows("partners_reference.jsonl")
    if (BUNDLE / "earlier_round_programmes.jsonl").exists():
        programmes += read_rows("earlier_round_programmes.jsonl")
    unmatched = []
    for programme in programmes:
        if programme.get("institution_id"):
            next(row for row in census if row["id"] == programme["institution_id"]).setdefault("programme_ids", []).append(programme["id"])
            continue
        name = programme["fields"]["school_name"]["value"]
        chinese = re.split(r"[A-Za-z(（]", name)[0].strip().replace("\u200e", "")
        country = programme["fields"]["country"]["value"].strip()
        alias = next((key for key in sorted(ALIASES, key=len, reverse=True) if name.startswith(key)), None)
        if alias:
            matches = [row for row in census if row["id"] == "tku-sister-" + ALIASES[alias]]
        else:
            matches = [row for row in census if normalize(row["school_name"]) in {
                normalize(chinese), normalize(chinese.removeprefix(country))}]
        if len(matches) != 1:
            # Keep omitted institutions; directory omission is not a cancelled agreement.
            key = normalize(name)
            row = next((x for x in census if x.get("programme_identity") == key), None)
            if row is None:
                basis = programme["fields"]["school_name"]["evidence"][0]
                row = dict(id="tku-programme-" + programme["id"], school_name=name, english_name="",
                           country=country, directory_url=basis["source_url"], listing_url=basis["source_url"],
                           checked_at=basis["checked_at"], programme_identity=key,
                           scope="programme_list_not_in_sister_directory", availability_status="reference_only",
                           selection_note="甄選名單有此校，但姊妹校總覽未匹配；保留來源矛盾，不推定協議撤銷。")
                census.append(row)
                unmatched.append(row["id"])
            matches = [row]
        matches[0].setdefault("programme_ids", []).append(programme["id"])
    return census, {row["id"]: row for row in programmes}, unmatched


def build():
    census, programmes, unmatched = reconcile()
    enrichment = {r["id"]: r for r in read_rows("partner_enrichment.jsonl")} if (BUNDLE / "partner_enrichment.jsonl").exists() else {}
    photos={r['id']:r for r in json.loads((BUNDLE/'campus_asset_manifest.json').read_text()) if r.get('review_status')=='verified_asset'}
    locations={r['id']:r for r in json.loads((BUNDLE/'campus_location_manifest.json').read_text())}
    commons={r['id']:r for r in json.loads((BUNDLE/'commons_campus_index.json').read_text())}
    coordinates={r['id']:r for r in json.loads((BUNDLE/'campus_candidates.json').read_text())}
    schools = []
    for row in census:
        cells = {}
        for key, label in FIELDS.items():
            records = [programmes[k] for k in row.get("programme_ids", [])]
            known = [{"programme_id": p["id"], "academic_year": p["academic_year"],
                      "selection_status": p["selection_status"], **p["fields"][key]}
                     for p in records if key in p["fields"]]
            current = [fact for fact in known if fact["selection_status"] == "listed"]
            verified = [f for f in current if f["status"] == "verified"]
            cells[key] = dict(label=label, status="verified_current" if verified else
                             "conflict" if any(f["status"] == "needs_confirmation" for f in current) else
                             "missing_in_source" if any(f["status"] == "missing_in_source" for f in current) else
                             "reference_only" if any(f["value"] is not None for f in known) else "not_verified_new",
                             values=known,
                             reason="僅來源適用年度／梯次可用；協議不等於本期名額。" if known else
                             "此項未取得適用本期的公開原文；不表示官方明示尚未公告。",
                             checked_entries=[dict(source_url=row["directory_url"], checked_at=row.get("detail_checked_at", row["checked_at"]),
                                                   locator="姊妹校簡介／計畫列表", role="directory_reference",
                                                   applicable_year="general directory; not a selection cycle")])
            if key in enrichment.get(row["id"], {}).get("fields", {}):
                cells[key]["public_reference"] = enrichment[row["id"]]["fields"][key]
                if cells[key]["status"] == "not_verified_new":
                    cells[key]["status"] = enrichment[row["id"]]["fields"][key]["status"]
            if key.startswith('host_') or key in {'latest_forms','course_restrictions','housing','housing_costs','costs','insurance','living_costs','transport'}:
                cells[key]['public_source_check_ids']=[s['id'] for s in enrichment.get(row['id'],{}).get('source_checks',[])]
                cells[key]['source_blocker_ids']=[s['id'] for s in enrichment.get(row['id'],{}).get('blockers',[])]
                if not cells[key].get('public_reference') and not current:
                    cells[key]['reason']='公開來源已查，尚未取得可核實本期／本計畫的此欄原文；開啟錯誤及接待校／母校適用範圍分別列出。不代表官方明示尚未公告。'
            if key=='campus_photo':
                cells[key]['asset_search_check']={k:v for k,v in commons.get(row['id'],{}).items() if k!='response'}
                photo=photos.get(row['id'])
                if photo:
                    cells[key].update(status='verified_asset',reason='實際校景、作者與自由授權已核對；歷史拍攝期及校區標明，不代表当期交換校區。',
                        public_reference=dict(value=photo['caption'],status='verified_asset',evidence=[dict(source_url=photo['source_url'],checked_at=photo['checked_at'],applicable_year=photo['applicable_year'],role='licensed_campus_photo',locator='Commons Summary/Licensing and downloaded visual review',quote=photo['identity_quote'],license=photo['license'],license_url=photo['license_url'],sha256=photo['sha256'])]))
            if key=='coordinates':
                cells[key]['asset_search_check']=coordinates.get(row['id'],{})
                location=locations.get(row['id'])
                if location:
                    cells[key].update(status='verified_asset',reason=location['location']['note'],public_reference=dict(value={'latitude':location['location']['latitude'],'longitude':location['location']['longitude'],'precision':location['location']['precision']},status='verified_asset',evidence=[location['evidence']]))
        schools.append({**row, "fields": cells,'public_source_checks':enrichment.get(row['id'],{}).get('source_checks',[]),
                        'source_blockers':enrichment.get(row['id'],{}).get('blockers',[])})
    counts = {key: dict(Counter(r["fields"][key]["status"] for r in schools)) for key in FIELDS}
    audit = dict(base_commit="59a20f27fcee00fb597abc79e75ec11778317422", checked_date="2026-10-11",
                 directory_count=286, institution_denominator=len(schools), programme_count=len(programmes),
                 programme_only_institutions=unmatched, latest_round_schools=4, latest_round_quota=7,
                 currently_open_home_applications=0, field_counts=counts, schools=schools,
                 interpretation="分母為286筆官方姊妹校總覽與既有交換計畫名單的機構聯集。reference_only與一般接待校原文不算本期完成；所有協議列不產生名額或母校資格。")
    path = BUNDLE / "full_census_audit.json"
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    baseline = BUNDLE / "full_census_baseline.json"
    if not baseline.exists():
        baseline.write_bytes(path.read_bytes())
    print(json.dumps({key: value for key, value in audit.items() if key != "schools"}, ensure_ascii=False))


if __name__ == "__main__":
    build()
