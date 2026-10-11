from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import datetime, hashlib, json, os

H = Path(__file__).parent
R = Path('/workspace/abroad-ntu-completion-20261011')
S = R / 'docs/ntu-completion-20261011/stage9'
read = lambda p: json.loads(p.read_text())
publication = read(H / 'publication.json')
verified = read(H / 'remote-publication-verification.json')
result = read(H / 'finalize-result.json')
commit = publication['remote_commit']
assert verified['remote_commit'] == commit
assert verified['source_sha256'] == result['source_sha256']
headers = {
    'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
    'Accept': 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'X-GitHub-Api-Version': '2022-11-28',
}

def call(path, method='GET', data=None):
    payload = None if data is None else json.dumps(data, ensure_ascii=False).encode()
    request = Request('https://api.github.com/repos/blizzard-new/abroad/' + path,
                      headers=headers, method=method, data=payload)
    with urlopen(request, timeout=60) as response:
        return json.load(response)

before = call('pulls/9')
assert before['head']['sha'] == commit and before['draft'] and not before['merged']
links = []
for label, name in [('可回填Excel', '288校逐欄查核_可回填.xlsx'),
                    ('問題解決報告', '問題解決報告.md'),
                    ('結構化候選JSON', '結構化候選資料.json'),
                    ('回填ZIP', '臺大288校候選查核_可回填.zip')]:
    path = 'docs/ntu-completion-20261011/stage9/' + name
    links.append(f'[{label}](https://github.com/blizzard-new/abroad/blob/{commit}/{quote(path, safe="/")})')
tests = '\n'.join('- ' + name + ': ' + value['final_line']
                  for name, value in result['tests'].items())
outcomes = '\n'.join('- `' + key + '`: ' + str(value)
                     for key, value in result['conclusions'].items())
