"""Compile with XeLaTeX and retain the exact native A1 drawing page."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
from pypdf import PdfReader, PdfWriter

source = Path(__file__).resolve().parent
with TemporaryDirectory() as temp:
    for _ in range(2):
        subprocess.run(["xelatex", "-halt-on-error", "-interaction=batchmode",
                        "-output-directory=" + temp, "main.tex"], cwd=source, check=True)
    compiled = PdfReader(Path(temp) / "main.pdf")
    drawing = PdfReader(source / "figures/supply-plan.pdf")
    writer = PdfWriter()
    sheets = 0
    for page in compiled.pages:
        if page.mediabox.width > 2000 and page.mediabox.height > 1500:
            writer.add_page(drawing.pages[0])
            sheets += 1
        else:
            writer.add_page(page)
    if sheets != 1:
        raise ValueError("Expected one A1 drawing")
    writer.write(source / "BSE3227_HVAC_Design_Report.pdf")
