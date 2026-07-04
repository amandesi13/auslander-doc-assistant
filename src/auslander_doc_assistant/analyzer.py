from __future__ import annotations

import re

from .models import ActionItem, DocumentAnalysis, DocumentType, ExtractedFact


DOCUMENT_KEYWORDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.residence_permit: ("aufenthaltstitel", "ausländerbehörde", "zusatzblatt", "residence permit", "aufenthaltserlaubnis"),
    DocumentType.anmeldung: ("anmeldung", "wohnungsgeberbestätigung", "bürgeramt", "meldebehörde"),
    DocumentType.health_insurance: ("krankenversicherung", "mitgliedsbescheinigung", "health insurance", "krankenkasse"),
    DocumentType.rental_contract: ("mietvertrag", "kaution", "warmmiete", "vermieter", "kündigungsfrist"),
    DocumentType.university_enrollment: ("immatrikulationsbescheinigung", "semesterbeitrag", "matrikelnummer", "enrollment"),
    DocumentType.job_contract: (
        "arbeitsvertrag",
        "werkstudent",
        "hiwi",
        "studentische hilfskraft",
        "student helper",
        "second job",
        "zweiter job",
        "zih login",
        "stuhl",
        "chair",
        "stunden pro woche",
        "vergütung",
    ),
    DocumentType.broadcasting_fee: ("rundfunkbeitrag", "beitragsnummer", "ard zdf deutschlandradio"),
}

REQUIRED_DOC_PATTERNS = (
    r"(?:bitte|please).{0,80}(?:senden|send|einreichen|submit).{0,160}",
    r"(?:benötigen|required|required documents|unterlagen).{0,180}",
)

DATE_PATTERN = re.compile(r"\b(?:\d{1,2}\.\d{1,2}\.\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b", re.IGNORECASE)
FEE_PATTERN = re.compile(r"\b\d{1,4}(?:[.,]\d{2})?\s?(?:€|EUR|Euro)\b", re.IGNORECASE)
HOURS_PATTERN = re.compile(r"\b\d{1,2}\s?(?:h|hours|stunden)\s?/?\s?(?:week|woche|Woche)?\b", re.IGNORECASE)


def analyze_document(text: str) -> DocumentAnalysis:
    normalized = normalize(text)
    document_type = classify_document(normalized)
    facts = extract_facts(text, document_type)
    deadlines = DATE_PATTERN.findall(text)
    fees = FEE_PATTERN.findall(text)
    required_documents = extract_required_documents(text, document_type)
    actions = build_actions(document_type, facts, required_documents, deadlines, fees)

    return DocumentAnalysis(
        document_type=document_type,
        plain_english_summary=summarize(document_type, facts, deadlines, fees),
        extracted_facts=facts,
        required_documents=required_documents,
        action_items=actions,
        deadline_candidates=deadlines,
        fee_candidates=fees,
        polite_german_reply=generate_german_reply(document_type, required_documents),
    )


def classify_document(normalized_text: str) -> DocumentType:
    scores: dict[DocumentType, int] = {}
    for document_type, keywords in DOCUMENT_KEYWORDS.items():
        scores[document_type] = sum(1 for keyword in keywords if keyword.casefold() in normalized_text)
    best_type, score = max(scores.items(), key=lambda item: item[1])
    return best_type if score > 0 else DocumentType.unknown


def extract_facts(text: str, document_type: DocumentType) -> list[ExtractedFact]:
    facts: list[ExtractedFact] = []
    if dates := DATE_PATTERN.findall(text):
        facts.append(ExtractedFact(label="Dates found", value=", ".join(dict.fromkeys(dates))))
    if fees := FEE_PATTERN.findall(text):
        facts.append(ExtractedFact(label="Fees found", value=", ".join(dict.fromkeys(fees))))
    if hours := HOURS_PATTERN.findall(text):
        facts.append(ExtractedFact(label="Working hours found", value=", ".join(dict.fromkeys(hours))))

    email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}", text)
    if email_match:
        facts.append(ExtractedFact(label="Contact email", value=email_match.group(0), confidence=0.8))

    if document_type == DocumentType.job_contract and "20" in text:
        facts.append(ExtractedFact(label="Student work warning", value="Check total weekly hours across all jobs during the semester.", confidence=0.6))

    return facts


