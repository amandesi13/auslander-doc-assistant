from __future__ import annotations

import os
from pathlib import Path


def extract_text(path: Path, enable_ocr: bool = False, tesseract_cmd: str | None = None, tessdata_dir: str | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf_text(path)
        if text.strip() or not enable_ocr:
            return text
        return extract_ocr_text(path, tesseract_cmd=tesseract_cmd, tessdata_dir=tessdata_dir)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        return extract_image_ocr(path, tesseract_cmd=tesseract_cmd, tessdata_dir=tessdata_dir)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_pdf_text(path: Path) -> str:
    import fitz

    chunks: list[str] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                chunks.append(f"[Page {page_index}]\n{text}")
    return "\n\n".join(chunks)


def extract_ocr_text(path: Path, tesseract_cmd: str | None = None, tessdata_dir: str | None = None) -> str:
    import fitz
    import pytesseract
    from PIL import Image

    configure_tesseract(pytesseract, tesseract_cmd, tessdata_dir)
    chunks: list[str] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            text = pytesseract.image_to_string(image, lang="deu+eng")
            if text.strip():
                chunks.append(f"[Page {page_index} OCR]\n{text.strip()}")
    return "\n\n".join(chunks)


def extract_image_ocr(path: Path, tesseract_cmd: str | None = None, tessdata_dir: str | None = None) -> str:
    import pytesseract
    from PIL import Image

    configure_tesseract(pytesseract, tesseract_cmd, tessdata_dir)
    return pytesseract.image_to_string(Image.open(path), lang="deu+eng")


def configure_tesseract(pytesseract, tesseract_cmd: str | None, tessdata_dir: str | None) -> None:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir
