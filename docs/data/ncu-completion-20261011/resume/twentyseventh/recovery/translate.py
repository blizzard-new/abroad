from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyseventh');D=R/'docs/data/ncu-completion-20261011/resume/twentyseventh'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==8
translations=[
'''【2024/25拉羅歇爾校區】秋季四年級全球工程課程為英語，至少選兩個完整教學單元，不能拆單元；英語課表列管理、工業工程、工業專案、人文語言，以及資料科學／機械與能源選項。春季法語專長每組15 ECTS，須整組修。
拉羅歇爾與卡薩布蘭卡校區的開課語言及專長不同；研究專案兩學期皆可詢問，但非所有系保證接收。中央未年介紹限定全球工程課程（Global Engineering Program），外校其他英法語路徑不自動對中央協議開放。
網頁只說交換生9月初開學，沒有116確定日期。2024/25舊表：拉羅歇爾秋2024/9/2–12/20，春核心2025/1/6、專長2/24起至5月中；卡薩布蘭卡春核心1/2、專長另2/24，依方案區分，非116校曆。
中央未年介紹明列僅秋季一學期，9月至12月；不能因外校通用資料列春季，就推定中央本方案可以春季或一年。''',
'''中央公開的未年介紹建議學生簽證問題向西班牙駐臺相關代表機構洽詢。這只是舊校方轉介，原件使用使領館稱呼，不據此認定當前機關名称或臺灣學生適用程序；116規則與本人資格須向主管機關核對。''',
'''Douglas入境交換資源明確說沒有自有學生宿舍；可選寄宿家庭或私人租屋，由本人找房，未保證住宿。一般溫哥華生活頁所列Global Education City學生住宅是外部選項，不能當成Douglas校內房。
校方列寄宿服務，但不為所有公司背書；查看屋內並核對租客權利後再簽約付款。中央未年介紹也說無校內住宿、國際處協助找房，協助不等於床位或房價保證。''',
'''已讀入境交換頁明確說一般交換學生繳母校學雜費，Douglas不收交換學雜費，每月U-Pass交通票免費；書籍教材、基本醫療保險、食宿及個人支出自付。
付費訪問學生須繳一般國際生學雜費；資料表9–12學分及免申請費屬訪問方案，不能套一般交換。ELLA語言課程參加者仍屬交換、免外校學費。
中央介紹檔名標付費，內文卻泛稱交換；不能只憑檔名推翻兩種方案的區別。中央116適用哪種方案未確認，不能保證免費或一律付費。
未年資源頁估算：合租屋私人房每月房租及水電800–1000加幣，套房或一房公寓1500–2400加幣是替代選項；每週食品100–150加幣，單次晚餐25、含小費30、加酒45加幣。計程車或Uber約3.25加幣起跳加每公里1.84加幣；Cypress滑雪季票400加幣為可選娛樂，不能當全體強制費用或移民財力要求。
中央未年介紹估每學期5500–7500加幣生活費，依住宿而變；這是每學期、不是每月，也不是含全部學費的當期總價。不同來源及計價週期分開保留，不混成單一新預算。''',
'''學術頁列全時修讀9–15學分（約3–5門課），15學分相當於30 ECTS；申請流程頁卻說通常12–15學分，最低要求與通常負荷分開。
不能修應用社區研究與健康科學；當代藝術（音樂／視覺藝術）及運動科學須系所特別許可。概覽列健康科學不代表可修；保留概覽與具體排除清單的差異。
須具先備條件，修讀同等或較低層級課程；3000–4000進階課很難有位，建議選通識選修，並非全部禁止。若當期課表未出，前一年同學期課表只供參考。中央未年介紹另說健康及人類／社會服務不開放，當代藝術及運動科學需許可；秋冬較多課、夏較少，不保證名額。
一般秋9–12月、冬1–4月、夏5–8月，夏季選擇較少；可交換一或兩學期（4或8個月），但不能取消中央歷史項目的一學期限制。2027–28授課、考試及迎新未核。舊日期連結404，新入口沒有啟用中的申請期起迄，不用舊年補值。中央未年介紹的秋9–12月、冬1–4月也不等於本期開放或精確考日。''',
'''中央未年介紹限ACP或ASAP，列12學分範圍；超過12學分須額外付學分費，不是禁止選第13學分，也不保證任一課程可選。
中央未年介紹秋9–12月、春3–6月；學期頁使用學期制稱呼，費用頁卻按季度計價，兩種週期各照原件保留，不擅統一。''',
'''未年原件第1頁說需購買強制健康保險；第2頁圖片卻允許自備符合UCI保障要求的保單，或使用UCI每季585美元保險。保留兩頁說明差異，不改成強制購買UCI方案；每季不是每學期，價格及豁免條件须更新確認。''',
'''中央未年介紹對應UCI繼續教育方案，辦公位置為爾灣校內第一棟238號，位於Pereira與Brandywine路一帶。這不是宣稱所有課程都在該棟，也未據此改動地球代表校址。'''
]
p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==693;keys={(r['original'],r['url'])for r in rows};ledger=[]
for item,zh in zip(x['items'],translations,strict=True):
 e=item['evidence'];original=e['original_text'];url=e['sources'][0]['url']
 for val in [original,zh]:
  assert (val,url)not in keys;rows.append({'original':val,'url':url,'zh':zh});keys.add((val,url))
 ledger.append({'theme':item['theme'],'school_name':item['school_name'],'original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'translation_sha256':hashlib.sha256(zh.encode()).hexdigest(),'reason':'合併舊新中文化，保留方案、計費週期、適用限制及來源版本差異。'})
shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json');p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(D/'updated-card-translations.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print({'cards':len(ledger),'rows':len(rows)})
