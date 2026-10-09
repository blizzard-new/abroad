"""Resumable, offline NTU destination research. Outputs candidates for review.

This never writes a production service or the bundled catalogs. ROR identifies
an institution by its official domain AND country; Wikidata supplies the school
point (never the ROR city centre) and Commons supplies attributed photographs.
Official student-life excerpts retain their page, retrieval time and year scope.
Run with .venv/bin/python -m scripts.research_ntu_destinations /tmp/ntu-research.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import threading
import time
import unicodedata
from urllib.parse import urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup
from PIL import UnidentifiedImageError
from pypdf import PdfReader
import requests

from exchange_info.life_context import OFFICIAL_THEME_PATTERNS
from exchange_info.school_image_collector import _prepare_image_bytes
from scripts.refresh_university_locations import COUNTRIES

ROOT = Path(__file__).resolve().parents[1]
NTU = ROOT / "src/exchange_info/official_data/ntu"
UA = "UniWayExchangeCatalog/1.0 (public university source verification)"
COUNTRY_CODES = COUNTRIES | {"希臘": "GR", "冰島": "IS", "盧森堡": "LU", "科索沃": "XK"}
# University systems have no single destination campus. Do not choose an HQ.
SYSTEMS = {"加州大學", "加州州立大學"}


def host(url: str) -> str:
    return re.sub(r"^www\d*\.", "", (urlsplit(url).hostname or "").lower())


def related_domain(left: str, right: str) -> bool:
    return bool(left and right and (left == right or left.endswith("." + right) or right.endswith("." + left)))


def name_key(value: str) -> str:
    value = re.sub(r"\([^()]*\)", "", value).casefold()
    value = re.sub(r"^the\s+", "", value)
    value = unicodedata.normalize("NFKD", value)
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def https_url(url: str) -> str:
    return "https://" + url[7:] if url.startswith("http://") else url


def json_line(record: dict) -> str:
    # str.splitlines also treats these Unicode characters as row delimiters.
    return re.sub(r"[\x0b\x0c\x1c-\x1e\x85\u2028\u2029]", lambda m: "\\u%04x" % ord(m[0]),
                  json.dumps(record, ensure_ascii=False)) + "\n"


def repair_utf8(text: str) -> str:
    """Recover UTF-8 pages previously decoded with requests' Latin-1 default."""
    def decode(match):
        try:
            return match[0].encode("latin-1").decode("utf-8")
        except UnicodeError:
            return match[0]
    return re.sub(r"(?:[\xc2-\xf4][\x80-\xbf]{1,3})+", decode, text)


def identify(row: dict, candidates: list[dict]) -> dict | None:
    """Reject country/domain conflicts and ambiguous institutions sharing a host."""
    expected = COUNTRY_CODES.get(row["country"])
    domain = host(row["official_website"])
    matches = []
    for c in candidates:
        countries = {p["geonames_details"]["country_code"] for p in c.get("locations", [])}
        domains = c.get("domains", []) + [host(x["value"]) for x in c.get("links", []) if x.get("type") == "website"]
        if (c.get("status") == "active" and "education" in c.get("types", [])
                and expected and countries == {expected}
                and any(related_domain(domain, d) for d in domains)):
            matches.append(c)
    exact = [c for c in matches if any(name_key(n["value"]) == name_key(row["research_name"])
                                      for n in c.get("names", []))]
    if len(exact) == 1:
        return exact[0]
    primary = [c for c in matches if domain in c.get("domains", [])]
    if len(primary) == 1 and not re.search(r"campus|faculty of|school of|學院|研究科|學部", row["research_name"] + row["school_name"], re.I):
        return primary[0]
    # An institute, faculty or branch must match its own registry name.
    if re.search(r"school of|faculty of|college of|campus|學院|研究科|學部", row["research_name"] + row["school_name"], re.I):
        return None
    return matches[0] if len(matches) == 1 else None


def distance_km(lat: float, lng: float, city: dict) -> float:
    a = math.sin(math.radians(lat - city["lat"]) / 2) ** 2
    a += math.cos(math.radians(lat)) * math.cos(math.radians(city["lat"])) * math.sin(math.radians(lng - city["lng"]) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(a)))


