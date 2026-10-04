"""Gemini-powered legal document generator (uses the current `google-genai` SDK)."""

import logging
import os

from dotenv import load_dotenv

from document.formatter import sanitize_text

load_dotenv()
logger = logging.getLogger("legalease.ai")

DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiConfigError(RuntimeError):
    """Missing or invalid AI configuration."""


class GeminiGenerationError(RuntimeError):
    """The AI service failed or returned unusable output."""


class GeminiDocumentGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
        self._client = None

    def _get_client(self):
        if not self.api_key or self.api_key == "your_api_key_here":
            raise GeminiConfigError("GEMINI_API_KEY is not configured.")
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @staticmethod
    def build_prompt(document_type, parties, terms, effective_date) -> str:
        return f"""You are a legal document drafting assistant. You are NOT a lawyer and you do not give legal advice.
Draft a complete, professional "{document_type}" using ONLY the information supplied below.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

TERMS AND CONDITIONS (user-supplied, may be separated by semicolons):
{terms}

EFFECTIVE DATE:
{effective_date}

STRUCTURE REQUIREMENTS:
- Start with a clear title on the first line, prefixed with "# ".
- Then an introduction/preamble stating the effective date and identifying the parties.
- Include numbered sections (use headings like "1. Definitions", "2. Scope and Purpose", ...), written in formal legal language.
- Cover, where appropriate for this document type: purpose/scope, obligations and responsibilities of each party, payment/compensation, term and termination, confidentiality, dispute resolution, general provisions.
- Turn EVERY supplied term into a properly worded clause inside the relevant section. Do NOT just copy the semicolon-separated terms; integrate them into coherent clauses and keep their specific figures (amounts, durations, dates) exactly as given.
- End with a signature section ("IN WITNESS WHEREOF") with signature, name, and date lines for each party.

STRICT RULES:
- Do NOT invent personal information (addresses, ID numbers, registration numbers, amounts, dates) that was not supplied. Where a needed detail is missing, use a bracketed placeholder such as [Address of Party A].
- Do NOT cite or invent specific laws, statutes, sections, court cases, registration requirements, or legal citations. If governing law is needed, use a placeholder like [Governing Jurisdiction].
- Output plain text only. Use "# " only for the title and plain numbered headings for sections. No tables, no code blocks, no commentary before or after the document.
"""

    def generate_document(self, document_type, parties, terms, effective_date) -> str:
        client = self._get_client()
        prompt = self.build_prompt(document_type, parties, terms, effective_date)
        try:
            response = client.models.generate_content(model=self.model_name, contents=prompt)
            raw = getattr(response, "text", None)
        except GeminiConfigError:
            raise
        except Exception as exc:  # never leak key; log only exception type
            logger.error("Gemini call failed: %s", type(exc).__name__)
            raise GeminiGenerationError("The AI service request failed.") from None
        cleaned = sanitize_text(raw)
        if not cleaned:
            raise GeminiGenerationError("The AI service returned an empty document.")
        return cleaned
