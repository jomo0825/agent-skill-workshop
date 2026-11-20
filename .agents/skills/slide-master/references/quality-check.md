# 品質檢查

## 生成後逐頁人工核對

- 對照原稿／內容記錄檢查所有文字、標點、數字與頁序。
- 確認備註沒有成為可見文案，參考圖文字沒有混進成品。
- 原始截圖與事實圖表正確，流程方向清楚，沒有遺漏或重複。
- 全尺寸與投影大小均可閱讀，無裁字、假字、糊字及不必要裝飾。
- 中文 OCR 只能輔助，不能取代實際檢視。

## 組裝後結構檢查

```sh
python .agents/skills/slide-master/scripts/check_deck.py output/redesigned.pptx --manifest output/work/source.json --images output/work/images
```

驗證 16:9、頁數、每頁恰一張圖片、滿版位置、沒有裁切或連結，以及嵌入圖片是否與核對後的 PNG 相同。**通過只證明檔案結構，不證明圖片中的中文字正確。**

## 渲染檢視

用 PowerPoint 或 LibreOffice 開啟最終 PPTX，逐頁檢查。若已安裝 LibreOffice，可在儲存庫根目錄執行：

```sh
soffice --headless --convert-to pdf --outdir output output/redesigned.pptx
```

不同系統可能須用完整執行檔路徑。確認匯出 PDF 頁數、比例、畫面與已核對 PNG 一致，再看總覽確認整份風格連貫。若無法渲染，交付時明確說明尚未完成此步。
