"""投影片生成大師：JSON → 原生可編輯圖表、圖形與六頁 PowerPoint。

閱讀順序：main → validate → statistics → build → 各 add_* 函式。
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from lxml import etree
from pptx.oxml.ns import qn


SKILL_DIR = Path(__file__).resolve().parents[1]
FONT = "Microsoft JhengHei"
INK = "17324D"
MUTED = "536579"


def require_text(value, field, limit):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} 必須是非空字串")
    if len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f"{field} 限制 {limit} 字元，且不可包含換行或控制字元")
    return value


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("輸入必須是 JSON 物件")
    for key, limit in [("title", 28), ("subtitle", 64), ("author", 32)]:
        require_text(data[key], key, limit)
    for key, count, limit in [("architecture", 3, 14), ("pipeline", 4, 12)]:
        if not isinstance(data[key], list) or len(data[key]) != count:
            raise ValueError(f"{key} 必須恰有 {count} 個項目")
        for value in data[key]:
            require_text(value, key, limit)
    if not isinstance(data["conclusion"], list) or not 1 <= len(data["conclusion"]) <= 3:
        raise ValueError("conclusion 必須有 1 至 3 個項目")
    for value in data["conclusion"]:
        require_text(value, "conclusion", 40)
    samples = data["samples"]
    if not isinstance(samples, list) or not 2 <= len(samples) <= 12:
        raise ValueError("samples 必須有 2 至 12 筆")
    labels = set()
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError("每筆 sample 必須是物件")
        label = require_text(sample["label"], "sample.label", 12)
        if label in labels:
            raise ValueError(f"重複測試標籤：{label}")
        labels.add(label)
        for field in ("reference", "measured"):
            value = sample[field]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"{label}.{field} 必須是有限數值，不可為布林值")
    theme = data.get("theme", {})
    if not isinstance(theme, dict):
        raise ValueError("theme 必須是物件")
    accent = theme.get("accent", "087F8C")
    if not isinstance(accent, str) or not re.fullmatch(r"[0-9a-fA-F]{6}", accent):
        raise ValueError("theme.accent 必須是六位十六進位色碼，例如 087F8C")
    return data


def statistics(samples):
    errors = [abs(item["measured"] - item["reference"]) for item in samples]
    if not all(math.isfinite(value) for value in errors):
        raise ValueError("誤差超出可計算範圍")
    return {"sample_count": len(samples), "mae": math.fsum(e / len(errors) for e in errors),
            "max_error": max(errors), "errors": errors, "unit": "°C"}


def apply_font(paragraph, size=24, color=INK, bold=False):
    paragraph.font.name = FONT
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = RGBColor.from_string(color)
    for run in paragraph.runs:
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor.from_string(color)
        rpr = run._r.get_or_add_rPr()
        ea = rpr.find(qn("a:ea"))
        if ea is None:
            ea = etree.SubElement(rpr, qn("a:ea"))
        ea.set("typeface", FONT)


def text(slide, value, x, y, w, h, size=24, color=INK, bold=False, center=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(0.02)
    frame.margin_top = frame.margin_bottom = 0
    frame.text = value
    for paragraph in frame.paragraphs:
        apply_font(paragraph, size, color, bold)
        if center:
            paragraph.alignment = PP_ALIGN.CENTER
    return box


def new_slide(prs, title, index, accent):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
    text(slide, title, 0.7, 0.45, 11.8, 0.65, 30, bold=True)
    text(slide, f"{index:02d}", 12.0, 6.95, 0.6, 0.25, 11, accent)
    text(slide, "教學模擬資料", 0.72, 6.96, 4, 0.24, 11, MUTED)
    return slide


def add_cover(prs, data, hero, accent):
    slide = new_slide(prs, "", 1, accent)
    text(slide, data["title"], 0.8, 1.55, 5.55, 1.65, 36, bold=True)
    text(slide, data["subtitle"], 0.8, 3.5, 5.3, 1.1, 22, MUTED)
    text(slide, data["author"], 0.8, 5.45, 5.5, 0.55, 18, accent)
    # 配圖等比例縮入版位，不將整頁投影片做成圖片。
    picture = slide.shapes.add_picture(str(hero), Inches(6.4), Inches(1.5), width=Inches(6.3))
    if picture.height > Inches(4.6):
        factor = Inches(4.6) / picture.height
        picture.width = int(picture.width * factor)
        picture.height = Inches(4.6)
        picture.left = Inches(6.4) + (Inches(6.3) - picture.width) // 2
    slide.notes_slide.notes_text_frame.text = "圖片為AI生成的示意插畫，非真實設備或精確電路。數據均為教學模擬值。"


def diagram_node(slide, value, x, y, width, accent):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(x), Inches(y), Inches(width), Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string("F1F6F8")
    shape.line.color.rgb = RGBColor.from_string(accent)
    shape.text_frame.word_wrap = True
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    shape.text = value
    for paragraph in shape.text_frame.paragraphs:
        paragraph.alignment = PP_ALIGN.CENTER
        apply_font(paragraph, 22, INK, True)


def arrow(slide, x, y, accent):
    shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y), Inches(0.3), Inches(0.4))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(accent)
    shape.line.fill.background()


def add_architecture(prs, data, accent):
    slide = new_slide(prs, "系統架構", 2, accent)
    for index, value in enumerate(data["architecture"]):
        x = 0.8 + index * 4.03
        diagram_node(slide, value, x, 2.4, 3.55, accent)
        if index < 2:
            arrow(slide, x + 3.66, 2.8, accent)
    text(slide, "硬體與資料流示意", 0.8, 1.45, 10, 0.5, 22, accent)
    text(slide, "本範例以 JSON 提供模擬輸入，未直接連接感測器。",
         0.8, 4.5, 11.7, 0.85, 24, MUTED)
    slide.notes_slide.notes_text_frame.text = "節點由輸入的 architecture 提供，為原生可編輯形狀。硬體僅為示意。"


def add_pipeline(prs, data, accent):
    slide = new_slide(prs, "處理流程", 3, accent)
    for index, value in enumerate(data["pipeline"]):
        x = 0.8 + index * 3.17
        text(slide, f"{index+1:02d}", x, 1.8, 2.4, 0.5, 24, accent, True)
        diagram_node(slide, value, x, 2.5, 2.42, accent)
        if index < 3:
            arrow(slide, x + 2.65, 2.9, accent)
    text(slide, "同一套程式處理輸入、計算與投影片輸出。",
         0.8, 4.6, 11.7, 0.85, 24, MUTED)


def add_samples(prs, data, accent):
    slide = new_slide(prs, "測試數據", 4, accent)
    values = CategoryChartData()
    values.categories = [sample["label"] for sample in data["samples"]]
    values.add_series("參考溫度", [sample["reference"] for sample in data["samples"]])
    values.add_series("量測溫度", [sample["measured"] for sample in data["samples"]])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS,
                                  Inches(0.9), Inches(1.55), Inches(11.5), Inches(4.8), values).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.name = FONT
    chart.legend.font.size = Pt(14)
    chart.value_axis.has_title = True
    chart.value_axis.axis_title.text_frame.text = "溫度 (°C)"
    for paragraph in chart.value_axis.axis_title.text_frame.paragraphs:
        apply_font(paragraph, 16)
    chart.category_axis.tick_labels.font.name = FONT
    chart.category_axis.tick_labels.font.size = Pt(14)
    chart.value_axis.tick_labels.font.name = FONT
    chart.value_axis.tick_labels.font.size = Pt(14)
    for series, color in zip(chart.series, [accent, "D77A33"]):
        series.format.line.color.rgb = RGBColor.from_string(color)
        series.format.line.width = Pt(2.5)
    slide.notes_slide.notes_text_frame.text = "原始資料：本次 JSON 的 samples。數值為教學模擬值，圖表含原生數據，可在 PowerPoint 編輯資料。"


def add_results(prs, data, stats, accent):
    slide = new_slide(prs, "誤差分析結果", 5, accent)
    text(slide, "平均絕對誤差 MAE", 0.8, 1.6, 4, 0.5, 22, MUTED)
    text(slide, f'{stats["mae"]:.3f} °C', 0.8, 2.2, 4, 0.85, 36, accent, True)
    text(slide, "最大絕對誤差", 0.8, 3.3, 4, 0.5, 22, MUTED)
    text(slide, f'{stats["max_error"]:.3f} °C', 0.8, 3.9, 4, 0.85, 36, accent, True)
    text(slide, f'共 {stats["sample_count"]} 筆模擬測試值', 0.8, 5.25, 4.4, 0.6, 18, MUTED)
    table = slide.shapes.add_table(len(data["samples"]) + 1, 2,
                                   Inches(5.6), Inches(1.6), Inches(6.7), Inches(4.7)).table
    table.columns[0].width = Inches(2.7)
    table.columns[1].width = Inches(4.0)
    for row, values in enumerate([("測試點", "絕對誤差 (°C)")] +
                                 [(s["label"], f"{e:.3f}") for s, e in zip(data["samples"], stats["errors"])]):
        for col, value in enumerate(values):
            cell = table.cell(row, col)
            cell.text = value
            cell.margin_top = cell.margin_bottom = Pt(2)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(accent if row == 0 else "F1F6F8")
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for paragraph in cell.text_frame.paragraphs:
                apply_font(paragraph, 17, "FFFFFF" if row == 0 else INK, row == 0)
    slide.notes_slide.notes_text_frame.text = "每筆絕對誤差 = abs(measured-reference)。MAE為平均值；最大誤差為其中最大值。結果由程式計算，無產品性能推論。"


def add_conclusion(prs, data, accent):
    slide = new_slide(prs, "結論與重現", 6, accent)
    for index, value in enumerate(data["conclusion"]):
        text(slide, f"{index+1:02d}", 0.8, 1.65 + index * 1.2, 0.7, 0.5, 24, accent, True)
        text(slide, value, 1.75, 1.65 + index * 1.2, 10.6, 0.95, 25)
    text(slide, "資料與版型由同一套 Skill 重複產生", 0.8, 5.9, 11.5, 0.55, 20, MUTED)


def build(data, out, hero):
    validate(data)
    if not hero.is_file():
        raise ValueError(f"找不到配圖：{hero}")
    stats = statistics(data["samples"])
    accent = data.get("theme", {}).get("accent", "087F8C").upper()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    prs.core_properties.title = data["title"]
    prs.core_properties.author = data["author"]
    add_cover(prs, data, hero, accent)
    add_architecture(prs, data, accent)
    add_pipeline(prs, data, accent)
    add_samples(prs, data, accent)
    add_results(prs, data, stats, accent)
    add_conclusion(prs, data, accent)
    out.mkdir(parents=True, exist_ok=True)
    # 先完成暫存檔，再替換成果，避免建置中途失敗破壞既有簡報。
    temporary = out / ".slides.tmp.pptx"
    prs.save(str(temporary))
    temporary.replace(out / "slides.pptx")
    report = {"title": data["title"], "slide_count": len(prs.slides), "accent": accent,
              "simulated_data": True, "statistics": stats, "outputs": ["slides.pptx", "report.json"]}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="從 JSON 製作六頁可編輯 PowerPoint")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--hero", type=Path, default=SKILL_DIR / "assets/sensor-hero.png")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = build(data, args.out, args.hero)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"產生失敗：{error}", file=sys.stderr)
        return 2
    print(json.dumps({"out": str(args.out.resolve()), **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
