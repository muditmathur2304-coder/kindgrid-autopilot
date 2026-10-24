"""Offline release-gate tests. No Gumroad, Buffer, or Drive mutations.

Fixtures include genuinely openable XLSX files, not only ZIP/XML impostors.
These tests do not replace item-specific 12+ business calculation edge cases.
"""
import io
import random
import unittest
import warnings
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage

from src.paired_release import validate_tool_xlsx


def workbook(*, count=12, art=True, sheets=2, external=False, macro=False,
             detached=False, tiny_art=False, text_only=False, duplicate=False):
    """Create a real XLSX, optionally corrupting one release requirement."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Calculator"
    for i in range(1, count + 1):
        ws.cell(i, 1, i)
        ws.cell(i, 2, i + 1)
        ws.cell(i, 3, "<f>A1+B1</f>" if text_only else f"=A{i}+B{i}")
    if sheets > 1:
        wb.create_sheet("Instructions")
    rng = random.Random(20261016)
    dimensions = (100, 100) if tiny_art else (600, 300)
    im = Image.frombytes("RGB", dimensions,
                         rng.randbytes(dimensions[0] * dimensions[1] * 3))
    picture = io.BytesIO()
    im.save(picture, format="PNG")
    if art and not detached:
        picture.seek(0)
        ws.add_image(XLImage(picture), "E1")
    out = io.BytesIO()
    wb.save(out)
    if not art or external or macro or detached or duplicate:
        with ZipFile(out, "a", ZIP_DEFLATED) as archive:
            if not art:
                archive.writestr("misc/filler", random.Random(4).randbytes(32000))
            if detached:
                archive.writestr("xl/media/unattached.png", picture.getvalue())
            if external:
                archive.writestr("xl/externalLinks/externalLink1.xml", "<externalLink/>")
            if macro:
                archive.writestr("xl/vbaProject.bin", b"not-real-macro")
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("xl/workbook.xml", "<workbook/>")
    return out.getvalue()


def fake_zip_with_unattached_image_and_xml_formula_tags():
    """Old release gate accepted this ZIP, although Excel cannot open it."""
    out = io.BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", "<workbook/>")
        for i in (1, 2):
            archive.writestr(f"xl/worksheets/sheet{i}.xml",
                             "<worksheet>" + "<f>A1+B1</f>" * 12 + "</worksheet>")
        rng = random.Random(20261016)
        picture = io.BytesIO()
        Image.frombytes("RGB", (600, 300),
                        rng.randbytes(600 * 300 * 3)).save(picture, format="PNG")
        archive.writestr("xl/media/guide.png", picture.getvalue())
    return out.getvalue()


class ToolFirstXlsxTests(unittest.TestCase):
    def test_accepts_real_interactive_illustrated_workbook(self):
        validate_tool_xlsx(workbook(), "KG-TEST")

    def test_rejects_fake_zip_that_old_gate_accepted(self):
        with self.assertRaisesRegex(ValueError, "invalid Excel workbook structure"):
            validate_tool_xlsx(fake_zip_with_unattached_image_and_xml_formula_tags(),
                               "KG-TEST")

    def test_rejects_pdf_instead_of_workbook(self):
        with self.assertRaisesRegex(ValueError, "size is implausible"):
            validate_tool_xlsx(b"%PDF-1.7" * 100, "KG-TEST")

    def test_rejects_corrupt_archive(self):
        with self.assertRaisesRegex(ValueError, "invalid Excel workbook archive"):
            validate_tool_xlsx(b"X" * 16000, "KG-TEST")

    def test_rejects_insufficient_formula_logic(self):
        with self.assertRaisesRegex(ValueError, "at least 10 formulas"):
            validate_tool_xlsx(workbook(count=2), "KG-TEST")

    def test_rejects_formula_markup_stored_as_plain_text(self):
        with self.assertRaisesRegex(ValueError, "at least 10 formulas"):
            validate_tool_xlsx(workbook(text_only=True), "KG-TEST")

    def test_rejects_single_sheet_document(self):
        with self.assertRaisesRegex(ValueError, "multi-sheet"):
            validate_tool_xlsx(workbook(sheets=1), "KG-TEST")

    def test_rejects_no_attached_instructional_visual(self):
        with self.assertRaisesRegex(ValueError, "attached instructional"):
            validate_tool_xlsx(workbook(art=False), "KG-TEST")

    def test_rejects_detached_media_file(self):
        with self.assertRaisesRegex(ValueError, "attached instructional"):
            validate_tool_xlsx(workbook(detached=True), "KG-TEST")

    def test_rejects_tiny_embedded_image(self):
        with self.assertRaisesRegex(ValueError, "attached instructional"):
            validate_tool_xlsx(workbook(tiny_art=True), "KG-TEST")

    def test_rejects_external_links(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(external=True), "KG-TEST")

    def test_rejects_macros(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(macro=True), "KG-TEST")

    def test_rejects_duplicate_zip_members(self):
        with self.assertRaisesRegex(ValueError, "duplicate XLSX archive members"):
            validate_tool_xlsx(workbook(duplicate=True), "KG-TEST")


if __name__ == "__main__":
    unittest.main()
