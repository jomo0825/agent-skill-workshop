"""Extract a PPTX into a portable page ledger. This does not render the slides."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def extract(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError(f"Output already exists: {destination}")
    prs = Presentation(str(source))
    if not prs.slides:
        raise ValueError("Source has no slides")
    if abs(prs.slide_width / prs.slide_height - 16 / 9) > 0.01:
        raise ValueError("This workshop expects a 16:9 source deck")
    media_dir = destination.parent / f"{destination.stem}-media"
    if media_dir.exists():
        raise ValueError(f"Media directory already exists: {media_dir}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    pages = []

    def visit(shapes, page, prefix):
        for number, shape in enumerate(sorted(shapes, key=lambda s: (s.top, s.left)), 1):
            key = f"{prefix}-{number}"
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                visit(shape.shapes, page, key)
            elif shape.has_text_frame:
                if shape.text.strip():
                    page["visible_text"].append(shape.text)
            elif shape.has_table:
                page["tables"].append([[cell.text for cell in row.cells] for row in shape.table.rows])
                page["visible_text"].extend("\t".join(cell.text for cell in row.cells) for row in shape.table.rows)
                page["review_required"].append(f"{key}: table layout requires visual review")
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                media_dir.mkdir(exist_ok=True)
                image_path = media_dir / f"{key}.{shape.image.ext}"
                image_path.write_bytes(shape.image.blob)
                page["media"].append({"path": image_path.relative_to(destination.parent).as_posix(),
                                      "sha256": hashlib.sha256(shape.image.blob).hexdigest()})
            else:
                page["review_required"].append(f"{key}: {shape.shape_type}, inspect original render")

    for index, slide in enumerate(prs.slides, 1):
        page = {"number": index, "visible_text": [], "notes": "", "media": [],
                "tables": [], "review_required": []}
        visit(slide.shapes, page, f"slide-{index:02d}")
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            page["notes"] = slide.notes_slide.notes_text_frame.text
        if slide._element.get("show") == "0":
            page["review_required"].append("Hidden source slide: confirm intended inclusion")
        pages.append(page)
    manifest = {"schema_version": 1,
                "source": os.path.relpath(source, destination.parent).replace(os.sep, "/"),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "slide_count": len(pages), "slides": pages,
                "extraction_notice": "Approximate reading order; inspect original slides including master/background content."}
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = extract(args.source, args.manifest)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"Extracted {result['slide_count']} slides to {args.manifest}")
    warnings = sum(len(page["review_required"]) for page in result["slides"])
    if warnings:
        print(f"REVIEW REQUIRED: {warnings} item(s). Inspect source.json and original slides.")


if __name__ == "__main__":
    main()
