from pathlib import Path

def replace(path, old, new):
    file = Path(path)
    text = file.read_text()
    assert text.count(old) == 1, (path, text.count(old))
    file.write_text(text.replace(old, new))

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
