import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/slide-master/scripts'))
sys.path.insert(0, str(ROOT / 'examples'))
from assemble_deck import assemble
from check_deck import check
from extract_deck import extract
from create_vanilla import create, PAGES


class DeckToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'vanilla.pptx'
        self.manifest = self.root / 'source.json'
        self.images = self.root / 'images'
        self.images.mkdir()
        self.output = self.root / 'result.pptx'
        create(self.source)
        extract(self.source, self.manifest)
        for index in range(1, 5):
            # Synthetic test fixtures only; not a substitute for imagegen artwork.
            Image.new('RGB', (1280, 720), (index * 40, 20, 30)).save(self.images / f'slide-{index:02d}.png')

    def test_extract_preserves_text_order_and_nonvisible_notes(self):
        data = json.loads(self.manifest.read_text(encoding='utf-8'))
        self.assertEqual(data['slide_count'], 4)
        for page, (lines, notes) in zip(data['slides'], PAGES):
            self.assertEqual(page['visible_text'], lines)
            self.assertEqual(page['notes'], notes)
            self.assertNotIn(notes, page['visible_text'])

    def test_round_trip_preserves_picture_bytes_and_order(self):
        assemble(self.manifest, self.images, self.output)
        self.assertEqual(check(self.output, self.manifest, self.images), [])
        prs = Presentation(str(self.output))
        for index, slide in enumerate(prs.slides, 1):
            self.assertEqual(slide.shapes[0].image.blob, (self.images / f'slide-{index:02d}.png').read_bytes())

    def test_rejects_missing_or_extra_pages(self):
        Image.new('RGB', (1280, 720)).save(self.images / 'slide-05.png')
        with self.assertRaisesRegex(ValueError, 'count exactly'):
            assemble(self.manifest, self.images, self.output)
        (self.images / 'slide-05.png').unlink()
        (self.images / 'slide-02.png').unlink()
        with self.assertRaisesRegex(ValueError, 'count exactly'):
            assemble(self.manifest, self.images, self.output)

    def test_rejects_non_widescreen_picture(self):
        Image.new('RGB', (1280, 1280)).save(self.images / 'slide-02.png')
        with self.assertRaisesRegex(ValueError, '16:9'):
            assemble(self.manifest, self.images, self.output)

    def test_rejects_changed_source_and_existing_output(self):
        assemble(self.manifest, self.images, self.output)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            assemble(self.manifest, self.images, self.output)
        self.source.write_bytes(self.source.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'changed since extraction'):
            assemble(self.manifest, self.images, self.root / 'new.pptx')

    def test_checker_detects_text_overlay_and_geometry_errors(self):
        assemble(self.manifest, self.images, self.output)
        prs = Presentation(str(self.output))
        prs.slides[0].shapes.add_textbox(0, 0, Inches(2), Inches(1)).text = 'overlay'
        prs.slides[1].shapes[0].left = Inches(1)
        prs.save(str(self.output))
        failures = check(self.output, self.manifest, self.images)
        self.assertTrue(any('exactly one picture' in f for f in failures))
        self.assertTrue(any('not full bleed' in f for f in failures))

    def test_checker_detects_replaced_image(self):
        assemble(self.manifest, self.images, self.output)
        Image.new('RGB', (1280, 720), 'white').save(self.images / 'slide-01.png')
        self.assertTrue(any('differs' in f for f in check(self.output, self.manifest, self.images)))

    def test_extract_preserves_embedded_media(self):
        prs = Presentation(str(self.source))
        image_path = self.images / 'slide-01.png'
        prs.slides[0].shapes.add_picture(str(image_path), 0, Inches(6), width=Inches(1))
        prs.save(str(self.source))
        other = self.root / 'with-media.json'
        data = extract(self.source, other)
        media = self.root / data['slides'][0]['media'][0]['path']
        self.assertEqual(media.read_bytes(), image_path.read_bytes())


if __name__ == '__main__':
    unittest.main()
