from pathlib import Path
import os,json,datetime,hashlib
from urllib.parse import quote
from urllib.request import Request,urlopen
H=Path(__file__).parent;R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'docs/ntu-completion-20261011/stage8'
publication=json.loads((H/'publication.json').read_text());verified=json.loads((H/'remote-publication-verification.json').read_text());result=json.loads((H/'finalize-result.json').read_text());commit=publication['remote_commit'];assert verified['remote_commit']==commit
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'}
def call(path,method='GET',data=None):
    with urlopen(Request('https://api.github.com/repos/blizzard-new/abroad/'+path,headers=headers,method=method,data=None if data is None else json.dumps(data,ensure_ascii=False).encode()),timeout=60) as response:return json.load(response)
before=call('pulls/9');assert before['head']['sha']==commit and before['draft'] and not before['merged']
links=[]
for label,name in [('可回填Excel','288校逐欄查核_可回填.xlsx'),('問題解決報告','問題解決報告.md'),('結構化候選JSON','結構化候選資料.json'),('回填ZIP','臺大288校候選查核_可回填.zip')]:
    path='docs/ntu-completion-20261011/stage8/'+name;links.append(f'[{label}](https://github.com/blizzard-new/abroad/blob/{commit}/{quote(path,safe="/")})')
tests='\n'.join('- '+name+': '+value['final_line'] for name,value in result['tests'].items())
body=f'''臺大合作校有舊年度、院級與申請階段混用的參考，以及來源正文尚未逐項讀取的缺口。此Draft把已核對的短引用、原年度／入學期／校區／program／階段及官方URL呈現在合作校摘要與生活指南；所有1,373則維持 `selection_rule_confirmed=false`，不能替代116-1正式甄選規則。

本批700→1,373，新增673則；上一批700則逐筆保留。固定501校欄、117校、890原本文SHA的優先候選集合已全部讀完（501／501、0待讀），來源閱讀紀錄2,229列、人工語意625列、引用來源611件；1,228原件版本以42件ZIP按SHA封存，原554版本／19分件不變。

全288校14欄可回填表保持4,032列；282校10類共2,820列仍未達「所有當期子項完整核實」。全矩陣尚有429個欄位帶可讀候選待該欄語意核對；固定優先集合完成不等全部缺口解決。任一生活段落缺{result['life_gap']}校，原46校獨立接待校網域生活来源仍缺{result['independent46_gap']}校；上批把蘭州手冊NTU代存算作獨立接待校網域的分類有誤，38更正39（上一批與本批actual runtime均39，原46成員及全部1963段舊生活證據保留）。照片與座標各缺3，UC／CSU分配校區與圖片再製許可等限制保留。

已公告的臺大116-1共通時程／資格獨立列11項；报名臺灣2026/11/3 10:00–11/9 16:00。未將海外接收容量當臺大名額，也未將舊年改標2027–28。臺大288筆資格、名額、截止、狀態與身份和main逐筆相同；282空白／6零，workflow及其他母校catalog byte一致，未merge／deploy。

驗證綁來源SHA `{result['source_sha256']}`，源／程式／測試／materialized檔於整輪測試不變：

{tests}

全288 API逐筆檢查1,373則正文、scope、URL在首10顯示項與未確認守門；兩步重建byte-idempotent。固定PR8 `9927ec1d8765a9772671bbaa68e7f920995f1258` 在隔離樹合併驗證，產品檔原byte保留。其既有部分JS擷取測試首次33通過／1失敗，補齊隔離測試所漏PR8輔助函式後34通過，原斷言未改、修前log及修補SHA保留；未改PR9產品或測試來修該隔離問題。全套非E2E首次2184通過／1失敗是生活段數固定快照1963未跟上161則新增，更新為2124、原錯誤頁排除斷言保留後整套重跑；源／產品程式不改，修前log與測試SHA保留。實際未mock CGU兩sheet／77校含Lincoln於前／中／後另驗。

交付（固定本批commit、已從GitHub下載並逐byte／SHA驗）：{' · '.join(links)}。Excel7表／0公式、回填ZIP完整性通過；未宣稱Excel GUI全表目視。來源實際查核時刻及每日比較基準在報告與JSON，不把閱讀時間冒稱全網重查日期。Library先前401且父端停止重試，無Library檔案ID；原舊Excel未取，282集合從臺大官方288 portalID重建，未宣稱舊逐格對齊。
'''
title='臺大288校來源查核：1,373則參考與固定501組正文覆蓋'
updated=call('pulls/9','PATCH',{'title':title,'body':body});assert updated['head']['sha']==commit and updated['draft'] and not updated['merged']
after=call('pulls/9');assert after['body']==body and after['title']==title and after['head']['sha']==commit
(H/'pr9-final-description.md').write_text(body)
receipt={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'PR_url':after['html_url'],'remote_commit':commit,'title':title,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'body_read_back_exact':True,'draft':after['draft'],'merged':after['merged']}
(H/'pr9-description-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))
