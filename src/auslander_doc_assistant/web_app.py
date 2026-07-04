from __future__ import annotations

import os
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from .analyzer import analyze_document
from .extract_text import extract_text

app = FastAPI(title="Auslander Doc Assistant", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Auslander Doc Assistant</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 920px; margin: 40px auto; padding: 0 20px; color: #18212f; }
    h1 { margin-bottom: 4px; }
    .muted { color: #5e6b7a; }
    form { border: 1px solid #d9e0e8; padding: 18px; border-radius: 8px; margin: 24px 0; }
    button { padding: 10px 14px; border: 0; border-radius: 6px; background: #145ea8; color: white; cursor: pointer; }
    input { margin: 8px 0 14px; }
  </style>
</head>
<body>
  <h1>Auslander Doc Assistant</h1>
  <p class="muted">Privacy-first document helper for international students and newcomers in Germany.</p>
  <form method="post" action="/analyze" enctype="multipart/form-data">
    <label>Upload PDF, image, or text file</label><br>
    <input type="file" name="file" required><br>
    <label><input type="checkbox" name="ocr" value="true"> Enable OCR fallback</label><br>
    <button type="submit">Analyze document</button>
  </form>
  <p class="muted">No uploaded file is stored permanently. This prototype uses rule-based extraction and does not provide legal advice.</p>
</body>
</html>
"""


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...), ocr: str | None = Form(default=None)) -> str:
    suffix = Path(file.filename or "document.txt").suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        text = extract_text(tmp_path, enable_ocr=ocr == "true")
        analysis = analyze_document(text)
    finally:
        tmp_path.unlink(missing_ok=True)

    actions = "".join(f"<li><strong>{item.title}</strong>: {item.detail} <em>({item.urgency})</em></li>" for item in analysis.action_items)
    facts = "".join(f"<li><strong>{fact.label}</strong>: {fact.value}</li>" for fact in analysis.extracted_facts)
    docs = "".join(f"<li>{doc}</li>" for doc in analysis.required_documents)
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Document Analysis</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 980px; margin: 40px auto; padding: 0 20px; color: #18212f; }}
    section {{ border-top: 1px solid #d9e0e8; padding-top: 16px; margin-top: 18px; }}
    pre {{ background: #f6f8fb; padding: 12px; white-space: pre-wrap; }}
    a {{ color: #145ea8; }}
  </style>
</head>
<body>
  <a href="/">Back</a>
  <h1>Analysis</h1>
  <p><strong>Detected type:</strong> {analysis.document_type.value}</p>
  <p>{analysis.plain_english_summary}</p>
  <section><h2>Action checklist</h2><ul>{actions}</ul></section>
  <section><h2>Extracted facts</h2><ul>{facts or "<li>No strong structured facts detected.</li>"}</ul></section>
  <section><h2>Required documents</h2><ul>{docs or "<li>No required documents detected automatically.</li>"}</ul></section>
  <section><h2>Polite German reply draft</h2><pre>{analysis.polite_german_reply}</pre></section>
  <section><p><strong>Disclaimer:</strong> {analysis.disclaimer}</p></section>
</body>
</html>
"""


def main() -> None:
    uvicorn.run("auslander_doc_assistant.web_app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8200")), reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
