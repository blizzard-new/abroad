"""Expose NTU reference text without upgrading it to a current-cycle rule."""
from __future__ import annotations

import re

from .models import PartnerStudentSummary, PartnerUniversity


def ntu_partner_summary(partner: PartnerUniversity) -> PartnerStudentSummary:
    caution = "116-1合作校條件尚未全面核實；以下為官方參考資料，原文年份與適用身分須分別確認。"
    source = f"臺大合作校資料來源：{partner.source_url}"

    def points(value: str | None, missing: str, *, group_references: bool = False) -> list[str]:
        # Keep every source paragraph, including its year, exceptions and conflicts.
        # Chinese portal text is retained; English original text is not claimed translated.
        paragraphs = [re.sub(r"[ \t\u00a0]+", " ", text).strip()
                      for text in re.split(r"\n\s*\n", value or "") if text.strip()]
        if group_references and any("【接待校公開來源補查，" in p for p in paragraphs):
            # The overview renders ten points. Nine reference fields plus one
            # introduction retain every paragraph without changing shared UI.
            introduction = [caution]
            fields: dict[str, list[str]] = {}
            in_references = False
            for paragraph in paragraphs:
                in_references |= "【接待校公開來源補查，" in paragraph
                match = re.match(r"^([^：\n]+參考)：", paragraph) if in_references else None
                if match:
                    fields.setdefault(match[1], []).append(paragraph)
                else:
                    introduction.append(paragraph)
            return ["\n\n".join([*introduction, source]),
                    *("\n\n".join(group) for group in fields.values())]
        return [caution, *paragraphs, source] if paragraphs else [caution, missing, source]

    return PartnerStudentSummary(
        study_period=partner.study_period,
        application_deadline=partner.application_deadline,
        eligibility_points=points(partner.eligibility, "尚未取得資格文字；請核對官方當期規定。"),
        application_steps=points(partner.application_info, "尚未取得申請文件文字；不代表官方未公告。", group_references=True),
        tuition_points=points(partner.tuition_info, "尚未取得註冊繳費文字；不推定免學費。"),
        translated_from_english=False,
    )


def with_ntu_partner_summary(partner: PartnerUniversity) -> PartnerUniversity:
    return partner.model_copy(update={"student_summary_zh": ntu_partner_summary(partner)})
