from auslander_doc_assistant.analyzer import analyze_document
from auslander_doc_assistant.models import DocumentType


def test_detects_hiwi_job_document_and_hours_warning():
    text = """
    Studentische Hilfskraft HiWi Vertrag
    Beginn: 01.08.2026
    Arbeitszeit: 10 Stunden/Woche
    Bitte senden Sie Ihre Immatrikulationsbescheinigung und Krankenversicherung.
    """

    analysis = analyze_document(text)

    assert analysis.document_type == DocumentType.job_contract
    assert any("working-time" in item.title.lower() or "required documents" in item.title.lower() for item in analysis.action_items)
    assert "01.08.2026" in analysis.deadline_candidates


def test_detects_residence_permit_documents():
    text = """
    Ausländerbehörde Dresden
    Für Ihren Aufenthaltstitel benötigen wir Reisepass, Zusatzblatt,
    Immatrikulationsbescheinigung und Nachweis der Krankenversicherung.
    Termin: 15.09.2026
    """

    analysis = analyze_document(text)

    assert analysis.document_type == DocumentType.residence_permit
    assert "Passport / Reisepass" in analysis.required_documents
    assert "Zusatzblatt" in analysis.required_documents
    assert "15.09.2026" in analysis.deadline_candidates


def test_detects_fee_candidate():
    analysis = analyze_document("Rundfunkbeitrag Beitragsnummer. Bitte zahlen Sie 18,36 EUR.")

    assert analysis.document_type == DocumentType.broadcasting_fee
    assert "18,36 EUR" in analysis.fee_candidates
