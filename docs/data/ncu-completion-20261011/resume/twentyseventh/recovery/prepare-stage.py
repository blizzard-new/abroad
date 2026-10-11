from pathlib import Path
W=Path('/workspace/ncu-resume-work/twentyseventh');s=Path('/workspace/ncu-resume-work/twentysixth/stage.py').read_text();s=s[:s.index("rid='ncu-060';sid=")]
s=s.replace('twentysixth','twentyseventh').replace('46c70072273f4b472b6ed8a5b2fe2ece66e8bd93','573126cce6def44dc4c35c7c0f8ce9b59e093a0b').replace('第二十六批','第二十七批')
s=s.replace("ledger.append({'source_id':sid", "if n.get('selected_passages'):\n  s['visual_review']['page_transcriptions']=n['selected_passages'];s['visual_review']['include_native_with_selected_passages']=True\n  s['page_transcriptions']=n['selected_passages']\n  js(B/f'{sid}-visual-review.json',s['visual_review'])\n ledger.append({'source_id':sid")
s=s.replace("'native_full_read':True,", "'native_full_read':True,'native_text_limitations':n.get('native_text_limitations'),'blank_visual_pages':n.get('blank_visual_pages',[]),'selected_passages':n.get('selected_passages',[]),")
s=s.replace("for sid,rid in rows.items():\n if sid", "for sid,rid in rows.items():\n if rid not in records:records[rid]={'source_ids':[],'fields':{},'applicability':'中央公開未年學校介紹，僅歷史參考。','host_documents':[]}\n if sid")
(W/'stage.py').write_text(s)
