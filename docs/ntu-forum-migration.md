# 臺大論壇 migration

PR #1新增的學校討論板ID為`ntu`。目前追蹤的論壇函式只接受`cgu`、`ntpu`及`university:`開頭，造成臺大發文回傳`board_forbidden`。

待核准SQL：[20261008130000_ntu_school_board.sql](../supabase/migrations/20261008130000_ntu_school_board.sql)。尚未連線讀取或修改正式Supabase；此工作階段沒有可呼叫的Supabase工具。

## 修改範圍

只在`public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)`的討論板檢查新增一條：

```sql
or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')
```

保留已部署函式的其餘內容、擁有者、授權、`SECURITY DEFINER`與`search_path`。不修改帳號或貼文資料。已包含這條規則時不重複修改；函式缺少或既有檢查不同時，整份migration中止，不猜測替換。

## 驗證

SQL及PL/pgSQL語法解析涵蓋31份migration。隔離PostgreSQL 17測試使用真實的追蹤論壇SQL與先前校別選擇補丁，再透過`service_role`可執行的正式publication入口呼叫。

```bash
EXCHANGE_TEST_POSTGRES=1 python -m pytest -q tests/test_ntu_school_board_migration.py
```

測試檢查migration前臺大被拒、套用後發文與留言成功、重送冪等、既有三種討論板成功，以及錯誤校名、討論板、身分token及未驗證email仍被拒。另檢查重跑結果、函式定義只差新增的一行、權限保留，以及遇到未知函式定義時中止。測試容器不連網、不開放主機埠，結束即移除。

這是論壇migration的PostgreSQL驗證，沒有宣稱完整Supabase服務或正式部署已驗證。

## 正式套用

使用者明確同意後，先讀取正式函式定義與權限，確認與預期校別檢查一致，再在受控資料庫連線中套用這一份SQL。不要以此授權執行全部尚未套用的migration。若現場定義不同，先整理差異供檢視。

套用後核對函式定義、權限及migration紀錄，再用臺大測試帳號驗證發文與留言。合併或更新GitHub PR不等於migration已套用，也不等於正式主機已更新。
