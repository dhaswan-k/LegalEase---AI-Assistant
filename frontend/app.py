"""LegalEase AI - Streamlit frontend."""

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
import streamlit as st
from dotenv import load_dotenv

from document.docx_generator import format_docx
from document.formatter import (
    LONG_DISCLAIMER,
    format_html_preview,
    safe_filename,
    sanitize_text,
)
from document.pdf_generator import format_pdf
from document.txt_generator import generate_txt

load_dotenv(ROOT / ".env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
GENERATE_URL = f"{BACKEND_URL}/generate"
LOGO_PATH = ROOT / "assets" / "logo.png"
LOGO = str(LOGO_PATH) if LOGO_PATH.is_file() else None

DOC_TYPES = [
    "Employment Contract", "NDA", "Lease Agreement", "Employment Offer Letter",
    "Freelance Contract", "Service Agreement", "General Agreement", "Other",
]

st.set_page_config(page_title="LegalEase AI", page_icon="⚖️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1100px;}
    .le-hero {background: linear-gradient(120deg,#14284b,#27467f); color:#fff; padding: 22px 28px;
              border-radius: 12px; margin-bottom: 18px;}
    .le-hero h1 {margin:0; font-size: 2rem; color:#fff;}
    .le-hero p {margin:4px 0 0; opacity:.85; font-size:1.05rem;}
    .le-section {font-weight:600; color:#14284b; font-size:1.1rem; margin: 6px 0 2px;}
    .le-disclaimer {font-size:.85rem; color:#667; border-left:3px solid #c9a227; padding-left:10px; margin-top:10px;}
    div.stButton > button[kind="primary"] {background:#14284b; border:0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- session state ----------
for key, default in {
    "generated": False,
    "edited_text": "",
    "doc_type": "",
    "terms": "",
    "date_str": "",
    "last_request": None,
}.items():
    st.session_state.setdefault(key, default)


# ---------- helpers ----------
def call_backend(payload: dict):
    """Returns (document_text | None, error_message | None, field_errors dict)."""
    try:
        resp = requests.post(GENERATE_URL, json=payload, timeout=180)
    except requests.exceptions.ConnectionError:
        return None, "Unable to connect to the LegalEase backend.", {}
    except requests.exceptions.Timeout:
        return None, "The request timed out. Please try again.", {}
    except requests.exceptions.RequestException:
        return None, "Unable to connect to the LegalEase backend.", {}

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200 and data.get("success") and data.get("document"):
        return sanitize_text(data["document"]), None, {}
    if resp.status_code == 422:
        return None, "Please fix the highlighted fields.", data.get("errors", {})
    if resp.status_code in (500, 502):
        return None, (
            "Unable to generate the document right now. "
            "Please check the AI service configuration and try again."
        ), {}
    return None, data.get("detail") or "Something went wrong. Please try again.", {}


def run_generation(payload: dict):
    with st.spinner("Drafting your document with Gemini..."):
        doc, err, field_errs = call_backend(payload)
    if doc:
        st.session_state.generated = True
        st.session_state.edited_text = doc
        st.session_state.doc_type = payload["document_type"]
        st.session_state.terms = payload["terms"]
        st.session_state.date_str = payload["effective_date"]
        st.session_state.last_request = payload
        st.success("Document Generated Successfully")
    else:
        st.error(err)
        for field, msg in field_errs.items():
            st.warning(f"**{field.replace('_', ' ').title()}**: {msg}")
        if st.session_state.last_request and not field_errs:
            st.info("You can retry using the **Retry** button below.")
        st.session_state.failed_request = payload


# ---------- sidebar ----------
with st.sidebar:
    if LOGO:
        st.image(LOGO, use_container_width=True)
    st.markdown("### ⚖️ LegalEase AI")
    st.caption("AI-assisted legal drafting")
    st.markdown("**How it works**")
    st.markdown("1. Choose a document type\n2. Add parties & terms\n3. Generate & review\n4. Edit\n5. Download TXT / DOCX / PDF")
    st.markdown(f'<div class="le-disclaimer">{LONG_DISCLAIMER}</div>', unsafe_allow_html=True)
    st.caption(f"Backend: {BACKEND_URL}")

# ---------- hero ----------
st.markdown(
    '<div class="le-hero"><h1>⚖️ LegalEase AI</h1><p>AI-Powered Legal Document Generator</p></div>',
    unsafe_allow_html=True,
)

# ---------- input form ----------
st.markdown('<div class="le-section">1. Document details</div>', unsafe_allow_html=True)
col_a, col_b = st.columns([1, 1])
with col_a:
    choice = st.selectbox("Document Type", DOC_TYPES)
    custom_type = ""
    if choice == "Other":
        custom_type = st.text_input("Custom document type", placeholder="e.g. Partnership Deed")
with col_b:
    eff_date = st.date_input("Effective Date", value=date.today(), format="DD/MM/YYYY")

col_c, col_d = st.columns([1, 1])
with col_c:
    parties = st.text_area(
        "Parties Involved",
        height=200,
        placeholder="Jane Doe (Service Provider)\nTechNova Inc. (Client)",
        help="One party per line with their role in brackets.",
    )
with col_d:
    terms = st.text_area(
        "Terms & Conditions",
        height=200,
        placeholder="Payment within 30 days; Confidentiality must be maintained; Either party may terminate with 15 days notice",
        help="Separate multiple terms with semicolons (;).",
    )
st.caption("Tip: separate multiple terms with semicolons (;). Each becomes its own clause.")

document_type = custom_type.strip() if choice == "Other" else choice
payload = {
    "document_type": document_type,
    "parties": parties.strip(),
    "terms": terms.strip(),
    "effective_date": eff_date.strftime("%d %B %Y"),
}

if st.button("Generate Document", type="primary", use_container_width=True):
    missing = []
    if not payload["document_type"]:
        missing.append("Document Type")
    if not payload["parties"]:
        missing.append("Parties Involved")
    if not payload["terms"]:
        missing.append("Terms & Conditions")
    if missing:
        for m in missing:
            st.error(f"{m} cannot be empty.")
    else:
        run_generation(payload)

if st.session_state.get("failed_request") and not st.session_state.generated:
    if st.button("Retry"):
        run_generation(st.session_state.failed_request)

# ---------- preview / edit / download ----------
if st.session_state.generated:
    st.divider()
    st.markdown('<div class="le-section">2. Preview & edit</div>', unsafe_allow_html=True)
    tab_prev, tab_edit = st.tabs(["Formatted preview", "Edit document"])
    with tab_edit:
        st.text_area(
            "Edit the document below. Downloads use this edited version.",
            key="edited_text",
            height=520,
        )
        if st.button("Regenerate from original inputs") and st.session_state.last_request:
            run_generation(st.session_state.last_request)
            st.rerun()
    with tab_prev:
        st.markdown(format_html_preview(st.session_state.edited_text), unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="le-section">3. Download</div>', unsafe_allow_html=True)

    current = sanitize_text(st.session_state.edited_text)
    dtype = st.session_state.doc_type or "Document"
    terms_for_table = st.session_state.terms
    stamp = eff_date.isoformat() if eff_date else date.today().isoformat()

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Download TXT",
            data=generate_txt(current),
            file_name=safe_filename(dtype, "txt", stamp),
            mime="text/plain",
            use_container_width=True,
        )
    with d2:
        try:
            docx_bytes = format_docx(current, dtype, terms_for_table, LOGO)
            st.download_button(
                "Download DOCX",
                data=docx_bytes,
                file_name=safe_filename(dtype, "docx", stamp),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Could not build the DOCX file ({type(exc).__name__}). Try simplifying unusual characters.")
    with d3:
        try:
            pdf_bytes = format_pdf(current, dtype, terms_for_table, LOGO)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=safe_filename(dtype, "pdf", stamp),
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Could not build the PDF file ({type(exc).__name__}). Try simplifying unusual characters.")

    st.markdown(f'<div class="le-disclaimer">{LONG_DISCLAIMER}</div>', unsafe_allow_html=True)
