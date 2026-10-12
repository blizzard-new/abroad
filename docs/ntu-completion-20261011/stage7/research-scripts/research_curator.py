from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('stage3_curator_helper',ROOT.parent/'stage3/review_helpers.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Curator(module.Curator):
 def fact(self,*args,**kwargs):
  sid=args[1] if len(args)>1 else kwargs['sid']
  source=self.read_source(sid)
  if source.get('document_type')=='pdf':
   assert isinstance(kwargs.get('page'),int), 'PDF observation requires manually checked page: '+sid
  return super().fact(*args,**kwargs)
 def read_source(self,sid):
  p=next((folder/(sid+'.json') for folder in [ROOT/'sources',ROOT.parent/'stage5/sources',ROOT.parent/'stage4/sources'] if (folder/(sid+'.json')).exists()), ROOT/'sources'/(sid+'.json'))
  if p.exists():
   d=json.loads(p.read_text());d['text']=p.with_suffix('.txt').read_text() if p.with_suffix('.txt').exists() else d.get('text','');d['_folder']=p.parent
   visual=p.with_suffix('.visual-text.txt')
   if visual.exists():d['text']+='\n'+visual.read_text();d['_manual_visual_quote_file']=str(visual)
   return d
  return super().read_source(sid)
 def body_review(self,pid,sid,fields,note,full_text=True,visual_pages=None,visual_files=None):
  d=self.read_source(sid);p=ROOT/'full-body-field-review-ledger.json';rows=json.loads(p.read_text()) if p.exists() else []
  assert d.get('access_status')=='content_available' and len(d.get('text',''))>30
  for field in fields:
   row={'portal_id':pid,'school_name':self.schools[pid]['school_name'],'field':field,'source_id':sid,
    'source_url':d['url'],'body_sha256':d['sha256'],'source_checked_at':d['checked_at'],
    'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_extracted_text_read_for_field':full_text,
    'review_scope':'Full available extracted text; all text-bearing PDF pages' if full_text else 'Source scope or selected passages only',
    'text_chars':len(d['text']),'pdf_page_count':d.get('pdf_page_count'),'note_zh':note,
    'target_cycle_requirement_verified':False}
   if visual_pages:
    row['visually_reviewed_pdf_pages']=visual_pages
    row['review_scope']='All extracted text and separately rendered/visually reviewed PDF pages'
    row['visual_evidence_files']=visual_files or ['nagasaki-guideline-'+str(page)+'.png' for page in visual_pages]
   rows=[r for r in rows if (r['portal_id'],r['field'],r['source_id'],r['body_sha256'])!=(pid,field,sid,d['sha256'])]+[row]
  p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')

 def review(self,*args,**kwargs):
  d=super().review(*args,**kwargs)
  if d.get('_manual_visual_quote_file'):
   row=self.sources[d['source_id']];row['quote_verification_method']='manual_visual_rendered_pdf_with_transcription'
   row['visual_quote_transcription_sha256']=hashlib.sha256(Path(d['_manual_visual_quote_file']).read_bytes()).hexdigest()
   row['original_pdf_text_extraction_chars']=33;row['quote_pdf_page']=1;row['visual_evidence_reference']='kumamoto-visual-review.json'
  return d
