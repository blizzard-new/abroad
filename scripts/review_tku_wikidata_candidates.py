"""Only explicit institution decisions can promote public representative points."""
import json
from pathlib import Path
from fetch_tku_asset_entities import values

B=Path(__file__).resolve().parents[1]/'src/exchange_info/official_data/tku'
# Individually read TKU name/country/domain and all returned entity roles.
ACCEPT={343:'Q7426174',342:'Q4095278',336:'Q702486',341:'Q16257923',340:'Q268749',339:'Q8070488',338:'Q3268248',334:'Q7894245',327:'Q1035745',326:'Q1143226',321:'Q51077300',313:'Q1789101',311:'Q15143',317:'Q30263747',310:'Q534643',308:'Q1147874',301:'Q1756541',300:'Q7726772',303:'Q5468340',290:'Q3028249',289:'Q2371481',306:'Q5698213',288:'Q10829106',285:'Q573061',283:'Q1138384',281:'Q31249',284:'Q700758',299:'Q3104287',277:'Q6972380',278:'Q1075104',270:'Q1230739',276:'Q492766',266:'Q3298919',261:'Q483032',263:'Q7392844',267:'Q209344',258:'Q1539129',253:'Q10829104',275:'Q1278780',248:'Q782682',252:'Q835366',251:'Q1397589',249:'Q1639978',239:'Q452406',243:'Q4393424',241:'Q1141452',245:'Q4614615',238:'Q476521',236:'Q189441',227:'Q1073666',225:'Q6132246',223:'Q470963',224:'Q19856020',214:'Q1519696',213:'Q349055',218:'Q1232180',221:'Q4587760',212:'Q24590282',209:'Q806480',210:'Q1144682',202:'Q1071862',206:'Q1391752',201:'Q501841',199:'Q581252',197:'Q127745',192:'Q1506552',190:'Q41790'}
DEFER={337:'三個非等同校區座標，需官方命名校區對應；TKU中國大陸標籤與澳門地理所在地另有矛盾。',280:'結果只有Thai Nguyen Agriculture and Forestry，不能代入母體Thai Nguyen University。',268:'里爾多個校区及歷史合併機構，不選第一座標。',240:'加拿大York University有兩個點；排除英國University of York及美國York University。',217:'Amity多個機構／地區校區，泛稱與amity.edu不足以指定Noida。',203:'TKU舊Paris Diderot与Paris Cité合併母體／校區未對應，不替換為巴黎笛卡爾校址。',319:'2026機構合併需核對現官方校區與保留歷史協議，不能自動轉為新大學。',246:'香港地理所在地與TKU原中國大陸標籤需分開核實。',207:'泛校級座標可能為市中心行政址，需官方地址／實體校區佐證。',323:'Wikidata未載官方網址，仍需官方校區地址佐證。',330:'Wikidata未載官方網址，仍需官方校區地址佐證。',242:'Wikidata未載官方網址，仍需官方校區地址佐證。'}
ACCEPT.pop(334)
ACCEPT.update({193:'Q2039033',191:'Q4570168',198:'Q1243904',187:'Q1236345',186:'Q6975161',183:'Q14917503',184:'Q1147063',185:'Q32821',177:'Q4475815',174:'Q985755',176:'Q2496116',171:'Q16947',168:'Q3152650',118:'Q1026868',119:'Q1144750',117:'Q941806',152:'Q23101',108:'Q143451',107:'Q7707466',146:'Q5613747',147:'Q8070947',105:'Q1188786',154:'Q1589630',166:'Q3496652',103:'Q1323040',100:'Q168000',40:'Q1133142',7:'Q612665',99:'Q1256981',68:'Q132478',97:'Q1164229',95:'Q1056123',38:'Q335924',37:'Q5701008',94:'Q1813761',93:'Q2590529',34:'Q6130118',21:'Q1145992',92:'Q5290855',90:'Q624564',141:'Q7487933',140:'Q864879',89:'Q1661325',47:'Q671642',20:'Q54096',9:'Q754656',6:'Q378134',161:'Q1107944',32:'Q6452217',31:'Q910518',62:'Q27621',87:'Q861548',70:'Q84151',10:'Q232141',3:'Q1145497',53:'Q606140',85:'Q1026926',84:'Q3233786',133:'Q835779',130:'Q832550',27:'Q963709',83:'Q1946114',26:'Q1030755',52:'Q18360632',127:'Q6544465',60:'Q702303',65:'Q1094742',82:'Q3443498',81:'Q1026912',63:'Q926068',57:'Q1815710',44:'Q625945',43:'Q6452737',79:'Q1026919',80:'Q1026939',11:'Q1305486',56:'Q1401524',78:'Q625103',77:'Q1937387',24:'Q7310500',74:'Q457281',75:'Q1026941',72:'Q597236',41:'Q491127',23:'Q4402470',22:'Q5116467',217:'Q4746980'})
DEFER.pop(217)
DEFER.update({334:'TKU地址Campo de Tiro與Wikidata中央La Garza座標不一致，需指定實體校區，不以行政舊址替代。',8:'Wikidata49.8094/-97.1328在Winnipeg方向，與官方TKU Brandon地址不同城市；拒絕該點待官方校區來源。',15:'Franche-Comté與Marie and Louis Pasteur新母體及官方域名已不同，先核實現官方校區／保留歷史機構。',49:'New Era College搜尋命中印度／Botswana，照片命中菲律賓New Era University；全部不能作馬來西亞新紀元學院。',86:'三一學院本輪都是Cambridge/Oxford/Dublin，TKU為trincoll.edu Hartford美國；異國近名結果全部拒絕。',175:'澳門大學新橫琴與舊氹仔兩點不能直接選首個，需官方新校區命名與行政地理區別。',167:'雲南大學東陸與呈貢多點，需官方校區對應。'})


