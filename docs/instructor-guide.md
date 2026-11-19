# 教師帶課指引

## 教學安排

採「先看完成品 → 說清需求 → 讀懂程式 → 修改 → 驗證」；學生不必從空白資料夾起步。課程目標是理解與改造可重用流程，不是三小時內精通 Python 或排程最佳化。

課前確認學生可下載專案、執行 Python 3.10+，Agent 平台能存取專案與執行程式。若無個人生圖權限，可由教師投影示範並使用隨附圖片。完整時間配置見 course-outline.md。

## 開場示範：個人一週生活助理

先開 examples/demo/week-plan.html，問學生：哪件事不能同時做？哪件事已經過期？為什麼 600 分鐘的整理任務沒有被硬塞進去？

再顯示 data/demo.json，讓學生知道成果與資料之間可核對。固定日期是重現教學用，不是當週日曆。

## 第二章：設計單

投影 design-example.md，逐欄對照實際專案：

| 設計單 | 專案對應 |
|---|---|
| 任務／適用時機 | SKILL.md 的 description 與流程 |
| 輸入／規則 | data/*.json、references/rules.md |
| 程式工具 | scripts/planner.py |
| 素材 | assets/banner.png 與 image-prompt.md |
| 驗收 | tests、expected-results.md、實際輸出 |

學生複製空白版；先改需求再改檔案，避免把「會呼叫 Agent」誤當作「會設計 Skill」。

## 第三章：程式生成示範

從 code-walkthrough.md 的資料流講起。用以下請求現場生成一個小程式：

> 請在 exercises/overlap_demo.py 產生 intervals_overlap，接受四個含時區的 datetime。判斷兩段行程是否重疊；相鄰不算。加入三個可執行驗證案例，實際執行。請不要修改既有 planner.py。

接著回到完整腳本，說明同樣的邏輯已封裝供 Agent 重複使用。不要為了展示生成而現場重寫整支排程器，時間留給驗證與整合。

## 第四章：影像生成示範

依 assets/image-prompt.md 生成插畫，展示「生成 → 挑選 → 保存 → 程式讀取 → 出現在報告」。這張圖的生成與 Python 的排程是不同階段，不需要替所有學生設定影像 API。

新圖保存前備份原版。程式讀取固定檔名 banner.png；只換圖片不改程式。學生若修改檔名，需連同讀取位置一起更新。

## 第五章：整合示範

> 請使用專案中的 weekly-assistant Skill。讀取 data/demo.json，週一起點 2026-11-23，輸出至 output/teacher-demo。沿用 Python 與圖片，實際執行後根據 plan.json 摘要說明衝突與未安排項目，提供成果位置。

換成 second-week.json、2026-11-30 再執行，強調重用而非每次重造。讓學生比較 Agent 說的時間是否與 JSON 相同。

## 建議驗收規準（100 分）

| 項目 | 配分 | 可觀察證據 |
|---|---:|---|
| 設計單與實作一致 | 20 | 輸入、輸出、規則與檔案可對照 |
| 程式工具可執行且結果正確 | 25 | 正常與異常案例，實際 JSON |
| 素材保存並被使用 | 15 | assets 與 HTML 中實際圖片 |
| Skill 能重用工具與素材 | 25 | 第二份資料重跑，不重寫程式 |
| 變更／修正紀錄 | 15 | 說明修改位置、原因與重測證據 |

## 常見卡點

- 中文顯示不正常：檔案一律 UTF-8；Windows 可用 `python -X utf8` 執行。
- 找不到 .agents：開啟隱藏檔顯示；確認解壓縮的是完整資料夾。
- Skill 未被探索：直接指定讀取 SKILL.md；確認 Agent 開啟的是專案根目錄。
- HTML 在 GitHub 顯示原始碼：下載後用本機瀏覽器開啟，不需要部署網站。
- 圖片變了報告沒變：HTML 內嵌圖片，重跑後才會更新。
- 格式錯誤：先用錯誤訊息定位 JSON 欄位，不要先改掉驗證條件。

## 發布與分享

專案網址：https://github.com/jomo0825/agent-skill-workshop

只上傳本課程模擬資料與素材，不加入個人行程、帳號憑證或課堂學員資料。可先用 GitHub 的 Code → Download ZIP 發給學生；需要學員保留版本時再教 Fork。
