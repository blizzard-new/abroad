"""Per-hunk reconciliation of fixed TKU with reviewed CCU/NCU/NTU changes."""
from pathlib import Path
import re
root=Path('/workspace/abroad-six')
pattern=re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n',re.M|re.S)
def resolve(name,choices):
 p=root/name;s=p.read_text();blocks=list(pattern.finditer(s));assert len(blocks)==len(choices),(name,len(blocks),len(choices))
 choices=iter(choices)
 def sub(m):
  c=next(choices);return c(m[1],m[2]) if callable(c) else c
 p.write_text(pattern.sub(sub,s))
ours=lambda a,b:a
theirs=lambda a,b:b
both=lambda a,b:a+b
resolve('pyproject.toml',[both,both])
p=root/'pyproject.toml';p.write_text(p.read_text().replace('CGU, NTPU, NTU, CCU and NCU','CGU, NTPU, NTU, CCU, NCU and TKU'))
resolve('src/exchange_info/advisor.py',[both])
resolve('src/exchange_info/application_documents.py',[
 both,
 '                                workflow.home_university in {"國立中正大學", "淡江大學"}\n',
 lambda a,b:a+'            else '+b.lstrip(),
])
resolve('src/exchange_info/models.py',[
 '        "open", "agreement_only", "departmental_reference", "not_open", "needs_confirmation", "zero_quota", "fee_paying", "closed", "reference_only", "quota_unconfirmed"\n',
 theirs,ours,
])
resolve('src/exchange_info/openapi_contract.py',['OPENAPI_CONTRACT_VERSION = "2026-10-09.2"\n'])
resolve('src/exchange_info/storage.py',[
 both,'from .university_registry import CCU, CGU, NTPU, NTU, NCU, TKU\n',
 lambda a,b:a.replace('BUNDLED_NCU_DIR))','BUNDLED_NCU_DIR, BUNDLED_TKU_DIR))'),
])
resolve('src/exchange_info/university_registry.py',[both,lambda a,b:a.replace('(CGU, NTPU, NTU, CCU, NCU)','(CGU, NTPU, NTU, CCU, NCU, TKU)')])
resolve('src/exchange_info/api.py',[
 lambda a,b:a+')\n'+b,
 both,both,theirs,theirs,ours,'',
 lambda a,b:a.replace('        profiles = load_destination_profiles(resolved_data_dir, include_bundled_baseline=True)\n','        profiles = published_destination_profiles()\n'),
])
p=root/'src/exchange_info/api.py';p.write_text(p.read_text().replace('if university.id in {"ccu", NCU.id}','if university.id in {"ccu", NCU.id, "tku"}'))
resolve('src/exchange_info/static/app.js',[
 ours,
 lambda a,b:"    jlptLevel:profile.jlpt_level || '',\n"+a,
 lambda a,b:a+'  }\n'+b,
 both,
 lambda a,b:a.replace('qualificationLabel: ', 'qualificationLabel: activeUniversityProfile().id === "tku" ? "淡江須依語組、學制、梯次及官方矛盾項確認資格" : '),
 lambda a,b:a.replace('function readApplicationContextForm() {\n',b),
 lambda a,b:'  const request = beginSchoolDataRequest("templates", requestedSchool);\n'+b.replace('const isCurrent = () => requestId', 'const isCurrent = () => schoolDataRequestIsCurrent(request) && requestId'),
 theirs,theirs,
 lambda a,b:b.split('\n',1)[0]+'\n'+a,
 lambda a,b:a.replace('const sourceLabel = item.official_form_verified ?', 'const sourceLabel = activeHomeSchool() === "淡江大學" && item.download_available ? (item.applicability_status === "reference_only" ? "開啟官方一般參考表格" : "開啟校方原表／表單入口") : item.official_form_verified ?'),
 lambda a,b:a.replace('${item.download_available ? "<b>官方表格</b>" : ""}', '${item.conditional ? "<b>符合條件才需要</b>" : ""}${item.download_available ? "<b>官方表格</b>" : ""}'),
 lambda a,b:a.replace('report.home_university === "國立中央大學" ?', 'report.home_university === "淡江大學" ? "欄已有當期依據；請逐欄看適用範圍" : report.home_university === "國立中央大學" ?'),
 lambda a,b:b.replace('<details class="life-evidence-source">', '${row.original_excerpt ? `<small class="life-applicability-note">官網參考；適用校區與年度請核對來源。${row.checked_at ? ` 查閱 ${escapeHtml(formatDate(row.checked_at))}` : ""}</small>` : ""}<details class="life-evidence-source">'),
 lambda a,b:a.replace('language_test: languageTest,','language_test: languageTest || null,'),
 theirs,
 lambda a,b:"        jlptLevel: payload.jlpt_level || '',\n"+a,
])
p=root/'src/exchange_info/static/app.js';s=p.read_text();s=s.replace('[...(context.flags || [])].sort()]);','[...(context.flags || [])].sort(), context.partner_document_states || {}]);');p.write_text(s)
resolve('src/exchange_info/static/index.html',[
 theirs,
 lambda a,b:a.replace('<option value="agreement_only">', '<option value="closed">表列交換校／校內申請已截止</option><option value="reference_only">舊期參考／不能作當期申請</option><option value="quota_unconfirmed">當期名額或期間待確認</option><option value="agreement_only">'),
 both,
 lambda a,b:b.replace('20261009-tku-reader-expiry-1','20261009-six-schools-integration-1'),
])
resolve('tests/e2e/conftest.py',[ours])
resolve('tests/e2e/test_ntu_school.py',[lambda a,b:a.replace('to_have_count(5)','to_have_count(6)').replace('"國立中央大學"]','"國立中央大學", "淡江大學"]')])
resolve('tests/test_fit_signals.py',['    assert len(profiles) == 789\n'])
resolve('tests/test_frontend_contract.py',[theirs,theirs,theirs,theirs,theirs,ours,theirs,theirs,theirs])
resolve('tests/test_ntu_integration.py',[lambda a,b:a.replace('"ncu"]','"ncu", "tku"]')])
resolve('tests/test_school_completeness.py',[lambda a,b:b.replace("'淡江大學':4", "'國立中央大學':214,'淡江大學':4").replace('== 575','== 789')])
resolve('tests/test_school_photo_and_match.py',[ours])
resolve('tests/test_supabase_migration_syntax.py',[lambda a,b:a.replace('== 32','== 35').replace('== 557','== 564').replace('== 69','== 74')])
resolve('tests/test_task_documents_and_reference_plan.py',[
 lambda a,b:a.replace('== 1065','== 1069').replace('== 851','== 855'),
 '    assert len(workflows) == 1069\n',
])
