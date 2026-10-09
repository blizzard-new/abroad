from pathlib import Path
s=Path('/workspace/abroad-pr3/tests/test_ntu_school_board_migration.py').read_text()
s=s.replace('MIGRATIONS = Path(__file__).parents[1] / "supabase/migrations"', 'MIGRATIONS = Path("/workspace/abroad-pr3/supabase/migrations")')
needle='        assert publish("generic", board="university:example", school="其他學校")["status"] == "committed"'
s=s.replace(needle,needle+'\n        for key, school in [("ccu", "國立中正大學"), ("ncu", "國立中央大學")]:\n            result = publish("probe-" + key, board=key, school=school)\n            print("NEW_SCHOOL_RPC", key, json.dumps(result, ensure_ascii=False), flush=True)\n            assert result["status"] == "board_forbidden"\n')
Path('/workspace/integration-tools/test_forum_probe.py').write_text(s)
