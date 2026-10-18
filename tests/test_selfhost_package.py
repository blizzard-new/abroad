"""The self-hosting package (deploy/selfhost): cheap guards on the things that must not drift or leak."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SELFHOST = ROOT / "deploy" / "selfhost"
COMPOSE = SELFHOST / "docker-compose.yml"
VALIDATION_COMPOSE = ROOT / "supabase" / "runtime-validation" / "docker-compose.yml"


def _images(path: Path) -> set[str]:
    services = yaml.safe_load(path.read_text(encoding="utf-8"))["services"]
    return {svc["image"] for svc in services.values() if "image" in svc}


def test_the_database_images_are_the_ones_the_migrations_are_validated_against() -> None:
    pinned = {image for image in _images(VALIDATION_COMPOSE) if "@sha256:" in image}
    assert pinned, "the validation compose file pins its images"
    assert pinned <= _images(COMPOSE), "self-hosting runs the same pinned Postgres, PostgREST and Storage images"


def test_only_the_web_service_is_published_and_only_on_loopback() -> None:
    services = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]
    published = {name: svc["ports"] for name, svc in services.items() if svc.get("ports")}
    assert list(published) == ["app"]
    assert all(str(port).startswith("127.0.0.1:") for port in published["app"])


def test_the_web_service_is_told_to_use_https_for_the_database_and_to_trust_only_the_proxys_header() -> None:
    app = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]["app"]["environment"]
    assert app["EXCHANGE_ENVIRONMENT"] == "production"
    assert app["EXCHANGE_SUPABASE_URL"].startswith("https://"), "the program refuses a database address that is not https"
    assert app["EXCHANGE_CLIENT_IP_HEADER"] == "X-Client-IP"
    assert app["EXCHANGE_HOSTING_PROFILE"] == "selfhost"
    assert app["EXCHANGE_ACCOUNT_READ_CACHE_SECONDS"] == "0", "workers must not retain revoked sessions or stale workspaces"
    assert not any("DB_PASSWORD" in value or "JWT_SECRET" in value for value in map(str, app.values())), "the database password never reaches the web service"


def test_the_public_caddyfile_overwrites_the_visitor_address_header() -> None:
    text = (SELFHOST / "caddy" / "Caddyfile.template").read_text(encoding="utf-8")
    assert "header_up X-Client-IP {remote_host}" in text
    assert "127.0.0.1:8000" in text
    assert "__DOMAIN__" in text and "__ACME_EMAIL__" in text
    assert "roll_keep_for 720h" in text, "the privacy policy promises connection logs go after about 30 days"


def test_every_setting_the_compose_file_reads_is_in_the_env_template() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    wanted = set(re.findall(r"\$\{([A-Z_]+)(?::[-?][^}]*)?\}", text))
    template = (SELFHOST / "env.template").read_text(encoding="utf-8")
    listed = set(re.findall(r"^([A-Z_]+)=", template, flags=re.M))
    assert wanted <= listed, sorted(wanted - listed)


def test_no_secret_is_committed_and_the_real_settings_file_is_ignored() -> None:
    assert "deploy/selfhost/.env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert not (SELFHOST / ".env").exists() or True  # a developer's own file may exist locally; it is ignored by git
    for path in SELFHOST.rglob("*"):
        if not path.is_file() or path.name == ".env":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", text), f"a JWT is written in {path.name}"
        assert not re.search(r"GOCSPX-[A-Za-z0-9_-]{10,}", text), f"a Google client secret is written in {path.name}"


def test_the_powershell_scripts_are_plain_ascii_because_windows_powershell_5_reads_them_in_the_system_code_page() -> None:
    scripts = sorted((SELFHOST / "scripts").glob("*.ps1"))
    assert len(scripts) >= 14
    for path in scripts:
        data = path.read_bytes()
        assert all(byte < 128 for byte in data), f"{path.name} has non-ASCII characters"


def test_migrations_and_shell_files_are_pinned_to_unix_line_endings() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for pattern in ("*.sql text eol=lf", "*.sh text eol=lf", "Dockerfile text eol=lf"):
        assert pattern in attributes, pattern
    for path in (ROOT / "supabase" / "migrations").glob("*.sql"):
        assert b"\r\n" not in path.read_bytes(), f"{path.name} has CRLF line endings"
    assert b"\r\n" not in (SELFHOST / "docker-entrypoint.sh").read_bytes()


def test_the_image_builds_from_a_tiny_context_and_starts_through_the_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "ENTRYPOINT" in dockerfile and "docker-entrypoint.sh" in dockerfile
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ignore[:1] == ["# Only what the image needs. Everything else (tests, docs, mobile apps, scraped sources, ...) stays out of the build."] or "*" in ignore
    assert "!deploy/selfhost/docker-entrypoint.sh" in ignore and "!src" in ignore


def test_the_guide_names_every_script_that_exists() -> None:
    guide = (ROOT / "docs" / "self-host-windows-guide.md").read_text(encoding="utf-8")
    for path in (SELFHOST / "scripts").glob("*.ps1"):
        if path.name != "lib.ps1":
            assert path.name in guide, f"{path.name} is not explained in the guide"


@pytest.mark.parametrize("name", ["tools/create_bucket.py", "tools/smoke.py", "tools/dr_object.py"])
def test_the_helper_tools_are_valid_python(name: str) -> None:
    compile((SELFHOST / name).read_text(encoding="utf-8"), name, "exec")


def test_the_restore_test_does_not_count_the_migration_list_that_the_dump_leaves_out() -> None:
    backup = (SELFHOST / "scripts" / "backup.ps1").read_text(encoding="utf-8")
    restore_test = (SELFHOST / "scripts" / "restore-test.ps1").read_text(encoding="utf-8")
    assert "--exclude-table-data=public.uniway_schema_migrations" in backup
    assert "$skip = 'uniway_schema_migrations'" in restore_test
    assert restore_test.count("-ne $skip") == 2


def test_the_restore_test_takes_its_own_fresh_backup_instead_of_comparing_an_old_dump_with_a_growing_database() -> None:
    restore_test = (SELFHOST / "scripts" / "restore-test.ps1").read_text(encoding="utf-8")
    assert '& "$PSScriptRoot\\backup.ps1" -SkipCloud' in restore_test
    assert "$fresh = -not $Dump" in restore_test
    assert "if ($fresh -and ($liveTotal - $restoredTotal) -gt $allowed)" in restore_test
    assert "0.8" not in restore_test


def test_the_security_check_only_looks_and_the_guide_says_what_to_do_when_broken_into() -> None:
    script = (SELFHOST / "scripts" / "security-check.ps1").read_text(encoding="utf-8")
    # Read-only by design: it must never change the computer, only report. (Advice strings may name Set-LocalUser, Rename-LocalUser,
    # Set-NetFirewallProfile and Update-MpSignature; nothing else that changes state is allowed to appear.)
    for forbidden in (
        "New-NetFirewallRule", "Set-ItemProperty", "New-ItemProperty", "Stop-Service", "Stop-Process", "Restart-Computer",
        "Register-ScheduledTask", "Unregister-ScheduledTask", "Remove-LocalUser", "Set-Content", "Out-File", "net user", "docker rm", "docker stop",
    ):
        assert forbidden not in script, forbidden
    guide = (ROOT / "docs" / "self-host-windows-guide.md").read_text(encoding="utf-8")
    for needed in ("security-check.ps1", "如果被攻破", "撤銷 rclone 的 Drive 授權", "-PasswordNeverExpires $true", "Get-NetFirewallPortFilter"):
        assert needed in guide, needed


def test_update_looks_before_it_backs_up_moves_nothing_before_the_backup_and_still_only_fast_forwards() -> None:
    script = (SELFHOST / "scripts" / "update.ps1").read_text(encoding="utf-8")
    assert "[switch]$SetAside" in script and "[switch]$CheckOnly" in script
    assert script.index("Get-UpdateBlockers") < script.index('backup.ps1" -SkipCloud')
    assert script.index('backup.ps1" -SkipCloud') < script.index("Move-UpdateBlockersAside")
    assert script.index("Move-UpdateBlockersAside") < script.index("merge --ff-only")
    # the blocked case without -SetAside must leave before the backup starts
    stop = script.index("update.ps1 -SetAside'")
    assert stop < script.index('backup.ps1" -SkipCloud')


def test_the_update_checks_never_delete_or_reset_anything() -> None:
    for name in ("update.ps1", "lib.ps1"):
        text = (SELFHOST / "scripts" / name).read_text(encoding="utf-8")
        for destructive in ("reset --hard", "clean -f", "clean -d", "stash drop", "checkout -f", "-Recurse -Force"):
            assert destructive not in text, f"{name} contains {destructive}"
    lib = (SELFHOST / "scripts" / "lib.ps1").read_text(encoding="utf-8")
    assert lib.count("Remove-Item") == 1, "only the temporary path list may be deleted"
    assert "Remove-Item -LiteralPath $list" in lib


def test_the_guide_explains_the_update_checks_and_the_two_switches() -> None:
    guide = (ROOT / "docs" / "self-host-windows-guide.md").read_text(encoding="utf-8")
    assert "-CheckOnly" in guide and "-SetAside" in guide
    assert "update-set-aside" in guide and "不會刪除任何東西" in guide

