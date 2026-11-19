# 程式閱讀地圖

入口檔：`.agents/skills/weekly-assistant/scripts/planner.py`。

## 先看資料流

```text
JSON + 週一起點
    ↓ main：讀檔與處理錯誤
    ↓ build_plan → validate：檢查資料與規則
    ↓ 固定行程衝突檢查
    ↓ subtract：扣除占用時段，建立空檔
    ↓ 依優先級／期限逐項安排待辦
    ├── plan.json：可核對的結果
    └── render_html + assets/banner.png → week-plan.html
```

## 各函式負責什麼

| 函式 | 讀懂的重點 | 適合提問 |
|---|---|---|
| parse_dt | 要求輸入有 UTC offset，轉換成固定 +08:00 | 為何不能混用沒有時區的時間？ |
| validate | 驗證必要欄位、時段、id、期限與分鐘數 | 為何不在資料缺漏時偷偷給預設值？ |
| subtract | 從多個空檔中扣掉已占用的部分 | 同一行程跨日，還能不能正確扣除？ |
| build_plan | 固定行程不動，待辦採可解釋的貪婪安排 | 為何結果不保證最佳？ |
| render_html | 跳脫文字，嵌入圖片，產生離線報告 | 為何分享 HTML 不必另附圖片？ |
| main | 命令列參數、輸入輸出與失敗回報 | Agent 要如何知道有沒有真的成功？ |

## 想改什麼，先看哪裡

- 改個人行程與偏好：先改 data，不必改程式。
- 改助手行為與詢問時機：看 SKILL.md。
- 改判斷規則：先改 references/rules.md，再改 build_plan 與測試。
- 改圖片：看 assets，保留 banner.png 檔名即可。
- 改報告樣式：看 render_html 的 CSS 與組合方式。

## 為什麼某些工作交給 Python

時間重疊、分鐘數與期限比較需要確定且可重複驗證的結果；Agent 用來理解需求、協作修改程式與解釋實際輸出。不要讓 Agent 每次自行估算時間後，跳過已驗證工具。
