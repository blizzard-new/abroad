"""Apply explicit, individually reviewed reuse decisions; never fuzzy promotion."""
from pathlib import Path
from urllib.parse import urlsplit
import hashlib,json,re,unicodedata
from tku_baseline_assets import BASE

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'
# These IDs were individually read against their TKU English name, official
# domain/country, source identity, photograph and campus description.
PHOTO_IDS={329,325,318,309,286,282,273,269,265,262,237,208,205,181,178,172,164,163,126,125,112,159,157,160,150,106,148,145,104,111,14,46,36,35,144,13,33,143,142,139,58,158,138,137,136,16,1,19,29,134,132,2,64,18}
LOCATION_IDS={329,325,333,318,309,286,282,273,272,269,265,262,260,232,237,228,208,205,211,181,178,172,164,163,126,125,151,112,159,157,160,150,110,106,148,145,104,4,111,46,98,36,35,144,13,33,143,142,139,58,158,138,137,136,88,45,16,1,19,29,134,132,2,64,42,18}
DISTINCT_CAMPUSES={163:'照片為Sungai Long，既有代表點為Kampar；兩校區不視為同一位置。',18:'照片為Grosshadern，代表點為慕尼黑主建築；不聲稱是同一校區。',125:'照片為榆中校區，淡江目錄地址為蘭州校址；歷史校景與代表點分開。',35:'照片為片淵校區桂林會館，淡江目錄地址為文教校區；不是同一校區。',137:'照片為江灣校區入口，代表點／目錄地址不推定同一校區。',145:'照片為之江舊址校區，不推定為本期交換校區或目錄主校址。',148:'照片為千佛山校區，目錄校址與代表點另外保存。'}


def build(candidates):
    reviewed=[]
    audit={r['id']:r for r in json.loads((B/'full_census_audit.json').read_text())['schools']}
    programmes=[json.loads(l) for l in (B/'partners_reference.jsonl').read_text().splitlines()]
    for row in candidates:
        identifier=row['id'];number=int(identifier.rsplit('-',1)[1]) if identifier.startswith('tku-sister-') else None
        photo_ok=number in PHOTO_IDS or identifier.startswith('tku-programme-mainland-macau-kinmen-115-')
        location_ok=number in LOCATION_IDS
        directory=row['directory'];country=directory['country'] if directory else audit[identifier]['country']
        identity_evidence=[dict(source_url=directory['directory_url'],checked_at=directory['detail_checked_at'],applicable_year='sister agreement institution identity, not current nomination',locator='TKU sister detail English name/country/official website/address',quote=' / '.join(str(directory.get(k) or '') for k in ['english_name','country','directory_website','directory_address']))] if directory else [dict(source_url='https://www.oieie.tku.edu.tw/',checked_at='2026-10-08',applicable_year='115 programme reference only',locator='Retained TKU programme institution row',quote=row['school_name'])]
        if not directory:
            original=next(r for r in programmes if r['fields']['school_name']['value']==row['school_name'])
            identity_evidence=[dict(e,quote=row['school_name']) for e in original['fields']['school_name']['evidence']]
        identity_evidence += [dict(source_url=r['discovery_source_url'],checked_at=r['checked_at'],applicable_year='institution identity only; home rules not reused',locator=f"Fixed-base {r['home']}/partner_research.jsonl: {r['school_name']}",quote=' / '.join(str(r.get(k) or '') for k in ['research_name','country','official_website'])) for r in row['other_home_identity_candidates']]
        out=dict(id=identifier,school_name=row['school_name'],country=country,checked_at='2026-10-11',baseline_commit=BASE,
            identity_evidence=identity_evidence,photo_candidates=row['photos'],coordinate_candidates=row['locations'],
            photo_decision='accepted' if photo_ok and row['photos'] else 'no_licensed_baseline_candidate',
            coordinate_decision='accepted' if location_ok and row['locations'] else 'no_verified_baseline_candidate',
            campus_pair_scope=DISTINCT_CAMPUSES.get(number,'照片與校級代表點分別保留來源及精度；沒有推定本期提名校區或兩者為同一位置。'))
        if number==7:
            out.update(photo_decision='rejected_wrong_institution',coordinate_decision='rejected_wrong_institution',rejection_reason='淡江為Vrije Universiteit Brussel（VUB, vub.ac.be, Pleinlaan2），既有素材為Université libre de Bruxelles（ULB, ulb.be, Q574606）。同中文譯名及同國不足以配對。',rejection_sources=['https://www.vub.be/en','https://www.wikidata.org/wiki/Q574606'])
        if number==260:
            out.update(photo_decision='rejected_not_campus_scene',rejection_reason='已實看：只有研究所室內木牌，不是使用者要求的真實校園景觀。')
        if out['photo_decision']=='accepted':
            source=row['photos'][0];path=ROOT/'src/exchange_info'/source['local_path'].split('?')[0].removeprefix('/');digest=hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest==source['content_hash'] and source['artist'] and source['license_url']
            caption=source.get('description') or '校園照片來源未提供更精確圖說；不推定本期指定交換校區。'
            if number==1:caption='維也納大學Universitätsring主建築外觀與前方Liebenberg紀念碑（2015-04-12）。'
            photo=dict(id=identifier,school_name=row['school_name'],country=country,source_url=source['official_page_url'],image_source_url=source['image_source_url'],
                author=source['artist'],license=source['license_name'],license_url=source['license_url'],license_capture_url=source['official_page_url']+'#Licensing',
                caption=caption,photo_date='2015-04-12' if number==1 else '拍攝日期未由既有素材欄位提供；不得以查核日代替拍攝日',
                identity_quote=caption,identity_source_url=identity_evidence[0]['source_url'],checked_at=source['checked_at'],
                applicable_year='historical campus photograph; current TKU nomination campus not established',transformations='Existing repository derivative cropped to16:9; no further modification',
                review_status='verified_asset',local_path=source['local_path'],sha256=digest,bytes=path.stat().st_size,width=source['width'],height=source['height'],
                acquisition_status='reused_baseline_asset',baseline_commit=BASE,identity_evidence=identity_evidence,campus_pair_scope=out['campus_pair_scope'],campus_pair_mismatch=number in DISTINCT_CAMPUSES,
                visual_review=dict(sha256=digest,checked_at='2026-10-11',result='pass',method='Actual existing image inspected in numbered contact-sheet batch; TKU English name/domain/country and baseline Commons identity/license checked individually.',note=caption))
            photo['license_url_original']=photo['license_url']
            if photo['license_url'].startswith('http://creativecommons.org/'):
                photo['license_url']=photo['license_url'].replace('http://','https://',1)
            out['accepted_photo']=photo
        if out['coordinate_decision']=='accepted':
            pairs={(x['latitude'],x['longitude']) for x in row['locations']};assert len(pairs)==1,identifier
            source=max(row['locations'],key=lambda x:x['geocoded_at'])
            out['accepted_coordinate']=dict(id=identifier,verification_status='verified_asset',acquisition_status='reused_baseline_asset',baseline_commit=BASE,identity_evidence=identity_evidence,
                location={k:v for k,v in source.items() if k not in {'school_name','country'}},
                evidence=dict(source_url=source['source_url'],identity_source_url=source['identity_source_url'],checked_at=source['geocoded_at'],applicable_year='retained representative institution point; current nomination campus not established',role='retained_baseline_representative_location',locator=f"Fixed-base university_locations.jsonl: {source['school_name']} / {source['country']}",quote=source['note']),campus_pair_scope=out['campus_pair_scope'])
            if number in DISTINCT_CAMPUSES:out['accepted_coordinate']['location']['note']+=' '+DISTINCT_CAMPUSES[number]
        reviewed.append(out)
    assert len(reviewed)==287
    (B/'reused_asset_review.json').write_text(json.dumps(reviewed,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(institutions=287,accepted_photo_candidates=sum('accepted_photo' in r for r in reviewed),accepted_coordinate_candidates=sum('accepted_coordinate' in r for r in reviewed),explicit_rejections=sum(r.get('rejection_reason') is not None for r in reviewed))))


