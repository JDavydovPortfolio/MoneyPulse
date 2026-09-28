import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.premium_gui import PremiumDocumentProcessor


def test_desktop_window_initializes_offscreen(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()

    assert window.windowTitle().startswith("MoneyPulse")
    assert window.pipeline.llm.provider_id == "ollama"
    assert window.pipeline.llm.model == "gemma4:e4b"
    assert window.process_btn.isEnabled() is False

    window.close()
    app.processEvents()
