# 三校五組修正不可變索引

資料候選：`2159409cacb6d8ac36bbafcc3ca6f2925f860fc9`。基準：`bb4cecd8030946e59bed494509d206c356e5c210`。僅 NUFS ncu-130、熊本 ncu-134、龍谷 ncu-135；116 當期待確認，仍 74 partial／214、外校完整核准 0。

- [龍谷文件階段](schools/ncu-135/documents.json)：初次十項（JLPT 有則附），住宿兩項，入寮時無日本可用帳戶者的到校開戶兩項。未取得表格本體明列，條件符合仍不解除當期下載封鎖。
- [熊本語言](schools/ncu-134/fields/language.json)、[資格](schools/ncu-134/fields/eligibility.json)：英頁非英語母語者的成績提交、J 非日本學生與日頁外国籍條件分開。
- [熊本保險](schools/ncu-134/fields/insurance.json)：同原件第 8 頁可選私人保險約 15,000 日圓一次性付款；舊資料不是 116 現價。
- [NUFS 課程](schools/ncu-130/fields/courses.json)：Study Abroad 學生不能修 GJP 課程，與不能換方案分開。

[七個精確原文定位](../../../sources/ncu/next3-review-20261009/five-corrections-source-ledger.json)保留 URL、原件 SHA、頁／行、原文與查核日。51 欄、172 原文定位、527 JSON，最大 41,001 bytes；小索引從固定 Git 候選讀回，未覆寫舊 71 與 bb806740 索引。

```bash
python scripts/build_ncu_review_index.py --check --output-dir docs/ncu-review-index/next3-2159409c
python scripts/build_ncu_review_index.py --output-dir docs/ncu-review-index/next3-2159409c --school ncu-135 --field host_documents --original
```
