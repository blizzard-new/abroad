from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentysixth');D=R/'docs/data/ncu-completion-20261011/resume/twentysixth'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==5
translations={
('雷恩','academics'):'學習協議由母校協調人核准，線上選課，個別課程學分及當期清單須核對最新課程目錄。\n2026–27到校前線上選課，秋／全年6月、春11月聯絡註冊。最低管理課數：Level 2八門，Level 3四門（完整一個方向加至少一門核心），Level 4四門，Level 5三至五門且同一專長，原表註可能微調。原表只接受因撞堂而更課；30 ECTS通常對應15美制或60英制學分，不保證中央抵免。\n未註年官網說一學期或全年，Level 2僅秋季，考試通常12月／4月、補考6–7月，不為個別學生更改考日。\n2026–27表列秋各級9月中至12月底；春Level 3一月中開始，Level 2、4、5一月初開始，均至四月底。這與未註年官網Level 2僅秋季的說明不同，保留衝突，不能據此宣稱中央Level 2春季已開放。',
('圖爾','housing'):'未註年交換入口說明，多數入境交換生可取得TYS附家具住宿，非全體保證，仍须另行申請。\n2026–27表可向TYS申請學生住宿，租金約每月330–500歐元，不等於校方保證床位；校區有圖爾庫、波里及勞馬，波里距圖爾庫約140公里、勞馬約90公里，不能當同一通勤點。',
('圖爾','cost'):'2026–27表免交換學生學費、課程及註冊費；學生會約55歐元是每學年自願加入、校方推薦，不能改為每學期必繳費或全部生活免費。\n2026–27表每月生活費600–1000歐元，隨租金而異且不含休閒活動；另列租金330–500歐元為組成參考，不把房租重複加到生活總額，也不當全部支出全包。',
('圖爾','social'):'提名後SoleMOVE寄啟用信，申請通常3–4週審理；提交後及早依住宿供應商期限找房，保險、居留及旅行再依錄取安排。\n錄取後以SoleMOVE電子郵件內連結確認交換，另安排保險、住宿及適用居留；Erasmus+線上學習協議另有適用段落，不能套全部雙邊學生。\n2026秋迎新8/24–26實體舉行，沒有遠距方式，行前迎新6/9；2027春迎新1/7–8，朋輩導生聯絡資訊以電子郵件寄送。這些不是116的2027秋／2028春日期。\n2026秋到校參考：人口登記機關駐點9/7、9、14依姓氏分組，9/23、28開放一般學生，先至少一天送線上表。護照或正式身分證須到場攜帶，駕照不接受；非EU/EEA居留卡與圖爾庫註冊證明若先上傳，可不再帶紙本。此為2026校方說明，116程序及資格仍需主管機關確認。\n2026–27表為每名交換生安排芬蘭朋輩志願導生，成績單在考核期結束後五週內發出，非最後上課日即取得；一般迎新月份不取代先前已核2026秋／2027春確日。',
('俄斯','academics'):'一份未年官方表列最低20 ECTS、建議30 ECTS，最低要求與建議分開。\n另份未年VSB表只寫建議23–30 ECTS，不是最低23；與另一表最低20、建議30的表述分開保留。個別課程、接收學院與中央116方案待確認。'}
p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==683;keys={(r['original'],r['url'])for r in rows};ledger=[]
for item in x['items']:
 e=item['evidence'];original=e['original_text'];url=e['sources'][0]['url'];zh=translations[(item['school_name'][:2],item['theme'])]
 for val in [original,zh]:
  assert (val,url)not in keys;rows.append({'original':val,'url':url,'zh':zh});keys.add((val,url))
 ledger.append({'theme':item['theme'],'school_name':item['school_name'],'original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'translation_sha256':hashlib.sha256(zh.encode()).hexdigest(),'reason':'新舊參考合併後完整中文化，保留版本差異、年/月、條件及來源；同年重複描述合併但不删事實。'})
shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json')
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'updated-card-translations.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print({'cards':len(ledger),'rows':len(rows)})
