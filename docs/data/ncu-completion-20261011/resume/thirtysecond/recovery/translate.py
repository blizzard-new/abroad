from pathlib import Path
import json,hashlib,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtysecond');D=R/'docs/data/ncu-completion-20261011/resume/thirtysecond'
x=json.load(open(W/'pending-chinese-cards-after.json'));assert x['pending_evidence_rows']==1 and x['partners']==2
zh='技術科學學院規定所申請系所至少20 ECTS；具先修、非大學部整組課程者，可另選同學院或自然科學最多10 ECTS。工程碩士不能選專題模組、研發與碩士論文；機械及生產工程另須至少20 ECTS相關數學並交課程說明，其他系依各自先修。2027植物科學及Viborg搬遷屬其他領域，多數工程課目仍2026版，秋約4/1、春約10/1再確認。2026–27表列全時每學期30 ECTS、一般一學院且多數一系選課；工程前述20加10的例外另依具體規定。丹麥02及格，部分課只記通過或不通過；學生可自行下載正式PDF成績，不假定校方自動寄送。'
e=x['items'][0]['evidence'];original=e['original_text'];url=e['sources'][0]['url'];p=R/'src/exchange_info/official_data/life_translations_zh.json';rows=json.load(open(p));assert len(rows)==751;keys={(r['original'],r['url'])for r in rows}
for value in [original,zh]:
 assert(value,url)not in keys;rows.append({'original':value,'url':url,'zh':zh})
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');shutil.copy2(W/'pending-chinese-cards-after.json',W/'pending-chinese-cards-before-translation.json');(D/'updated-card-translations.json').write_text(json.dumps([{'school_name':x['items'][0]['school_name'],'theme':'academics','original':original,'url':url,'zh':zh,'original_sha256':hashlib.sha256(original.encode()).hexdigest()}],ensure_ascii=False,indent=2)+'\n')
# Remove repeated batch scope note introduced by two field updates on one host.
p=R/'sources/ncu/2026-10-11/reviewed-host-records.json';rs=json.load(open(p));note='；第三十二批原件全讀。中央116名額、方案與實際接收未核；不同年度及學院條件分開，未啟用期限提醒。';rs['ncu-083']['applicability']=rs['ncu-083']['applicability'].replace(note+note,note);p.write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
p=D/'added-host-records.json';added=json.load(open(p));added['ncu-083']=rs['ncu-083'];p.write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
