"""Capture public host evidence for every TKU census institution, with bounded links.

Existing CGU/NTPU host URLs are discovery seeds, not copied outbound rules.
All captures remain candidates until content and institutional scope are reviewed.
"""
from __future__ import annotations

import concurrent.futures
import gzip
from tku_capture_io import read_bytes, exists, captures as stored_captures
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exchange_info.school_identity import same_school

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
STORE = BUNDLE / "host_census_sources"
EXTRA_SEEDS = {
    "343": ["https://www.sathyabama.ac.in/international-relations/overview", "https://www.sathyabama.ac.in/sites/default/files/2023-05/Student%20Exchange%20Policy%20%282%29.pdf"],
    "339": ["https://oes.mnnu.edu.cn/info/1024/1572.htm"],
    "338": ["https://icep.mapua.edu.ph/InternationalPrograms/AcademePartners.aspx", "https://www.mapua.edu.ph/"],
    "337": ["https://oga.cityu.edu.mo/page-83"],
    "335": ["https://enrollmentmanagement.baruch.cuny.edu/international-student-service-center/"],
    "301": ["https://www.vdu.lt/en/international-cooperation/for-students/vmu-bilateral-exchange-studies/incoming-exchange-students/", "https://www.vdu.lt/en/international-cooperation/for-students/practical-information-for-incoming-students/"],
    "300": ["https://tcnj.edu/", "https://iss.tcnj.edu/preparing-for-tcnj/what-you-need-to-know/about-the-united-states/"],
    "287": ["https://presidencyuniversity.in/"],
    "288": ["https://aep.tuaf.edu.vn/en/admission/7-exchange-program-procedure-and-form"],
    "299": ["https://www.uregina.ca/"],
    "276": ["https://int.unn.ru/erasmus/", "https://eng.unn.ru/"],
    "266": ["https://vit.ac.in/"],
    "269": ["https://www.ucm.es/english"],
    "275": ["https://www.scu.edu.au/"],
    "241": ["https://www.westernsydney.edu.au/"],
    "240": ["https://www.yorku.ca/international/global-learning/incoming-academic-exchange/"],
    "279": ["https://www.tcd.ie/global/mobility/inbound/"],
    "225": ["https://enweb.lnu.edu.cn/", "https://ie.lnu.edu.cn/info/13193/2202.htm"],
    "218": ["https://www.ugr.es/en/"],
    "219": ["https://www.hacettepe.edu.tr/english/"],
    "191": ["https://www.fjnu.edu.cn/english/7512/list.htm"],
    "186": ["https://oica.nqu.edu.tw/p/450-1003-7908%2Cc0.php?Lang=zh-tw"],
    "tku-programme-mainland-macau-kinmen-115-88b1b8ee97f6": ["https://global.sjtu.edu.cn/en/", "https://english.seiee.sjtu.edu.cn/english/info/8087.htm"],
}


