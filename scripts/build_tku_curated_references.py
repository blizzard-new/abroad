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
    retry=B/'meiji_2027_attachment_checks_retry1.json'
    if retry.exists():
        checks=json.loads(retry.read_text())
        assert len(checks)==5 and all(r.get('source_id') and r.get('content_reviewed') for r in checks)
        facts['latest_forms']['attachment_check_history']=facts['latest_forms']['attachment_checks']
        facts['latest_forms']['attachment_checks']=checks
        facts['latest_forms']['reason']='五份指定模板有限重試後HTTP200，原檔SHA256與PDF／Word內文均核對；首次503留存歷史。連結由AY2027簡章p.8確認，Word自身未載年度、英語表內AY2026課表僅參考。淡江當期提名未核實。'
        forms=[captured(r['source_id']) for r in checks]
        for source,needle in zip(forms,['This certification is valid for the date after April 2026','1000-2000','400-','1000-2000','1000 words or more']):
            f=fact('latest_forms',facts['latest_forms']['value'],1,needle,source,source['applicable_year'])[1]
            if not source.get('pages'):f['evidence'][0]['locator']='DOCX word/document.xml text'
            facts['latest_forms']['evidence']+=f['evidence']
        facts['latest_forms']['value']+=' 已實讀五模板：健康證明須2026/4後由醫師英／日文填寫，X光為入學前一年內；日文大學部理工及希望指導之農學另列三位教師，日文研究生三位教師除助教、經營研究科免填；英語表內AY2026課表只供參考，不表示2027課程已定。'
        for source,needle in [(forms[0],'X-rays taken within 1year'),(forms[1],'指導を希望する教員'),(forms[2],'Courses (AY2026)'),(forms[4],'not required for applicants to the Graduate School of Business Administration')]:
            extra=fact('latest_forms','',1,needle,source,source['applicable_year'])[1]
            if not source.get('pages'):extra['evidence'][0]['locator']='DOCX word/document.xml text'
            facts['latest_forms']['evidence']+=extra['evidence']
    curated=[dict(id='tku-sister-178',fields=facts)]
    retry_index=B/'host_source_retry_checks.json'
    if retry_index.exists():
        jwu_meta=next((r for r in json.loads(retry_index.read_text()) if '2027-28_AdmissionGuide.pdf' in r['source_url'] and r.get('http_status')==200),None)
        if jwu_meta:
            jwu=captured(jwu_meta['source_id']);assert len(jwu['pages'])==21 and '2027-2028 Program' in jwu['pages'][0]['text']
            def jwfact(key,value,page,needle,year='2027–2028 host incoming programme; TKU nomination unverified'):
                result=fact(key,value,page,needle,jwu,year)
                result[1]['reason']='實讀日本女子大學官方2027–2028接待交換簡章；學期／語言track與淡江當期提名對應未核實，不產生母校名額或文件流程。'
                for e in result[1]['evidence']:e['application_round']='Fall September2027 / Spring April2028 / winter intensive2028; separate host admission deadlines'
                return result
            jfacts=dict([
                jwfact('host_eligibility','接待校明示接受男性交換生，不能因校名推定僅限女性；英文建築設計交換須有相關主修先修背景且僅秋季。',2,'accepts male exchange students'),
                jwfact('host_language','日語regular programme須完成至少兩年日語學習；到校分班A2/B1，N3/N2為課程目標／程度，不能改成母校或接待校統一JLPT證書門檻。英文建築設計可選preA1/A1初級日語課，但須相關主修背景。',4,'at least two year of Japanese language study'),
                jwfact('department_scope','2027/4起八學部16系，經濟學部新增；2028/4時尚設計與人間科學為未來不同年度，不套進2027年初。英文建築設計僅秋季並需相關背景；一般日語regular programme可依學歷、語言与課程容量跨系選課。',5,'previous study experience in a related major'),
                jwfact('study_period','一年2027/9中旬–2028/7底；秋單學期至2028/1底、秋加冬集中至2月底；冬加春2028/2初–月底再4初–7底；春單學期2028/4初–7底，各選項分開。',6,'Mid-September 2027 ~ End of July 2028'),
                jwfact('host_nomination_deadline','一年／秋／秋加冬：2027/3/1；冬加春：2027/7/31；春單學期：2027/9/30。都是接待校母校提名期限，淡江校內甄選期限仍未知。',20,'NOMINATION & APPLICATION SCHEDULE'),
                jwfact('host_deadline','一年／秋／秋加冬：2027/4/10；冬加春：2027/9/1；春單學期：2027/11/1。不得用此期限表示淡江仍收新申請。',20,'April 10, 2027'),
                jwfact('course_restrictions','日語regular programme每學期至少14學分、日語5堂每週共10學分且至少兩門regular courses；英文建築設計至少12學分且限秋季。p.10英語課表明示只是2026例子、不保證同課開設；不當2027已定課表。',7,'Minimum credits: 14 credits per semester'),
                jwfact('housing','兩種校外share house與寄宿家庭：share house1步行3分鐘、2大眾運輸45分鐘；寄宿最長公共運輸約一小時。有不同設備／餐食，沒有保證每位學生分配同房型。',15,'ACCOMMODATION'),
                jwfact('housing_costs','簡章p.15估share house1每月JPY87,000、2每月JPY120,000，各JPY40,000入住費由JWU支援；寄宿約USD30（原文JPY4,840）每日另加通勤及安排費。原文USD1=JPY160與30美元對應4,840日圓算術不一致，保留待確認；不是現行匯率或固定帳單。',15,'87,000'),
                jwfact('costs','選冬季集中日語文化課約JPY10,000實習費，實際依內容調整；6學分，需母校與秋或春合併提名，一年交換預期參加。不把此額當整個交換總費。',9,'Approximately ¥10,000'),
                jwfact('campus','官方接待國際處Mejiro校址2-8-1 Mejirodai, Bunkyo-ku, Tokyo；建築及院系修課依programme核對，地址不是宿舍或已確定TKU分配校區。',21,'2-8-1 Mejirodai'),
                jwfact('transport','接待校international student supporters可協助接機、選課、設施及語言交流；屬支援服務而非免費機票／每位保證接送。住宿步行3分鐘與運輸45分鐘／一小時依房型分开。',14,'Airport pick-up assistance'),
            ])
            for key,page,needle in [('host_eligibility',5,'previous study experience'),('host_language',7,'aiming for N3'),('course_restrictions',8,'Minimum credits: 12'),('course_restrictions',10,'examples from the 2026 academic year'),('housing_costs',15,'40,000 yen move-in fee'),('housing_costs',15,'US＄30')]:
                jfacts[key]['evidence']+=jwfact(key,'',page,needle)[1]['evidence']
            curated.append(dict(id='tku-sister-326',fields=jfacts))
    if (B/'milestone3_reviewed_host_facts.json').exists():
        additions=json.loads((B/'milestone3_reviewed_host_facts.json').read_text())
        assert not {r['id'] for r in curated}.intersection(r['id'] for r in additions)
        curated.extend(additions)
    (B/"curated_partner_facts.json").write_text(json.dumps(curated,ensure_ascii=False,indent=2)+"\n")
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
    reviews=B/'reused_asset_review.json'
    if reviews.exists():
        present={r['id'] for r in locations}
        locations.extend(r['accepted_coordinate'] for r in json.loads(reviews.read_text()) if 'accepted_coordinate' in r and r['id'] not in present)
    geographic_reviews=B/'wikidata_asset_review.json'
    if geographic_reviews.exists():
        present={r['id'] for r in locations}
        locations.extend(r['accepted_coordinate'] for r in json.loads(geographic_reviews.read_text()) if 'accepted_coordinate' in r and r['id'] not in present)
    official_reviews=B/'official_geography_review.json'
    if official_reviews.exists():
        present={r['id'] for r in locations}
        locations.extend(r['accepted_coordinate'] for r in json.loads(official_reviews.read_text()) if 'accepted_coordinate' in r and r['id'] not in present)
    additional_reviews=B/'milestone3_geography_review.json'
    if additional_reviews.exists():
        present={r['id'] for r in locations}
        locations.extend(r['accepted_coordinate'] for r in json.loads(additional_reviews.read_text()) if 'accepted_coordinate' in r and r['id'] not in present)
    (B/'campus_location_manifest.json').write_text(json.dumps(locations,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(curated_host_institutions=len(curated),host_fields=sum(len(r['fields']) for r in curated),new_physical_campus_locations=2,reused_baseline_representative_locations=1,total_displayable_locations=len(locations))))


if __name__=='__main__':main()
