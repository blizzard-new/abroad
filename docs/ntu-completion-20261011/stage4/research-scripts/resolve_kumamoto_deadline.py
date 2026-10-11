from research_curator import Curator
import hashlib
c=Curator();s=c.schools['1293'];sid='82e61715a66fdb22'
for o in s['observations']:
 if o['field']=='deadlines' and o['source_id']==sid and '未視覺核清' in o['text_zh']:
  o['text_zh']='熊本2025/26factsheet p2已目視核對：秋2025提名舊3/7有刪除線，紅字修訂為2025/3/14；學生申請2025/4/18。春2026提名2025/10/10、申請2025/11/14。原疑日期矛盾已由版面修訂標記解決，但仍全為舊期，不改標2027。';o['applicability_status']='older_year_reference';o['evidence_locator']='Rendered PDFp2 strike-through March7 replaced by red March14; kumamoto-factsheet2025-page2.png';o['observation_id']=hashlib.sha256(('1293|deadlines|'+sid+'|'+o['text_zh']).encode()).hexdigest()[:20];o['visual_page_verification']='kumamoto-factsheet2025-page2.png'
c.body_review('1293',sid,['eligibility','language','deadlines','documents','cost','housing'],'完整兩頁正文與p1/2版面均已讀；p2明顯刪除線3/7與紅字3/14為修訂，已解原文字層日期疑問。',visual_pages=[1,2],visual_files=['kumamoto-factsheet2025-page1.png','kumamoto-factsheet2025-page2.png'])
c.decision('1293','deadlines',[sid],'reviewed_previous_cycle_revision_resolved','2025秋提名3/7已刪、紅字3/14替代，原版面可確定；不能因缺2027新期就保留已解3/7vs3/14矛盾。')
c.fact('1293',sid,'eligibility','熊本2025/26factsheet p2明确大二以上；較早未標年12頁brochure p4稱本科大三。新旧年級有差異，採2025/26作該期參考，仍須2027正式版，不能把兩版本合成通用硬門檻。','熊本2025/26 p2 vs 官网/media/2022/02/旧brochure p4；UG Short-Term Exchange','Kumamoto University - Fact Sheet 2025/26',page=2,period='version_conflict',locator='Rendered2025/26p2 GradeRequirements; scannedbrochurep4 ProgramOverview')
c.save();print('observations',sum(len(x['observations']) for x in c.schools.values()))
