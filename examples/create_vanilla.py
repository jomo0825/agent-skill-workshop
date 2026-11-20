"""Create the editable four-page source used by the workshop."""
import argparse
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt


PAGES = [
    (["投影片生成大師", "從香草版到視覺設計", "Agent Skill 技術實作"], "深色封面。左側標題，右側以稜鏡呈現原稿轉換為設計稿。"),
    (["一個 Skill，三種資源", "scripts：處理檔案", "assets：提供視覺素材", "references：保存設計規則"], "白底概念頁。以三個不同意象呈現三種資源。"),
    (["從原稿到成品", "讀取原稿", "選擇風格", "逐頁生成", "組裝與檢查"], "白底流程頁。四個步驟由左到右，箭頭連接。"),
    (["內容保留，設計升級", "香草版", "標題與文字", "設計版", "圖像與版面", "保留原文與頁序"], "比較頁。以深淺對照原稿與設計稿，下方強調保留原文與頁序。"),
]


def create(output):
    output = Path(output)
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    for lines, notes in PAGES:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        for index, line in enumerate(lines):
            box = slide.shapes.add_textbox(Inches(.7), Inches(.7 + index * .9), Inches(12), Inches(.8))
            p = box.text_frame.paragraphs[0]
            p.text = line
            p.font.name, p.font.size, p.font.bold = "Microsoft JhengHei", Pt(36 if index == 0 else 25), index == 0
        slide.notes_slide.notes_text_frame.text = notes
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    create(args.output)
