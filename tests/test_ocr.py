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
    return ImageFont.load_default()


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
