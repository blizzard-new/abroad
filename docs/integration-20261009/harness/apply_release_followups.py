from pathlib import Path

def replace(path, old, new):
    file = Path(path)
    text = file.read_text()
    assert text.count(old) == 1, (path, text.count(old))
    file.write_text(text.replace(old, new))

replace('src/exchange_info/models.py',
        '        if not any(getattr(self, name) for name in fields):',
        '        if not any(getattr(self, name) for name in fields) and not self.model_fields_set.intersection(fields):')
replace('src/exchange_info/application_documents.py',
        '                        step.phase if requirement.stage in {"after_application", "second_submission"}',
        '                        step.phase if workflow.home_university == "淡江大學"\n'
        '                        or requirement.stage in {"after_application", "second_submission"}')
replace('src/exchange_info/workflow_structuring.py',
        '            infer_from_text=infer_from_text,',
        '            infer_from_text=infer_from_text,\n'
        '            preserve_reviewed_metadata=workflow.home_university != "淡江大學",')
replace('src/exchange_info/workflow_structuring.py',
        '    infer_from_text: bool = True,\n) -> ApplicationDocumentRequirement:',
        '    infer_from_text: bool = True,\n'
        '    preserve_reviewed_metadata: bool = True,\n) -> ApplicationDocumentRequirement:')
replace('src/exchange_info/workflow_structuring.py',
        '    if requirement.stage is not None:',
        '    if requirement.stage is not None and preserve_reviewed_metadata:')
replace('src/exchange_info/static/regions.js',
        '["比利時", "Belgium"], ["盧森堡", "Luxembourg"],',
        '["比利時", "Belgium"], ["盧森堡", "Luxembourg"], ["摩納哥", "Monaco"],')
replace('src/exchange_info/static/regions.js',
        '["加拿大", "Canada"], ["墨西哥", "Mexico"]],',
        '["加拿大", "Canada"], ["墨西哥", "Mexico"], ["巴哈馬", "Bahamas", "加勒比海", "Caribbean"]],')
replace('tests/test_tku_continuation.py',
        "SimpleNamespace(school_name='淡江大學'))",
        "SimpleNamespace(school_name='淡江大學', academic_gpa_minimum=None))")
replace('tests/test_rag.py',
        '    unconsented_rewrite = client.post(\n'
        '        "/ai/rewrite-document",\n'
        '        json={"text": "這是我自行撰寫且需要調整語氣的交換申請內容。" * 2, "action": "formalize", "ai_consent_granted": True},',
        '    unconsented_rewrite = client.post(\n'
        '        "/ai/rewrite-document",\n'
        '        json={"text": "這是我自行撰寫且需要調整語氣的交換申請內容。" * 2, "action": "formalize"},')
replace('tests/test_tku_web_evidence.py',
        'import json\nimport subprocess',
        'import json\nimport os\nimport subprocess')
replace('tests/test_tku_web_evidence.py',
        '    process = subprocess.Popen([sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)',
        '    # Reproduce the original buffered logger regardless of the outer test runner.\n'
        '    environment = {key: value for key, value in os.environ.items() if key != "PYTHONUNBUFFERED"}\n'
        '    process = subprocess.Popen([sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)')
replace('src/exchange_info/static/index.html',
        'community-reader.js?v=20261009-tku-reader-expiry-1',
        'community-reader.js?v=20261009-six-schools-integration-1')
replace('tests/test_community_permissions.py',
        '        "ntu",\n        "tku",',
        '        "ntu",\n        "tku",\n        "ccu",\n        "ncu",')
replace('tests/test_ccu_seventeenth_pass.py',
        '    assert all(r.applicability_status is None for w in workflows if w.home_university != HOME',
        '    assert all(r.applicability_status is None for w in workflows\n'
        '               if w.home_university in {"長庚大學", "國立臺北大學", "國立臺灣大學"}')

replace('tests/test_destination_tips.py',
        '    return {row["country"] for row in rows} - {"臺灣"}',
        '    return {destination_tips.canonical_country(row["country"]) for row in rows} - {"臺灣"}')
