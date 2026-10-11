"""Disable two exact pictures from a fixed integration report; preserve originals."""
import gzip,hashlib,json,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from tku_capture_io import BUNDLE as B,read_bytes
from tku_photo_identity_policy import apply_photo_identity_policy

BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
BLOCKER='8b7570acca35fc10154e52e8621b9829bc9a815b'
ROOT=Path(__file__).resolve().parents[1]
def main():
 old=json.loads(subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/campus_asset_manifest.json'],cwd=ROOT))
 selected={r['id']:r for r in old if r['id'] in {'tku-sister-65','tku-sister-52'}}
 cs=json.loads((B/'fixed_photo_blocker_source_checks.json').read_text());assert len(cs)==4
 def E(c,needle,locator):
  assert needle in c['text']
  return dict(source_url=c['source_url'],content_sha256=c['sha256'],checked_at=c['checked_at'],capture_file=c['capture_file'],locator=locator,quote=needle,applicable_year='Original campus photograph/attribution only; not current exchange availability')
 ev65=[E(cs[0],'Block B, University of the West of England','Commons Summary/Caption/Author: different institution'),dict(source_url=selected['tku-sister-65']['identity_source_url'],checked_at=selected['tku-sister-65']['checked_at'],locator='TKU official institution entry retained at fixed M5 SHA',quote=selected['tku-sister-65']['identity_address'],applicable_year='TKU named institution identity, not photograph allocation')]
 ev52=[E(cs[1],'Author Unknown author Unknown author','Commons Information Author and CC BY4.0 Licensing'),E(cs[2],'Log into Facebook','Actual original-source response redirects to login; no login attempted'),E(cs[3],'Uploaded a work by {{Unknown|author}}','Commons original2024-04-13 upload history; uploader not established as author/licensor')]
 specs=[('tku-sister-65','rejected_wrong_institution','原圖正文與來源category明示University of the West of England／Frenchay；淡江條目為University of Sunderland，屬不同機構，已停止展示錯圖，非同校多校區差異。需原件可核的Sunderland具名校景及授權、作者、拍攝期。',ev65),('tku-sister-52','pending_attribution_licensor_chain','UAEMEX FCPyS A棟身分可辨，但Commons作者Unknown author重複、2024上傳歷史稱unknown作者且來源Facebook實回登入頁；未取得支持作者／授權人credit的獨立原件聲明，停止展示，不判侵權、不把uploader當作者。需公開原件／授權與署名說明或可核替代圖。',ev52)]
 rows=[]
 for identifier,status,reason,ev in specs:
  photo=selected[identifier];path=ROOT/'src/exchange_info'/photo['local_path'].removeprefix('/');assert hashlib.sha256(path.read_bytes()).hexdigest()==photo['sha256']
  rows.append(dict(id=identifier,school_name=photo['school_name'],status=status,reason=reason,withdrawn_photo_sha256=photo['sha256'],withdrawn_local_path=photo['local_path'],prior_photo=photo,evidence=ev,display_accepted=False,original_file_retained=True,visual_review='Actual two local images opened2026-10-11; visual campus appearance cannot establish a different institution or licensor',withdrawal_overrides_old_visual_pass=True))
 result=dict(input_commit=BASE,blocker_document_commit=BLOCKER,blocker_document_url='https://github.com/blizzard-new/abroad/blob/'+BLOCKER+'/docs/source-recovery-20261011/TKU-PHOTO-BLOCKERS.md',checked_date='2026-10-11',prior_photos=264,current_photos=262,coordinates_unchanged=264,schools=rows)
 (B/'fixed_photo_blocker_holds.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 current=json.loads((B/'campus_asset_manifest.json').read_text());accepted=apply_photo_identity_policy(current)
 assert len(accepted)==262 and {r['id'] for r in old}-{r['id'] for r in accepted}==set(selected)
 assert all(r==next(p for p in old if p['id']==r['id']) for r in accepted)
 (B/'campus_asset_manifest.json').write_text(json.dumps(accepted,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(input_commit=BASE,blocker_document_commit=BLOCKER,withdrawn=2,retained_unchanged=262,coordinates_unchanged=264),ensure_ascii=False))
if __name__=='__main__':main()
