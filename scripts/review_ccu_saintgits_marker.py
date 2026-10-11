"""Reproduce the exact Saintgits Engineering marker, including the contact redirect."""
from __future__ import annotations

import json

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from review_ccu_followup_batch import evidence, fact, receipt, response_text


def main():
    contact = receipt(74, "engineering-contact-followup")
    # The guessed engineering contact route actually redirects to Design School.
    # Its official same-group link names the Engineering institution explicitly.
    assert contact["resolved_url"] == "https://saintgits.org/saintgits-design-school/contact-us/"
    soup = BeautifulSoup(response_text(contact), "html.parser")
    link = "https://goo.gl/maps/zxt3rGJ8S46DX3ws7"
    assert soup.find("a", href=link)
    assert "Saintgits Design School" in soup.get_text(" ", strip=True)
    root = receipt(74, "engineering-root-followup")
    assert root["resolved_url"] == "https://saintgits.org/saintgits-college-of-engineering/"
    assert "Saintgits College of Engineering" in response_text(root)
    marker = receipt(74, "engineering-official-map-marker")
    identity = "Saintgits+College+of+Engineering+(Autonomous),+Kottayam,+Kerala"
    assert identity in marker["resolved_url"]
    assert "!3d9.5100096!4d76.5513594" in marker["resolved_url"]
    assert "@9.5100096,76.5491707" in marker["resolved_url"]
    partner = next(json.loads(line) for line in (B / "partners.jsonl").read_text().splitlines()
                   if json.loads(line)["source_pages"][0] == 74)
    note = ("官方同集團Design School聯絡頁（工學院contact路由實際轉址）所連地圖，"
            "目的地明確命名Saintgits College of Engineering (Autonomous), Kottayam, Kerala。"
            "採!3d/!4d機構marker9.5100096,76.5513594，不採@視窗經度76.5491707，"
            "不採既有空拍照片的camera GPS；此為工學院代表點，不保證個人授課樓或Design School交換資格。")
    ev = [evidence(74, "engineering-root-followup", "Saintgits College of Engineering"),
          evidence(74, "engineering-contact-followup", "Saintgits Design School; " + link),
          evidence(74, "engineering-official-map-marker", identity + " !3d9.5100096!4d76.5513594")]
    ev[1]["resolved_url"] = contact["resolved_url"]
    ev[2]["resolved_url"] = marker["resolved_url"]
    row = {"school_name": partner["school_name"], "country": partner["country"],
           "city": "Kottayam", "latitude": 9.5100096, "longitude": 76.5513594,
           "geocode_status": "verified", "geocoded_at": marker["checked_at"],
           "source_url": marker["source_url"], "identity_source_url": contact["resolved_url"],
           "precision": "representative", "note": note}
    points = json.loads((B / "campus-coordinate-review.json").read_text())
    points["schools"]["74"] = {"decision": "accepted", "field": fact(row, ev, reason=note)}
    (B / "campus-coordinate-review.json").write_text(json.dumps(points, ensure_ascii=False, indent=2) + "\n")
    print("Reviewed Saintgits Engineering actual marker; contact redirect and viewport preserved")


if __name__ == "__main__":
    main()