body = f'''已讀官方來源仍混有不同學年、校區、交換方案與申請階段，通用「待判」無法指出使用者還缺什麼。此Draft在合作校摘要及生活指南呈現原文引用、適用範圍、官方URL，以及每欄具體缺項。固定429欄／121校全部形成終局結論，0欄再因同一份已讀候選正文無限待判；所有參考仍不提升為當期正式甄選規則。

本批1,373→1,485，新增112則有範圍參考；原1,373則觀察及原2,124段生活證據逐筆保留。429欄結論：

{outcomes}

`verified_scoped_reference`僅核實原文件範圍；原年度／學期／校區／incoming方向等子項分開記錄。其餘均附SID-specific可採或拒用理由、原件SHA及必要外部條件。只有明治課表「2027年8月上傳」及神奈川課表「2027年3／4月」原文明示待公告的兩欄才用`officially_unannounced`，未找到不算確實未公告。未新增取件或擴張搜尋；僅列少數必要官方連結，不新增无界隊列。

固定501優先候選集合在第8批已读完：501／117校／890原件SHA分母不變。現來源閱讀紀錄4,025列、人工語意1,009列、引用來源648件；1,389原件版本以44件ZIP封存，原1,228版本／42分件逐件不變。Macau相同SID的舊／新原件SHA分開保留，未覆寫版本。

全288校×14類可回填表4,032列；282待定校×原10類的2,820欄仍0欄達到「當期所有子項完整核實」。所有1,485則`selection_rule_confirmed=false`，不將舊年改標2027–28、不把海外接收名額替代臺大甄選名額。臺大已公告116-1共通時程／資格獨立列11項；報名臺灣2026/11/3 10:00–11/9 16:00。正式288筆資格、名額、期限、狀態和身份與main一致，名額282空白／6零；工作流、其他母校catalog與共享app.js守門未變。

任一生活來源現272校／2,146段，仍缺{result['life_gap']}校。原46校獨立接待校網域生活來源同成員／同non-NTU口徑仍缺{result['independent46_gap']}校；第7批報告38误算蘭州(819)臺大代存原校PDF為海外網域，第7／8批actual runtime均39，本批沒有刪來源或改分母。保留逐校URL對照及更正收據。照片／座標仍各缺3；UC、CSU分配校區未指定，特魯瓦原圖／作者／授權未齊，蒙斯地址／校區無一致可核坐標，均正式保留。

驗證綁來源SHA `{result['source_sha256']}`。來源、程式、測試及materialized檔於整輪測試不變：

{tests}

全288校API檢查1,485則正文／scope／URL及429欄具體結論，桌面／手機實跑。兩步重建byte-idempotent；固定PR8 `9927ec1d8765a9772671bbaa68e7f920995f1258`於隔離樹组合驗收，PR8產品bytes原樣保留，座標修改記錄無交集。

本批首次隔離focused為36通過／1失敗：JSON值相同但結論key插入順序不穩，修重放程式pop／reinsert，原idempotence斷言未改。首次瀏覽器17通過／2失敗是新測試漏展開既有官方指南；補展開操作後保留內容／可見性／溢出斷言。首次全套430通過／7skip後為修問題而中止，組合瀏覽器亦中止且0完成，未稱完整通過。修前log、程式、測試、SHA及修後完整重跑收據全部保留；引用來源與原件SHA未變。

其後完整回歸2189通過／1失敗／13跳過：60個新verification欄首次建置時尚無source_urls，結論key位置與重放不同，JSON值完全相同。改為觀察迴圈建立來源／狀態後再寫入結論；原單次重建與歷史重放byte斷言不改，兩項針對修正驗證通過，再重跑上述四組。失敗整輪log與輸入SHA、修前程式／runtime、單次建置產物及逐欄診斷全部保留，來源SHA與資料值未改。

交付（固定本批commit，已從GitHub下載並逐byte／SHA驗）：{' · '.join(links)}。Excel8表／0公式、ZIP CRC通過；只目視慶北手機／桌面兩張結論截圖，未宣稱全校頁或Excel全表GUI目視。每日基準保留來源實際checked_at，本批0取件，不把閱讀／測試時間冒稱全網重新查核。父端負責每日臺灣10:00排程，本輪未重建排程，未發信、登入或繞封鎖。

另有固定429外的4項歷史限制（創價封面／未核掃描內頁、釜山文件資料夾、SNU宿舍介紹、HSG保險入口）保留原時間及具體來源不足；通用首頁不另生成992個假待讀工作項。原2026-10-07 Excel未取得，按臺大288 portal ID重建282集合，舊逐校／逐格精確重疊未知。Library先前401且父端停止重試，沒有Library檔案ID。PR9保持Draft，未merge或deploy；這是可取得既有範圍的最終驗收，未宣稱全282校當期缺口已解。
'''
patch_path = H.parent / 'stage8/fixed-pr8-test-extraction-dependencies.patch'
patch = patch_path.read_text()
assert (S / 'validation/fixed-pr8-test-extraction-dependencies.patch').read_text() == patch
body += '''
固定PR8的部分JS擷取測試需配套補齊新函式依賴；本批隔離組合驗收沿用第8批已公開的下列補丁。PR9對main的該測試保持原bytes，PR9獨立完整回歸通過。日後合併PR8需一併加入此測試補丁；原斷言不變。

```diff
''' + patch + '```\n'
title = '臺大288校資料：429欄終局判讀與1,485則有範圍參考'
updated = call('pulls/9', 'PATCH', {'title': title, 'body': body})
assert updated['head']['sha'] == commit and updated['draft'] and not updated['merged']
after = call('pulls/9')
assert after['body'] == body and after['title'] == title and after['head']['sha'] == commit
(H / 'pr9-final-description.md').write_text(body)
receipt = {
    'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'PR_url': after['html_url'], 'remote_commit': commit, 'title': title,
    'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'body_read_back_exact': True, 'draft': after['draft'], 'merged': after['merged'],
    'fixed_PR8_companion_test_patch_sha256': hashlib.sha256(patch.encode()).hexdigest(),
}
(H / 'pr9-description-verification.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
