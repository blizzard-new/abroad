# 三校小型review index

不可變資料候選 **bb806740e702892e78d358973cb2c54b739d3dbd**，基準012b580；這是74 partial中的三校subset，不取代71校2637de2凍結索引，也不表示116當期通過。

| 學校 | 欄位與原文定位 | home／host文件 | 未解問題 |
| --- | --- | --- | --- |
| NUFS ncu-130 | [17欄](schools/ncu-130/index.json) | [逐step文件](schools/ncu-130/documents.json) | [gaps](schools/ncu-130/gaps.json) |
| 熊本 ncu-134 | [17欄](schools/ncu-134/index.json) | [逐step文件](schools/ncu-134/documents.json) | [gaps](schools/ncu-134/gaps.json) |
| 龍谷 ncu-135 | [17欄](schools/ncu-135/index.json) | [逐step文件](schools/ncu-135/documents.json) | [gaps](schools/ncu-135/gaps.json) |

[manifest](manifest.json)綁定六份Git原件hash。51個field檔保留171個原文精確位置／SHA；source metadata及每段native text另有位置與hash，原始大檔留在候選Git。527份JSON最大41,001bytes，沒有把大原文混進小索引。生成與完整驗證：

```bash
python scripts/build_ncu_review_index.py --candidate-sha bb806740e702892e78d358973cb2c54b739d3dbd --baseline-sha 012b580b9c38b20da0e52394eef1428c2ea90261 --output-dir docs/ncu-review-index/next3-bb806740 --row-ids ncu-130 ncu-134 ncu-135
python scripts/build_ncu_review_index.py --check --output-dir docs/ncu-review-index/next3-bb806740
python scripts/build_ncu_review_index.py --output-dir docs/ncu-review-index/next3-bb806740 --school ncu-130 --field host_documents --original
```

最後一項只按定位讀回同SHA原文，不改寫資料。PDF頁、ZIP成員／工作表、HTML無頁碼按原件分列；當期適用性與閱讀完成度仍是不同資訊。對應[來源閱讀與取用限制](../../../sources/ncu/next3-review-20261009/README.md)。
