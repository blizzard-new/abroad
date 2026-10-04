import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.partner_localization import translate_partner_text
from exchange_info.public_translation import (
    PublicTranslationBatch, cached_translation, needs_translation,
    standardize_terms, translate_public_batch, _valid_translation,
)


@pytest.mark.parametrize("text", [
    "Les étudiants doivent fournir un certificat de langue.",
    "Die Bewerbung ist bis zum 15. Mai einzureichen.",
    "留学生は学生食堂を利用できます。",
    "기숙사 입주는 보장되지 않습니다.",
    "Студенты могут пользоваться библиотекой.",
    "สามารถใช้ห้องสมุดได้", "Housing", "Application Fee: $100",
])
def test_foreign_prose_is_detected(text):
    assert needs_translation(text)


@pytest.mark.parametrize("text", [
    "TOEIC 785", "TOEIC650分以上，建議CEFR B2為佳。",
    "TOEFL iBT 79 或 IELTS 6.5；GPA3.0/4.0。",
    "可至 Søknadsweb 申請。", "限選擇Bordeaux或Marseille校區。",
    "Sky Lounge 餐廳位於 Liberty Tower，提供學生餐飲。",
    "英檢成績須符合托福61分、IELTS 5或TOEIC600以上。",
])
def test_proper_names_and_exam_levels_are_preserved(text):
    assert not needs_translation(text)


def test_translation_preserves_exam_identity_and_numbers():
    source = "TOEIC 785 or IELTS 6.5 is required."
    assert _valid_translation(source, "須達 TOEIC 785 或 IELTS 6.5。")
    assert not _valid_translation(source, "須達 TOEFL 785 或 IELTS 6.5。")
    assert not _valid_translation(source, "須達多益 785 或 IELTS 6.5。")
    assert not _valid_translation(source, "須達 TOEIC 750 或 IELTS 6.5。")
    assert standardize_terms("多益 TOEIC 700 / toeic 785") == "TOEIC 700 / TOEIC 785"


def test_curated_translations_and_modal_may_keep_meaning(tmp_path):
    text = "Program Fees for Courses: $50-$200。"
    assert cached_translation(text, "https://example.edu", tmp_path) == ("課程費用: $50-$200。", "translated")
    assert "5 月" not in translate_partner_text("Interview may be requested.")
    assert "5 月" in translate_partner_text("31 May 2027")
    assert "5 月" in translate_partner_text("May 31 2027")


def test_translation_api_cached_reads_do_not_start_model(monkeypatch, tmp_path):
    monkeypatch.delenv("EXCHANGE_PUBLIC_TRANSLATION", raising=False)
    client = TestClient(create_app(data_dir=tmp_path))
    entries = [{"text": "Application Fee: $100。", "source_url": "https://example.edu"},
               {"text": "宿舍：TOEIC 785", "source_url": ""},
               {"text": "기숙사 입주는 보장되지 않습니다.", "source_url": "https://example.edu"}]
    result = client.post("/public-translations", json={"entries": entries}).json()["entries"]
    assert result[0]["zh"] == "申請費: $100。"
    assert result[1]["zh"] == "宿舍：TOEIC 785"
    assert result[2] == {"text": entries[2]["text"], "zh": "", "status": "pending"}
    assert client.post("/public-translations", json={"entries": entries * 2, "generate": True}).status_code == 422
    assert client.post("/public-translations", json={"entries": [{"text": "a" * 2401}]}).status_code == 422


def test_public_web_localization_preserves_state_and_private_boundaries():
    module_path = Path("src/exchange_info/static/public-content-zh.js").resolve()
    script = r"""
const assert = require('node:assert/strict');
const zh = require(process.argv[1]);
let calls = [];
global.fetch = async (url, options) => {
  const body = JSON.parse(options.body); calls.push(body);
  return {ok:true,json:async()=>({entries:body.entries.map(({text})=>({text,zh:'須達 TOEIC 785 或 IELTS 6.5。',status:'machine'}))})};
};
(async()=>{
  const original = {school_name:'Example University',country:'France',
    scope:'home_application',id:'source-1',source_url:'https://example.edu',
    eligibility:'TOEIC 785 or IELTS 6.5 is required.',
    student_summary_zh:{eligibility_points:['TOEIC 785 or IELTS 6.5 is required.']},
    title:'入學資格'};
  const result = await zh.localize('/student-dashboard?school=example',original);
  assert.equal(result.student_summary_zh.eligibility_points[0],'須達 TOEIC 785 或 IELTS 6.5。');
  for (const key of ['school_name','country','scope','id','source_url','eligibility']) assert.equal(result[key],original[key]);
  assert.equal(original.student_summary_zh.eligibility_points[0],'TOEIC 785 or IELTS 6.5 is required.');
  assert.equal(calls.length,1);
  for(const route of ['/auth/me','/account/workspace','/account/vault/documents','/community/private']) {
    const privateData={body:'private text',email:'someone@example.com',title:'Private document'};
    assert.equal(await zh.localize(route,privateData),privateData);
  }
  assert.equal(calls.length,1);
  assert.equal(zh.normalizeTerms('多益 TOEIC 700'),'TOEIC 700');
  assert.equal(zh.needsTranslation('TOEIC650分以上，建議CEFR B2為佳。'),false);
  for(const text of ['기숙사는 보장되지 않습니다.','Les étudiants peuvent postuler.','Die Bewerbung ist erforderlich.']) assert.equal(zh.needsTranslation(text),true);
  global.fetch=async()=>{throw new Error('offline')};
  const failed=await zh.localize('/student-experiences',{summary:'No rooms are guaranteed.',summary_zh:'',translation_status:'pending'});
  assert.equal(failed.summary,'No rooms are guaranteed.');
  assert.equal(failed.summary_zh,'No rooms are guaranteed.');
  assert.equal(failed.translation_status,'pending');
  assert.equal(zh.needsTranslation('სტუდენტებს შეუძლიათ განაცხადის შეტანა.'),true);
  const longData={description:'Students may apply. '.repeat(250)};
  const parts=zh.collect(longData);
  assert(parts.length>1 && parts.every(row=>row.text.length<=1800));
  assert.equal(parts[0].group.parts.join(''),longData.description);
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script, str(module_path)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
