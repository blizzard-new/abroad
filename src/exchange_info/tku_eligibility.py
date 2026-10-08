"""Programme-specific interpretation; never treats 70 screening score as GPA."""
from __future__ import annotations

from .tku_data import load_tku_records


def assess_tku_eligibility(*, round_id: str, academic_average: float | None = None,
                           department_top_percent: float | None = None, degree_level: str | None = None,
                           year_of_study: int | None = None, jlpt_level: str | None = None,
                           partner_id: str | None = None) -> dict:
    """Assess known home rules only, returning uncertainty instead of inferring inputs.

    A reference round can pass its historical academic rule; that never means an
    application is open now. Host GPA, nationality, departments and nomination
    remain separate requirements. JLPT N1 is stronger than N2, not vice versa.
    """
    if round_id not in {"jp-2027-2028-round-2","english-european-115","mainland-macau-kinmen-115"}:
        return {"academic_status":"needs_confirmation","home_status":"needs_confirmation",
                "application_status":"not_verified_new","notes":["未核實此年度梯次的規定，不能沿用舊版。"]}
    japanese = round_id == "jp-2027-2028-round-2"
    notes=[]; checks=[]
    if academic_average is not None and academic_average >= 75:
        academic="pass"
    elif not japanese and department_top_percent is not None and department_top_percent <= 40:
        academic="pass"
    elif japanese and department_top_percent is not None and department_top_percent <= 40:
        academic="needs_confirmation";notes.append("正文75分與Q&A系前40%替代規定有矛盾，待承辦確認。")
    elif academic_average is None or (not japanese and department_top_percent is None):
        academic="needs_confirmation"
    else:academic="fail"
    checks.append(academic)
    if japanese:
        if degree_level is None or year_of_study is None:checks.append("needs_confirmation")
        elif degree_level=="大學部":checks.append("pass" if year_of_study==3 else "fail")
        elif degree_level=="碩士班":checks.append("pass" if year_of_study in [1,2] else "fail")
        else:
            checks.append("needs_confirmation");notes.append("正文研究所與各校碩士學制、博士適用需個別確認。")
        uec = partner_id is not None and partner_id.endswith("-uec")
        if uec:
            checks.append("needs_confirmation")
            notes.append("JUSST須分開核對80分、GPA3.0與英語證明；電機／資工為優先。研究所英語課N1豁免未明示。")
        else:
            minimum="N1" if degree_level=="碩士班" or (partner_id or "").endswith("-ritsumeikan") else "N2"
            rank={"N1":1,"N2":2,"N3":3,"N4":4,"N5":5}
            checks.append("needs_confirmation" if jlpt_level not in rank else "pass" if rank[jlpt_level]<=rank[minimum] else "fail")
        notes.append("系所院推薦、外校GPA與在校修業期間須另查；學業達75不等於全部資格通過。")
    else:
        checks.append("needs_confirmation");notes.append("只核對舊期學業條件；其餘學制、國籍、語言及當期名額未作自動認定。")
    home="fail" if "fail" in checks else "needs_confirmation" if "needs_confirmation" in checks else "pass"
    return {"academic_status":academic,"home_status":home,
            "application_status":"closed" if japanese else "reference_only","notes":notes}
