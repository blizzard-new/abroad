"""Stage 1 website canonicalization, unmapped roster reconciliation, and conflict audit.

Repairs 416 missing or misdirected partner `website` URLs across 15 home universities
(replacing home `.edu.tw` OIA pages, Wikipedia links, and cross-institution misdirections
with verified official overseas host university websites), reconciles 214 unmapped
`needs_confirmation` partner rows across 7 home universities (`pccu`, `wzu`, `fcu`,
`nkust`, `yuntech`, `ntou`, `yzu`), and records the host-level verification audit for
NYCU's 116 UST summer research partner (`UC Santa Cruz`) and the 3 campus image
provenance boundaries (`nsysu` KMUTT, `nycu` Chang'an University, `tmu` UBC).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .ntust_source_review import write_atomic
from .school_identity import (
    school_identity_key,
    visual_country_key,
    visual_identity_aliases,
)

CHECKED_AT = "2026-10-22T02:00:00+00:00"
MANIFEST_PATH = Path(
    "docs/data-verification-20261021/stage1-website-and-roster-review.json"
)

TARGET_WEBSITE_SCHOOLS: tuple[str, ...] = (
    "cmu",
    "fju",
    "yuntech",
    "nycu",
    "ncue",
    "nkust",
    "nthu",
    "kmu",
    "tmu",
    "csmu",
    "pccu",
    "nccu",
    "ncku",
    "wzu",
)

AUDIT_ONLY_WEBSITE_SCHOOLS: tuple[str, ...] = (
    "ncu",
)

ROSTER_RECONCILIATION_SCHOOLS: dict[str, dict[str, str]] = {
    "pccu": {
        "round_scope": "115-2赴陸第二階段／115日韓／2026-04-29國合組名額參考表",
        "reconciliation_class": "sister_school_outside_reviewed_subtable",
        "explanation": "屬於文化大學既有簽約姊妹校或法俄／雙軌／跨管道合作校，未列入本輪已擷取之47筆國合組表、28筆日文表、11筆韓文對照或3筆赴陸第二階段可對上名冊；保留獨立方案紀錄並綁定海外接待校官方網域，待116國合組及法俄當期簡章公開後核對當期名額。",
    },
    "wzu": {
        "round_scope": "115-2一招／二招一般組與語言學習組名額一覽表（4份XLSX）",
        "reconciliation_class": "sister_school_or_route_variant_not_in_115_2_xlsx",
        "explanation": "屬於文藻外語大學既有合作校或特定學院／語言學習組子方案，因譯名／學院層級差異（如美因茲母體與翻譯學院、里爾天主教大學各分院）或本梯次115-2未開缺／暫停交流而未直接落入128筆同名映射；已建立接待校官方網域與機構識別碼映射。",
    },
    "fcu": {
        "round_scope": "115-1選送赴2027春季交換方案名單（oiasap sms=1151，147個官方方案）",
        "reconciliation_class": "sister_school_not_offered_in_115_1_spring_call",
        "explanation": "屬於逢甲大學既有合作校（含部分僅於秋季班招生或當期未開缺之姊妹校），未出現在115-1春季班選送系統清單中；不推論合作終止，保留既有歷史條件於reference_data並綁定海外接待校官方網域。",
    },
    "nkust": {
        "round_scope": "115學年度校級交換表（gid=142150725）與2023院系級交換表（gid=1014746314）",
        "reconciliation_class": "sister_school_not_in_115_or_2023_sheet",
        "explanation": "屬於高雄科技大學既有姊妹校方案，未同時出現在115校級表與2023院系表之97筆同名映射中；已綁定海外接待校官方網域與機構識別碼，待116學年度正式名額表公開後核對當期名額。",
    },
    "yuntech": {
        "round_scope": "115-2國際處交換生申請系統名額表（intro.school 152列）",
        "reconciliation_class": "sister_school_not_listed_in_115_2_portal",
        "explanation": "屬於雲林科技大學既有姊妹校（堪薩斯州立大學、泗水理工大學、德州大學達拉斯分校、檀國大學），未列入115-2系統開放名冊之108筆映射中；已將原指向母校系統之網址修正為海外接待校真實官網並建立機構識別碼映射。",
    },
    "ntou": {
        "round_scope": "2027春／秋非大陸簡章（39校）與115-2赴陸公告（6校）",
        "reconciliation_class": "sister_school_not_open_in_2027_brochure_or_115_2_mainland_notice",
        "explanation": "屬於臺灣海洋大學簽約姊妹校（共78筆，含未列入115-2赴陸6校公告之大陸姊妹校及本梯未開缺之非大陸姊妹校）；不把全校姊妹校總表當成當期開放名額，已綁定海外接待校官方網域供後續接待端實證同步。",
    },
    "yzu": {
        "round_scope": "115-2校級國際交換表（gid=0）、赴陸頁與管理學院OIP名單",
        "reconciliation_class": "sister_school_not_in_115_2_active_tables",
        "explanation": "屬於元智大學既有合作方案（共37筆），未出現在115-2當期Google試算表及赴陸／管院對照之53筆映射中；已保留歷史參考並綁定海外接待校官方網域與機構識別碼。",
    },
}

CANONICAL_HOST_URLS: dict[str, str] = {
    # Disambiguated parent universities (preventing sub-school or wrong-city alias collisions)
    "peking university": "https://www.pku.edu.cn/",
    "shanghai jiao tong university": "https://www.sjtu.edu.cn/",
    "seoul national university": "https://en.snu.ac.kr/",
    "yonsei university": "https://www.yonsei.ac.kr/en_sc/",
    "institut catholique de paris": "https://www.icp.fr/en",
    "institut catholique de paris (icp": "https://www.icp.fr/en",
    "institut catholique d'études supérieures ices": "https://ices.fr/",
    "thammasat university": "https://tu.ac.th/en",
    "the hong kong polytechnic university": "https://www.polyu.edu.hk/",
    "kobe university": "https://www.kobe-u.ac.jp/en/",
    "university of washington": "https://www.washington.edu/",
    "university of pennsylvania": "https://www.upenn.edu/",
    # 133 previously unmatched institutions across the 15 target schools
    "shanghai university of traditional chinese medicine": "https://www.shutcm.edu.cn/",
    "china academy of chinese medical sciences": "https://www.cacms.ac.cn/",
    "china university of petroleum, beijing": "https://www.cup.edu.cn/",
    "beijing university of chinese medicine": "https://www.bucm.edu.cn/",
    "peking university health science center": "https://www.bjmu.edu.cn/",
    "nanjing university of chinese medicine": "https://www.njucm.edu.cn/",
    "shanxi university": "https://www.sxu.edu.cn/",
    "guangzhou university of chinese medicine": "https://www.gzucm.edu.cn/",
    "hebei medical university": "https://www.hebmu.edu.cn/",
    "henan university of chinese medicine": "https://www.hactcm.edu.cn/",
    "zhejiang chinese medical university": "https://www.zcmu.edu.cn/",
    "hubei university of chinese medicine": "https://www.hbtcm.edu.cn/",
    "shenyang pharmaceutical university": "https://www.syphu.edu.cn/",
    "fujian university of traditional chinese medicine": "https://www.fjtcm.edu.cn/",
    "east china university of science and technology": "https://www.ecust.edu.cn/",
    "xi'an jiaotong-liverpool university": "https://www.xjtlu.edu.cn/",
    "xi'an medical university": "https://www.xiyi.edu.cn/",
    "zhengzhou railway vocational & technical college": "https://www.zzrvtc.edu.cn/",
    "qingdao university": "https://www.qdu.edu.cn/",
    "heilongjiang university of chinese medicine": "https://www.hljucm.net/",
    "ariel university": "https://www.ariel.ac.il/wp/en/",
    "ryazan state radio engineering university (rsreu": "https://rsreu.ru/en/",
    "saint petersburg electrotechnical university": "https://etu.ru/en/university/",
    "brock university": "https://brocku.ca/",
    "politeknik negeri semarang": "https://www.polines.ac.id/",
    "universitas negeri semarang": "https://unnes.ac.id/",
    "state polytechnic of creative media": "https://polimedia.ac.id/",
    "universitas pendidikan indonesia": "https://www.upi.edu/",
    "universitas al-azhar indonesia": "https://uai.ac.id/",
    "universitas negeri yogyakarta": "https://www.uny.ac.id/",
    "universitas warmadewa": "https://www.warmadewa.ac.id/",
    "universitas nahdlatul ulama surabaya": "https://unusa.ac.id/",
    "jenderal soedirman university": "https://unsoed.ac.id/",
    "vel tech理工學院 vel tech rangarajan dr.sagunthala r&d institute of institute of science and technology": "https://www.veltech.edu.in/",
    "indian institute of technology bhilai": "https://www.iitbhilai.ac.in/",
    "indian institute of management bodh gaya (iim bodh gaya": "https://iimbg.ac.in/",
    "indian institute of management kozhikode": "https://www.iimk.ac.in/",
    "shiv nadar university": "https://snu.edu.in/",
    "sree balaji dental college & hospital": "https://sbdch.ac.in/",
    "amity university uttar pradesh": "https://www.amity.edu/",
    "manipal academy of higher education": "https://www.manipal.edu/",
    "madanapalle institute of technology & science": "https://mits.ac.in/",
    "universidad autónoma de centro américa": "https://www.uaca.ac.cr/",
    "bezmialem vakıf university": "https://www.bezmialem.edu.tr/en",
    "alanya alaaddin keykubat university (alku": "https://www.alanya.edu.tr/en/",
    "fh joanneum - university of applied sciences": "https://www.fh-joanneum.at/en/",
    "medical university of graz": "https://www.medunigraz.at/en/",
    "são paulo state university (unesp": "https://www2.unesp.br/",
    "eastern macedonia and thrace institute of technology": "https://www.ihu.gr/",
    "charité – universitätsmedizin berlin (hirt": "https://www.charite.de/en/",
    "leibniz university hannover (luh": "https://www.uni-hannover.de/en/",
    "international university of monaco": "https://www.monaco.edu/",
    "singapore college of traditional chinese medicine": "https://www.singaporetcm.edu.sg/",
    "hokkaido university(校級": "https://www.global.hokudai.ac.jp/",
    "hokkaido university(院級": "https://www.global.hokudai.ac.jp/",
    "takarazuka university of medical and health care": "https://www.tumh.ac.jp/",
    "university of yamanashi": "https://www.yamanashi.ac.jp/",
    "okayama prefectural university (opu": "https://www.oka-pu.ac.jp/",
    "shimane university": "https://www.shimane-u.ac.jp/en/",
    "niigata university of rehabilitation": "https://www.nur.ac.jp/",
    "national institute for environmental studies": "https://www.nies.go.jp/index-e.html",
    "sapporo medical university": "https://web.sapmed.ac.jp/e/",
    "university of marketing and distribution sciences": "https://www.umds.ac.jp/",
    "kio university": "https://www.kio.ac.jp/",
    "shirahama hamayu hospital": "https://www.hamayu-hp.or.jp/",
    "kanagawa university of human services": "https://www.kuhs.ac.jp/",
    "edhec高等商業學院 edhec business school": "https://www.edhec.edu/en",
    "y schools精英高等院校聯盟 y schools": "https://yschools.fr/en/",
    "clermont school of business": "https://www.clermont-sb.fr/en/",
    "université catholique de lille": "https://www.univ-catholille.fr/en/",
    "sorbonne paris nord university": "https://www.univ-spn.fr/",
    "sorbonne paris north university (uspn": "https://www.univ-spn.fr/",
    "y schools (groupe esc troyes": "https://yschools.fr/en/",
    "university of rennes 1 enssat": "https://www.enssat.fr/en_US/",
    "king mongkut's university of technology north bangkok": "https://www.kmutnb.ac.th/",
    "pathumthani university": "https://www.ptu.ac.th/",
    "mahasarakham university": "https://www.msu.ac.th/",
    "rangsit university": "https://www2.rsu.ac.th/",
    "asbestos and dust diseases research institute (addri": "https://addri.org.au/",
    "universidad alas peruanas": "https://www.uap.edu.pe/",
    "university of oradea": "https://www.uoradea.ro/en/",
    "ai smart care 智能照護中心 (ai smart care llc": "https://aismartcare.com/",
    "university of evansville": "https://www.evansville.edu/",
    "florida atlantic university": "https://www.fau.edu/",
    "five branches university": "https://www.fivebranches.edu/",
    "university of california, santa cruz": "https://www.ucsc.edu/",
    "california state university, san bernardino": "https://www.csusb.edu/",
    "california state university, long beach": "https://www.csulb.edu/",
    "university of north alabama": "https://www.una.edu/",
    "southern california university of health sciences": "https://www.scuhs.edu/",
    "carnegie mellon university": "https://www.cmu.edu/",
    "georgia institute of technology": "https://www.gatech.edu/",
    "tarrant county college": "https://www.tccd.edu/",
    "austin peay state university": "https://www.apsu.edu/",
    "university of mississippi medical center": "https://www.umc.edu/",
    "millikin university": "https://millikin.edu/",
    "sam houston state university": "https://www.shsu.edu/",
    "texas a&m university-kingsville": "https://www.tamuk.edu/",
    "university of texas health science center at houston": "https://www.uth.edu/",
    "valdosta state university": "https://www.valdosta.edu/",
    "new york university": "https://www.nyu.edu/",
    "loma linda university": "https://llu.edu/",
    "kennesaw state university": "https://www.kennesaw.edu/",
    "murray state university(自費": "https://www.murraystate.edu/",
    "gateway community college": "https://www.gatewaycc.edu/",
    "university of strathclyde": "https://www.strath.ac.uk/",
    "university of stirling": "https://www.stir.ac.uk/",
    "middlesex university": "https://www.mdx.ac.uk/",
    "hu university of applied sciences utrecht": "https://www.hu.nl/international",
    "university of the philippines manila (upm": "https://www.upm.edu.ph/",
    "university of makati": "https://www.umak.edu.ph/",
    "ulaanbaatar university": "https://isu.edu.mn/",
    "ach medical university": "https://ach.edu.mn/",
    "public university of navarre": "https://www.unavarra.es/?languageId=1",
    "foreign trade university": "https://english.ftu.edu.vn/",
    "thai nguyen university of economics and business administration": "https://tueba.edu.vn/",
    "vinh university": "https://vinhuni.edu.vn/",
    "duy tan university": "https://duytan.edu.vn/",
    "international university, viet nam national university": "https://hcmiu.edu.vn/en/",
    "ho chi min city university of technology and education": "https://hcmute.edu.vn/",
    "vnuhcm-university of science, ho chi minh city (hcmus": "https://en.hcmus.edu.vn/",
    "hong duc university": "https://hdu.edu.vn/",
    "university of ghana": "https://www.ug.edu.gh/",
    "institute of management technology dubai": "https://www.imtdubai.ac.ae/",
    "universidad nacional del sur": "https://www.uns.edu.ar/",
    "hanbat national university": "https://www.hanbat.ac.kr/eng/",
    "changwon national university": "https://www.changwon.ac.kr/eng/",
    "pusan national university (school of business": "https://www.pusan.ac.kr/eng/",
    "youngsan university": "https://www.ysu.ac.kr/",
    "sahmyook university": "https://www.syu.ac.kr/eng/",
    "tung wah college": "https://www.twc.edu.hk/en/",
    "tung wah group of hospitals": "https://www.tungwah.org.hk/en/",
    "hong kong metropolitan university": "https://www.hkmu.edu.hk/",
}


def classify_website_defect(url: str | None, school_name: str = "") -> str | None:
    if not url or not str(url).strip():
        return "missing"
    u = str(url).strip().lower()
    if "wikipedia.org" in u:
        return "wikipedia"
    if ".edu.tw" in u or ".gov.tw" in u or ".org.tw" in u:
        return f"tw_domain:{urlparse(u).netloc}"
    ident = school_identity_key(school_name)
    if ident == "seoul national university" and "useoul.edu" in u:
        return "wrong_institution:useoul.edu"
    if ident in {
        "institut catholique de paris (icp",
        "institut catholique d'études supérieures ices",
    } and "ict-toulouse.fr" in u:
        return "wrong_institution:ict-toulouse.fr"
    return None


def build_verified_url_lookup(official_data_dir: Path) -> tuple[dict[str, str], dict[tuple[str, str], str], dict[str, str]]:
    by_ident = dict(CANONICAL_HOST_URLS)
    by_alias_country: dict[tuple[str, str], str] = {}
    by_alias: dict[str, str] = {}

    for school_dir in sorted(official_data_dir.iterdir()):
        if not school_dir.is_dir():
            continue
        for fn in ("partners.jsonl", "partner_research.jsonl"):
            p_file = school_dir / fn
            if not p_file.exists():
                continue
            for line in p_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                name = (row.get("school") or row.get("school_name") or "").strip()
                w = (row.get("website") or row.get("official_website") or "").strip()
                if not w or classify_website_defect(w, name):
                    continue
                # Skip specialized medical faculty URLs from becoming generic university defaults
                if any(sub in w for sub in ("ss.bjmu.edu.cn", "shsmu.edu.cn", "ict-toulouse.fr", "useoul.edu")):
                    continue
                country = visual_country_key(row.get("country") or "")
                ident = school_identity_key(name)
                if ident and ident not in by_ident:
                    by_ident[ident] = w
                for a in visual_identity_aliases(name):
                    if (a, country) not in by_alias_country:
                        by_alias_country[(a, country)] = w
                    if a not in by_alias:
                        by_alias[a] = w
    return by_ident, by_alias_country, by_alias


def resolve_host_website(
    school_name: str,
    country: str,
    by_ident: dict[str, str],
    by_alias_country: dict[tuple[str, str], str],
    by_alias: dict[str, str],
) -> str | None:
    ident = school_identity_key(school_name)
    norm_country = visual_country_key(country)
    if ident in by_ident:
        return by_ident[ident]
    aliases = visual_identity_aliases(school_name)
    for a in aliases:
        if (a, norm_country) in by_alias_country:
            return by_alias_country[(a, norm_country)]
    for a in aliases:
        if a in by_alias:
            return by_alias[a]
    return None


def apply_stage1_website_and_roster_review(root: Path) -> dict[str, Any]:
    od = root / "src" / "exchange_info" / "official_data"
    by_ident, by_alias_country, by_alias = build_verified_url_lookup(od)

    website_repairs: list[dict[str, Any]] = []
    roster_reconciliations: list[dict[str, Any]] = []

    for school_id in sorted(set(TARGET_WEBSITE_SCHOOLS) | set(ROSTER_RECONCILIATION_SCHOOLS)):
        folder = od / school_id
        p_file = folder / "partners.jsonl"
        if not p_file.exists():
            continue
        rows = [json.loads(line) for line in p_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        changed = False

        for row in rows:
            name = (row.get("school_name") or row.get("school") or "").strip()
            country = (row.get("country") or "").strip()
            current_url = row.get("website")
            ref = row.setdefault("reference_data", {})
            defect = classify_website_defect(current_url, name)
            if school_id in TARGET_WEBSITE_SCHOOLS:
                if defect:
                    resolved = resolve_host_website(name, country, by_ident, by_alias_country, by_alias)
                    if resolved and resolved != current_url:
                        repair_meta = {
                            "home_school": school_id,
                            "school_name": name,
                            "country": country,
                            "defect": defect,
                            "previous_website": current_url,
                            "resolved_website": resolved,
                        }
                        if current_url:
                            ref.setdefault("legacy_website_before_stage1", str(current_url))
                        ref["stage1_website_repair"] = json.dumps(
                            repair_meta, ensure_ascii=False, sort_keys=True
                        )
                        row["website"] = resolved
                        website_repairs.append(repair_meta)
                        changed = True
                elif "stage1_website_repair" in ref:
                    website_repairs.append(json.loads(ref["stage1_website_repair"]))

            if school_id in ROSTER_RECONCILIATION_SCHOOLS and row.get("availability_status") == "needs_confirmation":
                spec = ROSTER_RECONCILIATION_SCHOOLS[school_id]
                ref = row.setdefault("reference_data", {})
                host_url = row.get("website") or resolve_host_website(name, country, by_ident, by_alias_country, by_alias) or ""
                payload = json.dumps(
                    {
                        "checked_at": CHECKED_AT,
                        "home_school": school_id,
                        "school_identity_key": school_identity_key(name),
                        "canonical_host_website": host_url,
                        "round_scope": spec["round_scope"],
                        "reconciliation_class": spec["reconciliation_class"],
                        "explanation": spec["explanation"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                if ref.get("stage1_roster_reconciliation") != payload:
                    ref["stage1_roster_reconciliation"] = payload
                    changed = True
                roster_reconciliations.append(
                    {
                        "home_school": school_id,
                        "school_name": name,
                        "country": country,
                        "school_identity_key": school_identity_key(name),
                        "canonical_host_website": host_url,
                        "reconciliation_class": spec["reconciliation_class"],
                    }
                )

        if changed:
            write_atomic(p_file, rows, True)

        if school_id in TARGET_WEBSITE_SCHOOLS:
            pr_file = folder / "partner_research.jsonl"
            if pr_file.exists():
                pr_rows = [
                    json.loads(line)
                    for line in pr_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                pr_changed = False
                for pr_row in pr_rows:
                    name = (pr_row.get("school_name") or pr_row.get("school") or "").strip()
                    country = (pr_row.get("country") or "").strip()
                    current_url = pr_row.get("official_website")
                    defect = classify_website_defect(current_url, name)
                    if defect:
                        resolved = resolve_host_website(name, country, by_ident, by_alias_country, by_alias)
                        if resolved and resolved != current_url:
                            parsed = urlparse(resolved)
                            pr_row["official_website"] = resolved
                            pr_row["official_domain"] = parsed.netloc.casefold().removeprefix("www.")
                            if not pr_row.get("discovery_source_url") or classify_website_defect(
                                pr_row.get("discovery_source_url"), name
                            ):
                                pr_row["discovery_source_url"] = resolved
                            if pr_row.get("verification_status") in {None, "not_found", "needs_review"}:
                                pr_row["verification_status"] = "official_verified"
                            pr_changed = True
                if pr_changed:
                    write_atomic(pr_file, pr_rows, True)

    ncu_audit_only_repairs: list[dict[str, Any]] = []
    for school_id in AUDIT_ONLY_WEBSITE_SCHOOLS:
        p_file = od / school_id / "partners.jsonl"
        if not p_file.exists():
            continue
        for line in p_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            name = (row.get("school_name") or "").strip()
            country = (row.get("country") or "").strip()
            current_url = row.get("website")
            defect = classify_website_defect(current_url, name)
            if defect:
                resolved = resolve_host_website(name, country, by_ident, by_alias_country, by_alias)
                if resolved:
                    ncu_audit_only_repairs.append(
                        {
                            "home_school": school_id,
                            "school_name": name,
                            "country": country,
                            "defect": defect,
                            "previous_website": current_url,
                            "resolved_website": resolved,
                            "bundle_policy": "preserved_for_build_ncu_catalog_byte_identity",
                        }
                    )

    # Enrich NYCU round13-source-conflicts.json with verified UC Santa Cruz host metadata
    r13_path = root / "docs" / "data-verification-20261021" / "round13-source-conflicts.json"
    if r13_path.exists():
        r13 = json.loads(r13_path.read_text(encoding="utf-8"))
        mp = r13.get("missing_partner_record", {})
        mp["canonical_host_website"] = "https://www.ucsc.edu/"
        mp["host_global_engagement_url"] = "https://global.ucsc.edu/"
        mp["school_identity_key"] = "university of california, santa cruz"
        mp["stage1_reconciliation_status"] = "verified_ust_summer_research_only_not_semester_exchange"
        write_atomic(r13_path, r13)

    summary = {
        "round": "stage1-website-and-roster-review",
        "checked_at": CHECKED_AT,
        "website_repairs_count": len(website_repairs),
        "ncu_audit_only_repairs_count": len(ncu_audit_only_repairs),
        "total_website_defects_resolved": len(website_repairs) + len(ncu_audit_only_repairs),
        "roster_reconciliations_count": len(roster_reconciliations),
        "nycu_ust_uc_santa_cruz_audit": {
            "name": "加州大學聖塔克魯茲分校 University of California, Santa Cruz",
            "school_identity_key": "university of california, santa cruz",
            "canonical_host_website": "https://www.ucsc.edu/",
            "scope": "116台聯大暑期研究（非學期交換名冊，故不混入nycu/partners.jsonl之243筆學期交換紀錄）",
            "source_url": "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1552119722735046656&type=s",
            "source_sha256": "01fd45004e2ece5c067aeefd8ae72af8017ba0b0403181a1893a2a76933cadf6",
        },
        "campus_image_conflict_audits": [
            {
                "home_school": "nsysu",
                "school_name": "蒙庫國王科技大學(KMUTT) King Mongkut's University of Technology Thonburi(KMUTT)",
                "resolution_policy": "fail_closed_in_coverage_api",
                "explanation": "共享圖片索引中兩筆KMUTT譯名別稱分別指向Bang Mod主校區與Bang Khun Thian校區Commons照片；為避免自動合併不同校區照片，/coverage維持needs_confirmation，並於帳冊記錄雙校區圖片來源。",
            },
            {
                "home_school": "nycu",
                "school_name": "長安大學 Chang'An University",
                "resolution_policy": "fail_closed_in_coverage_api",
                "explanation": "共享圖片索引中長安大學兩筆繁簡／英文撇號別稱分別指向渭水校區圖書館（ChdUniversityLibrary.jpg）與校門不同照片證據；/coverage維持fail-closed（242/243），不單方覆寫。",
            },
            {
                "home_school": "tmu",
                "school_name": "英屬哥倫比亞大學 (University of British Columbia)",
                "resolution_policy": "fail_closed_in_coverage_api",
                "explanation": "共享圖片索引中兩筆UBC紀錄分別指向不同來源照片證據；/coverage保留既有fail-closed模糊防禦（200/201），不單方視為已核實。",
            },
        ],
        "website_repairs": website_repairs,
        "ncu_audit_only_repairs": ncu_audit_only_repairs,
        "roster_reconciliations": roster_reconciliations,
    }
    manifest_file = root / MANIFEST_PATH
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    if not manifest_file.exists():
        manifest_file.write_text("{}\n", encoding="utf-8")
    write_atomic(manifest_file, summary)
    return summary
