from pathlib import Path
import re
pattern=re.compile(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>>[^\n]+\n',re.S)
p=Path('src/exchange_info/api.py');s=p.read_text()
def api_merge(m):
 ours,theirs=m.group(1),m.group(2)
 if 'reviewed_image_coverage' in ours:
  return ours+'\n'.join(theirs.splitlines()[1:])+'\n'
 return theirs.replace('school_location(partner, location)','school_location(partner, location, resolved_data_dir)')
s=pattern.sub(api_merge,s).replace('campus_location(partner, location)','campus_location(partner, location, resolved_data_dir)');p.write_text(s)
for filename in ('src/exchange_info/static/app.js','src/exchange_info/static/index.html'):
 p=Path(filename);p.write_text(pattern.sub(lambda m:m.group(1),p.read_text()))
p=Path('src/exchange_info/static/app.js');s=p.read_text();s=s.replace('function schoolVisualRecordFor(schoolName, country = null) {','''function schoolVisualRecordFor(schoolName, country = null) {
  const home = state.dashboard?.school_name;
  if (home === "國立中央大學") {
    return state.ncuSchoolImages.find(row => visualSchoolIdentity(row.school_name) === visualSchoolIdentity(schoolName)
      && visualCountryIdentity(row.country) === visualCountryIdentity(country)) || { status: "license_unverified" };
  }
  if (home === "國立中正大學") {
    const partner = state.dashboard.partner_universities.find(row => visualSchoolIdentity(row.school_name) === visualSchoolIdentity(schoolName)
      && visualCountryIdentity(row.country) === visualCountryIdentity(country));
    if (partner?.reference_data?.ccu_completion) {
      let photo;
      try { photo = JSON.parse(partner.reference_data.ccu_campus_assets || "{}").photo; } catch (_) { /* Attribution stays absent. */ }
      return photo && partner.image_status === "verified" ? { status: "verified", local_path: partner.image_url,
        license_name: photo.license_name, license_url: photo.license_url,
        note: `攝影：${photo.artist} · ${photo.license_name} · ${photo.campus_caption}` } : { status: "missing" };
    }
  }''',1)
# Keep all frontend entrypoints on one integration version; sidecar content version remains its own.
s=s.replace('20261011-source-recovery-1','20261011-integration-1');p.write_text(s)
for name in ('index.html','styles.css'):
 p=Path('src/exchange_info/static')/name;s=p.read_text().replace('20261011-source-recovery-1','20261011-integration-1');p.write_text(s)
p=Path('src/exchange_info/ncu_completion.py');s=p.read_text().replace('def campus_location(partner, fallback):','''def campus_location(partner, fallback, data_dir=None):
    if data_dir is not None:
        from .university_locations import local_location_override
        operator = local_location_override(data_dir, partner.school_name, partner.country)
        if operator is not None:
            return operator''');p.write_text(s)
p=Path('src/exchange_info/university_locations.py');s=p.read_text();s=s.replace('from datetime import datetime','from datetime import datetime\nfrom functools import lru_cache')
start=s.index('    records: dict[tuple[str, str], UniversityLocation] = {}\n',s.index('def load_university_locations'))
end=s.index('\n\ndef public_location',start)
s=s[:start]+'''    records: dict[tuple[str, str], UniversityLocation] = {}
    for path in (LOCATION_CATALOG, Path(data_dir) / "processed" / "university_locations.jsonl"):
        records.update(_read_location_file(path))
    return VisualRecordIndex(records)


def _read_location_file(path: Path) -> dict:
    records = {}
    if not path.exists():
        return records
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = None
        try:
            raw = json.loads(line)
            record = UniversityLocation.model_validate(raw)
        except (ValueError, ValidationError):
            logger.warning("Invalid university location in %s at row %d", path.name, number)
            if isinstance(raw, dict) and isinstance(raw.get("school_name"), str):
                country = raw.get("country") if isinstance(raw.get("country"), str) else None
                record = UniversityLocation(school_name=raw["school_name"], country=country, geocode_status="needs_review")
            else:
                continue
        records[location_key(record.school_name, record.country)] = record
    return records


@lru_cache(maxsize=4)
def _operator_locations(path: Path, mtime_ns: int, size: int):
    return VisualRecordIndex(_read_location_file(path))


def local_location_override(data_dir: Path, school_name: str, country: str | None = None) -> UniversityLocation | None:
    """A local review (including pending/invalid) precedes a school's sidecar."""
    path = Path(data_dir) / "processed/university_locations.jsonl"
    if not path.exists():
        return None
    stat = path.stat()
    records = _operator_locations(path, stat.st_mtime_ns, stat.st_size)
    if records.get((school_name, country or "")) is None:
        return None
    return public_location(records, school_name, country).model_copy(update={"school_name": school_name, "country": country})
'''+s[end:];p.write_text(s)
