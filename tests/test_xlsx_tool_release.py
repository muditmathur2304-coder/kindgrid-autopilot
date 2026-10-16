"""Unit tests for the fail-closed tool-first paid XLSX publishing gate.

These fixtures are synthetic ZIP/XML spreadsheets and never contact a seller.
"""
import io
import random
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from src.paired_release import validate_tool_xlsx


def workbook(*, count=12, art=True, sheets=2, external=False, macro=False):
    buf = io.BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", "<workbook/>")
        for i in range(1, sheets + 1):
            formulas = "<f>A1+B1</f>" * count if i == 1 else "<f>C3*2</f>"
            archive.writestr(f"xl/worksheets/sheet{i}.xml",
                             "<worksheet><sheetData>" + formulas + "</sheetData></worksheet>")
        if art:
            rng = random.Random(20261016)
            im = Image.frombytes("RGB", (600, 300), rng.randbytes(600 * 300 * 3))
            picture = io.BytesIO()
            im.save(picture, format="PNG")
            archive.writestr("xl/media/calculation-guide.png", picture.getvalue())
        else:
            # Ensure the failing fixture is large enough to pass the file-size gate.
            archive.writestr("misc/filler", random.Random(4).randbytes(32000))
        if external:
            archive.writestr("xl/externalLinks/externalLink1.xml", "<externalLink/>")
        if macro:
            archive.writestr("xl/vbaProject.bin", b"not-real-macro")
    return buf.getvalue()


class ToolFirstXlsxTests(unittest.TestCase):
    def test_independent_valid_interactive_illustrated_file(self):
        validate_tool_xlsx(workbook(), "KG-TEST")

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

    def test_rejects_external_links(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(external=True), "KG-TEST")

    def test_rejects_macros(self):
        with self.assertRaisesRegex(ValueError, "macros and external links"):
            validate_tool_xlsx(workbook(macro=True), "KG-TEST")


if __name__ == "__main__":
    unittest.main()
