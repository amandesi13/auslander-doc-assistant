from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import analyze_document
from .extract_text import extract_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze German bureaucracy documents for international students.")
    parser.add_argument("document", type=Path, help="PDF, image, or text file to analyze.")
    parser.add_argument("-o", "--output", type=Path, default=Path("analysis.json"), help="JSON output path.")
    parser.add_argument("--ocr", action="store_true", help="Use OCR if PDF text extraction is empty or input is an image.")
    parser.add_argument("--tesseract-cmd", default=None, help="Path to tesseract executable.")
    parser.add_argument("--tessdata-dir", default=None, help="Path to tessdata directory.")
    args = parser.parse_args(argv)

    text = extract_text(args.document, enable_ocr=args.ocr, tesseract_cmd=args.tesseract_cmd, tessdata_dir=args.tessdata_dir)
    analysis = analyze_document(text)
    args.output.write_text(json.dumps(analysis.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Detected: {analysis.document_type.value}")
    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
