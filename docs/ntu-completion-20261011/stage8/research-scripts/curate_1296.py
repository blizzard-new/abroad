from research_curator import Curator
from finish_school import finish
c=Curator();f=c.fact;p='1296';s='3f121c21dd3c4772';scope='KNU Incoming Exchange共通，未標學年；Daegu/Sangju實際接收校區待指定'
f(p,s,'eligibility','KNU公開incoming資格列協定校本科在籍，須具英或韓語能力；非協定校另走Visiting。頁面雖列graduate課量，不能據此自推所有研究生皆可申。未找到本頁GPA硬線。',scope,'Currently enrolled on undergraduate program')
f(p,s,'language','KNU交換要求英或韓語能力，但公開文件說TOEFL/TOEIC證明不用交；舊2025/26表仍尊重母校提名標準。這不豁免臺大校內語言證明。',scope,'Language Proficiency Test (TOEFL/TOEIC) submission is not required.')
f(p,s,'deadlines','KNU未標年incoming頁：春10/15提名、10/30初申；秋4/15提名、4/30初申。2025/26PDF却春11/15、秋5/15初申；期別／版本不同未核，不能任選舊PDF較晚日或改年。',scope+'；與2025/26PDF初申期限不同','Nomination and Application Schedule',period='version_conflict')
f(p,s,'documents','KNU公開初申列online、母校推薦/在籍、成績、passport、ID照及財力（KRW800萬/一學期、1600萬/兩學期以上）；父母帳戶須親屬證明。電子發行bank可原件，非電子bank須寄紙本；非OECD在籍驗證/郵寄按原分類，臺灣個案未推定。',scope+'；國籍別認證要求仍須個別核','Certificate of Family Relations')
f(p,s,'courses','KNU一般本科最多18credits、graduate9；英授課表約1月/7月發給錄取交換生，網頁目前列2026課表，非2027保證。2025/26PDF本科最低6、master最多10，與未標年web研9不同，須按期別確認。',scope+'；英授開課與課量版本需核','Spring 2026 Course List')
f(p,s,'cost','KNU未標年頁估雙人校寮一學期USD500–1000，依無餐至每日3餐；餐廳無specialdiet。KRW800萬是財力證明，不是校寮或生活實際支出，不保證2027費率。',scope,'USD$500',theme='cost')
f(p,s,'housing','KNU共通web寫交換生自動分雙人房；2025/26要項則須另上網申寮，申請者可得。保留程序差別，不能漏做住房申請或直接當2027保證。',scope+'；與2025/26 separate application對照','automatically assigned',theme='housing')
f(p,s,'insurance_visa','KNU未標年頁估NHIS KRW71520/月，2025/26要項75490/月；ARC後加入是校方指引，原費率年別不同，不推2027保費或臺灣個人D2裁定。','KNU校方NHIS說明；web未標year、2025/26PDF舊費率','71,520')
f(p,'e33b81bda85adf09','documents','2025/26 checklist另要求住寮者TB檢驗英語結果由母國開立、入住時繳；D2、ARC、orientation是錄取／到校階段，不能全部當初申文件。要項中passport須離境後至少6月效期為舊版條件。','KNU2025/26 checklist；非2027–28新表','Tuberculosis test results',page=2,period='older_year_reference')
finish(c,p,'五原source為三個不同SHA完整讀：兩組~eng與正常路徑是相同本文。2025/26PDF與未標年web在初申10/30/4/30 vs11/15/5/15、grad9 vs10、住房auto vs另申、NHI71520 vs75490不同，不能任選2027值。Academic2026頁的2027degree earlydecision是學位招生，不是incoming期限。租費與銀行資金證明、初申與TB/D2/ARC階段分開。')
