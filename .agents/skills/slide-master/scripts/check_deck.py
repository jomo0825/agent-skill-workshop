"""Verify full-bleed picture structure, not the text drawn inside pictures."""
import argparse
import hashlib
import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def check(deck, manifest=None, images=None):
    prs = Presentation(str(deck))
    failures = []
    if not prs.slides:
        failures.append("No slides")
    if abs(prs.slide_width / prs.slide_height - 16 / 9) > 0.001:
        failures.append("Deck is not 16:9")
    if manifest is not None:
        data = json.loads(Path(manifest).read_text(encoding="utf-8"))
        if len(prs.slides) != data["slide_count"]:
            failures.append("Slide count differs from source manifest")
    for index, slide in enumerate(prs.slides, 1):
        if len(slide.shapes) != 1 or slide.shapes[0].shape_type != MSO_SHAPE_TYPE.PICTURE:
            failures.append(f"Slide {index}: expected exactly one picture and no other objects")
            continue
        shape = slide.shapes[0]
        if (shape.left, shape.top, shape.width, shape.height) != (0, 0, prs.slide_width, prs.slide_height):
            failures.append(f"Slide {index}: picture is not full bleed")
        if any((shape.crop_left, shape.crop_right, shape.crop_top, shape.crop_bottom)):
            failures.append(f"Slide {index}: picture is cropped")
        if abs(shape.image.size[0] / shape.image.size[1] - 16 / 9) > 0.01:
            failures.append(f"Slide {index}: picture aspect ratio is not 16:9")
        if any(rel.reltype.endswith('/hyperlink') for rel in slide.part.rels.values()):
            failures.append(f"Slide {index}: unexpected clickable hyperlink")
        if images is not None:
            expected = Path(images) / f"slide-{index:02d}.png"
            if not expected.is_file() or hashlib.sha256(expected.read_bytes()).digest() != hashlib.sha256(shape.image.blob).digest():
                failures.append(f"Slide {index}: embedded image differs from supplied PNG")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--images", type=Path)
    args = parser.parse_args()
    failures = check(args.deck, args.manifest, args.images)
    if failures:
        parser.exit(1, "FULL-BLEED DECK: FAIL\n" + "\n".join(failures) + "\n")
    print("FULL-BLEED DECK: PASS (structure only; visually verify all copy)")


if __name__ == "__main__":
    main()
