"""Synced CGU catalogue and suggested journeys, rendered by the shared platform UI."""
from __future__ import annotations

import json
from pathlib import Path

from .cgu_catalogue import CguCatalogue, CatalogueView
from .application_path import build_levels, level

CONTENT = Path(__file__).parent / 'demo_data/content.json'

CGU_SELECTION_GUIDE_URL = 'https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656'
CGU_SUBSIDY_PAGE_URL = 'https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15724'
CGU_NAVIGATOR_REGULATION_URL = (
    'https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/'
    'b85add3b-7d9e-43ff-b22f-f0657e11765c'
)
CGU_NAVIGATOR_PDF_URL = (
    'https://www.cgu.edu.tw/regulation/ServerFile/Get/'
    'e3b68a9a-e820-4614-a799-e88023a40161'
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
        str(context.get('academic_year') or '') == '116'
        and context.get('semester') in ('fall', 'full_year', 'undecided')
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
                    title='12/21 17:00 校內截止前完成長庚 116-1 申請（完成後自行記錄）',
                    official_deadline_at='2026-12-21T17:00:00+08:00',
                    deadline_confirmed=True,
                    deadline_source_url=sources['selection'],
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

    existing_doc_titles = {item.title for item in dashboard.document_explanations}
    if '長庚大學領航者補助作業要點（規章編號 2B00004）' not in existing_doc_titles:
        dashboard.document_explanations.insert(
            0,
            RuleExplanation(
                title='長庚大學領航者補助作業要點（規章編號 2B00004）',
                summary=(
                    '69 所合作校申請資格所稱「領航者補助作業要點」，為本校鼓勵在學學生赴國外大專校院修讀學分（含教育部學海飛颺計畫）之核心補助規範。'
                    '依國際處規定，完成校內交換／雙聯甄選申請並獲外校錄取且符合資格者，由國際處直接送補助金審查，不需額外單獨填表申請。'
                ),
                key_points=[
                    '申請資格（第 3 點）：具中華民國國籍且在臺灣地區設有戶籍、於本校就讀 1 學期以上之在學學生（不含國內及境外在職專班生）；歷年學業成績平均達 70 分以上為原則；外語能力符合附件一標準（英文等同多益 TOEIC 700 分、IELTS 5.5、TOEFL iBT 72、Duolingo 105、劍橋領思 160、GEPT 中高級聽讀或 FLPT 195 以上；國外學校要求更高者依該校規定）。',
                    '第一類地區補助上限（附件二）：一學期上限新臺幣 75,000 元、一學年上限 150,000 元（適用美、加、智利、墨西哥、英、法、德、荷、比、盧、瑞、奧、義、西、葡、北歐五國、匈牙利、斯洛維尼亞、以色列、新加坡、澳洲、紐西蘭）。',
                    '第二類地區補助上限（附件二）：一學期上限新臺幣 60,000 元、一學年上限 120,000 元（適用日、韓、泰、馬、印、捷克、波蘭、立陶宛、拉脫維亞、巴西、哥倫比亞、俄、土、蒙、南非及大陸港澳地區；教育部學海飛颺經費不含大陸及港澳，實際適用經費依國際處審查核定）。',
                    '班排前 30% 加碼與扣除規定（第 3 點、附件二備註）：申請時歷年學業成績班排名達前 30% 者，每學期得增加新臺幣 10,000 元。不得同時領取我國政府其他出國研修補助；同一學制曾領本校短期學分課程或其他出國研修／實習補助者，已領金額自本補助額度扣除。',
                    '複審配分與返國義務（第 5、9、10、11 點）：複審配分為在校成績 30%、外語能力 30%、讀書計畫及學校國際聲望 30%、特殊表現 10%。每學期至少修讀專業科目 1 門且返校至少採認 3 學分（未滿一學期不得領取）；返國後 2 週內須繳交返校手續單並上傳問卷、心得報告及分享短片。',
                ],
                applies_to=['交換學生', '雙學位', '自費研修'],
                source=navigator_source,
                document_url=CGU_NAVIGATOR_PDF_URL,
                document_type='補助辦法',
                full_text_extracted=True,
            ),
        )
    if '出國研修補助審查與學海惜珠說明' not in existing_doc_titles:
        dashboard.document_explanations.append(
            RuleExplanation(
                title='出國研修補助審查與學海惜珠說明',
                summary=(
                    '國際事務處同步為符合資格學生辦理領航者補助與教育部學海系列計畫；實際補助名額與金額依當年度教育部核定經費、本校預算規模與當期申請人數核定。'
                ),
                key_points=[
                    '免重複送件：完成校內出國交換／雙聯申請並通過初審、取得國外合作校入學許可後，國際處自動將符合資格者送交補助金複審會議。',
                    '學海惜珠專案：具低收入戶、中低收入戶或相關經濟不利證明之本國在學學生，得另依《長庚大學辦理教育部學海惜珠補助要點》備妥戶籍與相關證明洽國際處辦理。',
                    '修課語種注意：依本校補助規定，赴外研修若選讀以中文授課之組別（如部分合作校中文組），不予核發補助。',
                ],
                applies_to=['交換學生', '雙學位'],
                source=oia_subsidy_source,
                document_type='補助說明',
                full_text_extracted=True,
            )
        )

    dashboard.scholarship_info = [
        StudentInfoItem(
            title='長庚大學領航者補助重點（規章 2B00004）',
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