def extract_required_documents(text: str, document_type: DocumentType) -> list[str]:
    lower = text.casefold()
    common_docs = {
        "Passport / Reisepass": ("passport", "reisepass", "pass"),
        "Residence permit / Aufenthaltstitel": ("residence permit", "aufenthaltstitel", "aufenthaltserlaubnis"),
        "Enrollment certificate / Immatrikulationsbescheinigung": ("enrollment", "immatrikulationsbescheinigung", "current enrollment"),
        "Health insurance certificate / Krankenversicherungsnachweis": ("health insurance", "krankenversicherung", "mitgliedsbescheinigung"),
        "Rental confirmation / Wohnungsgeberbestätigung": ("wohnungsgeberbestätigung", "mietvertrag"),
        "Tax ID / Steuer-ID": ("steuer-id", "steueridentifikationsnummer", "tax id"),
        "Zusatzblatt": ("zusatzblatt",),
        "ZIH login": ("zih login", "zih-login"),
        "CV / Lebenslauf": ("cv", "lebenslauf"),
    }
    found = [label for label, keywords in common_docs.items() if any(keyword in lower for keyword in keywords)]

    if not found and document_type == DocumentType.residence_permit:
        found = [
            "Passport / Reisepass",
            "Residence permit / Aufenthaltstitel",
            "Enrollment certificate / Immatrikulationsbescheinigung",
            "Health insurance certificate / Krankenversicherungsnachweis",
        ]
    elif not found and document_type == DocumentType.health_insurance:
        found = ["Enrollment certificate / Immatrikulationsbescheinigung", "Passport or ID / Ausweis", "Current address / aktuelle Adresse"]

    return found


def build_actions(
    document_type: DocumentType,
    facts: list[ExtractedFact],
    required_documents: list[str],
    deadlines: list[str],
    fees: list[str],
) -> list[ActionItem]:
    actions = [
        ActionItem(title="Verify the document type", detail=f"Detected as `{document_type.value}`. Confirm this before acting."),
    ]
    if required_documents:
        actions.append(ActionItem(title="Prepare required documents", detail=", ".join(required_documents), urgency="high"))
    if deadlines:
        actions.append(ActionItem(title="Add deadline to calendar", detail=f"Possible deadline/date: {deadlines[0]}", urgency="high"))
    if fees:
        actions.append(ActionItem(title="Check payment requirement", detail=f"Possible fee/payment amount: {fees[0]}"))
    if document_type == DocumentType.job_contract:
        actions.append(ActionItem(title="Check working-time limits", detail="Confirm how this job combines with HiWi/student work and residence-permit rules.", urgency="high"))
    actions.append(ActionItem(title="Ask for confirmation if unclear", detail="Send the generated polite German reply to request clarification."))
    return actions


def summarize(document_type: DocumentType, facts: list[ExtractedFact], deadlines: list[str], fees: list[str]) -> str:
    parts = [f"This looks like a {document_type.value.replace('_', ' ')} document."]
    if deadlines:
        parts.append(f"It contains possible date/deadline references: {', '.join(dict.fromkeys(deadlines))}.")
    if fees:
        parts.append(f"It contains possible fee/payment references: {', '.join(dict.fromkeys(fees))}.")
    if not facts:
        parts.append("No strong structured facts were detected; read the original carefully.")
    return " ".join(parts)


def generate_german_reply(document_type: DocumentType, required_documents: list[str]) -> str:
    docs = german_document_list(required_documents) if required_documents else "die erforderlichen Unterlagen"
    return (
        "Sehr geehrte Damen und Herren,\n\n"
        f"vielen Dank für Ihre Nachricht. Ich bereite {docs} vor und werde diese schnellstmöglich einreichen. "
        "Falls noch weitere Unterlagen oder Informationen benötigt werden, geben Sie mir bitte kurz Bescheid.\n\n"
        "Mit freundlichen Grüßen\n"
        "Amandeep Singh"
    )


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def german_document_list(required_documents: list[str]) -> str:
    names = []
    for document in required_documents:
        if " / " in document:
            names.append(document.split(" / ", 1)[1])
        else:
            names.append(document)
    return ", ".join(names)
