"""The boss changes the office's daily times and fixed daily jobs by telling Leo; drafts still wait for approval."""

from datetime import date, datetime, time, timezone

import pytest

from office.config import Settings
from office.models import ChiefAction
from office.office import Office
from office.scheduler import tick


@pytest.fixture
def office(tmp_path):
    env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}
    return Office(Settings.from_env(env=env))


def do(office, **fields) -> str:
    return office.staff["chief"].execute(ChiefAction(**fields))


def wait_for(predicate, seconds=10.0):
    import time as clock

    end = clock.time() + seconds
    while clock.time() < end:
        if predicate():
            return True
        clock.sleep(0.05)
    return False


def test_start_and_posting_times_change_and_survive_a_restart(office, tmp_path):
    assert "改成 09:00" in do(office, type="set_office_times", which="start", times=["9:00"])
    assert "每天 3 篇" in do(office, type="set_office_times", which="threads", times=["21:00", "08:30", "12:30"])
    assert office.settings.daily_at == time(9, 0)
    assert office.settings.threads_slots == (time(8, 30), time(12, 30), time(21, 0))
    assert "開工 09:00；Threads 發文 08:30、12:30、21:00" in office.staff["chief"].state_text()

    morning = datetime(2030, 1, 7, 0, 30, tzinfo=timezone.utc)  # 08:30 in Taipei: before the new start time
    assert "run" not in tick(office, morning, background=False)
    assert tick(office, morning.replace(hour=1), background=False)["run"] == "2030-01-07"
    threads = [d for d in office.store.drafts() if d["channel"] == "threads"]
    assert len(threads) == 3  # one Threads post per posting time

    again = Office(Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}))
    assert again.settings.daily_at == time(9, 0)
    assert "07:30" in do(again, type="set_office_times", which="start", times=["default"])
    assert "看不懂" in do(again, type="set_office_times", which="start", times=["25:00"])
    assert "只能設一個" in do(again, type="set_office_times", which="instagram", times=["19:00", "20:00"])


def test_a_fixed_daily_job_runs_at_its_time_and_lands_in_the_inbox(office):
    answer = do(office, type="add_routine", task_kind="threads", instructions="這週的獎學金截止日", times=["15:00"])
    assert "R1｜每天 15:00｜阿脆寫一則 Threads：這週的獎學金截止日" in answer
    assert "R1｜每天 15:00" in office.staff["chief"].state_text()

    day = date(2030, 1, 7)
    at = lambda hh, mm: office.at(day, time(hh, mm)).astimezone(timezone.utc)  # noqa: E731
    assert office.run_routines(at(14, 59)) == []
    assert office.run_routines(at(15, 0)) == [1]
    assert office.run_routines(at(15, 30)) == []  # once a day
    assert wait_for(lambda: any(d["channel"] == "threads" and d["status"] in {"pending_approval", "needs_changes"} for d in office.store.drafts()))
    assert any("⏰ 固定排程 R1（15:00）" in m["text"] for m in office.store.chat())
    assert office.run_routines(at(15, 0).replace(day=8)) == [1]  # and again the next day

    assert "刪掉了：R1" in do(office, type="remove_routine", routine_id=1)
    assert office.routines() == []
    assert "沒有編號 R1" in do(office, type="remove_routine", routine_id=1)


def test_routine_rules(office):
    assert "只能交給新同事" in do(office, type="add_routine", task_kind="report", instructions="看 Dcard", times=["10:00"])
    office.hire("小美", "Dcard 研究員", "研究 Dcard")
    assert "小美查資料回報" in do(office, type="add_routine", name="小美", task_kind="report", instructions="看 Dcard", times=["10:00"])
    assert "IG 圖和影片請交給" in do(office, type="add_routine", name="小美", task_kind="carousel", instructions="x", times=["10:00"])
    assert "Mori做一則 IG 輪播" in do(office, type="add_routine", task_kind="carousel", instructions="選校", times=["11:00"])
    assert "沒有叫 阿明" in do(office, type="add_routine", name="阿明", task_kind="threads", instructions="x", times=["10:00"])
