"""Exercise the deployed forum RPC on an isolated PostgreSQL, never production."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
import uuid

import pytest
from exchange_info.community_repositories import PublicCommunityPublicationRequest, PublicCommunityResourceType, public_community_publication_fingerprint

MIGRATIONS = Path(__file__).parents[1] / "supabase/migrations"
MIGRATION = MIGRATIONS / "20261008130000_ntu_school_board.sql"
POSTGRES_IMAGE = "postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"
FUNCTION = "public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)"


def test_migration_versions_are_unique():
    versions = [path.name.split("_", 1)[0] for path in MIGRATIONS.glob("*.sql")]
    assert len(versions) == len(set(versions))


@pytest.mark.skipif(os.environ.get("EXCHANGE_TEST_POSTGRES") != "1", reason="opt in to isolated Docker PostgreSQL")
def test_ntu_forum_rpc_migration_preserves_authorization_and_replays():
    name = "exchange-ntu-migration-" + uuid.uuid4().hex[:10]

    def docker(*args, input=None, check=True):
        result = subprocess.run(["docker", *args], input=input, text=True, capture_output=True, check=False, timeout=60)
        if check and result.returncode:
            pytest.fail(result.stderr)
        return result

    def sql(text):
        return docker("exec", "-i", name, "psql", "-U", "postgres", "-qAt", "-v", "ON_ERROR_STOP=1", input=text).stdout.strip()

    def apply(filename):
        sql((MIGRATIONS / filename).read_text(encoding="utf-8"))

    def definition():
        return sql(f"select pg_get_functiondef('{FUNCTION}'::regprocedure);")

    def metadata():
        return sql(f"select jsonb_build_array(proowner,proacl,prosecdef,proconfig) from pg_proc where oid='{FUNCTION}'::regprocedure;")

    def publish(event, board="ntu", school="國立臺灣大學", account="ntu-test", token="a" * 64, kind="post", extra=None):
        payload = {"board_id":board,"board_kind":"university_exchange","school_name":school,
                   "post_type":"discussion","topic":"application","title":"論壇測試標題",
                   "body":"隔離資料庫測試內文，不會寫入正式平台。","identity_mode":"anonymous","status":"approved"}
        if kind == "comment":
            payload = {"post_id":"post-ntu-before","body":"隔離資料庫測試留言。","identity_mode":"anonymous","status":"approved"}
        payload.update(extra or {})
        payload["id"] = f"{kind}-{event}"
        payload["author_id"] = "identity-" + account
        payload["display_name"] = "用戶端提供的名稱"
        mutation_id = "runtime-ntu-migration-" + event
        request = PublicCommunityPublicationRequest(mutation_id=mutation_id, account_id=account, identity_id="identity-"+account,
                                                   access_token_hash=token, resource_type=PublicCommunityResourceType(kind), content=payload)
        fingerprint = public_community_publication_fingerprint(request)
        payload = request.content
        result = sql("begin; set local role service_role; select public.exchange_commit_public_community_publication("
                     f"'{mutation_id}','{fingerprint}','{account}','identity-{account}','{token}','{kind}',"
                     "$payload$" + json.dumps(payload, ensure_ascii=False) + "$payload$::jsonb); commit;")
        return json.loads(result)

    docker("run", "--detach", "--name", name, "--network", "none", "--tmpfs", "/var/lib/postgresql/data",
           "--env", "POSTGRES_PASSWORD=isolated-ntu-test-only", POSTGRES_IMAGE)
    try:
        for _ in range(60):
            if docker("exec", name, "pg_isready", "-U", "postgres", "-h", "127.0.0.1", check=False).returncode == 0:
                break
            time.sleep(.25)
        else:
            pytest.fail("isolated PostgreSQL did not become ready")
        sql("create role anon; create role authenticated; create role service_role; grant usage on schema public to service_role;")
        apply("20260728120722_accounts_workspaces.sql")
        sql("alter table public.exchange_accounts add column community_suspended_until timestamptz;")
        suspension = (MIGRATIONS / "20260823130000_atomic_workspace_and_suspension.sql").read_text()
        table_sql = "create table public.exchange_community_suspension_audits (" + suspension.split("create table public.exchange_community_suspension_audits (", 1)[1].split(";", 1)[0] + ";"
        sql(table_sql)
        for filename in ("20260823160000_atomic_public_community.sql", "20260930100000_discussion_threads_reactions.sql", "20261003100000_open_school_boards.sql"):
            apply(filename)
        # Apply the two exact school-choice patches affecting the forum. Other
        # functions in that migration belong to unrelated subsystems.
        choice = (MIGRATIONS / "20261007100000_school_choice_replaces_student_card.sql").read_text()
        sql(choice.split("begin\n", 1)[0] + "begin\n" + choice.split("  -- 2.", 1)[1].split("  -- 4.", 1)[0].split("\n", 1)[1] + "end\n$migration$;")
        assert "v_account.profile ->> 'home_university'" in definition()
        sql("""
insert into public.exchange_accounts(id,email,profile) values
 ('ntu-test','ntu@example.test','{"home_university":"國立臺灣大學","email_verified":true}'::jsonb),
 ('unverified','unverified@example.test','{"home_university":"國立臺灣大學","email_verified":false}'::jsonb);
insert into public.exchange_community_identities(id,account_id,display_name,access_token_hash) values
 ('identity-ntu-test','ntu-test','測試學生',repeat('a',64)),
 ('identity-unverified','unverified','未驗證學生',repeat('c',64));
""")
        assert publish("ntu-before")["status"] == "board_forbidden"
        old_def, old_metadata = definition(), metadata()
        apply(MIGRATION.name)
        new_def = definition()
        ntu_line = "           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')\n"
        assert new_def.replace(ntu_line, "") == old_def
        assert metadata() == old_metadata
        apply(MIGRATION.name)
        assert definition() == new_def
        assert publish("ntu-before")["status"] == "committed"
        assert publish("ntu-before")["idempotent"] is True
        assert publish("wrong-school", school="國立臺北大學")["status"] == "board_forbidden"
        assert publish("wrong-board", board="unsupported")["status"] == "board_forbidden"
        assert publish("wrong-token", token="b" * 64)["status"] == "identity_conflict"
        assert publish("unverified-email", account="unverified", token="c" * 64)["status"] == "email_unverified"
        assert publish("cgu", board="cgu", school="長庚大學")["status"] == "committed"
        assert publish("ntpu", board="ntpu", school="國立臺北大學")["status"] == "committed"
        assert publish("generic", board="university:example", school="其他學校")["status"] == "committed"
        assert publish("ntu-comment", kind="comment")["status"] == "committed"
        for role in ("anon", "authenticated"):
            assert sql(f"select has_function_privilege('{role}','{FUNCTION}','execute');") == "f"
        assert sql(f"select has_function_privilege('service_role','{FUNCTION}','execute');") == "f"
        assert sql("select has_function_privilege('service_role','public.exchange_commit_public_community_publication(text,text,text,text,text,text,jsonb)','execute');") == "t"
        # Unexpected definitions must abort rather than weaken another gate.
        sql(new_def.replace("= 'ntpu'", "= 'renamed-board'").replace(ntu_line, ""))
        failed = docker("exec", "-i", name, "psql", "-U", "postgres", "-qAt", "-v", "ON_ERROR_STOP=1", input=MIGRATION.read_text(), check=False)
        assert failed.returncode != 0 and "expected school-board allowlist not found" in failed.stderr
    finally:
        docker("rm", "--force", name, check=False)
