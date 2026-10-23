from office.config import Settings, _load_dotenv


def test_dotenv_ignores_inline_comments_and_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text('OFFICE_DRY_RUN=0      # 正式發佈\nOFFICE_MODEL="claude-sonnet-5-5" # 省錢\n# 註解\nOFFICE_THREADS_SLOTS=12:30,21:00\n', encoding="utf-8")
    values = _load_dotenv(env)
    assert values == {"OFFICE_DRY_RUN": "0", "OFFICE_MODEL": "claude-sonnet-5-5", "OFFICE_THREADS_SLOTS": "12:30,21:00"}


def test_dry_run_stays_on_unless_explicitly_disabled(tmp_path):
    home = str(tmp_path)
    assert Settings.from_env(env={"OFFICE_HOME": home}).dry_run is True
    assert Settings.from_env(env={"OFFICE_HOME": home, "OFFICE_DRY_RUN": "maybe"}).dry_run is True
    assert Settings.from_env(env={"OFFICE_HOME": home, "OFFICE_DRY_RUN": "0"}).dry_run is False


def test_example_env_file_parses_to_safe_defaults():
    from office.config import PROJECT_DIR

    values = _load_dotenv(PROJECT_DIR / ".env.example")
    assert values["OFFICE_DRY_RUN"] == "1"
    assert values["OFFICE_APPROVAL"] == "manual"
    assert values["OFFICE_THREADS_SLOTS"] == "12:30,21:00"


def test_example_allocation_gives_each_desk_its_tool(tmp_path):
    from office import brains
    from office.config import PROJECT_DIR

    values = _load_dotenv(PROJECT_DIR / ".env.example")
    settings = Settings.from_env(env={**values, "OFFICE_HOME": str(tmp_path)})
    first = {role: brains.chain(settings, role)[0] for role in brains.ROLES}
    assert first["threads"] == first["video"] == first["designer"] == "claude-code"
    assert first["reviewer"] == "codex"
    assert first["research"] == first["publisher"] == first["analyst"] == "antigravity"
    assert brains.chain(settings, "research")[1:] == ["claude-code", "api", "offline"]
    assert settings.images == "codex"


def test_antigravity_is_the_chief_in_the_example(tmp_path):
    from office import brains
    from office.config import PROJECT_DIR

    values = _load_dotenv(PROJECT_DIR / ".env.example")
    settings = Settings.from_env(env={**values, "OFFICE_HOME": str(tmp_path)})
    assert brains.chain(settings, "chief")[0] == "antigravity"
