from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyeighth');D=R/'docs/data/ncu-completion-20261011/resume/twentyeighth'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==5
translations=[
'校方鼓勵住校內高年級宿舍或國際之家，但不是強制或住宿保證。校外須看押金與租約責任；交換單學期房費是全年費率的60%，須以實際住宿合約確認。2026–27表說多數交換生住國際之家，校內房有限，錄取後應立即申請；多數入住不代表全體保證。',
'2026–27費用頁把一般交換與學費減免交換分表；一般交換表無學費項目，但有必繳學生費。減免方案每學期學費9000美元、另學院费566，不能套所有中央交換或保證全免其他費用。一般交換估秋10903、春11605、全年20808美元；單學期住房5099是全年8499的60%，不是一半；餐食3454、書籍450、學生費813，醫保秋1087、春1789美元。交通、個人及暑期支出不含，提前入住另每晚50美元。減免方案總額秋20469、春21171、全年39940美元，是不同方案；眷屬每人每年另加6000美元財力。2026–27資料表另建議個人支出每學期至少1500美元、特殊課另付；全年學生費1625與813乘二差1美元，按原表保留，不自行校正。全年住房與兩期相加不同，不把總額換成月費。',
'已讀官網規定最少12面授學分（約4門），混成課算面授；線上課須額外於12現場學分，不套其他美國學校允許一門線上計入全時的規則。可選外系，但500–799研究所課通常不提供交換。錄取後先排10–12門志願，用iNAU交換選課申請，協調人與顧問核先備後安排4–6門；保留或候補不保證名額。第二學期到校後才選，LOUIE欠費未清不發母校正式成績單。2026–27表另列每學期最少12、最多19學分（通常4–6門），牙科衛生及護理不開，音樂較高要求，仍看資格及餘額。一般秋8–12、春1–5月，一學期或全年依提名錄取確認；精確2027–28尚未核。2026–27表秋2026/8/24–12/11、春2027/1/11–5/7，前一週新生迎新，不移作116校曆。',
'ISSS全體須完成三步報到：入美前上傳護照及本人F1或J1簽證、I20或DS-2019；入美後上傳I20或DS-2019、I94、美國電話與地址、理解聲明；再至Blome第2棟或迎新現場確認。轉學生15日內、初次學生30日內現場報到，是未標年校方記述，116個人SEVIS與迎新通知另核。未年NAU折頁要求開課前一週迎新，提供社團、無障礙支援與校內工作實習入口；工作資訊不是聘用或本人資格保證。',
'J1須NAU學生醫保覆蓋DS-2019及J1全期，每學期由LOUIE收費。ISEP學生及符合美國政府或國際組織提供保險者可能有特定豁免，一般中央雙邊交換不能直接套用；F1的母國政府或美國雇主豁免是另一範圍。2026–27醫保秋1087、春1789、全年2876美元；豁免須ISSS當期截止前辦，之前學期不退，原頁未列確切期限。2026–27表概述全體交換購NAU醫保、直接記帳，另需麻疹接種證明才能註冊課程；特定身分豁免另存，不解讀成全無例外，麻疹證明也不是本表已列的完整初申附件。'
]
p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==709;keys={(r['original'],r['url'])for r in rows};ledger=[]
for item,zh in zip(x['items'],translations,strict=True):
 e=item['evidence'];original=e['original_text'];url=e['sources'][0]['url']
 for val in [original,zh]:
  assert (val,url)not in keys;rows.append({'original':val,'url':url,'zh':zh});keys.add((val,url))
 ledger.append({'theme':item['theme'],'school_name':item['school_name'],'original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'translation_sha256':hashlib.sha256(zh.encode()).hexdigest(),'reason':'合併舊新中文化，保留方案、計費週期、適用限制及來源版本差異。'})
shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json');p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'updated-card-translations.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print({'cards':len(ledger),'rows':len(rows)})
