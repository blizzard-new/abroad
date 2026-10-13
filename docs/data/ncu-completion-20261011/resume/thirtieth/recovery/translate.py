from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtieth');D=R/'docs/data/ncu-completion-20261011/resume/thirtieth'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==5
translations=[
'首次校方入口選住宿才交宿舍保證书，房源與偏好不保證，由校方分配。現有秀麗、女生月丘及關大全球宿舍可申；南千里國際廣場和國際交流會館不接收交換。保證人原則親屬，學生朋友不可；50萬日圓是債務保證上限，並非先繳押金。秀麗入寮15000、A／B月41000／43000日圓，月丘入寮22000、月42000，全球宿舍入寮20000、月63000，另各一個月租金押金抵末月。月費含水電網路寢具、餐費按次另收；入寮費不退，押金抵末月不能當全部退現金。全球宿舍網頁標題還寫南千里，但正文為全球宿舍／吹田未來，須按入住通知核對。寄宿家庭一般安排費20000、每次住宿4000另稅、至少28天含早晚餐，原單位未明不推全年總額；公寓約40000以上，合作社保證及JEES資格依外國住民身分，含日本雙籍不適用。未標年寄宿文宣含早晚餐、依需求Wi-Fi，房間及家庭只是示例；饮食或外食先通知，個人心得非全體承諾，沒有當期費用或截止。五頁全視讀，公開仍只留第1、5頁一般說明；離校約30–60分鐘未明校區及交通，不保證中央交換生相同路程、床位、設備或活動。',
'交換互免關西學費，仍繳中央學雜費，額外課程或實驗費依協議核對。JASSO是否採用與對象尚未定，其他合作校獎學金也不能當中央必有財力。一般含住房每月10萬至15萬日圓，交通保險等依本人，不預扣獎學金。2026學年起全體交換生須自付GTN Assistants，期間同在學期；企業文宣每月含稅1650日圓未證實等於116契約價，付款另通知。早歸仍在學不退，退出或整學期縮短才可依已用期間、手續費與退款匯率處理。寄宿文宣交通自付，含早晚餐及依需求Wi-Fi，但沒有通勤票價、寄宿單價、押金、稅額，不能拼成116全包價。',
'指定到達日尚未確定，抵達後領到達資料、參加迎新及住民程序，依分配入住；先取得簽證才買機票，不先寄行李到宿舍。離境期限與宿舍搬出日分開，可能期末前須搬離；住所、水電瓦斯、手機及銀行須結清，約定書另要求報告、失效居留卡和問卷於返國前後繳交。國保及海外保障另辦，打工先取得許可，暫離日本先問再入境程序，FAQ不等個人核准。寄宿FAQ建議先熟悉日語與習俗，饮食需求提前告知，外食先通知家庭。迎新介紹文化差異及誤解，文宣沒有當期日期、接送或指定家庭。',
'CGAF要求菲律賓住址、到達日期航班、合法停留末日、校方代表及ACR資訊。政府FAQ對持臨時訪客身分住滿六個月等情形列離境許可ECC-A，至少起飛72小時前可申，不能套全部交換生。TSU國際處在Villa Lucinda校區飯店三樓僅辦公室位置，不作授課或宿舍校區。表格另有學校代表身分號、學校認證、ACR號及效期、CRN、雙地住址與監護欄，不能只見空欄便要求每人新增辦理所有號碼。月份／一年是申請勾選欄，不保證核准同等合法停留；表內未列當期辦理日數或費用。',
'2026/10/8已讀菲律賓政府入口：9F為18歲以上修高於高中課程；FAQ將未滿18或非學位學習列SSP，2024線上公告另列不足一年短期課程、實習及受訓。SSP是在臨時訪客簽證下的許可，不能代替合法停留，也不能按年齡自動判定9F；須由移民局與學校核本人方案。SSP清單七類為校方代表請求函、CGAF（未成年由家長／監護簽）、護照資料與最新入境及有效停留、認證校方載學期接受函、代表移民局ID、飛行學校才須NBI證明、移民局證明。兩份CGAF正本、法律紙規格資料夾、宣誓公證、外國正本英譯及館處認證要求保留；舊清單與2024說明範圍差異須確認。9F轉換另有校方與學生聯函及乾印、校方接受函乾印、註冊主管推薦函；醫牙資格、轉系及入境滿六個月的NBI等依条件。CGAF的9F2023和SSP2016版本分開，均兩頁、3月內白底2x2實體黏貼非掃描照片，與TSU六個月相片要求不同；兒童表網址2025、內文2024/8/5生效，只適用時。政府費表5240披索加I-card50美元、9F轉換9720加50、延長4020加50均標2014/3/6，不當2026／2027報價。兩CGAF均學生簽證及SSP共用，不能依下載分類選定個人簽證；首页雖印一頁仍有實際第2頁，不能漏附。第2頁禁止填寫、核准及蓋章區供機關處理，不當申請人自行批准或一般簽名欄；長官署名差異僅供版本核對，不推現任或適用已核。'
]
p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==735;keys={(r['original'],r['url'])for r in rows};ledger=[]
for item,zh in zip(x['items'],translations,strict=True):
 e=item['evidence'];original=e['original_text'];url=e['sources'][0]['url']
 for val in [original,zh]:
  assert(val,url)not in keys;rows.append({'original':val,'url':url,'zh':zh});keys.add((val,url))
 ledger.append({'theme':item['theme'],'school_name':item['school_name'],'original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'translation_sha256':hashlib.sha256(zh.encode()).hexdigest()})
shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json');p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'updated-card-translations.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print({'cards':len(ledger),'rows':len(rows)})
