"""Render a plain-text resume into an ATS-friendly single-column PDF using fpdf2."""
import re

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from ..config import GENERATED_DIR

SECTION_RE = re.compile(r"^[A-Z][A-Z &/'\-]{2,}$")

NEW_LINE = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}


def _latin(s: str) -> str:
    return (s or "").encode("latin-1", "replace").decode("latin-1")


def text_to_pdf(text: str, out_path_pdf: str) -> str:
    pdf = FPDF(format="letter", unit="pt")
    pdf.set_margins(48, 48, 48)
    pdf.set_auto_page_break(auto=True, margin=48)
    pdf.add_page()
    pdf.set_text_color(20, 20, 20)

    for raw_line in text.splitlines():
        line = _latin(raw_line.rstrip())
        if not line.strip():
            pdf.ln(4)
            continue
        if SECTION_RE.match(line.strip()) and len(line.strip()) < 40:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11.5)
            pdf.multi_cell(0, 14, line.strip(), **NEW_LINE)
            pdf.set_draw_color(60, 60, 60)
            y = pdf.get_y()
            pdf.line(48, y + 1, pdf.w - 48, y + 1)
            pdf.set_y(y + 5)
            pdf.set_font("Helvetica", "", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 13, line, **NEW_LINE)

    pdf.output(out_path_pdf)
    return out_path_pdf


def pdf_path_for_job(job_id: int) -> str:
    return str(GENERATED_DIR / f"resume_job_{job_id}.pdf")
