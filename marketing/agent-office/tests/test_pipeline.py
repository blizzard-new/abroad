import json
from datetime import date, datetime, timezone

from office.pipeline import run_day
from office.scheduler import tick


def test_a_day_fills_the_inbox(make_office):
    office = make_office()
    run_id = run_day(office, date(2026, 10, 23))
    drafts = office.store.drafts(day="2026-10-23")
    kinds = sorted((d["channel"], d["format"]) for d in drafts)
    # Friday 2026-10-23 is a value day: two Threads posts, an IG carousel and its YouTube Short (no story without renders).
    assert kinds == [("instagram", "carousel"), ("threads", "text"), ("threads", "text"), ("youtube", "short")]
    assert {d["status"] for d in drafts} == {"pending_approval"}
    assert office.store.latest_run()["status"] == "done"
    assert office.store.latest_run()["plan"]["items"]
    # A second call the same day does not redo the work.
    assert run_day(office, date(2026, 10, 23)) == run_id
    assert len(office.store.drafts(day="2026-10-23")) == 4


def test_sunday_adds_the_weekly_long_video_and_reels_reuse_one_video(make_office):
    office = make_office()
    run_day(office, date(2026, 10, 25))
    kinds = sorted((d["channel"], d["format"]) for d in office.store.drafts(day="2026-10-25"))
    assert ("youtube", "long") in kinds
    assert ("instagram", "reel") in kinds and ("youtube", "short") in kinds


def test_auto_approval_schedules_reviewed_drafts(make_office):
    office = make_office(OFFICE_APPROVAL="auto")
    run_day(office, date(2026, 10, 23))
    assert {d["status"] for d in office.store.drafts()} == {"approved"}


def test_events_tell_the_story_of_the_day(make_office):
    office = make_office()
    run_day(office, date(2026, 10, 23))
    events = office.store.events(limit=500)
    handoffs = [(e["agent"], e["data"]["to"]) for e in events if e["kind"] == "handoff"]
    assert ("strategist", "threads") in handoffs
    assert ("threads", "reviewer") in handoffs
    assert ("threads", "boss") in handoffs
    assert ("designer", "video") in handoffs
    assert any(e["kind"] == "whiteboard" for e in events)


def test_clock_starts_the_day_and_publishes_due_drafts_in_dry_run(make_office):
    office = make_office(OFFICE_APPROVAL="auto", OFFICE_DAILY_AT="07:30")
    morning = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)  # 08:00 in Taipei
    done = tick(office, morning, background=False)
    assert done["run"] == "2026-10-23"
    evening = datetime(2026, 10, 23, 14, 0, tzinfo=timezone.utc)  # 22:00, every slot has passed
    tick(office, evening, background=False)
    drafts = office.store.drafts()
    assert {d["status"] for d in drafts if d["channel"] == "threads"} == {"published"}
    assert len(list((office.settings.outbox_dir / "2026-10-23").glob("*threads*.json"))) == 2
    # This office was built without renders, so posts that need images or video fail with a readable reason.
    media_posts = [d for d in drafts if d["channel"] != "threads"]
    assert all(d["status"] == "failed" and "圖片或影片" in d["error"] for d in media_posts)


def test_boss_can_edit_reject_and_approve(make_office):
    office = make_office()
    run_day(office, date(2026, 10, 23))
    first, second = [d for d in office.store.drafts() if d["channel"] == "threads"]
    edited = office.edit(first["id"], {"text": "改過的主文", "status": "published"})
    assert edited["payload"]["text"] == "改過的主文" and edited["status"] == "pending_approval"
    assert office.reject(second["id"], "太硬了")["status"] == "rejected"
    approved = office.approve(first["id"], publish_now=True)
    assert approved["status"] == "approved"
    office.staff["publisher"].publish_due()
    assert office.store.draft(first["id"])["status"] == "published"


def test_threads_posts_carry_their_picture_when_media_has_a_public_host(make_office):
    office = make_office(OFFICE_MEDIA_HOST="supabase", SUPABASE_URL="https://p.supabase.co")
    image = office.settings.media_dir / "2026-10-23" / "threads-x.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"\xff\xd8jpg")
    run_day(office, date(2026, 10, 23))
    draft = next(d for d in office.store.drafts() if d["channel"] == "threads")
    office.store.update_draft(draft["id"], media={"image": office.media_ref(image)})
    published = office.staff["publisher"].publish(office.store.draft(draft["id"]))
    assert published["status"] == "published"
    record = json.loads(next((office.settings.outbox_dir / "2026-10-23").glob(f"{draft['id']:05d}-threads-*.json")).read_text(encoding="utf-8"))
    create = next(c for c in record["calls"] if c["url"].endswith("/threads"))
    assert create["params"]["media_type"] == "IMAGE" and create["params"]["image_url"].endswith("/2026-10-23/threads-x.jpg")
