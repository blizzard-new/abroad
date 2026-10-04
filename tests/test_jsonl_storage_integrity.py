from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import exchange_info.storage as storage_module
from exchange_info.models import (
    CommunityAnswer,
    CommunityQuestion,
    ExperienceSubmission,
    UserAccount,
)
from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import (
    append_community_answer,
    append_community_question,
    append_experience_submission,
    data_paths,
    load_community_answers,
    load_community_questions,
    load_experience_submissions,
    load_user_accounts,
    save_user_accounts,
    write_jsonl,
)


def _account(index: int) -> UserAccount:
    return UserAccount(
        email=f"atomic-{index}@example.com",
        display_name=f"原子帳號 {index}",
    )


def test_storage_lock_key_does_not_change_when_parent_and_file_appear(
    tmp_path,
) -> None:
    path = tmp_path / "processed" / "user_accounts.jsonl"
    before = storage_module._storage_lock_key(path)

    path.parent.mkdir(parents=True)
    path.write_text("", encoding="utf-8")

    assert storage_module._storage_lock_key(path) == before


def test_jsonl_replacement_never_exposes_a_partially_written_destination(
    tmp_path,
) -> None:
    original = _account(0)
    first = _account(1)
    second = _account(2)
    save_user_accounts([original], tmp_path)
    path = data_paths(tmp_path)["user_accounts"]
    original_bytes = path.read_bytes()
    first_row_written = threading.Event()
    continue_write = threading.Event()
    errors: list[BaseException] = []

    def slow_rows():
        yield first
        first_row_written.set()
        assert continue_write.wait(timeout=5)
        yield second

    def writer() -> None:
        try:
            write_jsonl(path, slow_rows())
        except BaseException as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    thread = threading.Thread(target=writer)
    thread.start()
    assert first_row_written.wait(timeout=5)

    assert path.read_bytes() == original_bytes

    continue_write.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert errors == []
    assert [row.id for row in load_user_accounts(tmp_path)] == [
        first.id,
        second.id,
    ]
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []


def test_jsonl_write_failure_preserves_previous_file_and_cleans_temporary(
    tmp_path,
    monkeypatch,
) -> None:
    original = _account(0)
    replacement = _account(1)
    save_user_accounts([original], tmp_path)
    path = data_paths(tmp_path)["user_accounts"]
    original_bytes = path.read_bytes()

    def fail_replace(source, destination) -> None:
        raise OSError("simulated atomic replace failure")

    monkeypatch.setattr(storage_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated atomic replace failure"):
        save_user_accounts([replacement], tmp_path)

    assert path.read_bytes() == original_bytes
    assert [row.id for row in load_user_accounts(tmp_path)] == [original.id]
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []


def test_concurrent_jsonl_repository_account_upserts_do_not_lose_rows(
    tmp_path,
) -> None:
    accounts = [_account(index) for index in range(32)]
    start = threading.Barrier(len(accounts))

    def save(account: UserAccount) -> None:
        repository = JsonlAccountRepository(tmp_path)
        start.wait(timeout=10)
        repository.save_account(account)

    with ThreadPoolExecutor(max_workers=len(accounts)) as executor:
        futures = [executor.submit(save, account) for account in accounts]
        for future in futures:
            future.result(timeout=20)

    stored = JsonlAccountRepository(tmp_path).list_accounts()
    assert len(stored) == len(accounts)
    assert {row.id for row in stored} == {row.id for row in accounts}
    assert {row.email for row in stored} == {row.email for row in accounts}
    path = data_paths(tmp_path)["user_accounts"]
    assert len(path.read_text(encoding="utf-8").splitlines()) == len(accounts)
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []


@pytest.mark.parametrize(
    ("factory", "append", "load"),
    [
        (
            lambda index: CommunityQuestion(
                school_name="併發測試大學",
                home_university="長庚大學",
                topic="application",
                title=f"併發問題 {index}",
                body=f"這是第 {index} 筆同時寫入的申請問題。",
            ),
            append_community_question,
            load_community_questions,
        ),
        (
            lambda index: CommunityAnswer(
                question_id="concurrent-question",
                body=f"這是第 {index} 筆同時寫入且不應遺失的回答。",
            ),
            append_community_answer,
            load_community_answers,
        ),
        (
            lambda index: ExperienceSubmission(
                school_name="併發測試大學",
                home_university="長庚大學",
                title=f"交換經驗 {index}",
                summary=(
                    f"這是第 {index} 筆同時送出的交換經驗，"
                    "必須完整保存且不能被其他投稿覆蓋。"
                ),
                exchange_year="2026",
            ),
            append_experience_submission,
            load_experience_submissions,
        ),
    ],
)
def test_concurrent_jsonl_append_operations_do_not_lose_rows(
    tmp_path,
    factory,
    append,
    load,
) -> None:
    records = [factory(index) for index in range(24)]
    start = threading.Barrier(len(records))

    def save(record) -> None:
        start.wait(timeout=10)
        append(record, tmp_path)

    with ThreadPoolExecutor(max_workers=len(records)) as executor:
        futures = [executor.submit(save, record) for record in records]
        for future in futures:
            future.result(timeout=20)

    stored = load(tmp_path)
    assert len(stored) == len(records)
    assert {row.id for row in stored} == {row.id for row in records}
