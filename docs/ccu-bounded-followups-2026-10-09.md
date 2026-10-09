# CCU 指定缺值補核：AMU 一般保險與 Mapúa 手冊

先完成正常 TLS 安全修正並推送 `e38c205f5346a67ca3ab93055487df0484e0afed`，再只讀使用者指定的 AMU General Insurance、同側欄 Additional Insurance／Medical Services 三頁，以及已取得正常 TLS 的 Mapúa 34頁手冊。沒有擴展其他55校來源研究。

AMU 三頁各自正常 TLS HTTP200，保存原始 HTML、main正文、回應 SHA 與實際時間。[逐項查核](../src/exchange_info/official_data/ccu/twentyeighth-source-review.json)與原文 source records 分開记录。General Insurance 是一般 Students/Healthcare，非原博士生專屬頁；非EU學生自投NFZ、Card of the Pole／波蘭裔證明繳費例外、未滿18父母同意，以及護照／合法居留／在學證明均按身分保留。這些是投保手續，不增列為初次交換申請文件。

Additional Insurance 明載未被強制保險涵蓋者可向NFZ或私人保險／醫療服務提供者簽個人協議，所以不能把NFZ說為唯一強制方案。一般頁EHIC／S1的UK2020舊註，補充頁2020Q4的PLN483與未有2027更新的PLN55.80均保留為參考，不映射當期costs。頁中學生與博士生、D-13研究簽等身分分開，不以任何一種身分替代中正全部交換生。

AMU insurance從missing補為needs_confirmation；保單/保額、實際承保期間、繳交階段與當期NFZ資格／費率尚未核2027春，具體问题已列。Medical Services 只作一般門診登記／證件與保險證明、轉介例外／牙科涵蓋的生活參考，不把RMUA博士學校範例作全部學生必交文件。生活guidance保留獨立pending狀態，未混入當期buddy概要。

Mapúa 一般©2026手冊實體p18與p21明載護照在預定停留結束後仍有效6個月。當期2026/27 factsheet p6僅寫≥6月，未載起算點。護照文件保留兩種來源，項目改needs_confirmation、清楚補起算點與本期待核，不把一般手冊提升為本期已核新規。33校250項文件的當期確認數變為184、待確認66；原文件清單仍部分。

本次檢查確認原Mapúa欄位／概要／文件没有TOR／clearance／離境前流程映射。一般手冊實體p33的離境前申請TOR、clearance、Treasury付款評估與Customer Service領件日、通常1–2週及ILRAD feedback補為獨立return_preparation pending guidance。平台放在返國準備與目的地生活來源，沒有列進初次申請附件，也沒有保證1–2週出件。

海外17欄矩陣仍935欄：307當期確認、334待確認、202缺值、71矛盾、20參考、1明示未公告；新增一般生活guidance不增加17欄的當期完整數。來源總數980，合作條目104、流程／概要55維持。9份不安全歷史來源仍禁止用作現行映射，原始歷史payload与證據保持不變。新版未知與官方明示未公告繼續分開，未merge或部署。
