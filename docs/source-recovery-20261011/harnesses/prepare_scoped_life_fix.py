from pathlib import Path
import os,sys
root=Path(sys.argv[1])/'src/exchange_info'
def replace(name,text):
 p=root/name;t=p.with_name(p.name+'.memory-fix');t.write_text(text);os.replace(t,p)
ncu=(root/'ncu_student_view.py').read_text()
a=ncu.index('def _json_array_items(');b=ncu.index('\ndef _iter_audit_rows',a)
replace('json_stream.py','"""Incremental readers for reviewed, immutable source bundles."""\nimport json\n\n\n'+ncu[a:b].replace('_json_array_items','json_array_items'))
replace('ncu_student_view.py',ncu[:a]+'from .json_stream import json_array_items as _json_array_items\n\n'+ncu[b:])
ccu=(root/'ccu_overseas.py').read_text().replace('import re\n','import re\nimport threading\nfrom pathlib import Path\nfrom .json_stream import json_array_items\n')
a=ccu.index('@lru_cache(maxsize=1)\ndef reviewed_rows()');b=ccu.index('\ndef apply_overseas_review',a)
old=ccu[a:b]
start=old.index('        if set(row["fields"])');end=old.index('    return {row[')
validation='\n'.join(line[4:] if line.startswith('    ') else line for line in old[start:end].splitlines())
new='''def _validate_reviewed_row(row):
'''+validation+'''


def _selected_reviewed_rows(bundle, page=None):
    rows = {}
    identities = set()
    count = 0
    with (bundle / "overseas-reviewed-fields.json").open(encoding="utf-8") as handle:
        for row in json_array_items(handle):
            count += 1
            identities.add(row["ccu_page"])
            if page is None or row["ccu_page"] == page:
                _validate_reviewed_row(row)
                rows[row["ccu_page"]] = row
    if count != 55 or len(identities) != 55:
        raise ValueError("CCU overseas review must cover all 55 current/quota-unknown identities")
    return rows


@lru_cache(maxsize=1)
def reviewed_rows() -> dict[int, dict]:
    """Full audit/build interface: validate every receiving-school source."""
    return _selected_reviewed_rows(BUNDLE)


_reviewed_row_lock = threading.Lock()


@lru_cache(maxsize=4)
def _reviewed_row_payload(bundle: Path, signature: tuple[int, int], page: int) -> bytes:
    row = _selected_reviewed_rows(bundle, page).get(page)
    return json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def reviewed_row(page: int) -> dict | None:
    """Public detail lookup: retain four serialized rows, never the whole graph.

    The whole array and identity count are still parsed; all evidence returned
    for the selected school passes the same hash, source and excerpt checks.
    """
    path = BUNDLE / "overseas-reviewed-fields.json"
    stat = path.stat()
    with _reviewed_row_lock:
        payload = _reviewed_row_payload(BUNDLE, (stat.st_mtime_ns, stat.st_size), page)
    return json.loads(payload)

'''
ccu=ccu[:a]+new+ccu[b:]
ccu=ccu.replace('row = reviewed_rows().get(partner.source_pages[0])','row = reviewed_row(partner.source_pages[0])')
replace('ccu_overseas.py',ccu)
p=(root/'ccu_profile.py').read_text().replace('from .ccu_overseas import STATUS_LABELS, describe_field, reviewed_rows','from .ccu_overseas import STATUS_LABELS, describe_field, reviewed_row').replace('host = reviewed_rows().get(partner.source_pages[0])','host = reviewed_row(partner.source_pages[0])')
replace('ccu_profile.py',p)
l=(root/'life_context.py').read_text().replace('from functools import lru_cache','from collections.abc import Mapping\nfrom functools import lru_cache')
a=l.index('@lru_cache(maxsize=1)\ndef _bundled_ntu_research');b=l.index('\ndef read_research',a)
new='''class _LifeSnapshotIndex(Mapping):
    """Keep compact validated JSON; return fresh models only for requested hosts."""
    def __init__(self, records):
        self._records = records

    def __getitem__(self, key):
        return LifeResearchSnapshot.model_validate_json(self._records[key])

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)


@lru_cache(maxsize=1)
def _bundled_ntu_research() -> Mapping[tuple[str, str], LifeResearchSnapshot]:
    records = {}
    if BUNDLED_NTU_LIFE.exists():
        with BUNDLED_NTU_LIFE.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = reviewed_life_snapshot(LifeResearchSnapshot.model_validate_json(line))
                    if row.extraction_version == EXTRACTION_VERSION:
                        records[(school_identity_key(row.school_name), row.country or "")] = row.model_dump_json().encode("utf-8")
                except ValueError:
                    continue
    return _LifeSnapshotIndex(records)

'''
replace('life_context.py',l[:a]+new+l[b:])
print('Atomically prepared scoped CCU life validation, compact NTU life index, shared streaming reader.')
