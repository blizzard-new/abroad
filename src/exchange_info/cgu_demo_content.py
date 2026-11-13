"""Synced CGU catalogue and suggested journeys, rendered by the shared platform UI."""
from __future__ import annotations

import json
from pathlib import Path

from .cgu_catalogue import CguCatalogue, CatalogueView
from .application_path import build_levels, level

CONTENT = Path(__file__).parent / 'demo_data/content.json'

CGU_SELECTION_GUIDE_URL = 'https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656'
CGU_SUBSIDY_PAGE_URL = 'https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15724'
CGU_XIZHU_PAGE_URL = 'https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15725'
CGU_NAVIGATOR_REGULATION_URL = (
    'https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/'
    'b85add3b-7d9e-43ff-b22f-f0657e11765c'
)
CGU_NAVIGATOR_PDF_URL = (
    'https://www.cgu.edu.tw/regulation/ServerFile/Get/'
    'e3b68a9a-e820-4614-a799-e88023a40161'
)
CGU_XIZHU_REGULATION_URL = (
    'https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/'
    'd5fa7ac2-d65e-4dcd-8f18-0717d32d5639'
)
CGU_XIZHU_PDF_URL = (
    'https://www.cgu.edu.tw/regulation/ServerFile/Get/'
    'fe589216-9fe9-42b3-816c-31cde93b5d1a'
)
CGU_SHORT_TERM_REGULATION_URL = (
    'https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/'
    '188edb21-5c53-4cbe-9e55-81089f90528b'
)
CGU_SHORT_TERM_PDF_URL = (
    'https://www.cgu.edu.tw/regulation/ServerFile/Get/'
    'f036738d-a1c8-46b2-b208-bebf6901f0e5'
)
CGU_ZHUMENG_REGULATION_URL = (
    'https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/'
    '17a33812-80d0-45f1-b4ef-6c2cf40a0c50'
)
CGU_ZHUMENG_PDF_URL = (
    'https://www.cgu.edu.tw/regulation/ServerFile/Get/'
    '20198fac-b649-4e2e-816d-29e6c657c370'
)


class FrozenCatalogue:
    """Offline-isolated reader over the bundled CGU snapshot synced with app.uniway."""

    def __init__(self, path):
        self.store = CguCatalogue(path / 'unused-demo-cache.json')

    def view(self) -> CatalogueView:
        return self.store.view(refresh=False)


def _cgu_term_prompt(context) -> str:
    year = str(context.get('departure_year') or '').strip()
    academic_year = str(context.get('academic_year') or '').strip()
    semester = context.get('semester')
    if semester == 'fall':
        return f'{year} 秋季（{academic_year}-1）' if academic_year else f'{year} 秋季'
    if semester == 'spring':
        return f'{year} 春季（{academic_year}-2）' if academic_year else f'{year} 春季'
    if semester == 'full_year':
        return f'{year} 秋季・全學年（{academic_year}-1）' if academic_year else f'{year} 秋季・全學年'
    return f'{year} 尚未決定'.strip()


def journey_levels(context, evaluated, catalog, values=None):
    """Keep native direction/rule steps; add explicitly suggested personal tasks.

    The shared renderer, revision checks, storage and next-step logic remain in
    application_path.py. No recommendation is represented as official approval.
    """
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    sources = {row['id']: row['url'] for row in data['sources']}
    original = [item for stage in build_levels(context, evaluated, catalog, values) for item in stage['levels']]
    for row in original:
        if row['id'] == 'term':
            row['prompt'] = _cgu_term_prompt(context)
    stages, number = [], 0
    is_116_fall = (
        str(context.get('academic_year') or '') in ('116', '')
        and str(context.get('departure_year') or '2027') == '2027'
        and context.get('semester') in ('fall', 'full_year', 'undecided', None, '')
    )
    for index, stage in enumerate(data['stages']):
        items = [row for row in original if row['id'] in ('home', 'term', 'target')] if index == 0 else []
        if index == 1:
            items.extend(row for row in original if row['id'].startswith('check-'))
        for task in stage['tasks']:
            source = task.get('source')
            detail = task['detail']
            if source == 'lincoln' and 'Lincoln' not in context['target_school']:
                source = None
                detail = '此事項是否適用、文件及日期待目的校通知確認；請記下你查到的結果。'
            item = level('cgu-' + task['id'], task['title'], 'confirm', detail,
                         stage['title'], warning='個人準備紀錄／適用性待確認；不代表已送件、受理或錄取。')
            item['source_urls'] = [sources[source]] if source in sources else []
            if task['id'] == 'internal-submit' and is_116_fall:
                item.update(
                    title='116-1 校內申請截止（2026/12/21 17:00 校內截止前完成長庚申請）',
                    official_deadline_at='2026-12-21T17:00:00+08:00',
                    deadline_confirmed=True,
                    deadline_source_url=sources['selection'],
                    source_urls=[sources['selection']],
                )
            items.append(item)
        for item in items:
            number += 1
            item.update(stage=index, stage_key=stage['title'], number=number)
        stages.append(dict(key=stage['id'], title=stage['title'], icon='route', index=index, levels=items))
    return stages


