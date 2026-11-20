"""Assemble reviewed PNG pages into an image-only PowerPoint; no AI calls."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw
from pptx import Presentation
from pptx.util import Inches

from check_deck import check


def assemble(manifest, images, output):
    manifest, images, output = Path(manifest).resolve(), Path(images).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError(f"Output already exists: {output}; choose a new filename")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    count = data["slide_count"]
    if not isinstance(count, int) or count < 1 or count != len(data["slides"]):
        raise ValueError("Invalid manifest slide count")
    source = (manifest.parent / data["source"]).resolve()
    if source == output:
        raise ValueError("Cannot overwrite source")
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != data["source_sha256"]:
        raise ValueError("Source is missing or changed since extraction; extract it again")
    expected = [images / f"slide-{index:02d}.png" for index in range(1, count + 1)]
    if set(images.glob("slide-*.png")) != set(expected):
        raise ValueError("Image pages must match source count exactly: slide-01.png, slide-02.png, ...")
    for path in expected:
        with Image.open(path) as image:
            if image.format != "PNG" or abs(image.width / image.height - 16 / 9) > 0.01:
                raise ValueError(f"Expected a 16:9 PNG: {path.name}")
            if image.width < 1280 or image.height < 720:
                raise ValueError(f"Image is too small (minimum 1280x720): {path.name}")
            image.verify()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    for path in expected:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_picture(str(path), 0, 0, width=prs.slide_width, height=prs.slide_height)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    failures = check(output, manifest, images)
    if failures:
        raise ValueError("Saved deck failed structure check: " + "; ".join(failures))
    # Contact sheet is a viewing aid made from the final pages, not AI artwork.
    sheet = Image.new("RGB", (1008, ((count + 1) // 2) * 310), "#e7ebf0")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(expected):
        x, y = (index % 2) * 504 + 12, (index // 2) * 310 + 25
        with Image.open(path) as image:
            thumb = ImageOps.contain(image.convert("RGB"), (480, 270))
            sheet.paste(thumb, (x, y))
        draw.text((x, y - 18), f"Slide {index + 1:02d}", fill="#172342")
    sheet.save(output.with_name(output.stem + "-overview.png"))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = assemble(args.manifest, args.images, args.output)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"Saved {result}; structural check passed. Review image text separately.")


if __name__ == "__main__":
    main()
