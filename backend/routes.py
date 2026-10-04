"""API routes for LegalEase."""

import logging

from fastapi import APIRouter, HTTPException

from ai_core.gemini_generator import (
    GeminiConfigError,
    GeminiDocumentGenerator,
    GeminiGenerationError,
)
from backend.models import DocumentRequest, DocumentResponse, ErrorResponse
from document.formatter import sanitize_text

logger = logging.getLogger("legalease.routes")
router = APIRouter()

AI_ERROR_MESSAGE = (
    "Unable to generate the document right now. "
    "Please check the AI service configuration and try again."
)


@router.post(
    "/generate",
    response_model=DocumentResponse,
    summary="Generate a legal document draft",
    description=(
        "Validates the request, sends the document type, parties, terms and effective date "
        "to Gemini, and returns a structured legal document draft as text. "
        "The output is an AI-generated draft and should be reviewed by a qualified legal professional."
    ),
    responses={
        422: {"description": "Validation error (missing or empty fields)"},
        502: {"model": ErrorResponse, "description": "AI service failed or returned empty output"},
        500: {"model": ErrorResponse, "description": "Unexpected server error"},
    },
)
def generate_legal_document(request: DocumentRequest) -> DocumentResponse:
    try:
        generator = GeminiDocumentGenerator()
        text = generator.generate_document(
            request.document_type, request.parties, request.terms, request.effective_date
        )
        text = sanitize_text(text)
        if not text:
            raise GeminiGenerationError("Empty output")
        return DocumentResponse(success=True, document=text)
    except (GeminiConfigError, GeminiGenerationError) as exc:
        logger.error("Generation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=AI_ERROR_MESSAGE)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="An unexpected server error occurred.")
