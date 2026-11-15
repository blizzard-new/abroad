"""OFFICE_POST_EVERY_DAYS=2: the office makes and publishes its posts every second day, not every day."""

from datetime import date, datetime, timedelta, timezone

import pytest

from office import cadence, checkup
from office.brand import PILLAR_ROTATION, pillar_for
from office.config import Settings
from office.models import ChiefAction
from office.office import Office
from office.pipeline import run_day
from office.scheduler import tick


def make(tmp_path, **env) -> Office:
    base = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}
    base.update({k: str(v) for k, v in env.items()})
    return Office(Settings.from_env(env=base))


def morning(day: date) -> datetime:
    """09:00 in Taipei on that day: after the 07:30 start."""
    return datetime(day.year, day.month, day.day, 1, 0, tzinfo=timezone.utc)


def started(office: Office, day: date) -> bool:
    return tick(office, morning(day), background=False).get("run") == day.isoformat()


DAY = date(2030, 1, 7)


def test_every_day_is_still_the_default(tmp_path):
    office = make(tmp_path)
    assert office.settings.post_every_days == 1
    assert started(office, DAY) and started(office, DAY + timedelta(days=1)) and started(office, DAY + timedelta(days=2))


def test_every_second_day_the_office_works_and_the_days_between_stay_quiet(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    assert started(office, DAY)
    made = len(office.store.drafts())
    assert made > 0
    assert not started(office, DAY + timedelta(days=1))
    assert len(office.store.drafts()) == made  # nothing written on the day in between
    assert started(office, DAY + timedelta(days=2))
    assert not started(office, DAY + timedelta(days=3))
    assert started(office, DAY + timedelta(days=4))


def test_a_pause_does_not_make_the_office_wait_for_its_own_day(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    assert started(office, DAY)
    assert started(office, DAY + timedelta(days=8))  # the computer was off for a week: the first day back is a posting day
    assert not started(office, DAY + timedelta(days=9))
    assert started(office, DAY + timedelta(days=10))


def test_a_run_the_boss_starts_by_hand_counts_from_that_day(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    assert started(office, DAY)
    run_day(office, DAY + timedelta(days=1), force=True)  # 「開始今天的工作」 on the off day
    assert not started(office, DAY + timedelta(days=2))
    assert started(office, DAY + timedelta(days=3))


def test_three_days_and_nonsense_values(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=3)
    assert started(office, DAY) and not started(office, DAY + timedelta(days=1)) and not started(office, DAY + timedelta(days=2))
    assert started(office, DAY + timedelta(days=3))
    assert make(tmp_path / "a", OFFICE_POST_EVERY_DAYS="often").settings.post_every_days == 1
    assert make(tmp_path / "b", OFFICE_POST_EVERY_DAYS=0).settings.post_every_days == 1
    assert make(tmp_path / "c", OFFICE_POST_EVERY_DAYS=999).settings.post_every_days == 30


def test_a_failed_run_does_not_count_as_a_working_day(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    run_id = office.store.start_run(DAY.isoformat(), "offline")
    office.store.finish_run(run_id, "failed", error="企劃失敗")
    assert office.posting_day(DAY) and office.posting_day(DAY + timedelta(days=1))  # nothing succeeded, so every day is open


# ---- the other things that make posts ----
def at_local(day: date, hh: int, mm: int) -> datetime:
    return datetime(day.year, day.month, day.day, hh - 8, mm, tzinfo=timezone.utc)


def test_a_fixed_daily_post_job_follows_the_posting_days_and_a_report_does_not(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    chief = office.staff["chief"]
    assert "R1" in chief.execute(ChiefAction(type="add_routine", task_kind="threads", instructions="這週的獎學金截止日", times=["15:00"]))
    office.hire("小美", "Dcard 研究員", "研究 Dcard")
    assert "R2" in chief.execute(ChiefAction(type="add_routine", name="小美", task_kind="report", instructions="看 Dcard", times=["15:00"]))

    assert started(office, DAY)  # a posting day
    assert office.run_routines(at_local(DAY, 15, 0)) == [1, 2]
    off = DAY + timedelta(days=1)
    assert office.run_routines(at_local(off, 15, 0)) == [2]  # the Threads job waits; the report still runs
    assert office.run_routines(at_local(DAY + timedelta(days=2), 15, 0)) == [1, 2]  # and nothing was marked done while it waited


def test_a_hired_writer_with_a_daily_threads_post_follows_the_posting_days(tmp_path):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=2)
    colleague = office.hire("小美", "Threads 小編", "寫 Threads")
    office.update_hire(colleague.id, daily="寫一則關於住宿的 Threads", daily_kind="threads")
    assert tick(office, morning(DAY), background=False).get("hire_dailies") == ["小美"]
    assert "hire_dailies" not in tick(office, morning(DAY + timedelta(days=1)), background=False)
    assert tick(office, morning(DAY + timedelta(days=2)), background=False).get("hire_dailies") == ["小美"]


# ---- what a posting day contains ----
def test_the_content_rotation_still_reaches_every_pillar_when_only_every_second_day_posts():
    days = [date(2030, 1, 7) + timedelta(days=2 * n) for n in range(40)]
    assert {pillar_for(d, 2) for d in days} == set(PILLAR_ROTATION)
    # with calendar days alone, every second day would only ever reach half of the ten slots
    assert len({pillar_for(d) for d in days}) < len(set(PILLAR_ROTATION))
    # and every-day behavior is exactly what it was
    d = date(2030, 1, 7)
    assert pillar_for(d) == PILLAR_ROTATION[d.toordinal() % len(PILLAR_ROTATION)]


@pytest.mark.parametrize("every", [1, 2, 3])
def test_the_weekly_long_video_is_made_once_a_week_whichever_days_post(tmp_path, every):
    office = make(tmp_path, OFFICE_POST_EVERY_DAYS=every)
    strategist = office.staff["strategist"]
    monday = date(2030, 1, 7)
    posting = [monday + timedelta(days=n) for n in range(0, 57 + every, every)]  # a little past the last Sunday
    longs = [d for d in posting if any(s.channel == "youtube" and s.format == "long" for s in strategist.slots(d))]
    sundays = [d for d in (monday + timedelta(days=n) for n in range(57)) if d.weekday() == 6]
    assert len(sundays) == 8
    # each Sunday is made on exactly one posting day: that Sunday, or the first posting day after it when it was skipped
    for sunday in sundays:
        assert len([d for d in longs if 0 <= (d - sunday).days < every]) == 1, sunday
    # and no long video lands on a day that has no Sunday just before it
    assert all(any(0 <= (d - s).days < every for s in sundays + [monday - timedelta(days=1)]) for d in longs)


# ---- what the boss is told ----
def test_the_check_up_and_leo_say_when_the_next_posting_day_is(tmp_path):
    daily = make(tmp_path / "d")
    assert "OFFICE_POST_EVERY_DAYS=2" in checkup.cadence_rows(daily.settings, daily.store)[0].detail

    office = make(tmp_path / "e", OFFICE_POST_EVERY_DAYS=2)
    assert "今天是發文日" in checkup.cadence_rows(office.settings, office.store)[0].detail
    run_day(office, office.today())
    detail = checkup.cadence_rows(office.settings, office.store)[0].detail
    next_day = office.today() + timedelta(days=2)
    assert "今天已經開工" in detail and f"{next_day.month}/{next_day.day}" in detail
    assert "每 2 天一次" in office.staff["chief"].state_text()


def test_describe_for_a_day_between():
    class Store:
        def run_for_day(self, day):
            return None

        def last_run_day(self, before):
            return "2030-01-07"

    assert cadence.describe(Store(), 2, date(2030, 1, 8), "07:30") == "今天不發文，下一個發文日是 1/9"
    assert cadence.describe(Store(), 2, date(2030, 1, 9), "07:30") == "今天是發文日（07:30 開工）"
