"""Official, programme-scoped life guides for TKU; uncertain fields stay visible."""
from .models import DestinationProfile, SourceReference, StudentGuideSection, StudentGuideChecklistItem
from .tku_data import CHECKED_AT
from .tku_host_data import source_map

SECTIONS=[('host_programme_mapping','計畫及適用範圍'),('host_calendar','學期與課程日期'),
          ('housing','住宿安排'),('housing_costs','住宿與餐費'),('housing_application_deadline','住宿申請窗口'),
          ('living_costs','生活費估算'),('insurance','保險'),('visa_residence','簽證與居留'),
          ('course_restrictions','選課及學分'),('course_schedule_2027','當期課表'),
          ('arrival_preparation','行前及抵達'),('arrival_date','指定抵達日'),('transport','接送與通勤'),
          ('scholarships','獎助機會及條件')]


def build_tku_destination(record):
    f=record.fields; sources=source_map(); sections=[]
    mapping=f['host_programme_mapping']
    mapping_caution=mapping.reason if mapping.status=='needs_confirmation' else None
    for key,title in SECTIONS:
        fact=f[key]; basis='；'.join(f"{e.applicable_year}／{e.locator}" for e in fact.evidence)
        caution=(fact.reason or '此欄未完全核實，依來源原文與適用範圍確認。') if fact.status!='verified' else None
        if mapping_caution and key!='host_programme_mapping':caution='NICS對應本輪提名計畫待確認。'+(caution or '')
        sections.append(StudentGuideSection(key=key,title=title,summary=str(fact.value) if fact.value is not None else '此項當期內容尚未核實，見下列原因。',
            points=[f'來源適用：{basis}；查核2026-10-08。'],
            source_urls=list(dict.fromkeys(e.source_url for e in fact.evidence)),evidence_type='official',caution=caution))
    first=[]
    if f['arrival_preparation'].value:
        first.append(StudentGuideChecklistItem(title='依錄取生行前通知完成報到與住宿',
            detail=str(f['arrival_preparation'].value)+' 指定日期／程序不足處須先確認，不能直接購票。',
            source_urls=[e.source_url for e in f['arrival_preparation'].evidence],timing='依外校指定日期；尚未核實精確日'))
    first.append(StudentGuideChecklistItem(title='安排住所登記與國民健康保險',
        detail='官方一般居留指引：確定住所後14日內向所在地自治體辦住所登記；國民健康保險依居住地役所程序。保費與所需文件依最新規則，並非要求全部在72小時內完成。',
        source_urls=[sources['uec-residence']['source_url'],sources['uec-national-insurance']['source_url']],
        timing='住所確定後14日內（一般指引）',evidence_type='official'))
    packing=[StudentGuideChecklistItem(title='依本人國籍及COE準備签證文件',detail=str(f['visa_residence'].value),
        source_urls=[e.source_url for e in f['visa_residence'].evidence],timing='入境前，依所在地簽證機關規則')]
    if record.id.endswith('ritsumeikan'):
        packing.append(StudentGuideChecklistItem(title='確認需補的健康與學習支持文件',detail='錄取後全體填健康資訊；需支持者依外校另寄表準備醫師證明、處方或母校調整證明；不把條件式文件列成所有人必繳。',source_urls=[sources['ritsumeikan-2027-guide']['source_url']+'#page=21'],timing='錄取後；1月中截止為暫定'))
    used=list(dict.fromkeys(e.source_id for fact in f.values() for e in fact.evidence))
    used+=['uec-residence','uec-national-insurance']
    return DestinationProfile(home_university='淡江大學',school_name=str(f['school_name'].value),country='日本',
        housing_summary=str(f['housing'].value),cost_summary=str(f['costs'].value),transport_summary=f['transport'].value,
        campus_life_summary=str(f['course_restrictions'].value),student_guide_sections=sections,
        first_72_hours=first,packing_from_taiwan=packing,last_checked=CHECKED_AT,coverage_status='official_partial',
        coverage_note='逐項保存年度、查核日期與未知原因；一般／舊年度價格只供參考，非全部完整。NICS對應、非公開表及2027未核實項目以提示保留。',
        sources=[SourceReference(title=sources[s].get('title',s),source_url=sources[s]['source_url'],
            summary=f"{sources[s]['applicable_year']}／{sources[s]['role']}／查核2026-10-08") for s in dict.fromkeys(used)])
