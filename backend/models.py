"""Pydantic request/response models for the LegalEase API."""

from pydantic import BaseModel, Field, field_validator


def _require(value: str, label: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{label} cannot be empty.")
    return cleaned


class DocumentRequest(BaseModel):
    document_type: str = Field(..., description="Type of legal document, e.g. NDA", examples=["Freelance Work Contract"])
    parties: str = Field(..., description="Parties and roles", examples=["Jane Doe (Service Provider)\nTechNova Inc. (Client)"])
    terms: str = Field(..., description="Terms; may be separated by semicolons", examples=["Payment within 30 days; Confidentiality must be maintained"])
    effective_date: str = Field(..., description="Effective date of the document", examples=["03 October 2026"])

    @field_validator("document_type")
    @classmethod
    def _doc_type(cls, v: str) -> str:
        return _require(v, "Document type")

    @field_validator("parties")
    @classmethod
    def _parties(cls, v: str) -> str:
        return _require(v, "Parties")

    @field_validator("terms")
    @classmethod
    def _terms(cls, v: str) -> str:
        return _require(v, "Terms")

    @field_validator("effective_date")
    @classmethod
    def _date(cls, v: str) -> str:
        return _require(v, "Effective date")


class DocumentResponse(BaseModel):
    success: bool = True
    document: str


class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
