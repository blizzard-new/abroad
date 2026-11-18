"""Verify per-school saved-application, file upload and byte-identical download on loopback.

Use only disposable development data. These are actual HTTP transactions, measured separately
from the student UI checks. The saved task is a student's preparation note, not an official receipt.
"""

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import requests


def check_school(base, school, target_override=None, verify_levels=False):
    home = school["school_name"]
    params = {"home_school": home}
    result = {"id": school["id"], "home": home}
    with requests.Session() as client:

        def send(method, path, **kw):
            response = client.request(method, base + path, timeout=150, **kw)
            response.raise_for_status()
            return response

        start = time.monotonic()
        target = None
        try:
            email = f"file-check-{uuid4().hex[:12]}@example.com"
            code = send(
                "POST", "/auth/email-verification/request", json={"email": email}
            ).json()["development_code"]
            token = send(
                "POST",
                "/auth/email-verification/confirm",
                json={"email": email, "code": code},
            ).json()["verification_token"]
            send(
                "POST",
                "/auth/register",
                json={
                    "email": email,
                    "password": uuid4().hex + "A!",
                    "display_name": "文件驗證測試生",
                    "email_verification_token": token,
                    "accept_terms": True,
                },
            )
            send("PATCH", "/auth/me", json={"home_university": home})
            result["stage"] = "catalogue"
            dashboard = send(
                "GET", "/student-dashboard", params={"school": home, "compact": "true"}
            ).json()
            rows = dashboard["partner_universities"]
            result["catalogue_rows"] = len(rows)
            # Only attempt official-status open destinations. Other states are recorded for UI-specific gates.
            target = next(
                (p for p in rows if p.get("availability_status") == "open"), None
            )
            if target_override:
                target = next(
                    row for row in rows if row["school_name"] == target_override
                )
            if target is None:
                result["outcome"] = "no_explicit_open_status"
                result["availability"] = dict(
                    Counter(p.get("availability_status") for p in rows)
                )
                return result
            target = target["school_name"]
            result["target"] = target
            result["stage"] = "favorite"
            workspace = send("GET", "/account/workspace", params=params).json()[
                "workspace"
            ]
            workspace["favorite_schools"] = [target]
            workspace["application_schools"] = [target]
            send("PUT", "/account/workspace", json=workspace)
            result["stage"] = "create_plan"
            saved = send(
                "POST",
                "/account/application-paths",
                json={
                    **params,
                    "target_school": target,
                    "academic_year": "116",
                    "application_round": "116-1（2027 秋季出國）"
                    if school["id"] == "cgu"
                    else "",
                    "departure_year": "2027",
                    "semester": "fall",
                    "college": "管理學院",
                    "department": "資訊管理學系",
                    "degree_level": "大學部",
                    "revision": 0,
                },
            ).json()
            endpoint = "/account/application-paths/" + saved["plan"]["id"]
            levels = [level for stage in saved["stages"] for level in stage["levels"]]
            result["level_types"] = dict(Counter(l["kind"] for l in levels))
            result["submission_steps"] = [
                l["title"] for l in levels if l["kind"] == "submission"
            ]
            result["handoff_sources"] = [
                {
                    "title": level["title"],
                    "origin": level.get("task_origin"),
                    "source": next(iter(level.get("source_urls", [])), None),
                }
                for level in levels
                if level["kind"] == "submission"
            ]
            files = [level for level in levels if level["kind"] == "file"]
            result["file_basis"] = dict(
                Counter(level.get("document_basis", "catalogued") for level in files)
            )
            revision = saved["revision"]
            if verify_levels:
                # Pre-nomination requirements whose applicability is established for this profile.
                required = [
                    l
                    for l in levels
                    if l["kind"] == "file"
                    and not l.get("conditional")
                    and not re.search(
                        r"返國|出發|行前|入學後|抵達|歸國|回國|錄取後|提名後",
                        l["stage_key"],
                    )
                ]
                # A synthetic student can elect to attach a reference or their own list;
                # report that action separately from catalogued unconditional requirements.
                if not required:
                    required = next(
                        (
                            [l]
                            for l in files
                            if l.get("document_basis") in {"reference_year", "personal"}
                        ),
                        [],
                    )
                result["linked_documents"] = []
                versions = {}
                for index, item in enumerate(required):
                    result["stage"] = "link_plan_requirement"
                    data = (
                        f"測試用合成文件。{home}→{target}｜{item['title']}"
                    ).encode()
                    document = send(
                        "POST",
                        "/account/vault/documents",
                        data={
                            "label": item["title"][:100],
                            "category": "other",
                            "purpose": "application_preparation",
                            "retention_days": "30",
                            "consent": "true",
                        },
                        files={
                            "file": (f"synthetic-{index + 1}.txt", data, "text/plain")
                        },
                    ).json()
                    file_id = document["versions"][-1]["id"]
                    changed = send(
                        "PUT",
                        endpoint + "/steps/" + item["id"],
                        params=params,
                        json={
                            "revision": revision,
                            "step": {
                                "version_id": file_id,
                                "confirmed": True,
                                "value": "",
                                **(
                                    {"applicable": True}
                                    if item.get("conditional")
                                    else {}
                                ),
                            },
                        },
                    ).json()
                    revision = changed["revision"]
                    versions[item["id"]] = (file_id, data)
                    result["linked_documents"].append(
                        {
                            "title": item["title"],
                            "basis": item.get("document_basis", "catalogued"),
                        }
                    )
                final = send("GET", endpoint, params=params).json()
                for key, (file_id, data) in versions.items():
                    assert final["plan"]["steps"][key]["version_id"] == file_id
                    assert final["plan"]["steps"][key]["confirmed"] is True
                    grant = send(
                        "POST", "/account/vault/versions/" + file_id + "/download-grant"
                    ).json()
                    assert (
                        send(
                            "POST",
                            grant["download_url"],
                            headers={"X-Vault-Download-Token": grant["token"]},
                        ).content
                        == data
                    )
                result["verified_plan_files"] = len(versions)
            result["stage"] = "upload"
            contents = (f"模擬學生的測試文件。\n{home} → {target}\n").encode()
            document = send(
                "POST",
                "/account/vault/documents",
                data={
                    "label": "個人準備筆記",
                    "category": "other",
                    "purpose": "application_preparation",
                    "retention_days": "30",
                    "consent": "true",
                },
                files={"file": ("preparation.txt", contents, "text/plain")},
            ).json()
            version = document["versions"][-1]["id"]
            result["stage"] = "link_file"
            task = {
                "id": "sample-file",
                "kind": "document",
                "stage": "home",
                "title": "個人準備筆記",
                "action": "prepare",
                "status": "done",
                "file_version_id": version,
            }
            send(
                "PUT",
                endpoint + "/workspace",
                params=params,
                json={"revision": revision, "tasks": [task]},
            )
            restored = send("GET", endpoint, params=params).json()
            confirmed = next(
                t for t in restored["workspace"]["tasks"] if t["id"] == task["id"]
            )
            assert (
                confirmed["effective_status"] == "done"
                and confirmed["file_version_id"] == version
            )
            assert not restored["platform_submitted"]
            result["stage"] = "download"
            grant = send(
                "POST", "/account/vault/versions/" + version + "/download-grant"
            ).json()
            restored_bytes = send(
                "POST",
                grant["download_url"],
                headers={"X-Vault-Download-Token": grant["token"]},
            ).content
            assert restored_bytes == contents
            result["outcome"] = "saved_download_matches"
            result["stage"] = "document_roundtrip_verified"
        except (
            requests.RequestException,
            KeyError,
            AssertionError,
            StopIteration,
        ) as e:
            result["outcome"] = "error"
            result["error"] = str(e)[:200]
        finally:
            result["seconds"] = round(time.monotonic() - start, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8819")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--schools", nargs="*")
    parser.add_argument(
        "--verify-levels",
        action="store_true",
        help="Link and roundtrip a synthetic file at each unconditional preparation document level",
    )
    parser.add_argument(
        "--ui-results",
        type=Path,
        nargs="*",
        default=[],
        help="Use the actually selected partner from a completed browser journey",
    )
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Disposable loopback development server required")
    registry = requests.get(args.base + "/universities", timeout=120)
    registry.raise_for_status()
    targets = {}
    for path in args.ui_results:
        for row in map(json.loads, path.read_text().splitlines()):
            if row.get("can_start_rows") and row.get("target"):
                targets[row["id"]] = row["target"]
    done = set()
    if args.out.exists():
        done = {
            row["id"]
            for row in map(json.loads, args.out.read_text().splitlines())
            if row["outcome"] != "error"
        }
    with args.out.open("a", encoding="utf-8", buffering=1) as report:
        for school in registry.json():
            if school["id"] in done or (
                args.schools and school["id"] not in args.schools
            ):
                continue
            row = check_school(
                args.base, school, targets.get(school["id"]), args.verify_levels
            )
            print(json.dumps(row, ensure_ascii=False), file=report)
            print(
                row["id"],
                row["outcome"],
                row["seconds"],
                row.get("error", ""),
                flush=True,
            )


if __name__ == "__main__":
    main()
