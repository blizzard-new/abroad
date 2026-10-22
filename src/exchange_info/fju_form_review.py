"""FJU 116-1 application form requirements, scoped to the mother application."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest, pointer_parent
from .ntust_source_review import write_atomic

MANIFEST = 'docs/data-verification-20261021/round47-fju-form-review.json'
MANIFEST_SHA256 = '64b3e5ef9cd5b9320ee0c6f84bf7847b46151fe0fbdcb1c79f4b0c4154869e0e'
ARCHIVE_KEY = 'source_review_round47_form'

NEWS_URL = 'https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14'
FORM_URL = 'https://iscoie.fju.edu.tw/DownloadNewsFileServlet?file=1345'
PORTAL_URL = 'http://outgoing.oie.fju.edu.tw/'
CHECKED_AT = '2026-10-21T04:42:58.111712+00:00'
ENROLLMENT = '116-1申請表要求115學年度第二學期及交換期間均保有學籍，不得休學或畢業；違反者喪失交換資格。'
CONDITIONAL_STAMPS = '交換期間為大學部五年級以上，且因雙主修、輔系或學程學分未修畢而延畢者。'
PAPER = ('116-1赴姊妹校交換學生申請表須以電腦繕打、A4雙面列印；英文姓名須與護照拼音一致，'
         '二吋證件照可用電子檔彩色列印。本人及監護人均須親筆簽名蓋章，並經系所秘書、主任／所長、院長核可蓋章。'
         '交換期間為大五以上且因雙主修、輔系或學程學分未修畢而延畢者，另須相關單位秘書及主任核可。'
         '2026/12/24 16:30前繳交國際學生中心；本表未載繳件房號，實際安排依承辦通知。')
JLPT = ('已報名2026年第2回JLPT者，申請表允許於2027/01/31前補網路查詢成績證明；'
        '日語組申請時不填志願，待1月中email通知。選填及補件的實際安排依承辦通知，'
        '不可寫成1月31日只能收正式紙本證書，亦不把1月中通知推定為補件截止。')


def current_home_submission_step(rule_id: str) -> dict:
    """The actual two-page form distinguishes signatures and conditional stamps."""
    return {
        'rule_id': rule_id, 'order': 2, 'phase': '校內申請',
        'title': '完成交換生系統填報、上傳電子文件並繳交雙面紙本申請表',
        'responsible_party': '學生', 'responsible_unit': '輔大國際學生中心',
        'deadline_at': '2026-12-24T16:30:00+08:00', 'deadline_status': 'verified_exact',
        'deadline_source_url': NEWS_URL, 'deadline_checked_at': CHECKED_AT, 'deadline_reminder_eligible': True,
        'summary': '116-1收件及系統開放為2026/11/01至12/24 16:30；開放當日小時未載明。紙本只繳雙面申請表，其餘三項PDF上傳申請系統，各檔不超過20MB。',
        'details': [PAPER,
            '申請系統限校內網路開啟；交件後不得更改。',
            '電子檔1：中文簡歷至多2頁、中文讀書計畫至少500字且至多2頁、其他表現證明及清寒證明（無則免）合併同一PDF。',
            '電子檔2：中文歷年成績單含班排名，期間至114學年度第二學期；碩一用大學、博一用碩士歷年成績單。',
            '電子檔3：英語或交換校特殊語言檢定證明。'+JLPT,
            ENROLLMENT,
            '交換學分抵認依系所規定，國際處不保證抵認相同學分數或如期畢業。'],
        'document_requirements': [
            {'name': '赴姊妹校交換學生申請表（紙本雙面列印）',
             'signatures': ['學生本人（親筆簽名並蓋章）', '監護人（親筆簽名並蓋章）'],
             'stamps': ['系所秘書', '系主任／所長', '院長'],
             'official_form_url': FORM_URL, 'source_urls': [NEWS_URL, FORM_URL],
             'official_form_verified': True, 'applicability_status': 'verified_current', 'applicability_year': '116'},
            {'name': '電子檔1：中文簡歷（至多2頁）、中文計畫（至少500字、至多2頁）及其他審查資料合併PDF',
             'copy_type': 'digital', 'source_urls': [NEWS_URL, FORM_URL]},
            {'name': '電子檔2：中文歷年成績單（含班排名；碩一／博一依前一學制成績）',
             'copy_type': 'digital', 'source_urls': [NEWS_URL, FORM_URL]},
            {'name': '電子檔3：英語或交換學校特殊語言要求之檢定證明',
             'copy_type': 'digital', 'source_urls': [NEWS_URL, FORM_URL]},
            {'name': '雙主修／輔系／學程核可欄（指定延畢情形適用）',
             'conditional': True, 'condition': CONDITIONAL_STAMPS,
             'stamps': ['適用雙主修／輔系／學程秘書', '適用雙主修／輔系主任／所長或學程主任'],
             'official_form_url': FORM_URL, 'source_urls': [FORM_URL], 'official_form_verified': True,
             'stage': 'student_application', 'applicability_status': 'verified_current', 'applicability_year': '116'},
        ],
        'scope': {'home_universities': ['天主教輔仁大學'], 'academic_years': ['116'],
                  'application_rounds': ['第1學期（秋季班）']},
        'submission': {'method': 'mixed', 'office': '國際及兩岸教育處國際學生中心（繳件地點依承辦通知）',
                       'portal_url': PORTAL_URL},
        'action_url': NEWS_URL, 'source_urls': [NEWS_URL, FORM_URL],
        'checked_at': CHECKED_AT, 'support_status': 'verified',
    }


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('FJU form review manifest hash mismatch')
    return json.loads(raw)


def apply_fju_form_review(root: Path, *, bundle: Path | None = None) -> int:
    manifest = load_manifest(root)
    loaded = {}
    for scope in manifest['rows']:
        path = bundle / Path(scope['file']).name if bundle is not None else root / scope['file']
        if path not in loaded:
            loaded[path] = [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        matches = [row for row in loaded[path] if (row.get('school_name'), row.get('country')) ==
                   (scope['school_name'], scope['country'])]
        if len(matches) != 1:
            raise ValueError(f'FJU form route must match exactly once: {scope["school_name"]}')
        scope['file'] = str(path.resolve())
    changed = apply_review_manifest(root, 'fju', manifest, ARCHIVE_KEY, manage_profile_context=False)
    for scope in manifest['singletons']:
        path = bundle / Path(scope['file']).name if bundle is not None else root / scope['file']
        row = json.loads(path.read_text('utf8'))
        modified = False
        for patch in scope['patches']:
            try:
                parent, key = pointer_parent(row, patch['pointer'])
                previous, exists = parent[key], True
            except (KeyError, IndexError):
                previous, exists = None, False
            if exists and (previous == patch['value'] or previous not in patch['expected_values']):
                continue
            if not exists and not patch['expected_missing']:
                continue
            parent, key = pointer_parent(row, patch['pointer'], create=True)
            parent[key] = patch['value']
            modified = True
            changed += 1
        if modified:
            write_atomic(path, row, False)
    return changed