def discover():
    source=ROOT/'src/exchange_info'
    directories={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    photos=json.loads((source/'static/assets/school-images.json').read_text())['schools']
    locations=list(map(json.loads,(source/'official_data/university_locations.jsonl').read_text().splitlines()))
    labels={'大陸地區':'中國','中國大陸':'中國','澳大利亞':'澳洲','南韓':'韓國','台灣':'臺灣'}
    country=lambda s:labels.get(s,s)
    name=lambda s:re.sub(r'[\s\-_,.()（）;；:：\[\]＊*]','',unicodedata.normalize('NFKC',s or '')).casefold()
    domain=lambda s:(urlsplit(s or '').hostname or '').removeprefix('www.')
    known=[]
    for home in ['ntu','ntpu','ncu']:
        for line in (source/'official_data'/home/'partner_research.jsonl').read_text().splitlines():
            row=json.loads(line);row['home']=home;known.append(row)
    candidates=[]
    for row in json.loads((B/'full_census_audit.json').read_text())['schools']:
        directory=directories.get(row['id']);names={name(row['school_name'])}
        if directory:names|={name(directory['school_name']),name(directory['english_name'])}
        other=[x for x in known if country(x.get('country'))==country(row['country']) and (name(x['school_name']) in names or name(x.get('research_name')) in names or directory and domain(x.get('official_website')) and domain(x.get('official_website'))==domain(directory['directory_website']))]
        names|={name(x['school_name']) for x in other}
        matching=lambda r:name(r['school_name']) in names and country(r.get('country'))==country(row['country'])
        candidates.append(dict(id=row['id'],school_name=row['school_name'],directory=directory,other_home_identity_candidates=other,
            photos=[r for r in photos if matching(r) and r.get('artist') and r.get('license_url') and r['status']=='verified'],
            locations=[r for r in locations if matching(r) and r['geocode_status']=='verified']))
    (B/'reused_asset_candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')
    return candidates


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('candidate_file',type=Path,nargs='?');args=p.parse_args()
    build(json.loads(args.candidate_file.read_text()) if args.candidate_file else discover())
