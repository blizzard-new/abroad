from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
W=Path('/workspace/ncu-resume-work/twentyfirst')
refs={9:('23757a06778f7569716a19987dd1d39effce13f2','src/exchange_info/official_data/ntu/partners.jsonl'),10:('52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8','src/exchange_info/official_data/ccu/campus-assets.json'),13:('93cbd9dfee3af95f9ecc89cceb1ccd0e100778af','src/exchange_info/official_data/tku/campus_asset_manifest.json')}
patterns=re.compile(r'Normand|諾曼|IDRAC|\bISIT\b|Rennes|雷恩|翰尼|Troyes|特魯|Bing[oö]l|賓格|Alanya|Alaaddin|阿拉尼|Demirel|蘇萊曼|Jinan|濟南|济南|Nommensen|諾門|Thai.?Nguyen|太原|International University|胡志明',re.I)
manual={
'雷恩第一大學（原翰尼第一大學）':('ncu-022','不同機構，雷恩第一大學不是雷恩商學院；且donor無照片。'),
'特魯瓦科技大學':('ncu-036','同國校名候選，但donor image_status=missing、image_page_url空，沒有可重用照片。'),
'University of Economics and Law (UEL), Vietnam National University Ho Chi Minh City 越南胡志明市 經濟法律大學':('ncu-215','同大學系統不同成員：經濟法律大學不是International University；且donor無照片。'),
'Ho Chi Minh City University of Technology HCMUT胡志明市國家大學所屬百科大學':('ncu-215','同城/系統不同成員，HCMUT百科大學圖書館不能用作International University。授權存在不等於身分相符。'),
'Ho Chi Minh City University of Technology and Engineering HCMUTE胡志明科技工程大學':('ncu-215','HCMUTE科技工程大學中央大樓不是International University；不可用校名近似、所在城市或共同首字套用。'),
'太原大學':('ncu-213','太原大學系統主行政楼，不是已核實太原農林大學TUAF校園；不以同系統關係替代成員學校/教學校區核對。')}
receipts=[];candidates=[]
for pr,(sha,path) in refs.items():
 p=W/f'pr{pr}-latest-assets.json';data=[json.loads(l)for l in p.read_text().splitlines()]if pr==9 else json.load(open(p));data=data.get('schools',[])if isinstance(data,dict)else data
 receipts.append({'pr':pr,'fixed_sha':sha,'path':path,'source_url':f'https://github.com/blizzard-new/abroad/blob/{sha}/{path}','retrieved_exit_code':0,'response_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'record_count':len(data)})
 for row in data:
  name=row.get('school_name','')
  if not patterns.search(name):continue
  rid,reason=manual[name]
  candidates.append({'ncu_row_id':rid,'donor_pr':pr,'donor_sha':sha,'donor_school_name':name,'donor_country':row.get('country'),'photo_metadata':{k:row[k]for k in ['image_status','image_page_url','source_url','photo','caption','identity_address','identity_quote','license']if k in row},'decision':'not_reused','reason':reason})
assert len(candidates)==6
out={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'12剩餘缺圖項目候選搜尋與逐筆排除；僅照片相關欄，未合入任何donor名額、年度、資格或共用matcher。名稱搜索只是候選篩選，不自動認定相同學校。','source_receipts':receipts,'candidate_reviews':candidates,'new_usable_photos':0,'remaining_photo_gaps':12,'read_method_note':'廣泛git fetch未於合理等待內完成，主動終止僅本次唯讀fetch（退出143）；改GitHub contents GET固定SHA三檔皆退出0。不是環境断線或來源授權拒絕。'}
(W/'latest-donor-photo-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print({'candidate_reviews':6,'new_usable_photos':0,'remaining':12})
