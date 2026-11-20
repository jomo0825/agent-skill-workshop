# 版型與程式閱讀地圖

16:9、白底、深色字、單一 accent。字型預設 Microsoft JhengHei，輸出環境需要有繁體中文字型；不同系統可能替換字型，請開檔確認。中文字與圖表標籤均保留可編輯性。

| 頁 | 內容 | 可修改位置 |
|---|---|---|
| 1 | 標題、作者、AI生成配圖 | add_cover |
| 2 | 三節點系統架構、責任說明 | add_architecture |
| 3 | 四步處理流程 | add_pipeline |
| 4 | 參考／量測溫度原生折線圖 | add_samples |
| 5 | 統計數字與逐筆絕對誤差原生表格 | add_results |
| 6 | 結論與重現方法 | add_conclusion |

入口 `main` 讀取 JSON，`validate` 檢查型別與版型字數，`statistics` 計算結果，`build` 依序組裝六頁。原生圖表的數據另包含在 PPTX 內的活頁簿中。`inspect_deck.py` 可核對頁數、圖表數據、必要文字與物件是否超出頁面，但不保證無遮擋或字型替換。

`assets/sensor-hero.png` 是可重用配圖，不是整頁投影片；`scripts/` 與 `references/` 均不放本次產出。`--out` 指定的資料夾保存新 PPTX 與報告。
