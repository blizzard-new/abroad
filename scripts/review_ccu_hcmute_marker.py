"""Review the campus marker linked by HCMUTE's official GTSD2026 page."""
from __future__ import annotations

import json
from urllib.parse import unquote

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from review_ccu_followup_batch import evidence, fact, receipt, response_text


def main():
    index = receipt(68, "official-conference-index")
    index_body = BeautifulSoup(response_text(index), "html.parser")
    assert any(a.get("href", "").rstrip("/") == "https://gtsd2026.hcmute.edu.vn"
               for a in index_body.find_all("a", href=True))
    venue = receipt(68, "official-gtsd2026-public")
    soup = BeautifulSoup(response_text(venue), "html.parser")
    url = "https://maps.app.goo.gl/StEAfixJb3seGqCA7"
    link = soup.find("a", href=url)
    assert link and "No.1, Vo Van Ngan Street" in link.get_text(" ", strip=True)
    marker = receipt(68, "official-gtsd2026-campus-marker")
    resolved = unquote(marker["resolved_url"]).replace("+", " ")
    identity = "Trường Đại học Công nghệ Kỹ thuật Thành phố Hồ Chí Minh"
    assert identity in resolved
    assert "!3d10.8506324!4d106.7719131" in resolved
    assert "@10.8506324,106.7693382" in resolved
    original = next(r for r in json.loads((B / "profile-reviewed-fields.json").read_text())
                    if r["ccu_page"] == 68)
    partner = next(json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines()
                   if json.loads(line)["source_pages"][0] == 68)
    note = ("官方會議入口所連GTSD2026頁將No.1 Vo Van Ngan校址連至同名大學marker。"
            "採!3d/!4d的10.8506324,106.7719131，不採@視窗經度106.7693382，"
            "不從未地理配準的虛擬導覽像素或互相差異的未附原始來源座標猜值。"
            "此為校園代表點，會議資訊不證明個人接收校區、宿舍或2027課程安排。")
    ev = [evidence(68, "official-conference-index", "https://gtsd2026.hcmute.edu.vn"),
          evidence(68, "official-gtsd2026-public", link.get_text(" ", strip=True) + "; " + url),
          evidence(68, "official-gtsd2026-campus-marker", identity + " !3d10.8506324!4d106.7719131")]
    ev[-1]["resolved_url"] = marker["resolved_url"]
    row = {"school_name": partner["school_name"], "country": partner["country"],
           "city": original["fields"]["city"]["value"], "latitude": 10.8506324,
           "longitude": 106.7719131, "geocode_status": "verified",
           "geocoded_at": marker["checked_at"], "source_url": marker["source_url"],
           "identity_source_url": venue["source_url"], "precision": "representative", "note": note}
    points = json.loads((B / "campus-coordinate-review.json").read_text())
    points["schools"]["68"] = {"decision": "accepted", "field": fact(row, ev, reason=note)}
    (B / "campus-coordinate-review.json").write_text(json.dumps(points, ensure_ascii=False, indent=2) + "\n")
    print("HCMUTE official campus marker reviewed; original city and mother status preserved")


if __name__ == "__main__":
    main()
