from pathlib import Path
from urllib.parse import quote
import datetime, hashlib, json

H = Path(__file__).parent
R = Path('/workspace/abroad-ntu-completion-20261011')
S = R / 'docs/ntu-completion-20261011/stage9'
read = lambda p: json.loads(p.read_text())
publication = read(H / 'publication.json')
remote = read(H / 'remote-publication-verification.json')
pr = read(H / 'pr9-description-verification.json')
result = read(H / 'finalize-result.json')
run = read(S / 'validation/run-receipt.json')
assert publication['remote_commit'] == remote['remote_commit'] == pr['remote_commit']
assert remote['source_sha256'] == result['source_sha256'] == run['source_sha256']
assert result['observations'] == 1485 and result['delta'] == 112
assert result['life_count'] == 2146 and result['life_gap'] == 16 and result['independent46_gap'] == 39
assert sum(result['conclusions'].values()) == 429 and result['archive_versions'] == 1389 and result['archive_parts'] == 44
assert pr['body_read_back_exact'] and pr['draft'] and not pr['merged']
assert all(job['returncode'] == 0 for job in run['jobs'].values())
assert remote['PR9_draft_unmerged'] and remote['PR8_unchanged_draft_unmerged'] and remote['main_unchanged']
deliverables = [{**d, 'fixed_commit_url': 'https://github.com/blizzard-new/abroad/blob/'
                + publication['remote_commit'] + '/' + quote(d['path'], safe='/')}
                for d in remote['verified_downloads']]
links = read(S / '少數必要官方連結_未新增取件.json')
body = {
    'completed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'parent_thread_id': '01a11418-1d72-7319-807d-9ac7738f00d3',
    'repo': 'blizzard-new/abroad', 'stage': 'stage9_fixed429_final_conclusions',
    'PR_url': pr['PR_url'], 'remote_commit': publication['remote_commit'],
    'remote_tree': publication['remote_tree'], 'tested_source_sha256': result['source_sha256'],
    'deliverables': deliverables,
    'fixed_field_roster': {'fields': 429, 'schools': 121, 'concluded': 429,
                          'remaining_same_existing_body_pending': 0,
                          'outcomes': result['conclusions']},
    'candidate_observations': {'previous': 1373, 'added': 112, 'total': 1485,
                               'all_previous_preserved': True,
                               'all_selection_rule_confirmed_false': True},
    'full_matrix': {'schools': 288, 'fields': 14, 'rows': 4032},
    'original_282x10': {'rows': 2820, 'full_current_cycle_requirement_verified': 0,
                        'home_school_quota_blank': 282, 'home_school_quota_zero': 6},
    'announced_home_common_rules': {'items': 11, 'registration_timezone': 'Asia/Taipei',
                                  'registration_start': '2026-11-03T10:00:00+08:00',
                                  'registration_end': '2026-11-09T16:00:00+08:00'},
    'life': {'school_count': 272, 'evidence_count': 2146, 'any_evidence_gap': 16,
             'previous2124_all_preserved': True,
             'original46_independent_host_gap': 39,
             '38_to39_reason': '蘭州819的原校手冊由NTU代存，stage7報告誤算海外網域；stage7／8實際runtime均39，同46成員及全部來源保留。'},
    'assets': {'photo_gap_portal_ids': ['9', '12', '67'],
               'coordinate_gap_portal_ids': ['9', '12', '1302'],
               'UC_CSU_campus_unassigned': True, 'new_unbounded_search': False},
    'source_archive': {'raw_versions': result['archive_versions'],
                       'parts': result['archive_parts'],
                       'prior1228_versions42_parts_unchanged': True,
                       'new_fetches_this_stage': 0,
                       'full_body_review_rows': 4025, 'semantic_review_rows': 1009,
                       'quoted_source_count': 648},
    'tests': result['tests'],
    'all_tested_input_bytes_unchanged_during_tests': True,
    'PR8_simulation_companion_test_patch_required': True,
    'initial_failures_and_interrupted_runs_preserved': True,
    'complete_2189pass1fail13skip_run_preserved': True,
    'fresh_build_and_historical_replay_ordering_corrected_without_assertion_change': True,
    'downloaded_excel_sheets': remote['downloaded_excel_sheet_rows'],
    'downloaded_zip_crc_verified': remote['downloaded_zip_integrity_verified'],
    'necessary_public_link_rows': len(links),
    'necessary_unique_urls': len({row['link'] for row in links}),
    'remaining_limits': [
        '終局判讀只結案既有429欄；完整2820當期欄仍需具體年度、program、校區、提名／錄取、個人入口等資料。',
        '固定429以外4項歷史來源不足及原來源seed追溯保留，未將首頁可讀視為992個另開待讀項。',
        'UC／CSU未指定校區；特魯瓦原圖／作者／授權未齊；蒙斯地址／校區坐標缺一致官方證據。',
        '原2026-10-07工作簿未取得，重建當日官方288中282集合；與舊工作簿精確逐校／逐格重疊未知。',
        'Library先前401且父端停止重試，無Library檔案ID；已固定GitHubcommit四檔下載驗SHA。',
        '父端平行11校批次未在本環境取得，不宣稱已合併該批。',
    ],
    'main_unchanged': True, 'PR8_unchanged_draft_unmerged': True,
    'PR9_draft_unmerged': True, 'merge_or_deploy': False,
    'duplicate_daily_automation_created': False,
    'daily_baseline_path': str(S / 'daily-baseline-2026-10-11.json'),
    'daily_baseline_timestamp_note': '0新取件；保留個別來源原checked_at及三入口／288詳情實際查核時間。',
    'supporting_receipts': [str(H / n) for n in ['remote-publication-verification.json',
                                               'tested-remote-blob-receipts.json',
                                               'pr9-description-verification.json',
                                               'finalize-result.json']],
}
(H / 'final-parent-handoff.json').write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'handoff': str(H / 'final-parent-handoff.json'),
                  'remote_commit': body['remote_commit'], 'deliverables': len(deliverables)}, ensure_ascii=False))