def source_dashboard(dashboard):
    """Keep CGU's verified platform dashboard synced while populating verified CGU subsidy & document rules."""
    from .models import PageCategory, RuleExplanation, SourceReference, StudentInfoItem

    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    existing_urls = {src.source_url for src in dashboard.sources if src.source_url}
    for row in data['sources']:
        if row['url'] not in existing_urls:
            dashboard.sources.append(
                SourceReference(
                    title=row['title'],
                    source_url=row['url'],
                    summary=row['scope'] + ' 查核日期：' + row['checked_on'],
                )
            )
            existing_urls.add(row['url'])

    navigator_source = SourceReference(
        title='長庚大學法規彙編｜長庚大學領航者補助作業要點（規章編號 2B00004，114/10/28 修正）',
        source_url=CGU_NAVIGATOR_REGULATION_URL,
        category=PageCategory.SCHOLARSHIP,
        summary='114 年 10 月 28 日行政會議修正公告；查核日期：2026-11-12',
    )
    xizhu_source = SourceReference(
        title='長庚大學法規彙編｜長庚大學辦理教育部學海惜珠補助要點（規章編號 2B00005，115/01/05 修正）',
        source_url=CGU_XIZHU_REGULATION_URL,
        category=PageCategory.SCHOLARSHIP,
        summary='115 年 1 月 5 日行政會議修正公告；查核日期：2026-11-12',
    )
    short_term_source = SourceReference(
        title='長庚大學法規彙編｜長庚大學補助學生參加境外短期學分課程作業要點（規章編號 2B00010，114/10/28 修正）',
        source_url=CGU_SHORT_TERM_REGULATION_URL,
        category=PageCategory.SCHOLARSHIP,
        summary='114 年 10 月 28 日行政會議修正公告；查核日期：2026-11-12',
    )
    zhumeng_source = SourceReference(
        title='長庚大學法規彙編｜長庚大學辦理教育部學海築夢及新南向學海築夢補助要點（規章編號 2B00006，115/01/05 修正）',
        source_url=CGU_ZHUMENG_REGULATION_URL,
        category=PageCategory.SCHOLARSHIP,
        summary='115 年 1 月 5 日行政會議修正公告；查核日期：2026-11-12',
    )
    oia_subsidy_source = SourceReference(
        title='長庚國際事務處｜出國研修補助說明',
        source_url=CGU_SUBSIDY_PAGE_URL,
        category=PageCategory.SCHOLARSHIP,
        summary='國際事務處出國研修補助與申請流程說明；查核日期：2026-11-12',
    )
    selection_guide_source = SourceReference(
        title='長庚國際事務處｜校內申請選送須知',
        source_url=CGU_SELECTION_GUIDE_URL,
        category=PageCategory.EXCHANGE_APPLICATION,
        summary='116-1 校內基本門檻與 5 份應備文件清單；查核日期：2026-11-12',
    )
    for extra_src in (navigator_source, xizhu_source, short_term_source, zhumeng_source, oia_subsidy_source):
        if extra_src.source_url and extra_src.source_url not in existing_urls:
            dashboard.sources.append(extra_src)
            existing_urls.add(extra_src.source_url)

    extra_regulations = [
        RuleExplanation(
            title='長庚大學領航者補助作業要點（規章編號 2B00004）',
            summary=(
                '本校鼓勵在學學生赴國外大專校院修讀學分（含教育部學海飛颺計畫）之核心交換／雙聯研修補助。'
                '完成校內交換或雙聯甄選申請並獲外校錄取且符合資格者，由國際處直接送補助金審查，不需額外單獨填表申請。'
            ),
            key_points=[
                '申請資格（第 3 點）：具中華民國國籍且設籍臺灣地區、於本校就讀滿 1 學期以上（不含在職專班生）；歷年學業成績平均達 70 分以上為原則；英文等同多益 TOEIC 700 分、IELTS 5.5、TOEFL iBT 72 或 Duolingo 105 以上（國外學校要求更高者從其規定）。',
                '第一類地區補助上限（附件二）：一學期上限 NT$75,000、一學年上限 NT$150,000（歐美、紐澳、新加坡、以色列等）。',
                '第二類地區補助上限（附件二）：一學期上限 NT$60,000、一學年上限 NT$120,000（日、韓、泰、馬、印、捷克、波蘭、中南美、非澳其他及大陸港澳；教育部學海飛颺經費不含大陸港澳）。',
                '班排前 30% 加碼與扣除規定：申請時歷年班排名達前 30% 者每學期得加碼 NT$10,000；同一學制已領短期學分課程等補助者須扣除已領額度，不得重複領取我國政府其他出國研修補助。',
                '審查配分與返國義務：在校成績 30%、外語能力 30%、讀書計畫及學校國際聲望 30%、特殊表現 10%；每學期至少修專業科目 1 門並採認 3 學分，返國 2 週內繳交返校手續單、心得報告與分享短片。',
            ],
            applies_to=['交換學生', '雙學位', '自費研修'],
            source=navigator_source,
            document_url=CGU_NAVIGATOR_PDF_URL,
            document_type='長庚一般研修補助',
            full_text_extracted=True,
        ),
        RuleExplanation(
            title='長庚大學辦理教育部學海惜珠補助要點（規章編號 2B00005）',
            summary=(
                '專為經濟不利或低／中低收入戶且具中華民國國籍之在學學生設立之海外交換／雙聯補助，包含機票與生活費，'
                '須另備戶籍謄本與社福／家庭經濟證明洽國際處配合教育部期程申請。'
            ),
            key_points=[
                '對象資格（第 2 點）：設籍臺灣之中華民國國籍在學學生（須具備政府核發低收入戶、中低收入戶、身心障礙／特殊境遇家庭等有效經濟不利證明），獲本校交換／雙聯提名。',
                '補助項目與年限（第 4、6 點）：依教育部學海惜珠核定額度補助來回經濟艙機票與國外生活費（含學費差額）；補助期間最少 1 學期，最高不超過 1 學年。',
                '審查配分與應備證明（第 5、7 點）：經濟狀況及在校成績 40%、外語能力 30%、讀書計畫及國際聲望 30%；須附家長同意書、2 封師長推薦函與最新全戶戶籍謄本。',
                '返國義務與注意事項（第 9、10 點）：研修期間至少修 1 門專業科目並於返國 1 個月內繳交報告；同教育階段曾獲教育部出國補助者不得重複申請，且中文授課組別不予補助。',
            ],
            applies_to=['交換學生', '雙學位', '經濟不利專案'],
            source=xizhu_source,
            document_url=CGU_XIZHU_PDF_URL,
            document_type='教育部經濟不利補助',
            full_text_extracted=True,
        ),
        RuleExplanation(
            title='長庚大學補助學生參加境外短期學分課程作業要點（規章編號 2B00010）',
            summary=(
                '針對寒暑假或短期出國修習至少 1 學分課程之補助方案，須透過教學單位／帶隊教師於出國前 2 個月提出專案申請。'
            ),
            key_points=[
                '課程與學分條件（第 2、3 點）：赴境外高教機構參加經教務處／學系認定至少可採認 1 學分（大學部限專業選修或學分學程）之短期課程或暑期學校。',
                '補助金額與班排加碼（第 4 點）：一般核實補助來回機票費及註冊學分費上限 NT$30,000；班排名達前 30% 者，上限調高至 NT$40,000。',
                '申請資格與次數限制（第 3、5 點）：本校大學部／碩博士在學滿 1 學期（不含在職專班）、成績平均 70 分以上且英語等同多益 700 分；同一學制以申請 1 次為限，且若日後申請領航者補助須扣除本次已領額度。',
                '結案報告（第 8 點）：課程結束返國後 2 週內繳交核銷單據、學分採認證明、研習心得與學習照片集錦。',
            ],
            applies_to=['短期學分課程', '寒暑假交換'],
            source=short_term_source,
            document_url=CGU_SHORT_TERM_PDF_URL,
            document_type='短期學分補助',
            full_text_extracted=True,
        ),
        RuleExplanation(
            title='長庚大學辦理教育部學海築夢及新南向學海築夢補助要點（規章編號 2B00006）',
            summary=(
                '由本校專任教師擔任計畫主持人帶領學生赴海外機構／企業實習（含新南向國家），'
                '不接受學生個人單獨申請；依教師核定計畫取得教育部及本校配合款之機票與生活費補助。'
            ),
            key_points=[
                '主持教師統籌申請（第 2、4、6 點）：由專任教師依教育部期程（每年約 1 月底及 8/15 前）撰寫計畫向研究發展處與國際處彙整送件；學生應洽詢系所或實驗室教授參與。',
                '對象與語文資格（第 3 點）：設籍臺灣之我國國籍在學學生（不含在職專班），外語符合多益 700 分等相當門檻；同教育階段以領取 1 次為限（新南向實習不含中國及港澳地區）。',
                '補助內容與實習天數（第 5 點）：補助來回機票與實習期間部分生活費；一般學海築夢赴外實習須至少 30 天以上（印尼、印度及澳洲等可為 15–30 天），並於次年 10/31 前成行。',
                '返國報告義務（第 9 點）：實習結束後 2 週內提交 1,000 字以上實習心得報告及影像成果，並完成報帳核銷。',
            ],
            applies_to=['海外專業實習', '教師帶隊計畫'],
            source=zhumeng_source,
            document_url=CGU_ZHUMENG_PDF_URL,
            document_type='海外實習補助',
            full_text_extracted=True,
        ),
    ]

    existing_doc_titles = {item.title for item in dashboard.document_explanations}
    for reg_item in reversed(extra_regulations):
        if reg_item.title not in existing_doc_titles:
            dashboard.document_explanations.insert(0, reg_item)
            existing_doc_titles.add(reg_item.title)

    dashboard.scholarship_info = [
        StudentInfoItem(
            title='長庚大學領航者補助作業要點（規章編號 2B00004）',
            details=[
                '免額外申請：完成校內出國研修甄選、獲外校錄取且符合資格者，由國際事務處直接送補助金審查。',
                '地區額度上限：第一類地區（歐美、紐澳、新加坡、以色列等）每學期上限 NT$75,000／一學年上限 NT$150,000；第二類地區（日、韓、捷克、波蘭、東南亞等）每學期上限 NT$60,000／一學年上限 NT$120,000。',
                '優秀加碼：申請時歷年學業成績班排名達前 30% 者，補助金額每學期得增加 NT$10,000。',
                '資格與義務：本國籍在學滿 1 學期（不含在職專班）、平均 70 分以上、多益 700（或同等檢定）；返校每學期至少採認 3 學分，返國 2 週內完成結案報告。',
            ],
            source=navigator_source,
        )
    ]

    if not any(group.details for group in dashboard.required_documents):
        dashboard.required_documents = [
            StudentInfoItem(
                title='116-1 校內申請應備 5 份文件',
                details=[
                    '線上申請表：於 2026/11/02–12/21 17:00 間填妥 Google 線上申請表（交換與雙聯共用，最多填 2 個志願）。',
                    '家長同意書：依國際事務處規定格式填寫並經家長／監護人簽章之正本。',
                    '外國語文能力證明：多益 700 分（或同等外語檢定）及目標合作校規定之語文成績證明影本。',
                    '中文歷年成績單證明文件：含歷年學業平均正本（大學部申請者須含班級排名百分比）。',
                    '讀書計畫申請文件：以 1 頁為原則，說明選校動機、修課規劃與預期學習成果。',
                ],
                source=selection_guide_source,
            )
        ]

    return dashboard