# Second manual pass: institution aliases, country, domain and TKU address read.
ACCEPT.update({335:'Q809633',332:'Q10829028',314:'Q10996442',315:'Q1343386',244:'Q849209',264:'Q7452397',279:'Q258464',215:'Q661056',219:'Q1567050',194:'Q183170',123:'Q3551830',59:'Q538452',55:'Q7896059',39:'Q1007777',54:'Q3034637',67:'Q81090',61:'Q1054816',12:'Q1063665',76:'Q1075339',73:'Q659255',69:'Q459506',135:'Q23110',155:'Q4764380'})
DEFER[280]='正確母體Thai Nguyen University Q10841229已查得，但無座標；不得使用農林學院Q10829106的點。'
DEFER[216]='Business Breakthrough University為大學母體；TKU Kenichi Ohmae Graduate School為研究所，尚未核對校區／學制對應。'
DEFER[17]='舊Paris-Sorbonne與2018合併母體、歷史Sorbonne教堂場址需分開；不將歷史點推成當期提名校區。'
DEFER[322]='正確HZ機構Q2518381存在，但沒有座標；不猜補城市中心。'
DEFER[320]='正確IIC母體Q17063745存在但無座標／官方域名主張，需官方地理來源。'
DEFER[307]='正確長安大學母體Q5071561與Yanta分校命中，均無座標；不換用另一分校。'
DEFER[195]='正確ESIEA母體存在但沒有座標，TKU名錄為Laval校址，巴黎照片不能推成Laval座標。'
ACCEPT.update({324:'Q2495922',287:'Q22080602',200:'Q1017656',96:'Q7895785',49:'Q17052678',86:'Q1927705',30:'Q197720',71:'Q1138374'})
ACCEPT[50]='Q5646575'  # Current official hcu.edu.my title and Lim Lean Teng address read.
for n in (49,86):DEFER.pop(n,None)
DEFER[173]='官方TKU標籤巴拿馬但原地址Paso Canoas Costa Rica與巴拿馬機構不符，保留來源矛盾，不推定接待校區座標。'
DEFER[330]='正確SIU母體有點但無官方網址，來源點與原Thao Dien地址／Lewis及Fleming照片場址未對應。'
DEFER[28]='正確Tsuda母體有兩個接近但非完全同值的點；先保留多值，需命名校區來源確認。'


