"""Build all 25 closed 2027–28 Japanese first-round rows from the actual PDF."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
SPECS = [
    (33,2,"青山學院大學", "GPA2.5；至少已讀淡江一學期。"),
    (208,2,"關西大學", "研究所課程須教授接受及足夠開課人数，否則可參與大學部計畫；不接受具有日本國籍的雙籍生。"),
    (110,1,"同志社大學", "限已讀淡江日文系一學年；不接受具有日本國籍的雙籍生。"),
    (200,1,"櫻美林大學", "GPA2.5；至少已讀淡江一學期；僅大三下一學期。"),
    (35,4,"長崎大學", "一般交換需核對科系及標準；JLCP限日語及日本文化學習者且N2。"),
    (227,1,"山口大學", None),
    (111,1,"立命館大學", "N1；GPA3.0；至少已讀淡江一學年。"),
    (164,2,"東京外國語大學", "GPA2.0；至少已讀淡江一學期。"),
    (188,2,"學習院大學", None),
    (29,2,"早稻田大學", "N1（各系要求不同）；GPA依各系要求。"),
    (103,2,"法政大學", None),
    (34,2,"長崎外國語大學", "表列jiu.ac.jp為城西國際大學網域，不能當作長崎外國語申請入口。"),
    (260,2,"神奈川大學", None),
    (237,2,"關西學院大學", None),
    (112,5,"北海道大學", "GPA3.0；大學部限SA；研究所可SA/SRS且N1。"),
    (28,2,"津田塾大學", "限女生、大學部；GPA2.0；母校名額表載免住宿費。"),
    (274,2,"成蹊大學", "GPA2.5；至少已讀淡江一學期。"),
    (272,2,"千葉大學", "限大學部、大三下一學期，結束即返國；不接受具有日本國籍的雙籍生。"),
    (38,2,"鹿兒島大學", None),
    (31,2,"駒澤大學", "母校名額表載免住宿費。"),
    (23,1,"亞細亞大學", "研究所N1；母校名額表載住宿每月補助5萬日圓，接待校本期核實尚缺。"),
    (22,2,"中央學院大學", "限大學部。"),
    (169,1,"大阪公立大學", None),
    (202,2,"龍谷大學", None),
    (30,3,"電氣通信大學", "英語JUSST；電機／資工系所優先；平均80且GPA3.0。表列iBT67及IELTS6.0，正文使用或，連接條件矛盾待確認。"),
]


def main():
    source = json.loads((BUNDLE / "census_home_sources/jp-first-2027-guide.json").read_text())
    census = {r["id"]:r for r in map(json.loads, (BUNDLE/"partner_census.jsonl").read_text().splitlines())}
    rows=[]
    for i, (sister_id, quota, name, condition) in enumerate(SPECS, 1):
        institution = census[f"tku-sister-{sister_id}"]
        page = 13 if i <= 13 else 14
        def fact(value, locator, quote, *, status="reference_only", reason=None):
            return dict(value=value, status=status, reason=reason or "本年度已結束第一梯資料；不能充當第二梯或新開放名額。",
                        evidence=[dict(source_url=source["source_url"], source_id="jp-first-2027-guide",
                                       locator=locator, quote=quote, applicable_year="2027-2028",
                                       application_round="日語組第一次甄選（已截止）", role="home_outbound",
                                       checked_at=source["checked_at"])])
        fields={
            "school_name":fact(institution["school_name"]+" "+institution["english_name"],f"PDF p.{page} row {i}", name),
            "country":fact("日本", "PDF p.1 title", "赴日本姐妹校（日語組）"),
            "quota":fact(str(quota),f"PDF p.{page} row {i} 名額",str(quota)),
            "home_deadline":fact("2026/2/23–3/1 17:00 Asia/Taipei；申請修改3/2中午12:00另計。系所送國際處期限的公告22353本次HTTP503，該原文尚未取得，不能當作已核實期限。", "PDF p.3及p.16；公告22353開啟失敗另列", "2026年3月1日（星期日）下午5時止"),
            "home_eligibility":fact("淡江在學大二／研究所一、二；平均75，研究所一附大學四年成績單；系所院初選推薦。附錄排名替代條件須承辦確認。", "PDF p.2 壹一；附錄Q&A", "大學部二年級、研究所一、二年級在學學生"),
            "home_language":fact("大學部日語N2；研究所N1；立命館、早稻田另N1。UEC正文iBT67或IELTS6，與表格及連接詞矛盾，不能套新TOEFL量尺。", "PDF p.2 壹一（三）; p.13–14", "托福iBT67分以上證明或IELTS6.0以上"),
            "documents":fact("申請表親簽／系主任簽；中文歷年成績單正本；語言證明影本且面試驗原本；中文或日文授課老師推薦函1封；中日文自傳與研習計畫；切結書簽名蓋章；有則其他證明。總計A4單面16頁内，不裝訂，L型套；最多5志願。", "PDF p.3–4；p.15切結書；p.16修正表", "全部資料請勿超過16頁"),
            "study_period":fact("2027/4–2028/3範圍；原則一學年，指定期間依外校；櫻美林、千葉僅大三下一學期。", "PDF p.5 肆；p.13–14 名額表", "留學期間：2027.4-2028.3"),
            "department_scope":fact(condition,f"PDF p.{page} row {i} 備註",condition or "備註欄空白", status="reference_only" if condition else "missing_in_source", reason=None if condition else "本梯該列備註空白，不表示所有系所皆符合接待校資格。"),
            "insurance":fact("出國前投保海外醫療及意外保險，保單影本送淡江國際處存查；接待校另要求的保險須另外核對。", "PDF p.6 行前流程", "投保海外醫療及意外保險"),
        }
        rows.append(dict(id=f"jp-2027-2028-round-1-{sister_id}", institution_id=institution["id"],
                         home_university="淡江大學", round_id="jp-2027-2028-round-1",
                         academic_year="2027-2028", application_round="日語組第一次甄選",
                         selection_status="reference_only", selection_window_status="closed",
                         quota_status="numeric", quota_number=quota, fields=fields,
                         conflicts=["first-round-uec-language-conjunction"] if sister_id==30 else
                         ["first-round-nagasaki-wrong-url"] if sister_id==34 else []))
    assert len(rows)==25 and sum(r["quota_number"] for r in rows)==50
    (BUNDLE/"earlier_round_programmes.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows))
    print("25 closed first-round programmes; 50 historical quotas; 0 open applications")


if __name__=="__main__":main()
