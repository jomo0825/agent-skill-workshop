# 開場展示｜先看成品，再讀程式

## 課前

確認 Python 3.10+、requirements.txt 已安裝，並能開啟 PPTX。先下載完整成品與預覽；網路或環境出問題時，仍可用成品和原始碼繼續觀察，不把安裝排錯當開場。

## 前五分鐘

1. 開啟 examples/demo/slides.pptx，展示六頁與原生圖表、可編輯圖形。
2. 交給 Agent：

   > 使用 slide-master，讀取 data/sensor-demo.json，沿用現有工具產出簡報至 output/live-demo，實際執行並檢查後給我檔案。

3. 第一個原始碼畫面直接開 `.agents/skills/slide-master/SKILL.md`，讓學生看到完整內容。

## 接著十分鐘

由 SKILL.md 的一行命令打開 build_deck.py，只追 `main → validate → build → add_samples`。對照 sensor-hero.png 如何讀入，及 input-format.md 的限制。讓學生自己打開檔案；不要按頁數藏原始碼，也不要求先聽完所有名詞。

## 學生動手

先改 title 重跑，確認輸出文字有變。能自己完成者直接選 challenges.md 的任務。需要協助者再看函式、輸入與錯誤處理說明。以實際輸出判定完成，不以聽完講解或填表判定。

## 核對與範圍

第一組 MAE 0.300 °C，最大誤差 0.500 °C；第二組為 0.150 °C、0.300 °C。資料全為模擬值。六頁版型是課程起點，任意增頁、研究與文件解析尚未實作。進階修改須更新指示與檢查，不能只寫一個新欄位就宣稱支援。