replace('tests/test_destination_tips.py',
        'def test_every_destination_country_has_a_guide_and_nothing_else_does():\n'
        '    assert set(load_guides()) == destination_countries()',
        'def test_destination_guide_coverage_accounts_for_every_known_gap(client):\n'
        '    # The expanded six-school coordinate catalog includes countries with no\n'
        '    # researched guide. Keep those missing instead of fabricating tips or dates.\n'
        '    gaps = {"丹麥", "以色列", "冰島", "南非", "哥倫比亞", "墨西哥", "希臘",\n'
        '            "斯洛維尼亞", "智利", "澳門", "盧森堡", "科索沃", "芬蘭", "葡萄牙"}\n'
        '    assert set(load_guides()) | gaps == destination_countries()\n'
        '    assert not set(load_guides()) & gaps\n'
        '    for country in sorted(gaps):\n'
        '        assert destination_tips.guide_for_country(country) is None\n'
        '        response = client.get("/destination-tips", params={"country": country})\n'
        '        assert response.status_code == 404\n'
        '        assert response.json()["detail"] == "這個國家的出發前提醒還在整理中。"')

replace('tests/e2e/test_fit_and_completeness_ui.py',
        "    expect(body).to_contain_text('項資料完整')",
        "    expect(body).to_contain_text('項已提供資料')\n"
        "    expect(body).not_to_contain_text('項資料完整')")

replace('tests/e2e/test_region_search.py',
        '    assert "本期開放" in labels and not any("115" in label for label in labels), labels',
        '    assert "當期名額已列" in labels and not any("115" in label for label in labels), labels\n'
        '    assert {"名額尚未核實", "零名額", "當期名額或期間待確認"} <= set(labels), labels')

replace('tests/e2e/test_ncu_school.py',
        "expect(departure.locator('.workflow-documents > li.needs-confirmation')).to_contain_text('待官方確認')",
        "expect(departure.locator('.workflow-documents > li.needs-confirmation')).to_contain_text('適用性及送件細節待確認')")

replace('tests/e2e/test_life_context.py',
        'food.get_by_text("資料來源", exact=True).click()',
        'food.get_by_text("原文與來源", exact=True).click()')
replace('tests/e2e/test_life_context.py',
        '    expect(housing.get_by_text("Dorm rooms are not guaranteed.", exact=True)).to_be_visible()',
        '    expect(housing.get_by_text("中文翻譯尚未完成，可查看原文。", exact=True)).to_be_visible()\n'
        '    expect(housing.get_by_text("Dorm rooms are not guaranteed.", exact=True)).not_to_be_visible()\n'
        '    housing.get_by_text("原文與來源", exact=True).click()\n'
        '    expect(housing.get_by_text("Dorm rooms are not guaranteed.", exact=True)).to_be_visible()')
replace('scripts/validate_supabase_runtime.py',
        'governance_migration = migration.name == "20261009080000_atomic_governance_commands.sql"',
        'governance_migration = migration.name.endswith("_atomic_governance_commands.sql")')
replace('scripts/validate_supabase_runtime.py',
        '    if not migration_files:\n        raise RuntimeValidationError("No Supabase migrations were found.")',
        '    if not migration_files:\n        raise RuntimeValidationError("No Supabase migrations were found.")\n'
        '    if sum(path.name.endswith("_atomic_governance_commands.sql") for path in migration_files) != 1:\n'
        '        raise RuntimeValidationError("Exactly one atomic governance migration is required.")')
replace('tests/test_supabase_migration_syntax.py',
        '    governance = next(\n        result\n        for result in summary.results\n        if result.path.name == "20261009080000_atomic_governance_commands.sql"\n    )',
        '    governance_results = [result for result in summary.results\n'
        '                          if result.path.name.endswith("_atomic_governance_commands.sql")]\n'
        '    assert len(governance_results) == 1\n'
        '    governance = governance_results[0]')