class Research:
    def __init__(self, output: Path, *, refresh_html: bool = False, offline: bool = False, retry_errors: bool = False):
        self.output = output
        self.cache = output / "sources"
        self.cache.mkdir(parents=True, exist_ok=True)
        (output / "photos").mkdir(exist_ok=True)
        self.local = threading.local()
        self.refresh_html = refresh_html
        self.offline = offline
        self.retry_errors = retry_errors
        archive_path = output / "archive-sources.json.gz"
        self.archive = json.loads(gzip.decompress(archive_path.read_bytes())) if archive_path.exists() else {}

    def prior_source(self, url: str, attempt: dict) -> dict:
        prior = attempt.get("last_success") or self.archive.get(url)
        if prior:
            return prior | {"latest_attempt": {k: attempt.get(k) for k in ("checked_at", "http_status", "error")}}
        return attempt

    def fetch(self, url: str, *, max_bytes: int = 8_000_000) -> dict:
        if urlsplit(url).scheme != "https":
            return {"url": url, "error": "HTTPS required"}
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".json.gz")
        if path.exists():
            cached = json.loads(gzip.decompress(path.read_bytes()))
            for field in ("text", "title"):
                if cached.get(field):
                    cached[field] = repair_utf8(cached[field])
            if cached.get("error") and not self.retry_errors:
                return self.prior_source(url, cached)
            if not cached.get("error") and not (self.refresh_html and "html" in cached.get("content_type", "")
                    and "paragraphs" not in cached):
                return cached
        if self.offline:
            return self.archive.get(url) or {"url": url, "error": "Offline cache has no source"}
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
            self.local.session.headers["User-Agent"] = UA
            self.local.session.max_redirects = 4
        result = {"url": url, "checked_at": datetime.now(timezone.utc).isoformat()}
        try:
            started = time.monotonic()
            with self.local.session.get(url, timeout=(6, 16), stream=True) as response:
                result.update(final_url=response.url, http_status=response.status_code,
                              content_type=response.headers.get("Content-Type", ""))
                response.raise_for_status()
                if urlsplit(response.url).scheme != "https":
                    raise ValueError("Insecure redirect")
                parts, size = [], 0
                for part in response.iter_content(64_000):
                    size += len(part)
                    if size > max_bytes or time.monotonic() - started > 40:
                        raise ValueError("Response exceeds research bounds")
                    parts.append(part)
                content = b"".join(parts)
            result["sha256"] = hashlib.sha256(content).hexdigest()
            if "json" in result["content_type"]:
                result["json"] = json.loads(content)
            elif content.startswith(b"%PDF"):
                result["text"] = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(content)).pages[:30])
                result["title"] = urlsplit(response.url).path.rsplit("/", 1)[-1]
            elif "image" in result["content_type"]:
                # Photos stay separate from the compressed textual evidence.
                asset = self.cache / (result["sha256"] + ".image")
                asset.write_bytes(content)
                result["asset_path"] = asset.name
            else:
                # HTML meta charsets matter; requests defaults unlabelled HTML
                # to Latin-1, which silently corrupts Chinese/Japanese pages.
                soup = BeautifulSoup(content, "html.parser")
                result["title"] = soup.title.get_text(" ", strip=True) if soup.title else "Official student information"
                result["links"] = [{"url": urljoin(response.url, a["href"]), "text": a.get_text(" ", strip=True)}
                                   for a in soup.select("a[href]")][:2500]
                for node in soup.select("script,style,nav,header,footer,form,noscript"):
                    node.decompose()
                main = soup.find("main") or soup.find("article") or soup
                result["text"] = main.get_text("\n", strip=True)[:150_000]
                result["paragraphs"] = [node.get_text(" ", strip=True) for node in main.find_all(["p", "li", "tr"])
                                        if 40 <= len(node.get_text(" ", strip=True)) <= 1400][:1800]
        except (requests.RequestException, ValueError, OSError) as error:
            result["error"] = str(error)[:350]
            if path.exists():
                previous = json.loads(gzip.decompress(path.read_bytes()))
                if not previous.get("error"):
                    result["last_success"] = previous
        temp = path.with_suffix(".tmp-" + str(threading.get_ident()))
        temp.write_bytes(gzip.compress(json.dumps(result, ensure_ascii=False).encode(), mtime=0))
        temp.replace(path)
        return self.prior_source(url, result) if result.get("error") else result

    def get_json(self, base: str, **params):
        record = self.fetch(base + ("?" + urlencode(params) if params else ""))
        return record.get("json", {})

    def identity(self, row: dict) -> dict:
        result = {"school_name": row["school_name"], "country": row["country"], "location": None, "photo": None}
        if row["school_name"] in SYSTEMS:
            return result | {"note": "多校區交換體系；錄取校區未定，不以總部代替目的地。"}
        domain = host(row["official_website"])
        # ROR indexes institution domains, not necessarily their language subdomain.
        query_host = domain
        if len(domain.split(".")) > 3 and domain.split(".")[-2] in {"edu", "ac"}:
            query_host = ".".join(domain.split(".")[-3:])
        candidates = self.get_json("https://api.ror.org/v2/organizations", **{"query.advanced": "domains:" + query_host}).get("items", [])
        candidate = identify(row, candidates)
        if candidate is None:
            candidates = self.get_json("https://api.ror.org/v2/organizations", query=re.sub(r"\([^()]*\)", "", row["research_name"]).strip()).get("items", [])
            candidate = identify(row, candidates)
        if candidate is None:
            return result | {"note": "無唯一的 ROR 官方網域與國家身分對應。"}
        result["ror_id"] = candidate["id"]
        result["ror_names"] = candidate.get("names", [])
        result["domains"] = candidate.get("domains", [])
        ids = [x for x in candidate.get("external_ids", []) if x["type"] == "wikidata"]
        qid = (ids[0].get("preferred") or ids[0]["all"][0]) if ids else None
        if not qid or not re.fullmatch(r"Q\d+", qid):
            # Discover a candidate by name, then require the same official
            # domain and an exact registry label/alias. A name alone is not proof.
            found = self.get_json("https://www.wikidata.org/w/api.php", action="wbsearchentities", format="json",
                                  search=re.sub(r"\([^()]*\)", "", row["research_name"]).strip(), language="en", type="item", limit=5)
            matching = []
            names = {name_key(n["value"]) for n in candidate.get("names", [])} | {name_key(row["research_name"])}
            for match in found.get("search", []):
                entity = self.get_json(f"https://www.wikidata.org/wiki/Special:EntityData/{match['id']}.json").get("entities", {}).get(match["id"], {})
                labels = [x["value"] for x in entity.get("labels", {}).values()]
                sites = [x["mainsnak"]["datavalue"]["value"] for x in entity.get("claims", {}).get("P856", [])
                         if "datavalue" in x.get("mainsnak", {}) and x.get("rank") != "deprecated"]
                if any(name_key(n) in names for n in labels) and any(related_domain(host(u), domain) for u in sites):
                    matching.append(match["id"])
            if len(matching) != 1:
                return result | {"note": "ROR 無 Wikidata 校級對應，名稱與官網交叉查核亦未取得唯一身分。"}
            qid = matching[0]
        result["wikidata_id"] = qid
        entity = self.get_json(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json").get("entities", {}).get(qid, {})
        claims = entity.get("claims", {})
        values = lambda prop: [x["mainsnak"]["datavalue"]["value"] for x in claims.get(prop, [])
                               if x.get("rank") != "deprecated" and "datavalue" in x.get("mainsnak", {})]
        statements = [c for c in claims.get("P625", []) if c.get("rank") != "deprecated" and "datavalue" in c.get("mainsnak", {})]
        preferred = [c for c in statements if c.get("rank") == "preferred"]
        values625 = [c["mainsnak"]["datavalue"]["value"] for c in preferred or statements]
        points = {(p["latitude"], p["longitude"]) for p in values625 if p.get("globe", "").endswith("Q2")}
        # Duplicate statements for the same building can differ by a few metres.
        # Distinct campuses remain unresolved; never average their coordinates.
        if len(points) > 1 and all(distance_km(a, b, {"lat": c, "lng": d}) < .2 for a, b in points for c, d in points):
            points = {sorted(points)[0]}
        if len(points) == 1:
            lat, lng = next(iter(points))
            cities = [p["geonames_details"] for p in candidate["locations"]]
            nearest = min(cities, key=lambda c: distance_km(lat, lng, c))
            if distance_km(lat, lng, nearest) < 100:
                result["location"] = {"school_name": row["school_name"], "country": row["country"], "city": nearest["name"],
                    "latitude": lat, "longitude": lng, "geocode_status": "verified", "precision": "representative",
                    "source_url": f"https://www.wikidata.org/wiki/{qid}", "identity_source_url": candidate["id"],
                    "geocoded_at": datetime.now(timezone.utc).isoformat(),
                    "note": "校級代表位置：官方網域與國家已比對 ROR，學校座標取自 Wikidata P625；實際交換校區以錄取通知為準。"}
        images = values("P18")
        for image in images[:3]:
            photo = self.photo(row, qid, image)
            if photo:
                result["photo"] = photo
                break
        result["note"] = "ROR 身分已比對；照片仍須視覺核對。" if result["photo"] else "ROR 身分已比對；未取得可用授權照片。"
        return result

    def photo(self, row: dict, qid: str, filename: str) -> dict | None:
        metadata = self.get_json("https://commons.wikimedia.org/w/api.php", action="query", format="json",
            titles="File:" + filename, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=1600)
        pages = list(metadata.get("query", {}).get("pages", {}).values())
        info = pages[0].get("imageinfo", [{}])[0] if pages else {}
        ext = info.get("extmetadata", {})
        def plain(key):
            value = ext.get(key, {}).get("value", "")
            return BeautifulSoup(value, "html.parser").get_text(" ", strip=True) if "<" in value else value.strip()
        license_name, license_url = plain("LicenseShortName"), plain("LicenseUrl")
        if not re.search(r"^(CC BY(?:-SA)? [\d.]+|CC0|Public domain)$", license_name):
            return None
        unknown_artists = {"", "see below", "unknown", "n/a", "not provided"}
        artist = plain("Artist")
        if artist.casefold() in unknown_artists:
            artist = plain("Attribution")
        if license_name.startswith("CC BY") and artist.casefold() in unknown_artists:
            return None
        if not info.get("url") or not info.get("descriptionurl"):
            return None
        source = info.get("thumburl") or info["url"]
        image = self.fetch(source)
        if "asset_path" not in image:
            # Commons thumbnail endpoints sometimes impose stricter rate limits.
            source = info["url"]
            image = self.fetch(source)
        if "asset_path" not in image:
            return None
        try:
            prepared = _prepare_image_bytes((self.cache / image["asset_path"]).read_bytes(), allow_wide=True)
        except (OSError, ValueError, UnidentifiedImageError):
            return None
        if not prepared:
            return None
        content, width, height = prepared
        digest = hashlib.sha256(content).hexdigest()
        asset_name = "ntu-" + hashlib.sha256((row["country"] + "|" + row["school_name"]).encode()).hexdigest()[:14] + ".jpg"
        (self.output / "photos" / asset_name).write_bytes(content)
        return {"school_name": row["school_name"], "country": row["country"], "official_page_url": info["descriptionurl"],
            "image_source_url": source, "local_path": f"/static/assets/schools/{asset_name}?v={digest[:12]}",
            "width": width, "height": height, "content_hash": digest, "checked_at": image["checked_at"], "status": "candidate",
            "note": f"攝影：{artist} · {license_name} · 已裁切為 16:9；校級照片，交換校區須核對。",
            "artist": artist, "license_name": license_name, "license_url": license_url,
            "identity_source_url": f"https://www.wikidata.org/wiki/{qid}" if re.fullmatch(r"Q\d+", qid) else None,
            "description": plain("ImageDescription")[:1500]}

    def more_photos(self, row: dict, identity: dict) -> dict:
        qid = identity.get("wikidata_id")
        if not qid or identity.get("photo"):
            return identity
        entity = self.get_json(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json").get("entities", {}).get(qid, {})
        candidates = []
        article = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
        if article:
            page = self.get_json("https://en.wikipedia.org/w/api.php", action="query", format="json", titles=article,
                                 prop="pageimages", piprop="name", pilicense="free")
            candidates += [p["pageimage"] for p in page.get("query", {}).get("pages", {}).values() if p.get("pageimage")]
        categories = [c["mainsnak"]["datavalue"]["value"] for c in entity.get("claims", {}).get("P373", [])
                      if "datavalue" in c.get("mainsnak", {})]
        for category in categories[:1]:
            page = self.get_json("https://commons.wikimedia.org/w/api.php", action="query", format="json", list="categorymembers",
                                 cmtitle="Category:" + category, cmtype="file", cmlimit=100)
            candidates += [p["title"].removeprefix("File:") for p in page.get("query", {}).get("categorymembers", [])]
        negative = re.compile(r"logo|seal|emblem|portrait|headshot|\.svg$|\.pdf$|\.ogg$|\.webm$|flag|coat.of.arms|map\b|sport|football|team|president|rector|flower|bee\b|medal|plaque|poster|concert|cyclocross|actress|parade|cherry.blossom", re.I)
        candidates = [f for f in dict.fromkeys(candidates) if not negative.search(f)]
        candidates.sort(key=lambda f: bool(re.search(r"campus|building|main|aerial|entrance|library", f, re.I)), reverse=True)
        for filename in candidates[:10]:
            photo = self.photo(row, qid, filename)
            if photo and not negative.search(photo["description"]):
                return identity | {"photo": photo, "note": "照片取自已比對校級身分的百科／Commons 校級分類；仍須視覺核對。"}
        return identity

    def official_photo(self, row: dict, identity: dict) -> dict:
        if identity.get("photo"):
            return identity
        from exchange_info.school_image_collector import extract_image_candidates
        website = https_url(row["official_website"])
        # This fallback accepts only actual image bytes from a current official
        # page. It does not use screenshots, search thumbnails or insecure TLS.
        try:
            response = requests.get(website, timeout=(6, 15), headers={"User-Agent": UA})
            response.raise_for_status()
            if not response.url.startswith("https://") or len(response.content) > 4_000_000:
                return identity
            candidates = extract_image_candidates(response.text, response.url)
            for candidate in candidates[:7]:
                if re.search(r"logo|portrait|headshot|icon|event|news|alumni|sport", candidate.context + candidate.url, re.I):
                    continue
                image = self.fetch(https_url(candidate.url))
                if "asset_path" not in image:
                    continue
                try:
                    prepared = _prepare_image_bytes((self.cache / image["asset_path"]).read_bytes())
                except (OSError, ValueError, UnidentifiedImageError):
                    continue
                if not prepared:
                    continue
                content, width, height = prepared
                digest = hashlib.sha256(content).hexdigest()
                asset_name = "ntu-" + hashlib.sha256((row["country"] + "|" + row["school_name"]).encode()).hexdigest()[:14] + ".jpg"
                (self.output / "photos" / asset_name).write_bytes(content)
                photo = {"school_name": row["school_name"], "country": row["country"], "official_page_url": response.url,
                    "image_source_url": image["final_url"], "local_path": f"/static/assets/schools/{asset_name}?v={digest[:12]}",
                    "width": width, "height": height, "content_hash": digest, "checked_at": image["checked_at"], "status": "candidate",
                    "note": "圖片來源：合作校官網；已裁切為16:9；照片校區仍須核對。", "description": candidate.context[:1500]}
                return identity | {"photo": photo}
        except requests.RequestException:
            pass
        return identity

    def life(self, row: dict, seeds: list[str]) -> dict:
        evidence, pages, seen = [], [], set()
        official_host = host(row["official_website"])
        urls = [https_url(u) for u in seeds if related_domain(host(u), official_host) and urlsplit(u).scheme in {"http", "https"}]
        urls.append(https_url(row["official_website"]))
        archived = [https_url(u) for u, p in self.archive.items() if row["school_name"] in p.get("school_names", [])
                    and related_domain(host(p.get("final_url", "")), official_host)]
        archived = list(dict.fromkeys(archived))
        archived.sort(key=lambda u: not bool(re.search(r"housing|accommodation|living|student|incoming|exchange|factsheet|fact.sheet|guide", u, re.I)))
        urls = archived[:6] + urls
        queue = list(dict.fromkeys(urls))[:6]
        themes = {k: re.compile(v, re.I) for k, v in OFFICIAL_THEME_PATTERNS.items()}
        themes["climate"] = re.compile(r"\b(?:weather|climate|temperatures?|rainfall|snowfall)\b|氣候|気候|天氣|天候|날씨", re.I)
        extra = {
            "housing": r"logement|hébergement|alojamiento|alojamento|moradia|résidence|宿舎|宿舍|住宿",
            "cost": r"coût|costo|custo|lebenshaltung|loyer|alquiler|budget|費用|费用|生活费",
            "food": r"cafétéria|restauration|restaurante|comedor|mensa|食堂|餐饮|餐廳",
            "transport": r"transporte|métro|autobus|mobilité|verkehr|アクセス|交通",
            "social": r"associations étudiantes|vie associative|vereine|社团|社團|サークル",
            "safety": r"assurance|seguro|santé|salud|saúde|krankenversicherung|保険|保险|醫療",
            "campus_culture": r"étudiants internationaux|estudiantes internacionales|留学生|国际学生|國際學生",
        }
        themes.update({k: re.compile(themes[k].pattern + "|" + pattern, re.I) for k, pattern in extra.items()})
        while queue and len(pages) < 7:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            page = self.fetch(url)
            pages.append({k: page.get(k) for k in ("url", "final_url", "checked_at", "http_status", "sha256", "error", "title", "latest_attempt")})
            if page.get("error") or not related_domain(host(page.get("final_url", "")), official_host):
                continue
            text = page.get("text", "")
            if re.search(r"just a moment|verify you are human|access denied|enable javascript and cookies", text, re.I) and len(text) < 1200:
                continue
            lines = [re.sub(r"\s+", " ", s).strip() for s in page.get("paragraphs", []) or text.splitlines()]
            # Preserve a full bounded paragraph, not a keyword detached from its qualification.
            snippets = [s for s in lines if 55 <= len(s) <= 1400
                        and (len(s.split()) >= 8 or len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", s)) >= 25)]
            snippets = [s for s in snippets if not re.search(r"copyright|all rights reserved|cookie policy|privacy policy|cookies on|©", s, re.I)]
            years = sorted(set(re.findall(r"\b20(?:2[0-9]|3[0-9])(?:\s*[/–-]\s*(?:20)?\d\d)?\b", text)))
            scope = "官網原文節錄；校區、交換生適用性及費用期間須核對原頁，未認定為116-1招生條件。"
            if years:
                scope += " 原頁提及：" + "、".join(years[:10]) + "。"
            for theme, pattern in themes.items():
                current = [e for e in evidence if e["theme"] == theme]
                ranked = [s for s in snippets if pattern.search(s)]
                # Costs need currency/amount context; broad generic tuition mentions are not a living budget.
                if theme == "cost":
                    ranked = [s for s in ranked if re.search(r"living|rent|budget|monthly|per month|meal|insurance|lebenshaltung|loyer|mensuel|par mois|alquiler|por mes|custo|生活費|生活费|家賃|생활비", s, re.I)]
                    ranked = [s for s in ranked if not re.search(r"cover(?:age)?.*(?:medical treatment|\d.*euros)|(?:medical treatment|coverage).*\d", s, re.I)]
                ranked.sort(key=lambda s: (bool(re.search(r"\d|€|£|\$", s)), bool(re.search(r"exchange|incoming|international students|交換|留学", s, re.I))), reverse=True)
                for excerpt in ranked[:3]:
                    if len(current) >= 12 or any(e["text"] == excerpt for e in current):
                        break
                    item = {"theme": theme, "kind": "official", "text": excerpt, "original_text": excerpt,
                        "original_excerpt": True, "translation_status": "pending",
                        "sources": [{"title": page.get("title") or row["research_name"], "url": page["final_url"]}],
                        "checked_at": page["checked_at"], "scope": scope}
                    evidence.append(item)
                    current.append(item)
            # Follow useful official links rather than researching a Chinese display-name string.
            links = [a for a in page.get("links", []) if related_domain(host(a["url"]), official_host)
                     and a["url"].startswith("https://") and re.search(r"housing|accommodation|living.cost|student.life|incoming|exchange|international.students|campus.life|logement|alojamiento|wohnheim|宿舍|住宿|English|/en/$", a["url"] + " " + a["text"], re.I)]
            for link in sorted(links, key=lambda a: not bool(re.search(r"housing|accommodation|living.cost|student.life", a["url"], re.I)))[:4]:
                if link["url"] not in seen and link["url"] not in queue:
                    queue.append(link["url"])
        notes = ["已離線擷取合作校官網原文。查閱日期不等於內容更新日；2027/28費用、住宿名額及校區仍須確認。"]
        if any((p.get("latest_attempt") or {}).get("error") for p in pages):
            notes.append("部分官網本次連線失敗，保留上次成功取得的原文與原查閱日期；不代表已重新確認最新內容。")
        def priority(e):
            text, theme = e["text"], e["theme"]
            specific = (theme == "cost" and bool(re.search(r"monthly living|living expenses|monthly rent|rent.*\d|\d.*per month|lebenshaltung", text, re.I)))
            specific |= (theme == "housing" and bool(re.search(r"not provide|not guaranteed|limited|dormitor|residence halls?|home.stay|住宿|宿舍", text, re.I)))
            return specific, bool(re.search(r"\d|€|£|\$", text)), bool(re.search(r"exchange|incoming|international students|交換|留学", text, re.I))
        evidence = [e for theme in themes for e in sorted((e for e in evidence if e["theme"] == theme), key=priority, reverse=True)[:3]]
        return {"school_name": row["school_name"], "country": row["country"],
                "checked_at": datetime.now(timezone.utc).isoformat(), "status": "partial" if evidence else "unavailable",
                "evidence": evidence, "notes": notes,
                "location_signature": "", "extraction_version": 3, "pages": pages}


def life_seeds() -> dict:
    snapshot = json.loads(gzip.decompress((ROOT / "sources/ntu/2026-10-08-import.json.gz").read_bytes()))
    rows = [json.loads(line) for line in snapshot["files"]["verification/partners-116-1-updated-candidates.jsonl"].splitlines()]
    output = {}
    for r in rows:
        fields = r.get("latest_verification", {}).get("fields", {})
        evidence = [e for key in ("housing", "cost", "insurance_visa", "courses", "calendar", "documents")
                    for e in fields.get(key, {}).get("best_evidence", [])]
        output[r["partner"]["school_name"]] = list(dict.fromkeys(e["source_url"] for e in evidence))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--phase", choices=("identity", "life", "photos"), default="identity")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry", action="store_true", help="Re-extract using the cached sources and revised discovery rules")
    parser.add_argument("--refresh-html", action="store_true", help="Re-read old HTML caches to preserve inline links and full paragraphs")
    parser.add_argument("--offline", action="store_true", help="Use preserved source records only")
    parser.add_argument("--retry-errors", action="store_true", help="Retry failed source requests after connectivity is restored")
    args = parser.parse_args()
    research = Research(args.output, refresh_html=args.refresh_html, offline=args.offline, retry_errors=args.retry_errors)
    rows = [json.loads(line) for line in (NTU / "partner_research.jsonl").read_text().splitlines()]
    seeds = life_seeds() if args.phase == "life" else {}
    output = args.output / (args.phase + ".jsonl")
    existing = {r["school_name"]: r for r in map(json.loads, output.read_text().strip().split("\n"))} if output.exists() else {}
    todo = [r for r in rows if args.retry or r["school_name"] not in existing][:args.limit]
    identities = {r["school_name"]: r for r in map(json.loads, (args.output / "identity.jsonl").read_text().strip().split("\n"))} if args.phase == "photos" else {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        action = {"identity": research.identity, "life": research.life, "photos": research.more_photos}[args.phase]
        tasks = {pool.submit(action, row,
                            *([seeds.get(row["school_name"], [])] if args.phase == "life" else
                              [identities[row["school_name"]]] if args.phase == "photos" else [])): row for row in todo}
        for i, future in enumerate(as_completed(tasks), 1):
            row = tasks[future]
            try:
                record = future.result()
            except Exception as error:
                record = {"school_name": row["school_name"], "country": row["country"], "error": str(error)[:350]}
            existing[row["school_name"]] = record
            temp = output.with_suffix(".tmp")
            temp.write_text("".join(json_line(existing[r["school_name"]]) for r in rows if r["school_name"] in existing))
            temp.replace(output)
            print(json.dumps({"processed": i, "total": len(todo), "school": row["school_name"],
                              "located": bool(record.get("location")), "photo": bool(record.get("photo")),
                              "life_evidence": len(record.get("evidence", [])), "error": record.get("error")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
