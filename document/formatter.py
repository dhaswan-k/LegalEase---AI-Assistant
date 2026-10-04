"""Text sanitisation, parsing helpers, and HTML preview for LegalEase."""

import html
import re
import unicodedata
from datetime import date

DISCLAIMER = (
    "AI-generated draft for informational and drafting assistance only. "
    "Review by a qualified legal professional is recommended before use."
)
LONG_DISCLAIMER = (
    "LegalEase AI provides AI-assisted legal drafting for informational and drafting purposes. "
    "Generated documents should be reviewed by a qualified legal professional before signing or use."
)
FOOTER_TEXT = "Generated with LegalEase AI"

_REPLACEMENTS = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "–": "-", "—": "-", "−": "-",
    "…": "...", " ": " ", "•": "-", " ": " ", " ": " ",
    "​": "", "﻿": "", "‎": "", "‏": "",
}


def sanitize_text(text) -> str:
    """Normalise typography and whitespace without altering legal meaning."""
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    text = str(text)
    text = unicodedata.normalize("NFC", text)
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    # drop control chars except newline/tab
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)  # stray code fences
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_markdown(line: str) -> str:
    line = re.sub(r"^#{1,6}\s*", "", line)
    line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    line = re.sub(r"__(.+?)__", r"\1", line)
    line = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", line)
    return line.strip()


_SECTION_RE = re.compile(r"^(\d+(\.\d+)*[.)]|ARTICLE\s+\w+|SECTION\s+\w+|[IVX]+\.)\s+\S", re.I)


def classify_line(raw: str) -> str:
    """Return one of: blank, heading, sub, bullet, para."""
    line = raw.strip()
    if not line:
        return "blank"
    if line.startswith("#"):
        return "heading"
    clean = strip_markdown(line)
    if re.match(r"^\d+\.\d+", clean) or re.match(r"^\(?[a-z]\)\s", clean) or re.match(r"^\([ivx]+\)\s", clean, re.I):
        return "sub"
    if re.match(r"^[-*]\s+", clean):
        return "bullet"
    if re.match(r"^\d+[.)]\s+\S", clean) and len(clean) < 90:
        return "heading"
    if line.startswith("**") and line.endswith("**") and len(clean) < 90:
        return "heading"
    letters = [c for c in clean if c.isalpha()]
    if letters and clean.upper() == clean and len(clean) < 80 and len(letters) > 3:
        return "heading"
    if clean.endswith(":") and len(clean) < 70:
        return "heading"
    return "para"


def split_terms(terms) -> list:
    if not terms:
        return []
    parts = re.split(r";|\n", str(terms))
    return [p.strip(" \t-*•.") for p in parts if p.strip(" \t-*•.")]


def safe_filename(doc_type: str, ext: str, on: str = None) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", doc_type or "Document").strip("_") or "Document"
    stamp = on or date.today().isoformat()
    stamp = re.sub(r"[^0-9A-Za-z-]", "", stamp)
    return f"LegalEase_{base}_{stamp}.{ext.lstrip('.')}"


def to_latin1(text: str) -> str:
    """Make text safe for FPDF core fonts (latin-1)."""
    text = text.replace("₹", "Rs. ").replace("€", "EUR ").replace("£", "GBP ")
    return text.encode("latin-1", errors="replace").decode("latin-1")


def format_html_preview(text: str) -> str:
    """Return escaped, styled HTML in a scrollable container. Safe to embed with unsafe_allow_html."""
    text = sanitize_text(text)
    blocks = []
    first_heading = True
    for raw in text.split("\n"):
        kind = classify_line(raw)
        if kind == "blank":
            continue
        content = html.escape(strip_markdown(raw))
        if kind == "heading":
            if first_heading:
                blocks.append(f'<h1 class="le-title">{content}</h1>')
                first_heading = False
            else:
                blocks.append(f'<h3 class="le-h">{content}</h3>')
        elif kind == "sub":
            blocks.append(f'<p class="le-sub">{content}</p>')
        elif kind == "bullet":
            bullet_text = html.escape(re.sub(r"^[-*]\s+", "", strip_markdown(raw)))
            blocks.append(f'<p class="le-sub">&bull; {bullet_text}</p>')
        else:
            if first_heading:
                first_heading = False
            blocks.append(f'<p class="le-p">{content}</p>')
    css = (
        "<style>"
        ".le-doc{background:#fff;color:#1b1f2a;border:1px solid #d5d9e2;border-radius:8px;padding:32px 40px;"
        "max-height:520px;overflow-y:auto;font-family:'Times New Roman',Georgia,serif;line-height:1.6;"
        "box-shadow:0 2px 8px rgba(20,30,60,.08)}"
        ".le-title{text-align:center;font-size:22px;margin:0 0 18px;color:#14284b;text-transform:uppercase;letter-spacing:.5px}"
        ".le-h{font-size:16px;margin:20px 0 6px;color:#14284b}"
        ".le-p{margin:0 0 10px;text-align:justify;font-size:15px}"
        ".le-sub{margin:0 0 8px 24px;text-align:justify;font-size:15px}"
        ".le-note{margin-top:22px;padding-top:10px;border-top:1px solid #e1e4ec;font-size:12px;color:#667}"
        "</style>"
    )
    note = f'<div class="le-note">{html.escape(DISCLAIMER)}</div>'
    return f'{css}<div class="le-doc">{"".join(blocks)}{note}</div>'
