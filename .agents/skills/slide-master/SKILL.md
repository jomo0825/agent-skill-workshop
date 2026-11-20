---
name: slide-master
description: 使用本機 JSON 與既有 Python 工具製作可編輯 PowerPoint，包含技術圖表及保存的配圖。適用於生成、更新或重跑本專案投影片；不以輸出大綱代替實際 PPTX。
---

# 投影片生成大師

## 直接使用

範例內容、版型和資料已備好。先使用既有工具完成成果；使用者要求修改功能時才調整程式。

1. 確認輸入 JSON 與輸出資料夾。體驗範例使用專案根目錄 `data/sensor-demo.json`，明示資料是模擬測試值。輸入格式見 [references/input-format.md](references/input-format.md)。
2. 透過可執行 Python 的工具呼叫 `scripts/build_deck.py`。先解析此 Skill 的實際位置；以下命令以專案根目錄為工作目錄：

   ```sh
   python .agents/skills/slide-master/scripts/build_deck.py --input data/sensor-demo.json --out output/demo
   ```

3. 程式會沿用 `assets/sensor-hero.png`，產生六頁 `slides.pptx` 與 `report.json`。PowerPoint 文字、表格、圖表及技術流程圖皆為原生可編輯物件；生成配圖是點陣圖片。程式不需要模型金鑰，也不重新生成圖片。
4. 使用同一套工具檢查成果：

   ```sh
   python .agents/skills/slide-master/scripts/inspect_deck.py --pptx output/demo/slides.pptx --input data/sensor-demo.json
   ```

   檢查通過不代表視覺上沒有問題；可用 PowerPoint 或 LibreOffice 開啟確認文字與圖形。範例已有逐頁預覽，供對照。
5. 交付實際存在的 PPTX 及 report.json 路徑，根據報告中的真實統計說明結果。執行失敗時回報原因，不宣稱投影片已完成。

## 修改與重用

- 改內容或數據：另存 JSON，再次呼叫同一腳本；不要每次重寫整支程式。
- 改配色：使用 JSON 的 `theme.accent` 六位十六進位色碼。
- 改配圖：在環境具備生圖能力時，參考 [assets/image-prompt.md](assets/image-prompt.md)，先預覽新圖，再保存至 assets。可用 `--hero` 指定新檔。
- 改版型或功能：參考 [references/layout.md](references/layout.md)，調整對應函式後執行測試與成果檢查。
- 資料缺漏或不合法：指出欄位並修正可確認的問題；缺少真實資訊時詢問，不補造測量值。

## 限制

這是可閱讀、可修改的固定六頁教學產生器，不會自動研究題目、讀取任意文件或任意增加頁數。長文字超過版型限制會回報錯誤，請縮短或修改版型。輸出資料夾的同名檔會覆寫，保留版本時請換 `--out`。
