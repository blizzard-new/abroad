"""116-1 mother scoring rules; score bands are not exact-point formulae."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .host_source_review_round25 import apply_review_manifest, pointer_parent
from .ntust_source_review import write_atomic

MANIFEST = 'docs/data-verification-20261021/round48-fju-briefing-review.json'
MANIFEST_SHA256 = '0990dda59853ea282c1453cd916d1dfa65d774c91dde76b78fc07b69d7741195'
ARCHIVE_KEY = 'source_review_round48_briefing'
SLIDES_URL = 'https://iscoie.fju.edu.tw/DownloadNewsFileServlet?file=1344'
SCORING_FORMULA = ('116-1簡報第16頁：校內書面審查以在校歷年平均成績50%及語言能力50%計分；'
                   '申請大陸姊妹校雖非必須附外語能力，但有外語能力者總積分較高。'
                   '第20頁同分依序比較歷年班級排名百分比、歷年平均、語檢成績、社團競賽證明、讀書計畫與自傳。')
SCORING_TABLE_NOTE = ('116-1簡報第17頁語言評分不分區，有多種檢定者擇較高評分。'
 '舊制TOEFL iBT 46–59／60–78／79–93／94–101／102–109／110–114／115–120，'
 '分別對應40–49／50–59／60–69／70–79／80–89／90–99／100分；'
 'TOEIC 550–665／670–780／785–865／870–940／945–990，分別對應40–49／50–59／60–69／70–79／80–89分。'
 '這些區間內的精確換算方法未載明。IELTS 5.5／6.0／6.5／7.0／7.5／8.0／8.5及新制TOEFL 3.0／3.5／4.0／4.5／5.0／5.5／6.0，'
 '分別對應40／50／60／70／80／90／100分；未列值須向承辦確認。校內評分不取代母校及接待校申請門檻。')


def load_manifest(root: Path) -> dict:
    raw=(root/MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('FJU briefing manifest hash mismatch')
    return json.loads(raw)


def apply_fju_briefing_review(root: Path, *, bundle: Path | None = None) -> int:
    return apply_scoped_briefing_manifest(root, load_manifest(root), ARCHIVE_KEY, bundle=bundle)


def apply_scoped_briefing_manifest(root: Path, manifest: dict, archive_key: str, *, bundle: Path | None = None) -> int:
    loaded={}
    for scope in manifest['rows']:
        path=bundle/Path(scope['file']).name if bundle is not None else root/scope['file']
        if path not in loaded:
            loaded[path]=[json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        matches=[row for row in loaded[path] if (row.get('school_name'),row.get('country'))==
                 (scope['school_name'],scope['country'])]
        if len(matches)!=1:
            raise ValueError(f'FJU briefing route must match exactly once: {scope["school_name"]}')
        scope['file']=str(path.resolve())
    changed=apply_review_manifest(root,'fju',manifest,archive_key,manage_profile_context=False)
    for scope in manifest['singletons']:
        path=bundle/Path(scope['file']).name if bundle is not None else root/scope['file']
        row=json.loads(path.read_text('utf8'));modified=False
        for patch in scope['patches']:
            parent,key=pointer_parent(row,patch['pointer'])
            previous=parent[key]
            if previous==patch['value'] or previous not in patch['expected_values']:
                continue
            parent[key]=patch['value'];changed+=1;modified=True
        if modified:write_atomic(path,row,False)
    return changed
