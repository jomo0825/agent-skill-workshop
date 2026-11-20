# JSON 輸入格式

完整範例見 `data/sensor-demo.json`。Python 3.10+，安裝專案 requirements.txt。JSON UTF-8，欄位與字數由程式驗證。

| 欄位 | 型別與條件 | 用途 |
|---|---|---|
| title | 字串，1–28 字元 | 封面標題 |
| subtitle | 字串，1–64 字元 | 封面副標 |
| author | 字串，1–32 字元 | 示範作者 |
| theme.accent | 六位十六進位，例如 087F8C | 配色，可省略 theme |
| architecture | 恰好三個字串，各最多14字元 | 系統架構圖節點 |
| pipeline | 恰好四個字串，各最多12字元 | 處理流程節點 |
| samples | 2–12個物件 | 測試資料 |
| samples[].label | 不重複字串，最多12字元 | 測試點標籤 |
| samples[].reference | 有限數值，允許0，不允許布林值 | 參考溫度，°C |
| samples[].measured | 有限數值，允許0，不允許布林值 | 量測溫度，°C |
| conclusion | 1–3個字串，各最多40字元 | 最後一頁觀察與下一步 |

此範例固定處理溫度，單位為攝氏。資料須標示為教學模擬值，不作真實產品性能宣稱。平均絕對誤差 MAE 為每筆 `abs(measured-reference)` 的平均，最大絕對誤差取其中最大值。統計由 Python 計算，換資料時不手填結論數字。

六頁依序：封面、系統架構、處理流程、測試數據、誤差結果、結論。輸入只控制規格內的內容，增加額外 JSON 欄位不會自動新增功能。
