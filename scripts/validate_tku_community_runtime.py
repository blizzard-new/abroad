"""Exercise the selected policy in the existing disposable Supabase harness."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_supabase_runtime as runtime
from exchange_info.community_repositories import PublicCommunityPublicationRequest, PublicCommunityResourceType
from exchange_info.models import CommunityPost, CommunityPostComment, CommunityBoardKind, CommunityIdentityMode


def validate_policy(context):
    runtime._psql(context, """
insert into public.exchange_accounts(id,email,profile,created_at,updated_at) values
('runtime-tku-policy-member','tku-policy-member@example.test',jsonb_build_object('display_name','跨校會員','email_verified',true,'student_status_verified',false,'home_university','國立臺北大學','verified_university','國立臺北大學','verified_department','自填系所'),now()-interval '30 days',now()),
('runtime-tku-policy-pending','tku-policy-pending@example.test',jsonb_build_object('display_name','未驗證會員','email_verified',false,'student_status_verified',false),now()-interval '30 days',now()),
('runtime-tku-policy-student','tku-policy-student@example.test',jsonb_build_object('display_name','已驗證學生','email_verified',true,'student_status_verified',true,'verified_university','長庚大學','verified_department','資訊工程學系'),now()-interval '30 days',now());
""")
    for actor in ["member", "pending", "student"]:
        token = runtime._community_token(f"tku-policy-{actor}")
        runtime._psql(context, f"""
insert into public.exchange_community_identities(id,account_id,display_name,access_token_hash,created_at,updated_at)
values('runtime-tku-policy-identity-{actor}','runtime-tku-policy-{actor}','合成政策身分','{token}',now()-interval '30 days',now());
""")

    def publish(actor, resource, content, suffix):
        request = PublicCommunityPublicationRequest(
            mutation_id=f"runtime-tku-policy-{suffix}", account_id=f"runtime-tku-policy-{actor}",
            identity_id=f"runtime-tku-policy-identity-{actor}",
            access_token_hash=runtime._community_token(f"tku-policy-{actor}"),
            resource_type=resource, content=content.model_dump(mode="json"),
        )
        result = runtime._rpc(context, "exchange_commit_public_community_publication", runtime._public_publication_payload(request))
        runtime._require(result.status == 200, f"Policy RPC failed: {result.status} {result.payload}")
        return result.payload

    commits = 0
    for board, school in [("cgu","長庚大學"),("ntpu","國立臺北大學"),("ntu","國立臺灣大學"),("tku","淡江大學")]:
        post = CommunityPost(id=f"runtime-tku-policy-post-{board}", board_id=board,
            board_kind=CommunityBoardKind.UNIVERSITY_EXCHANGE, school_name=school,
            author_id="placeholder", display_name="不可採用的客户端名稱", title="合成跨校測試",
            body="已驗證 Email 的跨校會員可以發文。")
        committed = publish("member", PublicCommunityResourceType.POST, post, f"post-{board}")
        runtime._require(committed["status"] == "committed", f"Cross-school post denied: {committed}")
        runtime._require(committed["content"]["display_name"] == "匿名學生", "Client byline was trusted")
        runtime._require(publish("member", PublicCommunityResourceType.POST, post, f"post-{board}") == committed, "Policy retry differs")
        pending = publish("pending", PublicCommunityResourceType.POST, post, f"pending-{board}")
        runtime._require(pending["status"] == "email_unverified", f"Unverified writer allowed: {pending}")
        comment = CommunityPostComment(id=f"runtime-tku-policy-comment-{board}", post_id=post.id,
            author_id="placeholder", display_name="placeholder", body="合成跨校會員留言。")
        runtime._require(publish("member", PublicCommunityResourceType.COMMENT, comment, f"comment-{board}")["status"] == "committed", "Cross-school reply denied")
        runtime._require(publish("pending", PublicCommunityResourceType.COMMENT, comment, f"pending-comment-{board}")["status"] == "email_unverified", "Unverified reply allowed")
        commits += 2

    byline = CommunityPost(id="runtime-tku-policy-byline", board_id="ntpu",
        board_kind=CommunityBoardKind.UNIVERSITY_EXCHANGE, school_name="國立臺北大學",
        author_id="placeholder", display_name="不可採用的客户端名稱", title="合成系所署名",
        body="伺服器署名與身分預覽應相同。", identity_mode=CommunityIdentityMode.VERIFIED_DEPARTMENT)
    rejected = publish("member", PublicCommunityResourceType.POST, byline, "self-declared-byline")
    runtime._require(rejected["status"] == "student_verification_required", "Self-declared school authorized a verified byline")
    named = publish("student", PublicCommunityResourceType.POST, byline, "verified-byline")
    runtime._require(named["status"] == "committed", f"Verified byline denied: {named}")
    runtime._require(named["content"]["display_name"] == "長庚大學 資訊工程學系學生", "SQL byline differs from preview")
    counts = runtime._psql(context, """
select (select count(*) from public.exchange_community_posts where id like 'runtime-tku-policy-%'),
       (select count(*) from public.exchange_community_post_comments where id like 'runtime-tku-policy-%'),
       (select count(*) from public.exchange_community_publish_events where account_id like 'runtime-tku-policy-%');
""")
    runtime._require(counts == "5|4|9", f"Unexpected policy/retry counts: {counts}")
    return {"school_boards":4,"cross_school_posts":4,"cross_school_comments":4,
            "unverified_writes_denied":8,"retry_duplicates":0,"self_declared_byline_denied":True,
            "preview_matches_sql_byline":True,"committed_resources":commits+1}


def main():
    original = runtime.validate_runtime
    def validate(context):
        result = original(context)
        result["tku_selected_community_policy"] = validate_policy(context)
        return result
    runtime.validate_runtime = validate
    # Keep-free execution always uses the harness's generated project and mandatory
    # cleanup. It never reads or connects to a configured production project.
    return runtime.main([])


if __name__ == "__main__":
    raise SystemExit(main())
