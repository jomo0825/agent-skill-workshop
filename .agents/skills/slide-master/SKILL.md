---
name: slide-master
description: 將已有標題與文字的香草版 PPTX 重新設計成完整投影片圖片，再組裝為新的 PowerPoint。適用於簡報視覺重製，預設保留原文、頁數與頁序。
---

# 投影片生成大師

## 1. 任務與成果

把內容已確定的香草版 PPTX 轉成有一致視覺設計的簡報。**必須使用 imagegen 逐頁生成完整畫面，文字、插圖、圖解與版面一起生成。** 不用現成素材拼貼頁面，不以程式畫版面或疊加文字替代 imagegen。輸出的 PPTX 每頁只有這張滿版圖片。保留可編輯的原稿，說明成品文字已點陣化。

## 2. 輸入與前置條件

取得原始 PPTX、輸出資料夾及使用者指定的風格。未指定時採隨附科技風。需要能執行 Python 的環境，以及 Agent 可使用的 imagegen 工具；只有 Python 無法完成 AI 生圖。啟用平台提供的影像生成指引，使用內建 imagegen，不自行換成其他生圖途徑。

以下路徑皆相對於本 Skill 資料夾。從儲存庫根目錄執行時，加上 `.agents/skills/slide-master/` 前綴。

## 3. 執行流程

1. 執行 `python scripts/extract_deck.py INPUT.pptx WORK/source.json`，讀取逐頁文字、備註與圖片，檢查抽取結果。若含不支援的物件，先讀 [內容保留規則](references/content-rules.md)，完成補充檢視再繼續。
2. 讀 [視覺系統](references/style-system.md)，查看 `assets/style-board.png`，依內容選擇 `assets/examples/` 裡的對應頁型。這些圖片是風格參考，不可把範例文字當成新原稿內容。
3. 依 [生成提示詞範本](references/prompt-template.md) 為每頁寫 Prompt，保存於 `WORK/prompts/`。逐字提供原稿文字，附對應原稿預覽、風格參考與需要保留的原始圖片。
4. 由 Agent 呼叫 **imagegen，一頁一次呼叫**，生成完整 16:9 頁面，保存為 `WORK/images/slide-01.png` 起的連續檔名。`assets/` 只提供視覺參考，不是待拼貼的零件。逐頁核對原文與圖像，錯誤交由 imagegen 編修或重新生成，不能用原生文字或程式拼貼遮蓋。
5. 執行 `python scripts/assemble_deck.py WORK/source.json WORK/images OUTPUT.pptx`，將核對後圖片組成簡報。
6. 執行 `python scripts/check_deck.py OUTPUT.pptx --manifest WORK/source.json --images WORK/images`，再按 [品質檢查](references/quality-check.md) 渲染檢視。結構檢查通過不代表圖片裡的文字正確。

## 4. 工具與資源的分工

| 資源 | 用途 |
|---|---|
| `scripts/extract_deck.py` | 保存原文、備註、原始圖片及來源雜湊 |
| `scripts/assemble_deck.py` | 依原頁數組裝滿版圖片，產生總覽 |
| `scripts/check_deck.py` | 驗證頁數、比例、唯一圖片、滿版位置及圖片一致性 |
| `assets/` | 風格總覽與四種已完成頁型的視覺參考 |
| `references/` | 內容保留、視覺規則、Prompt 範本與驗證規則 |

## 5. 驗證與交付

交付新的 PPTX、逐頁 PNG 與總覽，保留原稿。核對文字、數值、頁序與來源圖片，檢查裁切、清晰度和整體一致性。圖片內的網址只能閱讀，不會自動保有超連結。保留此次 Prompt 與必要紀錄，方便重製。

## 6. 修改與失敗處理

- 預設只改設計，不能自行摘要、改寫、翻譯、增刪頁面。使用者要求修改內容時，記錄範圍與變動。
- 備註可作為非可見的視覺指引，不能直接印到頁面。備註若要求修改內文，先確認該修改是否已獲授權。
- imagegen 不可用時，交付已抽取的內容與 Prompt，明確說明尚未生成新頁面；不可改用程式繪圖、素材拼貼或拿隨附範例冒充此次成果。
- 不覆寫原稿。組裝腳本拒絕覆寫已有輸出，改用新檔名。過密文字若無法清晰呈現，與使用者討論拆頁或精簡。
