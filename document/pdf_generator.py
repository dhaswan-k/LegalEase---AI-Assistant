"""PDF export using fpdf2 (core Times font, latin-1 safe)."""

import os
import re

from fpdf import FPDF

from document.formatter import (
    DISCLAIMER,
    FOOTER_TEXT,
    classify_line,
    sanitize_text,
    split_terms,
    strip_markdown,
    to_latin1,
)

_WITNESS_RE = re.compile(r"IN WITNESS|SIGNATURE", re.I)


class _LegalPDF(FPDF):
    def __init__(self, title, logo_path=None):
        super().__init__(format="A4", unit="mm")
        self.doc_title = to_latin1(title)
        self.logo_path = logo_path if (logo_path and os.path.isfile(logo_path)) else None
        self.set_margins(22, 22, 22)
        self.set_auto_page_break(auto=True, margin=22)
        self.alias_nb_pages()

    def header(self):
        if self.logo_path:
            try:
                self.image(self.logo_path, x=(self.w - 22) / 2, y=8, w=22)
                self.set_y(8 + 22 + 2)
                return
            except Exception:
                pass
        self.set_font("Times", "B", 10)
        self.set_text_color(20, 40, 75)
        self.cell(0, 8, "LegalEase AI", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_font("Times", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"{FOOTER_TEXT}  |  Page {self.page_no()} of {{nb}}", align="C")
        self.set_text_color(0, 0, 0)


def _para(pdf, text, size=11, style="", indent=0.0, align="J", after=2.5, color=(0, 0, 0)):
    pdf.set_x(pdf.l_margin + indent)
    pdf.set_font("Times", style, size)
    pdf.set_text_color(*color)
    width = pdf.w - pdf.r_margin - pdf.get_x()
    pdf.multi_cell(width, 5.8, to_latin1(text), align=align, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(after)
    pdf.set_text_color(0, 0, 0)


def _render_lines(pdf, lines, title_done):
    for raw in lines:
        kind = classify_line(raw)
        if kind == "blank":
            continue
        text = strip_markdown(raw)
        if kind == "heading" and not title_done:
            _para(pdf, text.upper(), 16, "B", align="C", after=5, color=(20, 40, 75))
            title_done = True
        elif kind == "heading":
            pdf.ln(2)
            if pdf.get_y() > pdf.h - 45:
                pdf.add_page()
            _para(pdf, text, 12, "B", align="L", after=1.5)
        elif kind in ("sub", "bullet"):
            if kind == "bullet":
                text = "- " + re.sub(r"^[-*]\s+", "", text)
            _para(pdf, text, 11, "", indent=8)
        else:
            title_done = True
            _para(pdf, text, 11, "")
    return title_done


def _terms_table(pdf, terms):
    items = split_terms(terms)
    if not items:
        return
    if pdf.get_y() > pdf.h - 60:
        pdf.add_page()
    pdf.ln(3)
    _para(pdf, "Schedule A: Summary of Agreed Terms", 12, "B", align="L", after=2, color=(20, 40, 75))
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    w_no, w_t = 14, usable - 14
    pdf.set_font("Times", "B", 11)
    pdf.set_fill_color(20, 40, 75)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w_no, 8, "No.", border=1, align="C", fill=True)
    pdf.cell(w_t, 8, "Terms & Conditions", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", "", 11)
    for i, item in enumerate(items, 1):
        item = to_latin1(sanitize_text(item))
        lines = pdf.multi_cell(w_t, 6.5, item, dry_run=True, output="LINES")
        h = max(8, 6.5 * len(lines) + 2)
        if pdf.get_y() + h > pdf.h - 24:
            pdf.add_page()
        x, y = pdf.l_margin, pdf.get_y()
        pdf.rect(x, y, w_no, h)
        pdf.rect(x + w_no, y, w_t, h)
        pdf.set_xy(x, y + 1)
        pdf.cell(w_no, h - 2, str(i), align="C")
        pdf.set_xy(x + w_no + 1, y + 1)
        pdf.multi_cell(w_t - 2, 6.5, item, align="L")
        pdf.set_xy(x, y + h)
    pdf.ln(5)


def format_pdf(text, doc_type, terms=None, logo_path=None) -> bytes:
    """Build a PDF and return its bytes."""
    text = sanitize_text(text)
    pdf = _LegalPDF(doc_type or "Legal Document", logo_path)
    pdf.set_title(to_latin1(doc_type or "Legal Document"))
    pdf.set_author("LegalEase AI")
    pdf.add_page()

    lines = text.split("\n")
    split_idx = None
    if split_terms(terms):
        for i in range(len(lines) - 1, -1, -1):
            if _WITNESS_RE.search(lines[i]):
                split_idx = i
                break
    if split_idx is not None:
        done = _render_lines(pdf, lines[:split_idx], False)
        _terms_table(pdf, terms)
        _render_lines(pdf, lines[split_idx:], done)
    else:
        _render_lines(pdf, lines, False)
        _terms_table(pdf, terms)

    pdf.ln(4)
    _para(pdf, DISCLAIMER, 8.5, "I", align="L", color=(100, 100, 100))
    return bytes(pdf.output())
