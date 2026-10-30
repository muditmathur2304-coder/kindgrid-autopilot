"""Unit tests for the fail-closed tool-first paid XLSX publishing gate.

These fixtures are synthetic ZIP/XML spreadsheets and never contact a seller.
"""
import io
import random
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from src.paired_release import validate_tool_xlsx


def workbook(*, count=12, art=True, sheets=2, external=False, macro=False,
             cycle=False, cross_sheet_cycle=False, cross_sheet_reference=False):
    """Produce an actual XLSX, not hand-written unreferenced ZIP members."""
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as XLImage

    book = Workbook()
    ws = book.active
    ws.title = "Inputs"
    for index in range(count):
        row = index + 1
        ws.cell(row=row, column=1, value=2)
        ws.cell(row=row, column=2, value=3)
        ws.cell(row=row, column=3, value=f"=A{row}+B{row}")
    for index in range(1, sheets):
        book.create_sheet(f"Scenario {index}")
    if cycle:
        ws["A1"] = "=C1"  # C1 = A1 + B1
    if cross_sheet_cycle or cross_sheet_reference:
        other = book["Scenario 1"]
        other["A1"] = "=Inputs!C1"
        if cross_sheet_cycle:
            ws["A1"] = "='Scenario 1'!A1"
    if art:
        picture = illustration_bytes()
        ws.add_image(XLImage(io.BytesIO(picture)), "E2")
    buf = io.BytesIO()
    book.save(buf)
    book.close()
    if external or macro or not art:
        with ZipFile(buf, "a", ZIP_DEFLATED) as archive:
            if external:
                archive.writestr("xl/externalLinks/externalLink1.xml", "<externalLink/>")
            if macro:
                archive.writestr("xl/vbaProject.bin", b"not-real-macro")
            if not art:
                archive.writestr("misc/filler", random.Random(4).randbytes(32000))
    return buf.getvalue()


def illustration_bytes():
    rng = random.Random(20261016)
    im = Image.frombytes("RGB", (600, 300), rng.randbytes(600 * 300 * 3))
    picture = io.BytesIO()
    im.save(picture, format="PNG")
    return picture.getvalue()


class ToolFirstXlsxTests(unittest.TestCase):
    def test_independent_valid_interactive_illustrated_file(self):
        validate_tool_xlsx(workbook(), "KG-TEST")

    def test_rejects_same_sheet_circular_pricing_dependency(self):
        with self.assertRaisesRegex(ValueError, "circular formula dependency"):
            validate_tool_xlsx(workbook(cycle=True), "KG-TEST")

    def test_rejects_cross_sheet_circular_dependency(self):
        with self.assertRaisesRegex(ValueError, "circular formula dependency"):
            validate_tool_xlsx(workbook(cross_sheet_cycle=True), "KG-TEST")

    def test_accepts_non_circular_cross_sheet_reference(self):
        validate_tool_xlsx(workbook(cross_sheet_reference=True), "KG-TEST")

    def test_rejects_pdf_instead_of_workbook(self):
        with self.assertRaisesRegex(ValueError, "size is implausible"):
            validate_tool_xlsx(b"%PDF-1.7" * 100, "KG-TEST")

    def test_rejects_corrupt_archive(self):
        with self.assertRaisesRegex(ValueError, "invalid Excel workbook"):
            validate_tool_xlsx(b"X" * 16000, "KG-TEST")

    def test_rejects_insufficient_formula_logic(self):
        with self.assertRaisesRegex(ValueError, "at least 10 formulas"):
            validate_tool_xlsx(workbook(count=2), "KG-TEST")

    def test_rejects_single_sheet_document(self):
        with self.assertRaisesRegex(ValueError, "multi-sheet"):
            validate_tool_xlsx(workbook(sheets=1), "KG-TEST")

    def test_rejects_no_embedded_instructional_visual(self):
        with self.assertRaisesRegex(ValueError, "no actual instructional image"):
            validate_tool_xlsx(workbook(art=False), "KG-TEST")

    def test_rejects_orphan_image_not_anchored_to_a_worksheet(self):
        """An image hidden in xl/media must not pass the owner interior-visual gate."""
        buf = io.BytesIO(workbook(art=False))
        with ZipFile(buf, "a", ZIP_DEFLATED) as archive:
            archive.writestr("xl/media/orphan.png", illustration_bytes())
        with self.assertRaisesRegex(ValueError, "actually embedded on a worksheet"):
            validate_tool_xlsx(buf.getvalue(), "KG-TEST")

    def test_rejects_unreferenced_formula_xml(self):
        """A fake extra XML file cannot inflate the actual cell-formula count."""
        buf = io.BytesIO(workbook(count=2))
        with ZipFile(buf, "a", ZIP_DEFLATED) as archive:
            archive.writestr("xl/worksheets/sheet999.xml",
                             "<worksheet>" + "<f>A1+B1</f>" * 30 + "</worksheet>")
        with self.assertRaisesRegex(ValueError, "at least 10 formulas"):
            validate_tool_xlsx(buf.getvalue(), "KG-TEST")

    def test_rejects_external_links(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(external=True), "KG-TEST")

    def test_rejects_macros(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(macro=True), "KG-TEST")


if __name__ == "__main__":
    unittest.main()
