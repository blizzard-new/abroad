"""Index exact host reference excerpts; never infer current-cycle eligibility.

This fills the public-reference layer of the per-institution ledger, not the
reviewed four-school current eligibility engine. Each excerpt retains its page
context, source role, check time and a separate, explicitly unverified period.
"""
from __future__ import annotations

import gzip
from tku_capture_io import read_bytes, exists, captures
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
PATTERNS = {
    "host_eligibility": r"nominated by|nomination by|home universit.{0,60}(?:nomina|recommend)|partner universit.{0,60}(?:eligible|nomina|recommend)|出願資格|申请资格|申請資格|被推荐",
    "host_language": r"TOEFL|IELTS|JLPT|HSK|language (?:requirement|proficiency)|語学能力|日本語能力|語言要求|语言要求",
    "host_deadline": r"application deadline|deadline.{0,50}(?:application|exchange)|出願締切|申請截止|申请截止|报名截止",
    "host_nomination_deadline": r"nomination deadline|deadline.{0,40}nominat|提名截止|推薦締切",
    "latest_forms": r"application documents|documents.{0,40}(?:application|submit)|application form|required documents|申請書類|出願書類|申请材料|申請文件",
    "course_restrictions": r"course.{0,30}(?:restriction|registration|catalog|selection)|at least.{0,30}credits|maximum.{0,30}credits|科目履修|履修制限|选课|選課|课程目录",
    "housing": r"(?:accommodation|housing|dormitor|residence hall).{0,50}(?:student|apply|application|available|room|cost|fee)|学生寮|宿舍|住宿",
    "housing_costs": r"(?:accommodation|housing|rent|dormitor).{0,60}(?:cost|fee|\$|€|yen|EUR|USD)|(?:cost|fee|rent).{0,40}(?:housing|accommodation)|寮費|住宿費|住宿费",
    "costs": r"tuition (?:fee|waiver)|exchange student.{0,50}(?:fee|cost)|fees.{0,40}exchange|学費|学费|學費",
    "insurance": r"health insurance|medical insurance|insurance (?:coverage|mandatory|required)|国民健康保険|保險|保险",
    "living_costs": r"living (?:cost|expense)|cost of living|生活費|生活费",
    "transport": r"(?:campus|student).{0,40}(?:bus|transport|shuttle)|(?:bus|transport|shuttle).{0,40}(?:campus|student)|通学|通勤|交通",
}
BAD_BODY = re.compile(r"verify you are human|just a moment|enable javascript and cookies|access denied|attention required|captcha", re.I)
OUTBOUND_TITLE = re.compile(r"outbound|outgoing|交換留学制度の利用|国际交流.*出国", re.I)


def same_host(seed, final):
    a=urlsplit(seed).netloc.lower().removeprefix("www.")
    b=urlsplit(final).netloc.lower().removeprefix("www.")
    return a==b or a.endswith('.'+b) or b.endswith('.'+a)


def build():
    index=json.loads((BUNDLE/"host_census_capture_index.json").read_text())
    rows=[]
    for institution in index:
        references=[]; blockers=[]
        for meta in institution["sources"]:
            path=BUNDLE/"host_census_sources"/(meta["id"]+".json.gz")
            source=json.loads(gzip.decompress(read_bytes(path)))
            if source.get("error"):
                blockers.append({**meta,"reason":"official_endpoint_open_failed"});continue
            if source.get('http_status') != 200:
                blockers.append({**meta,"reason":"non_200_response_not_verified_source_content"});continue
            if source.get('content_extraction_status')=='legacy_DOC_parser_not_available':
                blockers.append({**meta,"reason":"binary_opened_content_and_period_not_verified"});continue
            if source['id']=='8e3de1e08d6326e72eaed8aa':
                assert '2026年辽宁大学辽宁省政府外国留学生奖学金生项目专业目录' in source['text']
                blockers.append({**meta,"reason":"2026_full_degree_doctoral_scholarship_not_TKU_exchange", "content_locator":"xl/worksheets/sheet1.xml A1"});continue
            if urlsplit(source['source_url']).path.lower().endswith(('.pdf','.docx')) and not source.get('local_file'):
                blockers.append({**meta,"reason":"expected_document_missing_verified_binary"});continue
            if BAD_BODY.search(source.get("text","")[:1000]):
                blockers.append({**meta,"reason":"challenge_page_not_source_content"});continue
            if not same_host(source["source_url"],source.get("final_url",source["source_url"])):
                blockers.append({**meta,"reason":"redirect_domain_requires_identity_review"});continue
            if OUTBOUND_TITLE.search(source.get("title","")):
                blockers.append({**meta,"reason":"host_outbound_page_not_TKU_incoming_rule"});continue
            paragraphs=source.get("paragraphs") or [line.strip() for line in source.get("text","").splitlines() if len(line.strip())>=35]
            for key,pattern in PATTERNS.items():
                matches=[(i,p) for i,p in enumerate(paragraphs,1) if re.search(pattern,p,re.I) and len(p)<=2200]
                # Preserve verbatim evidence, no inferred numeric threshold or deadline.
                for number,quote in matches[:2]:
                    pages=[p['page'] for p in source.get('pages',[]) if quote in (p.get('text') or '')]
                    locator=f"PDF page {','.join(map(str,pages))}; extracted line {number}" if pages else f"Extracted paragraph/line {number}; title: {source.get('title','PDF')}"
                    references.append(dict(key=key, value=quote, status="reference_only",
                        reason="接待校官方公開原文參考；來源年度、校區及淡江提名計畫對應尚未核實。不能當作本期母校申請資格或文件。",
                        evidence=[dict(source_id=source["id"], source_url=source["source_url"],
                            final_url=source.get("final_url"), locator=locator,
                            quote=quote, applicable_year="source period not independently established; public reference only",
                            role="host_general_reference", application_round="TKU nomination/programme mapping not verified",
                            checked_at=source["checked_at"], content_sha256=source["sha256"])]))
        fields={}
        for key in PATTERNS:
            values=[r for r in references if r["key"]==key]
            if values:
                fields[key]=dict(value="\n".join(r["value"] for r in values[:4]),status="reference_only",
                    reason=values[0]["reason"],evidence=[e for r in values[:4] for e in r["evidence"]])
        rows.append(dict(id=institution["id"],school_name=institution["school_name"],country=institution["country"],
                         fields=fields,reference_excerpts=references,source_checks=institution["sources"],blockers=blockers))
    for curated in json.loads((BUNDLE/'curated_partner_facts.json').read_text()) if (BUNDLE/'curated_partner_facts.json').exists() else []:
        row=next(row for row in rows if row['id']==curated['id'])
        row['fields'].update(curated['fields'])
        row['reviewed_host_year_fields']=list(curated['fields'])
    (BUNDLE/"partner_enrichment.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows))
    print(json.dumps(dict(institutions=len(rows),with_public_references=sum(bool(r["fields"]) for r in rows),
                         excerpt_count=sum(len(r["reference_excerpts"]) for r in rows),
                         fields=dict(Counter(key for row in rows for key in row["fields"]))),ensure_ascii=False))


if __name__=="__main__":build()
