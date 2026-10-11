"""Publish exact final checks and finite per-school requests; never sends messages."""
import argparse,gzip,hashlib,json,shutil,subprocess
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from tku_capture_io import BUNDLE as B

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs';OUT=DOC/'tku-census-evidence-20261011'
BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
MAIN='59a20f27fcee00fb597abc79e75ec11778317422'
def read(name):return json.loads((B/(name+'.json')).read_text())
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def tests(path):
 root=ET.parse(path).getroot();ss=[root] if root.tag=='testsuite' else list(root.iter('testsuite'))
 result={k:sum(int(s.get(k,0)) for s in ss) for k in ['tests','failures','errors','skipped']};result['passed']=result['tests']-result['failures']-result['errors']-result['skipped'];result['seconds']=round(sum(float(s.get('time',0)) for s in ss),3)
 return result
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);args=ap.parse_args()
 scoped=tests('/tmp/tku-milestone6-validation.xml');browser=tests('/tmp/tku-milestone6-browser-final.xml')
 assert scoped['passed']==220 and scoped['skipped']==4 and scoped['failures']==scoped['errors']==0
 assert browser['passed']==4 and browser['failures']==browser['errors']==0
 outcomes=read('milestone6_remaining_source_outcomes');full=read('milestone6_full_gap_outcomes');assets=read('milestone6_asset_outcomes');facts=read('curated_partner_facts');a=read('full_census_acceptance');cont=read('continuation_gap_closure');pack=json.loads(Path('/tmp/tku-milestone6-pack-only-final.json').read_text())
 assert pack['files']==4529 and pack['new_files']==74 and pack['status']=='passed'
 # Preservation is measured against named immutable inputs, not reported from memory.
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','src/exchange_info/official_data/tku'],cwd=ROOT,text=True).splitlines();snapshots=[p for p in paths if any('/milestone'+str(n)+'_' in p for n in [3,4,5])]
 for p in snapshots:assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
 oldfacts=json.loads(subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/curated_partner_facts.json'],cwd=ROOT));now={r['id']:r for r in facts};assert len(oldfacts)==40 and all(now[r['id']]==r for r in oldfacts)
 coords=B/'campus_location_manifest.json';assert coords.read_bytes()==subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/campus_location_manifest.json'],cwd=ROOT)
 prior=json.loads(subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/campus_asset_manifest.json'],cwd=ROOT));photos=read('campus_asset_manifest');assert len(photos)==262 and all(r==next(p for p in prior if p['id']==r['id']) for r in photos)
 preserved=dict(base=MAIN,m5=BASE,snapshot_files=len(snapshots),snapshots_byte_identical=True,prior_curated_institutions=40,prior_curated_fields=285,prior_curated_rows_exact=True,remaining262_photo_rows_exact=True,photo_withdrawals=['tku-sister-65','tku-sister-52'],coordinates_sha256=hashlib.sha256(coords.read_bytes()).hexdigest(),coordinates_byte_identical=True,original_programmes=128,current_profiles_prefix=4,original_profile_prefix_status=a['original_tku_destination_prefix'],other_home_bundles=a['other_home_bundles'],external36_rows_exact=True,shared_core_changes_this_milestone=[])
 OUT.mkdir(exist_ok=True);evidence=[]
 def save(p,name=None,gz=False):
  raw=p.read_bytes();target=OUT/(name or p.name);target=target.with_name(target.name+'.gz') if gz else target
  target.write_bytes(gzip.compress(raw,mtime=0) if gz else raw)
  entry=dict(file=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
  if gz:entry.update(original_bytes=len(raw),original_sha256=hashlib.sha256(raw).hexdigest())
  evidence.append(entry)
 for p in sorted(Path('/tmp').glob('tku-milestone6-*.log')):save(p,gz=True)
 for p in sorted(Path('/tmp').glob('tku-milestone6-*.xml')):save(p,gz=True)
 for p in sorted(Path('/tmp').glob('tku-milestone6-pack-only*.json')):save(p)
 for p in sorted(Path('/tmp').glob('tku-milestone6-map-*.png')):save(p,name=p.name.replace('tku-','',1))
 for folder,prefix in [('/tmp/tku-milestone6-ui-evidence','milestone6-'),('/tmp/tku-fixed-photo-ui-evidence','milestone6-fixed-photo-')]:
  for p in sorted(Path(folder).iterdir()):save(p,name=prefix+p.name)
 write(OUT/'milestone6-preservation-proof.json',preserved);save(OUT/'milestone6-preservation-proof.json')
 # Four domain-filtered web searches produced no usable source; actual captures,
 # not search snippets or absence of hits, support fields and stop decisions.
 search_note=dict(queries=4,result='No returned snippet adopted as applicable semester evidence; unrelated search results excluded',absence_is_not_proof_of_no_public_source=True,actual_trace='milestone6_official_link_inventory.json + all captured official-link inputs/checks')
 write(OUT/'milestone6-search-limit-note.json',search_note);save(OUT/'milestone6-search-limit-note.json')
 result=dict(branch='data/tku-completeness-20261011',main_baseline=MAIN,m5_input=BASE,photo_fix_commit='35e28149c926705ea620692baefcddce89bab3d4',data_checkpoint=args.checkpoint,checked_date='2026-10-11',pr='https://github.com/blizzard-new/abroad/pull/13',original98=full['statuses'],remaining42_initial=outcomes['initial_classifications'],remaining42_final=outcomes['final_classifications'],never_attempted_official_roots=0,same_body_alias_attempts=outcomes['same_body_alias_attempts'],new_manual_institutions=7,new_manual_fields=61,manual_institutions=len(facts),manual_fields=sum(len(r['fields']) for r in facts),official_reference_institutions=a['institutions_with_official_reference_excerpts'],official_reference_percent=round(a['institutions_with_official_reference_excerpts']/287*100,2),literal_excerpt_index=2350,semantic_host_year_review=cont['semantic_host_year_review'],directory_rows=286,institutions=287,programme_rows=153,profiles=287,latest_home_schools=4,latest_home_quota=7,new_home_applications=0,other_quota_statuses=dict(not_verified_new=149,reference_only=134),photos=262,photo_percent=round(262/287*100,2),coordinates=264,coordinate_percent=round(264/287*100,2),photo_gaps=25,coordinate_gaps=23,asset_gap_union=41,original_asset_gap_scope=39,new_asset_lead_institutions=8,new_display_assets=0,host_attempt_records=outcomes['attempt_records'],host_unique_urls=outcomes['unique_request_urls'],fixed_photo_source_attempts=4,public_captures=a['public_source_captures'],opened_sources=a['opened_sources'],failed_sources=a['failed_sources'],source_failure_statuses=a['source_failure_statuses'],new_attachment_statuses=dict(Counter(r['status'] for r in read('milestone6_attachment_reviews'))),source_conflicts=10,new_source_conflicts=5,tests=dict(scoped=scoped,browser=browser,openapi='exit0 current contract',javascript='node --check actual app.js / tku-campus-assets.js exit0'),pack_only=pack,preservation=preserved,initial_failures=dict(focused='4passed/3failed: test expected different PDF year wording, wrong nested excerpt shape, and a host eligibility field absent forNQU; tests corrected against real body/schema',full='217passed/3failed/4skipped same assertions; original log/XML retained',before_final_documents='220passed/4skipped86.85s, before last3 explicit document checks',before_audit_rebuild='6passed/1failed: added CoE manual fact ran against stale generated audit; rebuilt in dependency order; final suite includes exact API-value checks',fixed_photo_browser='initial2failed because guide detail was collapsed; explicit expand fixes retained originals',final_document_cli='initialexit2: --output unsupported; corrected --inputs/--checks; original argparse output retained',map_renderer='fitz ModuleNotFoundError and absent PNG view: corrected using installed pdftoppm; four actual rendered pages viewed; no dependency installed'),remaining_requests_file='milestone6_remaining_source_outcomes.json',remaining_asset_reasons_file='milestone6_asset_outcomes.json',global_source_exhaustion_proven=False)
 write(DOC/'tku-continuation-milestone6-20261011.json',result)
 intro=f'''第六批完成原98校範圍內的有限來源收斂，並優先撤下兩張整合阻擋照片。分支 `data/tku-completeness-20261011`，main基準 `{MAIN}`，第五批固定輸入 `{BASE}`，資料checkpoint `{args.checkpoint}`。同Draft PR13，沒有merge／deploy。

原42校官方根入口均已嘗試；SHA比對排除3個同正文HTTP／index別名的「新增來源」說法。初始分類為9校尚有未讀相關official leaf、12校指定入口失敗、21校已讀但無適用正文；本輪後7校接入61欄參考、12校入口失敗、23校已讀仍無適用內容。原98校累計27接入／36外部限制／35需來源，71校仍無可接入參考。原36限制逐項完全保留，沒有重試。

累計286官方名錄列／287機構及profiles、153計畫（原128＋25已截止日語第一梯歷史）；人工47校346欄、216/287校有官方參考（75.26%）、另2350段literal index不變。18校160欄可確認來源年期，含歷史資料；不等於淡江當期適用。最新2027–2028日語第二梯4校7名額已於2026/9/30中午Asia/Taipei截止，0新開放母校申請；其他283校名額149尚未核實新版／134協議或歷史參考。英歐語／中文組新版尚未核實，不稱官方尚未公告。

新增接待內容全部reference_only，帶官方URL、PDF頁或XLSXsheet/cell／原文、年期、查核時間與SHA。青山URL寫2007Spring但14頁正文實載2027春；新舊iBT量尺、科系／校區／研究所限制、兩階段申請與提名期限分開。兩份CoE各8表，實際2027/3及Office Use2027/4/1與校區地址核實；3/20或空日是預填值，不是保證行事曆。signature／health未載年度，不升成全部2027模板。

UADE一般學期／短期／dual-degree／freemover分開，兩份未載年指南實載5/15、11/15學生截止與4/30、10/31提名，不能補2027。UNA雙邊與無協議費用分開，西語能力與最多30ECTS保留；英語承諾DOCX一次ReadTimeout。NQU國際incoming與淡江臺灣國內交换未對應，網頁2張／兩表3張照片矛盾；表單母校博士勾選不等於接收博士。HQU正文2025港澳台簡章為歷史；指定下載目錄只列2019–2023簽證／承諾等，未取得2026/27更新，不證明官方尚未公告。PKU校級／院系級HMT報到及母校提名分開，common links的淡江不當名額。Aizu2027春In preparation與已過2026/9/17截止矛盾保留；Packet／Checklist明示母校Office取密碼，未請求／登入／解密。公開兩SAS表HTTP200實為含EncryptionInfo／EncryptedPackage的加密OLE，只有opaque bytes與格式已核對，不稱可讀模板。

新增5項pending官方確認：NQU照片張數、AGU英語替代證明條件、AGU成績單時間、AGUhealth模板與2027要求、Aizu2027春狀態／已過日期。加既有5項共10，兩方原件／頁碼保留，不修猜日期或默選。

照片阻擋固定文件SHA `8b7570acca35fc10154e52e8621b9829bc9a815b`；緊急修正 `{result['photo_fix_commit']}` 已先推送，逐項證據見 [照片修正報告](tku-photo-blockers-resolved-20261011.md)。Sunderland誤配UWE圖片撤下；UAEMEX正確校景但Unknown作者、Facebook原件登入門與unknown上傳歷史未支持獨立署名／授權人鏈，也撤下，不判侵權。262其餘照片與固定輸入逐筆完全相同，座標264逐byte不變。現262照片（91.29%）／264座標（91.99%），25／23缺，41校聯集（原39＋2撤下），不維持虛假264計數。

原39資產缺口中有明確新線索的8校已限查；UM2頁map封面Produced Aug2026與未完工新campus分開；UMA2頁地圖未由2025檔名定年；HZ两校区学科對應、IACT現地址、長安多校區、OSM特定研究建物及ESIEA經度矛盾不代配。Paris Grands Moulins真marker48.8292405,2.3817211與viewport分清，但Diderot協議承繼／指定campus未驗，僅候選。0新展示資產；不宣稱全球安全来源耗盡。

本輪56host capture records／54URL（兩Aizu格式複核重用同網址另ID），另4份照片原頁／原來源／歷史查核。10PDF（8文字＋2視讀map）、2CoE XLSX可開；2加密OLE不可讀內容、1DOCXtimeout另列。HTTP200本身不等於有適用內容。累計2700captures／2303opened／397failed含重試與歷史，不當2700當期規則。

最終相關TKU／CGU／NTPU／共用回歸：{scoped['passed']} passed、{scoped['skipped']} skipped、0failed/errors，{scoped['seconds']}秒；4skip為既有CGU條件。實際390/1280 browser {browser['passed']} passed、0failed/errors，{browser['seconds']}秒，真實展開學校卡片、來源及生活指南，最新年／track、unknown quota與兩撤下圖片／credit核對。不是全repository／另一session NTU全綠宣稱。OpenAPI --check與真實兩JS node --check exit0。

Pack-only只用manifest與transport parts還原{pack['files']}檔／{pack['archives']}封存／{pack['parts']}分片、{pack['restored_bytes']:,} bytes，逐檔SHA通過；舊4455檔／15archives／36parts原樣，新增74members（56hostJSON＋10PDF＋2XLSX＋2OLE＋4photo captures）。M3/M4/M5的{len(snapshots)}快照、既有40校285人工欄、原128programmes／4profiles前綴及其他CGU3／NTPU12／NTU17／CCU1215／NCU13官方檔不變。

初始錯誤及中間驗證保留：Focused4pass/3fail與full217pass/3fail/4skip是3個測試字串／shape／NQU缺欄假設，按實際原文／schema修正；新增CoE後Focused6pass/1fail因生成audit未重建，依序重建後最終完整套件核對全部實際API值。前一完整220pass/4skip86.85秒是最後3文件前，不能代替上列最終測試。照片browser未展開指南、最後文件抓取用不存在--output exit2、fitz未安裝／PNG未生成功能錯誤均保留或如實記載，改用真實--checks与已裝pdftoppm，沒有宣稱初次成功或安裝依賴。

第六批與照片fix只動TKU資料／抓取與生成器／測試／證據，無新增共享registry/API/UI/资格/母校文件catalog更動。整份PR較main既有shared api.py、school_content.py、app.js、index.html、regions.js等由主session統一整合；未動他校工作區、憑證、存取、付款或安全設定。

重現：以已凍結 `milestone6_*_inputs/checks` 及pack為來源，依序執行remaining_document_reviews、milestone6_reviews、milestone6_handoff、curated_references、public_references、census_audit、census_profiles、audit_tku_full_census、continuation_milestone及測試。intake builders用於請求前凍結，不能事後用新的index重造原「未嘗試」清單。爬取driver僅固定inputs，保留失敗與cooldown；不用網路即可重建交付資料。

下表逐校列最低所需校方內容；沒有送出訊息。所有逐URL狀態、原文／錯誤、日期、SHA在 [42校機讀證據](../src/exchange_info/official_data/tku/milestone6_remaining_source_outcomes.json)；完整98校、39資產及10項矛盾在相鄰milestone6／milestone5 JSON。尚未核實不等於官方未公告。

| ID／學校 | 初始／本輪分類 | 本輪attempts／接入欄 | 最少需校方提供 |
|---|---|---|---|
'''
 labels={'relevant_official_leaf_not_attempted':'未讀相關路徑','targeted_entry_attempt_failed':'指定入口失敗','read_but_no_applicable_content':'已讀無適用正文','connected_reference':'接入參考'}
 table=''.join('| '+r['id']+' '+r['school_name']+' | '+labels[r['initial_classification']]+'／'+labels[r['final_classification']]+' | '+str(r['new_attempt_records'])+'／'+str(len(r['reference_fields']))+' | '+r['minimum_school_provided_content'].replace('|','／')+' |\n' for r in outcomes['schools'])
 tail='\n原39資產缺口逐校停止原因（另兩照片withdrawal不混入原39分母）：\n\n| ID／學校 | 已查新線索或既有原因 |\n|---|---|\n'
 tail+=''.join('| '+r['id']+' '+r['school_name']+' | '+(r['milestone6_safe_path_review'] or '；'.join(v for v in [r.get('photo_reason'),r.get('coordinate_reason')] if v)).replace('|','／')+' |\n' for r in assets['schools'])
 tail+='\n本輪到此停止新增候選。35校仍需適用来源、36校外部限制、10來源矛盾與41資產缺口保留精確原因／最低所需資訊；有新官方正文或校方澄清才繼續。\n'
 (DOC/'tku-continuation-milestone6-20261011.md').write_text(intro+table+tail)
 write(OUT/'milestone6-evidence-manifest.json',dict(data_checkpoint=args.checkpoint,tests=result['tests'],entries=len(evidence),files=evidence))
 for e in evidence:
  blob=(OUT/e['file']).read_bytes();assert len(blob)==e['bytes'] and hashlib.sha256(blob).hexdigest()==e['sha256']
  if 'original_sha256' in e:assert hashlib.sha256(gzip.decompress(blob)).hexdigest()==e['original_sha256']
 print(json.dumps(dict(evidence_files=len(evidence),scoped=scoped,browser=browser,snapshot_files=len(snapshots),checkpoint=args.checkpoint),ensure_ascii=False))
if __name__=='__main__':main()
