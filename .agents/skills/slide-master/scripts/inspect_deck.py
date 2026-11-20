"""檢查實際 PPTX 與來源資料，與視覺檢查互補。"""

import argparse
import json
import math
import sys
from pathlib import Path

from pptx import Presentation
from build_deck import validate, statistics


def inspect(pptx, data):
    validate(data)
    prs = Presentation(str(pptx))
    issues = []
    if len(prs.slides) != 6:
        issues.append("頁數應為六頁")
    charts, tables, texts = [], [], []
    for index, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.left < 0 or shape.top < 0 or shape.left + shape.width > prs.slide_width + 100:
                issues.append(f"第{index}頁有物件超出左右邊界")
            if shape.top + shape.height > prs.slide_height + 100:
                issues.append(f"第{index}頁有物件超出下方邊界")
            if shape.has_text_frame:
                texts.append(shape.text)
            if shape.has_chart:
                charts.append(shape.chart)
            if shape.has_table:
                tables.append(shape.table)
                texts.extend(cell.text for row in shape.table.rows for cell in row.cells)
    if len(charts) != 1:
        issues.append("應包含一個原生可編輯圖表")
    else:
        chart = charts[0]
        if [category.label for category in chart.plots[0].categories] != [s["label"] for s in data["samples"]]:
            issues.append("圖表分類標籤與輸入不同")
        if len(chart.series) != 2:
            issues.append("應有兩組數列")
        else:
            for series, key in zip(chart.series, ("reference", "measured")):
                actual = list(series.values)
                expected = [s[key] for s in data["samples"]]
                if len(actual) != len(expected) or not all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10) for a, b in zip(actual, expected)):
                    issues.append(f"圖表 {key} 數據與輸入不同")
    if len(tables) != 1 or len(tables[0].rows) != len(data["samples"]) + 1:
        issues.append("誤差表格列數不正確")
    else:
        expected_errors = statistics(data["samples"])["errors"]
        for row_index, (sample, error) in enumerate(zip(data["samples"], expected_errors), 1):
            if tables[0].cell(row_index, 0).text != sample["label"] or tables[0].cell(row_index, 1).text != f"{error:.3f}":
                issues.append(f"誤差表格第{row_index}筆與輸入不同")
    combined = "\n".join(texts)
    stats = statistics(data["samples"])
    for required in [data["title"], f'{stats["mae"]:.3f} °C', f'{stats["max_error"]:.3f} °C',
                     *data["architecture"], *data["pipeline"], *data["conclusion"]]:
        if required not in combined:
            issues.append(f"缺少必要文字：{required}")
    return {"ok": not issues, "slide_count": len(prs.slides), "native_charts": len(charts),
            "native_tables": len(tables), "issues": issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description="核對實際PPTX與JSON資料")
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.pptx, json.loads(args.input.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"檢查失敗：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
