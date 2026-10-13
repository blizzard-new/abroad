from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtyfirst');D=R/'docs/data/ncu-completion-20261011/resume/thirtyfirst'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==3
translations=[
'交換生住宿優先但房型不保證，錄取後才申宿，原則最長一年。靜岡單人房月25000加共益2400＝27400日圓，共益含Wi-Fi及寢具，水電依用量、一次清潔13200另計。2027介紹濱松單人13800–15000，現網會館Ⅱ月20000加共益3300＝23300，Ⅰ單人15000另8000共益未明週期；不同房型來源不混成當期最低價。Ⅱ清潔離房收、Ⅰ清潔及窗簾費入住收。民間房2013/1價表為歷史，機構保證需房東接受及JEES保險，一般入住前兩週送表不是宿舍申請期限。英日表說通常五個獨立單人房組成一戶，共用餐廳、廚房、淋浴與廁所，不是五人同房；優先與多數入住不等保證床位，錄取後提供申宿說明。',
'2027春交換包免外校學費，另份介紹依學生身分，中央仍繳母校學雜。日語課私費聽講每學分14800、研究者或配偶每科9700日圓屬其他身分，不能套交換。2027春表及FAQ當時無交換獎學金資訊，介紹的日本語日本文化研修政府獎學金117000–119000是不同身分，限額及18–30歲、日語文化專業條件，非中央保證取得。春季英日表每月10萬日圓起，介紹8萬至10萬及未標年FAQ約8萬屬不同來源，不能拿低值保證足夠或抵財力門檻。校外租金標2013/1，不作116精確預算；水電交通保險依人房型。Spring2027日文表明寫每月約10萬起包含滯在費，英文概述生活費；不能再次全額加住宿後稱校方合計，仍要自行分項預算，不保證116够用。',
'本科大多日語，少量英語通識不是專業；碩士依系所。2027表允跨學部課，FAQ另排除全球共創學部跨部選課，須依所屬核對。表原則每週至少10小時約7堂，碩士與教授確認研究等值時數；FAQ說超過10小時及超過7堂，邊界差異保留，不直接判定7堂足夠。日語班需分級及教授同意，有學分不等中央畢業採認；2026秋課表只供別期參考。Spring2027碩士方案列人文社會、綜合科學技術及山岳流域三研究科，全校位置表另有教育、光醫等，不能當都開放交換。成績單須學生申請才發，不假定自動寄，學分採認出發前問母校。可選半年或一年，春4/1至9/30、秋10/1至3/31，春入住4/1及7月底期末課／考試，秋入住9月下旬及2月首週期末；按2027春表及一般模式分年，不作116已核行程。'
]
p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==745;keys={(r['original'],r['url'])for r in rows};ledger=[]
for item,zh in zip(x['items'],translations,strict=True):
 e=item['evidence'];original=e['original_text'];url=e['sources'][0]['url']
 for val in [original,zh]:
  assert(val,url)not in keys;rows.append({'original':val,'url':url,'zh':zh});keys.add((val,url))
 ledger.append({'theme':item['theme'],'school_name':item['school_name'],'original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'translation_sha256':hashlib.sha256(zh.encode()).hexdigest()})
shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json');p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'updated-card-translations.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print({'cards':len(ledger),'rows':len(rows)})
