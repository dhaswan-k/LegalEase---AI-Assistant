# ⚖️ LegalEase AI — AI-Powered Legal Document Generator

## Project Overview
LegalEase AI turns four simple inputs (document type, parties, terms, effective date) into a structured legal document draft using Google Gemini. You can preview it, edit it, and download it as **TXT, DOCX, or PDF**.

> LegalEase AI provides AI-assisted legal drafting for informational and drafting purposes. Generated documents should be reviewed by a qualified legal professional before signing or use.

## Features
- Gemini-generated legal drafts with numbered sections and a signature block
- Terms entered with semicolons are woven into proper clauses (not copied verbatim)
- Formatted HTML preview + editable text area; **downloads always use your edited text**
- DOCX: Times New Roman, A4, logo, title, headings, terms table (Schedule A), footer with page numbers
- PDF: A4, logo header, page numbers, terms table, auto page breaks
- Works without a logo; sanitises smart quotes, dashes and odd Unicode
- Gemini API key lives only on the backend

## Architecture
```
USER → STREAMLIT FRONTEND --HTTP POST /generate--> FASTAPI BACKEND → GEMINI (ai_core)
                ↑                                                      |
                └────────────── generated text ←───────────────────────┘
Streamlit preview/editor → document/ formatters → TXT | DOCX | PDF
```

## Tech Stack
Python 3.10+, FastAPI, Uvicorn, Pydantic, `google-genai` (current Gemini SDK), Streamlit, python-docx, fpdf2, Pillow, python-dotenv, requests.

## Folder Structure
```
LegalEase/
├── backend/        main.py, routes.py, models.py
├── ai_core/        gemini_generator.py
├── document/       formatter.py, txt_generator.py, docx_generator.py, pdf_generator.py
├── frontend/       app.py
├── assets/         logo.png   (replace with your own logo; app works without it)
├── tests/          test_exports.py
├── .env  .env.example  .gitignore  requirements.txt  README.md
```

## Prerequisites
- Python 3.10 or newer
- A Gemini API key from https://aistudio.google.com/apikey

## Installation (Windows)
```bash
cd LegalEase
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Setup
Edit `.env` (copy from `.env.example`):
```env
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-2.5-flash
BACKEND_URL=http://localhost:8000
```
`GEMINI_MODEL` is configurable. If a model name is rejected, pick a currently supported one from the Gemini docs (e.g. a `gemini-2.5-pro` or newer model). The PDF's `gemini-1.5-pro` has been retired, so the default is a current model.

## Running the Backend
From the project root:
```bash
uvicorn backend.main:app --reload
```
API: http://localhost:8000 — Swagger docs: http://localhost:8000/docs

## Running the Frontend
In a second terminal (venv activated, project root):
```bash
streamlit run frontend/app.py
```
Opens at http://localhost:8501.

## Usage
1. Select a document type (or choose **Other** for a custom one)
2. Enter parties, one per line, e.g. `Jane Doe (Service Provider)`
3. Enter terms separated by semicolons
4. Pick the effective date
5. Click **Generate Document**
6. Review the formatted preview
7. Open the **Edit document** tab to change the text
8. Download TXT / DOCX / PDF (named like `LegalEase_Freelance_Contract_2026-10-03.docx`)

## Testing
Offline tests (no API key needed) cover sanitising, validation, TXT, DOCX (table, footer, logo, with/without logo) and PDF (all five document types, long-document pagination):
```bash
python -m unittest discover -s tests -v
```
Manual end-to-end checks with a real key: generate an NDA, Employment Contract, Lease Agreement, Freelance Contract and Service Agreement; verify preview, edit → download uses edited text, the terms table in DOCX/PDF, the footer, special characters (₹, é, “quotes”), empty-field rejection, and stopping the backend to see "Unable to connect to the LegalEase backend."

## Technical choices
- `google-genai` replaces the deprecated `google-generativeai` package.
- `fpdf2` (maintained fork of `fpdf`) is used; core PDF fonts are Latin-1, so `₹` is written as `Rs.` in PDFs and unsupported characters become `?`. DOCX and TXT keep Unicode.
- The terms table appears as "Schedule A: Summary of Agreed Terms" just before the signature block, in DOCX and PDF.

## Troubleshooting
- **"Unable to connect to the LegalEase backend."** Start uvicorn first; check `BACKEND_URL` and port 8000.
- **"Unable to generate the document right now…"** Check `GEMINI_API_KEY`, `GEMINI_MODEL`, quota and internet access. Details are logged in the backend terminal (never the key).
- **`ModuleNotFoundError: backend` / `document`** Run commands from the project root.
- **Port in use** `uvicorn backend.main:app --port 8001` and set `BACKEND_URL=http://localhost:8001`.
- **Model not found (404)** Change `GEMINI_MODEL` in `.env` and restart the backend.