def capture(url, *, key_suffix=None):
    key = hashlib.sha256((url+(key_suffix or '')).encode()).hexdigest()[:24]
    path = STORE / (key + ".json.gz")
    if exists(path):
        return json.loads(gzip.decompress(read_bytes(path)))
    record = dict(id=key, source_url=url, checked_at=datetime.now(timezone.utc).isoformat())
    try:
        response = requests.get(url, timeout=(8, 22), headers={"User-Agent": "UniWayTKUReference/1.0"})
        record.update(http_status=response.status_code, final_url=response.url,
                      sha256=hashlib.sha256(response.content).hexdigest(), bytes=len(response.content),retry_after=response.headers.get('Retry-After'))
        response.raise_for_status()
        extension=urlsplit(url).path.lower()
        if extension.endswith('.pdf') and not response.content.startswith(b'%PDF'):
            raise ValueError('Expected PDF endpoint returned no PDF magic; no document content verified')
        if extension.endswith('.docx') and not response.content.startswith(b'PK'):
            raise ValueError('Expected Word endpoint returned no DOCX ZIP magic; no template content verified')
        if extension.endswith('.xlsx') and not response.content.startswith(b'PK'):
            raise ValueError('Expected workbook endpoint returned no XLSX ZIP magic')
        if extension.endswith('.doc') and not response.content.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
            raise ValueError('Expected legacy Word endpoint returned no OLE compound-file magic')
        if response.content.startswith(b"%PDF"):
            import io
            from pypdf import PdfReader
            record["pages"] = [dict(page=i + 1, text=page.extract_text()) for i, page in enumerate(PdfReader(io.BytesIO(response.content)).pages)]
            record["text"] = "\n".join(p["text"] or "" for p in record["pages"])
            asset = STORE / (key + ".pdf")
            asset.write_bytes(response.content)
            record["local_file"] = asset.name
        elif extension.endswith('.xlsx'):
            import io,zipfile
            from xml.etree import ElementTree
            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            with zipfile.ZipFile(io.BytesIO(response.content)) as workbook:
                shared=[]
                if 'xl/sharedStrings.xml' in workbook.namelist():
                    shared=[''.join(x.itertext()) for x in ElementTree.fromstring(workbook.read('xl/sharedStrings.xml')).findall('s:si',ns)]
                record['sheets']=[]
                for name in sorted(n for n in workbook.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)):
                    rows=[]
                    for row in ElementTree.fromstring(workbook.read(name)).findall('.//s:row',ns):
                        cells=[]
                        for cell in row.findall('s:c',ns):
                            v=cell.find('s:v',ns);value=v.text if v is not None else ''
                            if cell.get('t')=='s' and value:value=shared[int(value)]
                            elif cell.get('t')=='inlineStr':value=''.join(cell.find('s:is',ns).itertext())
                            cells.append((cell.get('r'),value))
                        rows.append(cells)
                    record['sheets'].append(dict(xml_part=name,rows=rows))
                record['paragraphs']=['\t'.join(f'{cell}={value}' for cell,value in row) for sheet in record['sheets'] for row in sheet['rows']]
                record['text']='\n'.join(record['paragraphs'])
            asset=STORE/(key+'.xlsx');asset.write_bytes(response.content);record['local_file']=asset.name
        elif extension.endswith('.doc'):
            asset=STORE/(key+'.doc');asset.write_bytes(response.content);record['local_file']=asset.name
            record.update(text='',content_extraction_status='legacy_DOC_parser_not_available',content_scope='Downloaded OLE Word binary; actual year and application content not verified')
        elif response.content.startswith(b"PK") and urlsplit(response.url).path.lower().endswith(".docx"):
            import io
            import zipfile
            from xml.etree import ElementTree
            with zipfile.ZipFile(io.BytesIO(response.content)) as office:
                root=ElementTree.fromstring(office.read("word/document.xml"))
                record["paragraphs"]=["".join(p.itertext()) for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")]
                record["text"]="\n".join(record["paragraphs"])
            asset=STORE/(key+".docx");asset.write_bytes(response.content)
            record["local_file"]=asset.name
            record["content_type"]="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            record["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
            record["links"] = [dict(title=a.get_text(" ", strip=True), url=urljoin(response.url, a["href"])) for a in soup.select("a[href]")]
            for element in soup.select("script,style,nav,header,footer"):
                element.decompose()
            record["text"] = soup.get_text("\n", strip=True)
            record["paragraphs"] = list(dict.fromkeys(p.get_text(" ", strip=True) for p in soup.select("p,li,td") if len(p.get_text(strip=True)) >= 30))
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    STORE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(record, ensure_ascii=False).encode(), mtime=0))
    return record


def domain(url):
    return urlsplit(url).netloc.casefold().removeprefix("www.")


def allowed_domain(url, allowed):
    candidate=domain(url)
    return any(candidate == host or candidate.endswith("." + host) for host in allowed)