def main():
    searches=json.loads((B/'wikidata_asset_batches.json').read_text())
    captures=json.loads((B/'wikidata_asset_entities.json').read_text())
    entities={q:(e,r) for r in captures for q,e in r.get('response',{}).get('entities',{}).items()}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    rows=[]
    grouped={}
    for s in searches:
        identifier=s['institution_id']
        if identifier not in grouped:grouped[identifier]=dict(s,response={'search':[]},search_evidence=[])
        group=grouped[identifier]
        group['response']['search']+=s.get('response',{}).get('search',[])
        group['search_evidence'].append({k:s.get(k) for k in ('source_url','checked_at','query','http_status','phase')})
    for s in grouped.values():
        number=int(s['institution_id'].rsplit('-',1)[-1]) if s['institution_id'].startswith('tku-sister-') else None
        row=dict(id=s['institution_id'],country=s['country'],query=s['query'],candidate_ids=[h['id'] for h in s.get('response',{}).get('search',[])],
            status='no_candidate' if not s.get('response',{}).get('search') else 'manual_review_pending',search_source_url=s['source_url'],checked_at=s['checked_at'],search_evidence=s['search_evidence'])
        row['candidate_ids']=list(dict.fromkeys(row['candidate_ids']))
        if number in DEFER:row.update(status='deferred_identity_or_campus',reason=DEFER[number])
        if number in ACCEPT:
            q=ACCEPT[number];assert q in row['candidate_ids']
            e,source=entities[q];points=values(e,'P625');assert len(points)==1 and values(e,'P856'),q
            d=census[s['institution_id']];point=points[0]
            quote=json.dumps({'label':e['labels'].get('en',{}).get('value'),'P17':values(e,'P17'),'P856':values(e,'P856'),'P625':point},ensure_ascii=False)
            row.update(status='accepted_representative',selected_entity=q,identity_evidence=dict(source_url=d['directory_url'],checked_at=d['detail_checked_at'],applicable_year='TKU agreement identity, not current exchange nomination',locator='English name / country / official domain / address',quote=' / '.join(str(d.get(k) or '') for k in ('english_name','country','directory_website','directory_address'))),
                rejected_other_candidates=[dict(qid=x,reason='人工核對採上列母體機構，未選擇之系所、醫院、中學、車站、歷史／異國同名實體不得自動轉用。') for x in row['candidate_ids'] if x!=q])
            row['accepted_coordinate']=dict(id=row['id'],verification_status='verified_asset',acquisition_status='new_reviewed_wikidata_reference',
                location=dict(city=None,latitude=point['latitude'],longitude=point['longitude'],geocode_status='verified',geocoded_at=source['checked_at'],
                    source_url='https://www.wikidata.org/wiki/'+q,identity_source_url=d['directory_url'],precision='representative',
                    note='人工核對淡江英文機構／國別／官方域名與Wikidata母體。校級代表點，非精確校園中心、宿舍或淡江本期提名分配校區；多校區院系須另查。'),
                evidence=dict(source_url=source['source_url'],content_sha256=source['sha256'],checked_at=source['checked_at'],applicable_year='public general institution geography checked 2026-10-11; not exchange allocation',role='public_institution_geographic_reference',locator=q+' P625/P17/P856',quote=quote),identity_evidence=[row['identity_evidence']])
        rows.append(row)
    (B/'wikidata_asset_review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(reviewed_acceptances=sum('accepted_coordinate' in r for r in rows),deferred=sum(r['status']=='deferred_identity_or_campus' for r in rows),searches=len(rows))))


if __name__=='__main__':main()
