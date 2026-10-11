"""Reviewed host-year facts and campus sources, separate from TKU nomination."""
import gzip
from tku_capture_io import read_bytes, exists, captures
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/"src/exchange_info/official_data/tku"


def captured(key):
    return json.loads(gzip.decompress(read_bytes(B/"host_census_sources"/(key+".json.gz"))))


def main():
    guide=captured("032fde05c3b972dc0c87ee4e")
    sheet=next(captured(p.stem.split('.')[0]) for p in captures(B/"host_census_sources")
               if "FACTSHEET4exchange_EN.html" in captured(p.stem.split('.')[0])["source_url"])
    assert "2027 Academic Year" in guide["pages"][0]["text"] and len(guide["pages"])==9
    def fact(key,value,page,needle,source=guide,year="2027 academic year; host incoming exchange only"):
        text=source["pages"][page-1]["text"] if source.get("pages") else source["text"]
        assert needle in text,(key,needle)
        start=text.index(needle)
        return key,dict(value=value,status="reference_only",source_period_verified=True,
            reason="已讀官方2027接待校文件；淡江當期提名對應尚未核實，不能變成母校開放名額或語言門檻。",
            evidence=[dict(source_id=source["id"],source_url=source["source_url"],checked_at=source["checked_at"],
                applicable_year=year,application_round="April/September 2027 incoming; TKU nomination unverified",role="host_incoming",
                locator=f"PDF p.{page}" if source.get('pages') else "AY2027 Fact Sheet section and exact source quotation",
                quote=text[start:start+500],content_sha256=source["sha256"])])
    facts=dict([
        fact("host_nomination_deadline","2027春：母校提名2026/9/9–10/9；2027秋：2027/2/2–3/8。春季提名已截止，不能由接待校上傳期限推定淡江仍受理新申請。",1,"September 9 to October 9, 2026"),
        fact("host_deadline","2027春：2026/10/16完成線上申請、材料上傳及COE；2027秋：2027/3/15。需要母校先提名。",1,"September 9 to October 16, 2026"),
        fact("host_eligibility","須為明治協議機構學生，依日語／英語track和院系條件申請；院系與期間申請後不可改。一般碩士院不支援學位論文，只有Global Governance接受博士交換。",3,"Student at one of Meiji University's partner institutions."),
        fact("host_language","日語門檻依院系從N4至N1；N1證書不限制考試年度，N2–N4須2025或2026測驗。英語track按院系及測驗種類逐列核對，PDF p.5明確分2026/1/21前後TOEFL兩種量尺，不能套用單一舊制分數。",3,"Japanese Language"),
        fact("department_scope","英文課Business Administration須商管相關在籍。建築都市設計年總招生28、Governance英語track年總8，屬明治計畫容量，不能作淡江名額；須依各院系限制及母校提名確認。",6,"Annual enrollment capacity is 28 students per year."),
        fact("study_period","期間須於申請前決定，線上申請後不得變更；抵達／入住春季2027/3下旬、秋季2027/9上旬。",6,"Duration must be decided before applying"),
        fact("latest_forms","接待校2027文件：語言證書、英／日文加蓋校方章及簽名成績單、明治指定Word研習計畫（大學部日文1000–2000字或英文400–800字）／研究計畫（研究生日文1000–2000字或英文至少1000字）、指定健康證明含必做X光、近3月4:3 JPG照片及涵蓋交換期間的護照；建築都市設計另寄PDF作品集。模板本身未載年度，依2027簡章p.8的明示連結使用。",8,"9. Application Documents"),
        fact("course_restrictions","2027課程申請時尚未定案，官方明示2027/3下旬才定案並於orientation告知；要修大量學分須申請前洽承辦。院系不能申請後更換；SGJS日語課限Nakano，不可選其他校区日語課。",9,"The classes conducted in the 2027AY have yet to be fixed"),
        fact("campus","Surugadai／Izumi／Ikuta／Nakano四校區；依院系配置。日語課一般在Surugadai，SGJS在Nakano，不把任一校址當所有交換學生的校區。",1,"SURUGADAI campus",sheet),
        fact("housing","2027春依2026/5資訊安排四宿舍；床位超額須自行找房，不能保證指定宿舍。申請後不可變更／取消，選自行找房後不能再申請校方宿舍。",1,"Housing arrangement",sheet),
        fact("housing_costs","先付一學期約5個月租金後抵達，一年交換第二學期租金到校後另付；首末月按日計費，但已付校方費用不退。租額僅2026/5參考、會變动，不作2027固定帳單。",1,"Residents are required to pay",sheet,"May 2026 dormitory reference for Spring 2027; amounts subject to change"),
        fact("insurance","須加入日本國民健康保險及明治學生健康保險；一般旅遊險／個人責任險的建議不能當作已含全部保險費。",1,"National Health Insurance",sheet),
        fact("living_costs","Fact Sheet引用JASSO東京都生活費估每月JPY150,000；屬一般生活參考，不等於個人總支出或當期固定費用。",1,"150,000",sheet,"general JASSO estimate cited by AY2027 Fact Sheet; personal costs vary"),
    ])
    facts['course_schedule']=dict(facts['course_restrictions'],status='explicit_not_finalized',value='明治官方2027簡章p.9明示申請時2027課程尚未定案，預定2027/3下旬定案。')
    for key,page,needle,source in [('host_eligibility',6,'Only the Graduate School of Global Governance offers',guide),
            ('host_language',5,'January 21,',guide),
            ('course_restrictions',1,'SGJS students cannot take Japanese courses',sheet),
            ('housing_costs',1,'As of May 2026',sheet)]:
        extra=fact(key,facts[key]['value'],page,needle,source)
        facts[key]['evidence'] += extra[1]['evidence']
    if (B/'meiji_2027_attachment_checks.json').exists():
        facts['latest_forms']['attachment_checks']=json.loads((B/'meiji_2027_attachment_checks.json').read_text())
        facts['latest_forms']['reason']+=' 五份指定模板本次開啟均HTTP503，僅文件要求及連結適用期已核實；附件內容和可開啟性尚未核實。'
    (B/"curated_partner_facts.json").write_text(json.dumps([dict(id="tku-sister-178",fields=facts)],ensure_ascii=False,indent=2)+"\n")
    locations=[]
    source=next(captured(p.stem.split('.')[0]) for p in captures(B/'host_census_sources')
                if captured(p.stem.split('.')[0])['source_url']=='https://www.rhul.ac.uk/')
    link=next(x for x in source['links'] if 'maps/place/Royal' in x['url'])
    assert '!3d51.425673!4d-0.5630625' in link['url']
    locations.append(dict(id='tku-sister-66',verification_status='verified_asset',location=dict(city='Egham',latitude=51.425673,longitude=-0.5630625,
        geocode_status='verified',geocoded_at=source['checked_at'],source_url=source['source_url'],identity_source_url='https://sister.tku.edu.tw/school-detail.asp?id=66',precision='campus',
        note='官方Royal Holloway頁明示Egham Surrey TW20 0EX，命名校園Google地標!3d/!4d；未採@視窗。英國及校名／地址核對；只表示實體Egham校園位置，當期交換校區仍須依提名核對。'),
        evidence=dict(source_url=source['source_url'],quote=link['title']+' '+link['url'],checked_at=source['checked_at'],applicable_year='general campus location, not an exchange allocation',role='host_campus_location',locator='Official homepage named Egham campus map link')))
    seikei=captured('95d55b14fe4c16ede6303158')
    assert '東京都武蔵野市吉祥寺北町3-3-1' in seikei['text']
    locations.append(dict(id='tku-sister-274',verification_status='verified_asset',location=dict(city='Musashino, Tokyo',latitude=35.711472,longitude=139.573278,
        geocode_status='verified',geocoded_at=seikei['checked_at'],source_url='https://commons.wikimedia.org/wiki/File:Seikei_University_(16).jpg',identity_source_url=seikei['source_url'],precision='campus',
        note='Commons授權照片標明Camera location 35°42′41.3″N 139°34′23.8″E；成蹊官方地址3-3-1 Kichijoji-Kitamachi核對，照片所見主建築校園內點，非精確校園中心或學生宿舍。'),
        evidence=dict(source_url='https://commons.wikimedia.org/wiki/File:Seikei_University_(16).jpg',quote='Camera location 35° 42′ 41.3″ N, 139° 34′ 23.8″ E; official address 東京都武蔵野市吉祥寺北町3-3-1',checked_at=seikei['checked_at'],applicable_year='2017 campus photograph point; current address verified 2026-10-11',role='licensed_campus_photo_location',locator='Commons Camera location + official Access address')))
    from tku_baseline_assets import existing_ritsumeikan_location
    locations.append(existing_ritsumeikan_location())
    (B/'campus_location_manifest.json').write_text(json.dumps(locations,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(curated_host_institutions=1,host_fields=len(facts),new_physical_campus_locations=2,reused_baseline_representative_locations=1,total_displayable_locations=len(locations))))


if __name__=='__main__':main()
