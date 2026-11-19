# 我的個人一週生活助理｜Agent Skill 三小時工作坊

**先跑出成果，再看懂、改一項、重新驗證。** 給工程／資訊背景產學專班學生的完整教學範例。

![個人助理報告橫幅](.agents/skills/weekly-assistant/assets/banner.png)

這個 Skill 讀取模擬行程與待辦，利用 Python 找出時間衝突、安排待辦，再將已生成的插畫嵌入 HTML 週計畫。包含可直接執行的程式、完整 Skill、設計單範本、填寫範例與課堂練習。

## 先看成果：不用 Agent 也能體驗

1. 在 GitHub 按 **Code → Download ZIP**，解壓縮。或使用 Git：

   ```sh
   git clone https://github.com/jomo0825/agent-skill-workshop.git
   cd agent-skill-workshop
   ```

2. 直接用瀏覽器開啟 [examples/demo/week-plan.html](examples/demo/week-plan.html)。GitHub 文字預覽不會執行 HTML，請先下載；無須架設網站。
3. 先觀察：上課與看牙衝突、4 項待辦已安排、2 項未安排。再讀 [預期結果](docs/expected-results.md)。

## 三分鐘執行

準備 **Python 3.10 以上**，不需要 pip install、不需要 API 金鑰，也不需要日曆帳號。在解壓縮後的專案根目錄開啟終端機：

```sh
python .agents/skills/weekly-assistant/scripts/planner.py --input data/demo.json --week 2026-11-23 --out output/demo
```

Windows 若找不到 `python`，可試 `py -3`；macOS／Linux 通常可使用 `python3`。確認版本在 3.10 以上。

執行後以瀏覽器開啟 `output/demo/week-plan.html`。同一資料夾的 `plan.json` 是可核對的分析結果。輸出檔同名會覆寫，做不同實驗請換 `--out`。

再換一週，程式與圖片都不用改：

```sh
python .agents/skills/weekly-assistant/scripts/planner.py --input data/second-week.json --week 2026-11-30 --out output/second-week
```

## 讓 Agent 使用 Skill

在 Codex 中開啟這個專案根目錄。Skill 放在 `.agents/skills/weekly-assistant/`，可依專案範圍探索。若環境支援明確引用，可使用 `$weekly-assistant`；實際介面依所用 Agent 平台而異。

將以下請求交給 Agent：

> 請使用這個專案的 weekly-assistant Skill，讀取 data/demo.json，規劃從 2026-11-23 開始的一週。沿用現有 Python 與圖片，輸出至 output/agent-demo。請實際執行，列出衝突與未安排原因，並給我 HTML 與 JSON 的位置。

若平台沒有自動發現 Skill，可明確請 Agent 讀取 `.agents/skills/weekly-assistant/SKILL.md` 後照指示執行。仍需要該環境具有本機檔案與 Python 執行能力；純聊天視窗不會只因上傳檔案就自動具備這些能力。

## 這個專案怎麼讀

```text
agent-skill-workshop/
├── README.md                         先從這裡開始
├── docs/
│   ├── course-outline.md             三小時章節與小節
│   ├── design-template.md            空白設計單
│   ├── design-example.md             完整填寫範例
│   ├── student-lab.md                學生循序練習
│   ├── instructor-guide.md           教師帶課與示範提示詞
│   ├── code-walkthrough.md           程式閱讀地圖
│   └── expected-results.md           可核對的預期結果
├── .agents/skills/weekly-assistant/
│   ├── SKILL.md                      Agent 的工作指示
│   ├── scripts/planner.py            確定性排程與報告程式
│   ├── references/rules.md           資料格式與規則
│   └── assets/
│       ├── banner.png                已生成、可重用的圖
│       └── image-prompt.md           影像提示詞與製作紀錄
├── data/                             兩週模擬資料
├── examples/                         已完成的 HTML 與 JSON
├── tests/                            排程邊界與輸出測試
└── .github/workflows/check.yml        GitHub 自動驗證設定
```

Windows 若看不到點開頭的資料夾，請在檔案總管開啟「顯示隱藏的項目」；GitHub 可直接瀏覽它們。

## 課程資料入口

- 教師：[課程大綱](docs/course-outline.md)、[帶課指引](docs/instructor-guide.md)。
- 學生：[設計單範本](docs/design-template.md)、[填寫範例](docs/design-example.md)、[實作練習](docs/student-lab.md)。
- 閱讀程式：[程式閱讀地圖](docs/code-walkthrough.md)、[預期結果](docs/expected-results.md)。

## 什麼是生成？什麼是重用？

- 製作 Skill：由 Agent 協作產生並修正 Python；影像工具產生插畫，保存至 assets。這個專案已提供完成版本供學生閱讀與修改。
- 執行 Skill：沿用 scripts 與 assets，對不同資料產生新結果。Python 程式本身不連線呼叫模型。
- Python 檔案是經由執行工具呼叫的腳本，不會因放入 scripts 就自動註冊為遠端 tool。
- 隨附圖片已由影像生成工具製作；完整提示詞見 assets/image-prompt.md。有生成能力的學生可換圖，沒有也能完成課程。

## 驗證

```sh
python -m unittest discover -s tests -v
```

本機驗證通過 10 個測試方法，涵蓋相鄰／跨週行程、資料驗證、待辦期限、不重疊、時區換算、第二週重用與 HTML 跳脫。GitHub Actions 設定於 Windows／Linux、Python 3.10／3.12 執行相同檢查；是否成功請查看實際 Actions 結果。

## 範例限制

固定 UTC+08:00、貪婪排程、待辦不拆分、不含交通緩衝。只產生建議，不修改真實日曆、不發送訊息。所有人物與活動均為模擬資料；教學分享時請沿用虛構資料。

本專案程式與教材採 [MIT License](LICENSE)。隨附 AI 生成圖片可隨本教學專案使用、修改與分享，不宣稱排他的著作權。

Skill 結構與專案探索方式參考 [OpenAI 官方文件](https://learn.chatgpt.com/docs/build-skills)。
