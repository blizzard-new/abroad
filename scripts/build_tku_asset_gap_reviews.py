"""Record concrete per-institution asset failures, without filling missing values."""
import json
from tku_capture_io import BUNDLE

PHOTO_NOTES = {
    287: '精確名稱命中Nissar Ahmed人物與Venugopalaswamy寺廟銘文；不是Presidency Bangalore校園。',
    253: '命中Color/Open Day活動、Hana Cam Tien人物及可移動隔間產品；沒有已核對的命名校舍外觀。',
    275: 'campus檢索無結果，Lismore候選為1944 RAAF飛機／軍人，不是Southern Cross大學。',
    206: '命中HUBrussel/Hogeschool-Universiteit Brussel照片及其他文獻／活動，非Université Saint-Louis Bruxelles。',
    166: '候選為現代經濟管理學院北門及校徽；前者與TKU名錄江西財經大學主體／地址對應未核實，後者不是校景。',
    44: '命中Miss Korea、演員照片與歌手廣播等人物題材，韓文精確校名未命中校園照片。',
    212: 'Campus-vtu已實見為人物宣傳畫面而拒收；Vtmt1僅稱VTMT campus Avadi，未核實與DR.RR/DR.SR大學主體對應。',
}
COORDINATE_NOTES = {
    328: 'ACAOM英名及精確百科名稱查無可核對實體點；官方acaom.edu HTTP200擷取無命名地圖連結或座標片段，仍需實體校舍數值來源。',
    312: 'Instituto Desarrollo/Paraguay/Asunción查無可核對實體點；官方首頁及contacto HTTP200擷取均無命名地圖或座標片段，不以Asunción市中心補值。',
    316: 'Van Lang Saigon College英名／別名查無可核對實體點；官方英文站連線由proxy回403而失敗，不能改用Van Lang University母體座標。',
    169: 'Q101579967大阪公立大學主體沒有P625；另兩命中分別為附屬醫院Q11440418與高專Q11441055，不能作校級代表點。舊osakafu-u官方端點兩次503歷史保留。',
    51: 'IHM College及Malaysia別名／精確百科名稱未命中；官方ihmc.edu.my HTTP200擷取無命名地圖或座標片段，不用同名他國飯店管理學院的點。',
    242: '官方當前地址為VSQ@PJ City Centre；Q16253618唯一點3.1182,101.635精度0.009度且无P856，沒有與現行校舍對應的細點，不以粗點當命名校園。',
}


def main():
    audit=json.loads((BUNDLE/'full_census_audit.json').read_text())
    photos={r['id'] for r in json.loads((BUNDLE/'campus_asset_manifest.json').read_text())}
    locations={r['id'] for r in json.loads((BUNDLE/'campus_location_manifest.json').read_text())}
    searches=json.loads((BUNDLE/'commons_asset_batches.json').read_text())
    official=json.loads((BUNDLE/'official_geography_checks.json').read_text())
    visual=json.loads((BUNDLE/'new_photo_visual_review_history.json').read_text())
    holds={r['id']:r for r in json.loads((BUNDLE/'photo_date_holds.json').read_text())}
    entity_sources={}
    for s in json.loads((BUNDLE/'wikidata_asset_entities.json').read_text()):
        for q,e in s.get('response',{}).get('entities',{}).items():
            if q not in {'Q101579967','Q11440418','Q11441055','Q16253618'} or q in entity_sources:continue
            claims={k:[v['mainsnak'].get('datavalue',{}).get('value') for v in e.get('claims',{}).get(k,[])] for k in ['P625','P856','P17']}
            entity_sources[q]=dict(source_url=s['source_url'],checked_at=s['checked_at'],content_sha256=s['sha256'],locator=f'Wikidata entity {q} labels.en and P625/P856/P17 claims',quote=json.dumps(dict(label=e.get('labels',{}).get('en'),claims=claims),ensure_ascii=False),applicable_year='Current stored entity claims retrieved2026-10-11; not TKU allocation evidence')
    rows=[]
    for d in audit['schools']:
        identifier=d['id']
        if identifier in photos and identifier in locations:continue
        n=int(identifier.rsplit('-',1)[-1]) if identifier.startswith('tku-sister-') else None
        r=dict(id=identifier,school_name=d['school_name'],checked_date='2026-10-11',applicable_year='Asset discovery/history only; TKU current nomination campus unverified')
        if identifier not in photos:
            checks=[s for s in searches if s['institution_id']==identifier][-2:]
            evidence=[]
            for s in checks:
                pages=list(s.get('response',{}).get('query',{}).get('pages',{}).values())
                evidence.append(dict(source_url=s['source_url'],checked_at=s['checked_at'],content_sha256=s.get('sha256'),locator='Retained Commons API query.pages; exact file titles',query=s.get('query'),http_status=s.get('http_status'),error=s.get('error'),candidate_count=len(pages),quote=json.dumps([p['title'] for p in pages],ensure_ascii=False)))
            rejected=[v['reason'] for v in visual.get(identifier,[]) if v.get('result') in {'reject','rejected'} and v.get('reason')]
            if identifier in holds:
                reason=('Hiu-01拍攝欄只有2008原始上傳日、無相機拍攝日期。' if n==37 else 'ULAT PA-2拍攝欄與EXIF拍攝時間皆空白。')+'年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。'
                evidence+=holds[identifier]['evidence']
            elif n in PHOTO_NOTES:reason=PHOTO_NOTES[n]
            elif rejected:reason='；'.join(dict.fromkeys(rejected))
            else:
                reason='；'.join(f"{e['query']}：HTTP{e['http_status']}、{e['candidate_count']}檔" for e in evidence)+'。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。'
            r.update(photo_reason=reason,photo_evidence=evidence,visual_rejections=[v for v in visual.get(identifier,[]) if v.get('result') in {'reject','rejected'}])
        if identifier not in locations:
            cell=d['fields']['coordinates'];candidate=cell.get('candidate_review') or {};alternative=cell.get('alternative_candidate_review') or {}
            reason=COORDINATE_NOTES.get(n) or alternative.get('reason') or candidate.get('reason')
            checks=[s for s in official if s['institution_id']==identifier]
            if reason is None:
                reason='上海交大官方國際處contact頁已實讀，但本輪沒有可核對的命名校區數值點；不能以上海市中心或另一分校替代。' if identifier.startswith('tku-programme-') else '逐校來源尚無可核對命名實體點；候選及實際端點結果如下。'
            r.update(coordinate_reason=reason,coordinate_candidate_review=candidate,coordinate_alternative_review=alternative,official_coordinate_checks=[{k:s.get(k) for k in ('source_url','checked_at','http_status','error','sha256','capture_file','map_links','coordinate_snippets')} for s in checks],entity_evidence=[entity_sources[q] for q in (['Q101579967','Q11440418','Q11441055'] if n==169 else ['Q16253618'] if n==242 else [])])
        rows.append(r)
    (BUNDLE/'milestone3_asset_gap_reviews.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(gap_institutions=len(rows),photo_gaps=sum('photo_reason' in r for r in rows),coordinate_gaps=sum('coordinate_reason' in r for r in rows))))


if __name__=='__main__':main()