DISCOVER = re.compile(r"incoming|exchange student|international (?:office|relation|student)|accommodation|housing|student life|insurance|courses for exchange|international cooperation|international affairs|global engagement|国際交流|国际学生|國際學生|留学生|交換留学|交換學生|交换生|国際課|國際事務|国际合作|国际交流|intercambio|movilidad|alojamiento|relaciones internacionales|estudiantes internacionales|étudiants internationaux|relations internationales|mobilité|logement|internationales|austausch|wohnen|unterkunft|studieren aus dem ausland|erasmus",re.I)


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    index_path=BUNDLE/'host_census_capture_index.json'
    prior_index={r['id']:r for r in json.loads(index_path.read_text())} if index_path.exists() else {}
    census = json.loads((BUNDLE / "full_census_audit.json").read_text())["schools"]
    profiles = []
    for home in ["cgu", "ntpu"]:
        profiles += [json.loads(line) for line in (BUNDLE.parent / home / "destination_profiles.jsonl").read_text().splitlines() if line.strip()]
    tasks = []
    for row in census:
        variants = [row["school_name"], row.get("english_name", "")]
        matches = [p for p in profiles if any(same_school(p["school_name"], name) for name in variants if name)]
        seeds = list(dict.fromkeys(source["source_url"] for p in matches for source in p.get("sources", [])))[:8]
        seeds += EXTRA_SEEDS.get(row["id"].removeprefix("tku-sister-"), [])
        website = row.get("directory_website")
        if website and website.startswith(("http://", "https://")):
            seeds.append(website.replace("http://", "https://", 1))
        # For the one institution omitted by the directory, use its programme URL.
        if not seeds and row.get("programme_ids"):
            programme_rows = [json.loads(line) for file in ["partners_current.jsonl", "partners_reference.jsonl"] for line in (BUNDLE / file).read_text().splitlines()]
            for p in programme_rows:
                if p["id"] in row["programme_ids"] and p["fields"].get("website", {}).get("value"):
                    value = p["fields"]["website"]["value"]
                    if value.startswith(("http://", "https://")):
                        seeds.append(value)
        tasks.append(dict(id=row["id"], school_name=row["school_name"], english_name=row.get("english_name"),
                          country=row["country"], directory_url=row["directory_url"], seeds=list(dict.fromkeys(seeds)),
                          discovery="TKU directory / same institution's CGU-NTPU official host URLs; no outbound transfer"))
    urls = sorted({url for task in tasks for url in task["seeds"]})
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        captures = dict(zip(urls, pool.map(capture, urls)))
    # One bounded same-host step discovers exchange/life pages, never logs in.
    for task in tasks:
        candidates = []
        allowed = {domain(url) for url in task["seeds"]}
        for seed in task["seeds"]:
            for link in captures[seed].get("links", []):
                label = link["title"].casefold()
                if not allowed_domain(link["url"],allowed) or not link["url"].startswith("https://"):
                    continue
                if DISCOVER.search(label):
                    if not re.search(r"outgoing|outbound|login|log in|apply now|form|申請系統", label):
                        candidates.append(link["url"])
        task["discovered_urls"] = list(dict.fromkeys(candidates))[:5]
    discovered = sorted({url for t in tasks for url in t["discovered_urls"]} - set(captures))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        captures.update(dict(zip(discovered, pool.map(capture, discovered))))
    # International-office and life entry pages often sit one level below a
    # homepage. Follow two more bounded levels, keeping every rejected/error page.
    for depth in range(2):
        new_urls = set()
        for task in tasks:
            allowed = {domain(url) for url in task["seeds"]}
            candidates = []
            for url in dict.fromkeys(task["seeds"] + task["discovered_urls"]):
                for link in captures[url].get("links", []):
                    label=link["title"].casefold()
                    if not allowed_domain(link["url"],allowed) or not link["url"].startswith("https://"):
                        continue
                    if DISCOVER.search(label):
                        if not re.search(r"outgoing|outbound|login|log in|apply now|申請系統",label):
                            candidates.append(link["url"])
            add = [url for url in dict.fromkeys(candidates) if url not in task["seeds"]+task["discovered_urls"]][:5]
            task["discovered_urls"] += add
            new_urls.update(set(add)-set(captures))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            urls=sorted(new_urls)
            captures.update(dict(zip(urls,pool.map(capture,urls))))
        print(json.dumps(dict(depth=depth+2,added_urls=len(new_urls))),flush=True)
    # Keep prior successful captures when discovery order changes, including
    # separately reviewed attachment sources on the same official host.
    for path in stored_captures(STORE):
        old=json.loads(gzip.decompress(read_bytes(path)))
        captures.setdefault(old['source_url'],old)
    for task in tasks:
        allowed={domain(url) for url in task['seeds']}
        task['discovered_urls'] += [url for url in captures if allowed_domain(url,allowed)
                                   and url not in task['seeds']+task['discovered_urls']]
        task["sources"] = [{k: captures[url].get(k) for k in ["id", "source_url", "final_url", "http_status", "checked_at", "sha256", "title", "error"]}
                           for url in dict.fromkeys(task["seeds"] + task["discovered_urls"])]
        # A refresh of bounded seed discovery must not discard later retries,
        # manually verified replacement domains or their failed-attempt history.
        present={s['id'] for s in task['sources']}
        task['sources'] += [s for s in prior_index.get(task['id'],{}).get('sources',[]) if s['id'] not in present]
    (BUNDLE / "host_census_capture_index.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(institutions=len(tasks), source_urls=len(captures), opened=sum("error" not in c for c in captures.values()),
                         errors=sum("error" in c for c in captures.values()), with_sources=sum(bool(t["sources"]) for t in tasks))))


if __name__ == "__main__":
    main()
