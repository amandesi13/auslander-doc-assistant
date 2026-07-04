import json

from auslander_doc_assistant.cli import main


def test_cli_writes_analysis(tmp_path):
    document = tmp_path / "letter.txt"
    output = tmp_path / "analysis.json"
    document.write_text("Krankenversicherung Mitgliedsbescheinigung bitte senden bis 01.08.2026", encoding="utf-8")

    assert main([str(document), "-o", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["document_type"] == "health_insurance"
    assert "01.08.2026" in payload["deadline_candidates"]
