from pathlib import Path
import json
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyfirst');S=R/'sources/ncu/2026-10-11/reviewed-host-records.json';D=R/'docs/data/ncu-completion-20261011/resume/twentyfirst';x=json.load(open(S))
spec={
'ncu-110':{'points':['母校未註年自費方案明列須繳中央與天普兩校學雜費；美國籍適用州外費率。外校正文2025–26所列每學期學費16956美元卻明註2024–25，每夏更新，不能當116報價。另508美元服務費僅訪學方案、175美元國際生費全體，個別課程可能另收費；不從同表Exchange方案推定自費也免學費。'],'sources':[{'id':'1twa72-6AdXRzdVzGy8qTlcnlJaiRvO0J','page':1},{'id':'1fjbURDv94SGZ42PI-Sz04ECxnZ0R6vYV','page':3}],'unresolved':'中央116自費方案、兩校最新學雜費及適用收費仍待核實。'},
'ncu-204':{'points':['未註年經濟商學院交換海報列免學費，僅屬該院交換方案；沒有免除中央學雜費、住宿、生活或簽證成本。不能擴為全校所有學程，中央116實際適用協議仍待確認。'],'sources':[{'id':'1Q7NgoqWBefphbjBdkdhrkoKNx4rLgSiF','page':1}],'unresolved':'未取得中央116院級適用確認及兩校最新其他收費。'}}
for rid,field in spec.items():x[rid]['fields']['tuition']=field
x['ncu-110']['fields']['cost']['points']=['外校2025–26正文估食宿7500、旅行書籍及個人支出2750美元／學期；食宿不是單純房租。這些為概估，不是116保證總價，兩校學雜費、保險及可能的課程費另計。']
x['ncu-204']['fields']['cost']['points']=['經管院未註年資料估生活$120–200／月，原件未註$幣別或完整包含範圍；母校舊表300美元／月另列，不能混為同年或同方案，也不能據此產生116固定總額。']
S.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');add=json.load(open(D/'added-host-records.json'))
for rid in add:add[rid]=x[rid]
(D/'added-host-records.json').write_text(json.dumps(add,ensure_ascii=False,indent=2)+'\n');print('tuition fields 2; batch fields',sum(len(r['fields'])for r in add.values()))
