"""Documented, per-hunk reconciliation of CCU/NCU with released NTU enrichment."""
from pathlib import Path
import re

root = Path('/workspace/abroad-integration')
pattern = re.compile(r'^<<<<<<< (?:HEAD|ours)\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n', re.M | re.S)
def resolve(name, choices):
    path = root / name
    text = path.read_text()
    blocks = list(pattern.finditer(text))
    assert len(blocks) == len(choices), (name, len(blocks), len(choices))
    index = iter(choices)
    def replace(match):
        choice = next(index)
        ours, theirs = match.groups()
        return choice(ours, theirs) if callable(choice) else choice
    path.write_text(pattern.sub(replace, text))

ours = lambda a,b:a
both = lambda a,b:a+b
resolve('pyproject.toml', ['description = "Web-first exchange application guide supporting CGU, NTPU, NTU, CCU and NCU students."\n'])
resolve('src/exchange_info/advisor.py', [lambda a,b:a[:a.rindex('    if is_ntu')] + b])
resolve('src/exchange_info/application_documents.py', [
    'from .ccu_sources import CHECKED_AT as CCU_SOURCE_CHECKED_AT\nfrom .ncu_document_conditions import document_applicability, preparation_state_key\nfrom .university_registry import NTPU, NTU, NCU, require_university, resolve_university\n',
    both,
    lambda a,b:a+'            else '+b.lstrip(),
])
resolve('src/exchange_info/application_rules.py', ['                "needs_confirmation" if partner.availability_status == "needs_confirmation" or ((is_ntu(request.home_school) or is_ncu(request.home_school)) and partner.quota is None) else "fail",\n'])
resolve('src/exchange_info/models.py', [both])
path=root/'src/exchange_info/models.py'
text=path.read_text()
text=text.replace('    academic_gpa: float | None = Field(default=None, ge=0, le=4.3)\n    current_year: str | None = Field(default=None, max_length=40)\n', '    academic_gpa: float | None = Field(default=None, ge=0, le=4.3)\n')
path.write_text(text)
resolve('src/exchange_info/storage.py', [
    'from .university_registry import CCU, CGU, NTPU, NTU, NCU\n',
    '    return tuple(directory / "application_workflows.jsonl" for directory in (BUNDLED_NTPU_DIR, BUNDLED_CGU_DIR, BUNDLED_NTU_DIR, BUNDLED_CCU_DIR, BUNDLED_NCU_DIR))\n',
    both,
])
resolve('src/exchange_info/university_registry.py', [lambda a,b:b.replace('SUPPORTED_UNIVERSITIES = (CGU, NTPU, NTU, NCU)', 'SUPPORTED_UNIVERSITIES = (CGU, NTPU, NTU, CCU, NCU)')])
resolve('src/exchange_info/workflow_structuring.py', [lambda a,b:a.replace('if method == ApplicationSubmissionMethod.UNKNOWN and not ccu_host_life:', 'if infer_from_text and method == ApplicationSubmissionMethod.UNKNOWN and not ccu_host_life:')])
resolve('src/exchange_info/api.py', [
    lambda a,b:a+'                        else '+b.lstrip(),
    both,
    ours,
    ours,
    ours,
    '',
    ours,
])
path=root/'src/exchange_info/api.py'
text=path.read_text().replace('            if university.id == NCU.id\n            else load_application_workflows(resolved_data_dir)\n', '            if university.id in {"ccu", NCU.id}\n            else load_application_workflows(resolved_data_dir)\n')
path.write_text(text)
resolve('src/exchange_info/static/app.js', [
    lambda a,b:a[:a.index('  $("#advisor-academic-rule")')]+b,
    ours, # Full serialized context and request generation includes NCU selection state.
    ours,
    lambda a,b:a+b[b.index('        const referenceSources'):],
    lambda a,b:a.replace('${safeSourceUrl(requirement.official_form_url) ?', '${!showReferenceForm && safeSourceUrl(requirement.official_form_url) ?').replace('</span>\n', '${referenceUrl && referenceUrl !== "#" ? `<small><a href="${escapeHtml(referenceUrl)}" target="_blank" rel="noopener noreferrer">官方參考表格（當期適用待確認）</a></small>` : ""}</span>\n'),
])
resolve('src/exchange_info/static/index.html', ['    <script src="/static/app.js?v=20261009-five-schools-integration-1" defer></script>\n'])
resolve('tests/test_ntu_integration.py', ['    assert [row["id"] for row in client.get("/universities").json()] == ["cgu", "ntpu", "ntu", "ccu", "ncu"]\n'])
