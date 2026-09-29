from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from src.ocr import OCRProcessor


def _font(size=36):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def test_ocr_extracts_synthetic_image(tmp_path):
    image_path = tmp_path / "synthetic.png"
    image = Image.new("RGB", (1800, 500), "white")
    draw = ImageDraw.Draw(image)
    draw.text((50, 60), "MONEYPULSE SYNTHETIC DEMO", fill="black", font=_font(42))
    draw.text((50, 150), "Business Name: Example Harbor Coffee LLC", fill="black", font=_font(36))
    draw.text((50, 240), "Requested Amount: 75000", fill="black", font=_font(36))
    image.save(image_path)

    text = OCRProcessor().extract_text(str(image_path))

    normalized = " ".join(text.split()).lower()
    assert "example harbor coffee" in normalized
    assert "75000" in normalized


def test_ocr_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        OCRProcessor().extract_text(str(tmp_path / "missing.png"))


def test_ocr_rejects_unsupported_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("synthetic", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file type"):
        OCRProcessor().extract_text(str(path))


def test_ocr_rejects_corrupt_image(tmp_path):
    path = tmp_path / "corrupt.png"
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Failed to load image"):
        OCRProcessor().extract_text(str(path))


def test_ocr_reads_every_page_of_real_pdf(tmp_path):
    pages = []
    for label in ("FIRST PAGE HARBOR COFFEE", "SECOND PAGE FUNDING 75000"):
        page = Image.new("RGB", (1800, 500), "white")
        ImageDraw.Draw(page).text((50, 100), label, fill="black", font=_font(42))
        pages.append(page)
    path = tmp_path / "application.pdf"
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=150)
    text = OCRProcessor().extract_text(str(path)).lower()
    assert "first page harbor coffee" in text
    assert "second page funding 75000" in text


def test_pdf_renderer_processes_one_page_at_a_time(tmp_path, monkeypatch):
    import src.ocr as ocr
    calls = []
    monkeypatch.setattr(ocr, "pdfinfo_from_path", lambda *args, **kwargs: {"Pages": 2})
    def render(path, **kwargs):
        calls.append((kwargs["first_page"], kwargs["last_page"]))
        return [Image.new("RGB", (100, 100), "white")]
    monkeypatch.setattr(ocr, "convert_from_path", render)
    monkeypatch.setattr(ocr.pytesseract, "image_to_string", lambda *args, **kwargs: "page")
    assert ocr._extract_from_pdf(tmp_path / "fixture.pdf") == "page\n\npage"
    assert calls == [(1, 1), (2, 2)]
