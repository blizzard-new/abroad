"""Validate bundled CCU attachments and rebuild home-rule provenance offline."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pypdf import PdfReader
from exchange_info.ccu_sources import *


def write(name, value):
    (BUNDLE / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    specs = [
        ("2027-spring-partners.pdf", PARTNERS_URL, "2027春季", 121, "current"),
        ("2027-spring-guidelines.pdf", GUIDELINES_URL, "2027春季", 8, "current"),
        ("2027-spring-application.doc", FORM_DOC_URL, "2027春季", None, "current"),
        ("2027-spring-application.odt", FORM_ODT_URL, "2027春季", None, "current"),
        (
            "guardian-consent.pdf",
            GUARDIAN_URL,
            "家長同意書",
            1,
            "current_linked_undated",
        ),
    ]
    sources = []
    texts = {}
    for filename, url, title, count, status in specs:
        path = BUNDLE / filename
        raw = path.read_bytes()
        if filename.endswith(".pdf"):
            reader = PdfReader(path)
            if len(reader.pages) != count:
                raise ValueError(f"{filename}: unexpected page count")
            text = "\n".join(page.extract_text() for page in reader.pages)
        elif filename.endswith(".odt"):
            with ZipFile(path) as archive:
                text = " ".join(ET.fromstring(archive.read("content.xml")).itertext())
        else:
            if not raw.startswith(b"\xd0\xcf\x11\xe0"):
                raise ValueError("Invalid DOC compound-file signature")
            # The uncompressed Word text stream contains the application title.
            text = raw.decode("utf-16-le", errors="ignore")
        if title not in re.sub(r"\s+", "", text):
            raise ValueError(f"{filename}: applicable title absent from contents")
        texts[filename] = text
        sources.append(
            dict(
                filename=filename,
                official_url=url,
                sha256=hashlib.sha256(raw).hexdigest(),
                bytes=len(raw),
                page_count=count,
                content_title_verified=title,
                status=status,
                academic_year=YEAR if status == "current" else None,
                application_round=ROUND if status == "current" else None,
                checked_at=CHECKED_AT.isoformat(),
                open_validation="PDF parser / ODT XML / DOC signature and embedded title",
            )
        )
    guide = PdfReader(BUNDLE / "2027-spring-guidelines.pdf")

    def evidence(
        value,
        pages,
        phrase,
        *,
        url=GUIDELINES_URL,
        status="verified_current",
        note=None,
    ):
        corpus = (
            " ".join(guide.pages[p - 1].extract_text() for p in pages)
            if url == GUIDELINES_URL
            else texts["2027-spring-application.odt"]
        )
        corpus = re.sub(r"\s+", " ", corpus)
        at = corpus.find(phrase)
        if at < 0:
            raise ValueError(f"Evidence phrase absent: {phrase}")
        return dict(
            value=value,
            official_url=url,
            source_pages=pages,
            original_excerpt=corpus[max(0, at - 15) : at + 180],
            academic_year=YEAR,
            application_round=ROUND,
            checked_at=CHECKED_AT.isoformat(),
            status=status,
            note=note,
        )

    home = {
        "school_name": HOME,
        "academic_year": YEAR,
        "application_round": ROUND,
        "checked_at": CHECKED_AT.isoformat(),
        "calendar_normalization": "官方原稱2027春季；115學年度第二學期是平台曆年換算，不是官方以115命名的另一梯次。",
        "scope": "CCU outbound／校級薦外；PartnerUniversity各筆資格是合作校接收中正學生的incoming条件。",
        "fields": {
            "academic_gpa_minimum": evidence(3.0, [1], "GPA須達3.0"),
            "academic_average_minimum": evidence(
                70, [1], "70分", note="AND GPA，不能二擇一；合作校更高標準另從其規定。"
            ),
            "home_enrollment": evidence(
                "至少在中正就讀滿兩學期，全程保有學籍", [1, 5], "就讀滿兩學期"
            ),
            "home_degree_year": evidence(
                "學士大二至大四上，碩博士二年級以上",
                [1],
                "大學部二年級",
                status="conflict",
                note="申請表另有大四上專案申請四下至五上一學年；須承辦確認例外。",
            ),
            "maximum_preferences": evidence(3, [1], "三個志願"),
            "home_program_exclusivity": evidence(
                "校級、院級交換僅能擇一", [1], "擇一申請"
            ),
            "exchange_frequency": evidence(
                "赴外交換或進修以一次為限，申請年限至多一年", [1], "一次為限"
            ),
            "language_validity": evidence(
                "兩年內有效，門檻依合作校與計畫", [3], "兩年內"
            ),
            "documents": evidence(
                "申請表、中英成績單、在學證明、語言證明、履歷、各志願研修計畫、條件性畢業審核、各校彌封推薦函、選擇性附件<=5頁",
                [3, 4],
                "歷年成績單",
            ),
            "home_online_and_paper": evidence(
                ROUND_DEADLINES,
                [2],
                "2026/08/26",
                note="線上23:59及次日紙本17:00必須各自完成；開始僅載即日起。三梯次學校分組依公告。",
            ),
            "fees": evidence(
                "繳中正學雜費；免合作校學費。機票、生活、保險自付，語言課和住宿可能另收費；少數學校免宿依個別規定",
                [5],
                "生活費",
            ),
            "home_minimum_courses": evidence(
                "合作校沒有最低要求時至少2門課、4學分或8 ECTS；較高合作校要求從嚴",
                [5, 6],
                "兩門課程",
            ),
            "credit_recognition": evidence(
                "本科上限畢業學分1/3，研究生1/2；非應屆交換結束次學期內，應屆次學期上課首週內",
                [6],
                "二分之一",
            ),
            "return_report": evidence("返國後一個月內交交換心得", [4, 5], "一個月內"),
            "arrival_safety": evidence("抵達後立即聯繫家人、系所與國際處", [7], "立即"),
            "academic_arrival_return_notice": evidence(
                "抵達及返國兩週內各填送一次予教學組",
                [2],
                "二周內",
                url=FORM_ODT_URL,
                note="ODT版面第2頁；與國際處即時安全聯繫／一個月心得不同。",
            ),
            "scholarship_old_window": evidence(
                "2026年2月至3月；不作2027当期申請期",
                [7],
                "2026年2",
                status="reference_only",
            ),
        },
        "next_round": dict(
            application_round="2027秋季",
            status="needs_confirmation",
            official_url=NEWS_URL,
            checked_at=CHECKED_AT.isoformat(),
            note="尚未核實新版；未查得官方明示尚未公告。",
        ),
    }
    conflicts = [
        dict(
            id="guideline-heading",
            official_url=GUIDELINES_URL,
            pages=[2],
            excerpt="四、2026 秋季校級薦外交換學生計畫時程",
            status="needs_confirmation",
            resolution="保留誤植，不把標題當成2026當期；使用公告和實際2026申請日、2027春季內容。",
        ),
        dict(
            id="fourth-year-exception",
            official_url=FORM_ODT_URL,
            pages=[1],
            excerpt="申請四下出國一學年 至五上",
            status="needs_confirmation",
            resolution="與簡章一般大四限制不同，不自動核准例外。",
        ),
        dict(
            id="chungnam-semester-year",
            official_url=PARTNERS_URL,
            pages=[53],
            excerpt="學期時間: 2027/03/02 – 2026/06/18",
            status="conflict",
            resolution="未自行更正2026為2027；semester_dates留空，原文保留於reference_data。",
        ),
        dict(
            id="uninter-language",
            official_url=PARTNERS_URL,
            pages=[119],
            excerpt="English B2 vs proof of language B1 minimum in English or/and Spanish",
            status="conflict",
            resolution="兩段均保留，不猜英文最低門檻。",
        ),
        dict(
            id="pardubice-general-admission",
            official_url=PARTNERS_URL,
            pages=[107],
            excerpt="Admission Process Overview: Pass the entrance exam / Pay tuition",
            status="needs_confirmation",
            resolution="可能誤列一般入學流程，未視為交換申請文件；與中正免合作校學費原則不同，須承辦确认。",
        ),
        dict(
            id="tohoku-jype-spring",
            official_url=PARTNERS_URL,
            pages=[35, 36],
            excerpt="JYPE Duration: F+S / F",
            status="needs_confirmation",
            resolution="表列秋季起始；2027春季是否可申請待承辦確認，不能由全校名額推得計畫開放。",
        ),
    ]
    for conflict in conflicts:
        conflict.update(
            academic_year=YEAR,
            application_round=ROUND,
            checked_at=CHECKED_AT.isoformat(),
        )
    write(
        "source-manifest.json",
        dict(
            checked_at=CHECKED_AT.isoformat(),
            sources=sources,
            additional_sources=[
                dict(
                    official_url=ANNOUNCEMENT_URL,
                    role="current_round_announcement",
                    published_at="2026-08-18",
                    academic_year=YEAR,
                    application_round=ROUND,
                    checked_at=CHECKED_AT.isoformat(),
                    snapshot_file="announcement.json",
                ),
                dict(
                    official_url=NEWS_URL,
                    role="latest_round_lookup",
                    checked_at=CHECKED_AT.isoformat(),
                    status="next_round_not_verified",
                ),
                dict(
                    official_url="https://s2.exam.ccu.edu.tw/ccuee_intro/stu/intro_index.php",
                    role="academic_units",
                    checked_at=CHECKED_AT.isoformat(),
                    status="verified_current_directory_not_exchange_rule",
                ),
            ],
            related_attachments_note="104筆PDF相關連結保留於field-audit.json；未逐份開啟核對，不列為已核實當期申請文件。",
        ),
    )
    write("home-rules.json", home)
    write("conflicts.json", conflicts)
    print(
        json.dumps(
            dict(
                validated_files=len(sources),
                home_fields=len(home["fields"]),
                conflicts=len(conflicts),
            )
        )
    )


if __name__ == "__main__":
    main()
