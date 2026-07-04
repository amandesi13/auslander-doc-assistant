from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    residence_permit = "residence_permit"
    anmeldung = "anmeldung"
    health_insurance = "health_insurance"
    rental_contract = "rental_contract"
    university_enrollment = "university_enrollment"
    job_contract = "job_contract"
    broadcasting_fee = "broadcasting_fee"
    unknown = "unknown"


class ExtractedFact(BaseModel):
    label: str
    value: str
    confidence: float = Field(ge=0, le=1, default=0.7)


class ActionItem(BaseModel):
    title: str
    detail: str
    urgency: str = "normal"


class DocumentAnalysis(BaseModel):
    document_type: DocumentType
    plain_english_summary: str
    extracted_facts: list[ExtractedFact]
    required_documents: list[str]
    action_items: list[ActionItem]
    deadline_candidates: list[str]
    fee_candidates: list[str]
    polite_german_reply: str
    disclaimer: str = "This is not legal advice. Verify requirements with the responsible authority, university, employer, or insurance provider."
