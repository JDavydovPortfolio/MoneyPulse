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
    assert window.pipeline.llm.model == "gemma4:e2b-it-qat"
    assert window.process_btn.isEnabled() is False

    window.close()
    app.processEvents()


def test_desktop_processes_synthetic_document(tmp_path, monkeypatch):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QMessageBox
    from test_pipeline import _pipeline, _synthetic_image

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()
    window.pipeline = _pipeline(tmp_path)
    image_path = tmp_path / "synthetic.png"
    _synthetic_image(image_path)
    window.files_selected([str(image_path)])
    window.process_documents()
    loop = QEventLoop()
    window.worker_thread.finished.connect(loop.quit)
    QTimer.singleShot(10000, loop.quit)
    loop.exec()
    assert window.worker_thread.wait(1000)
    app.processEvents()
    assert len(window.processed_documents) == 1
    assert window.processed_documents[0]["validation_status"] == "passed"
    assert "Example Harbor Coffee" in window.ocr_preview.toPlainText()
    assert window.data_tree.topLevelItemCount() > 0
    assert window.validation_list.count() > 0
    assert window.export_csv_btn.isEnabled()
    window.close()


def test_stop_keeps_processing_disabled_until_worker_finishes(tmp_path, monkeypatch):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QMessageBox
    import threading

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()
    release = threading.Event()
    def process(path):
        release.wait(5)
        return {"processing_status": "failed", "error": "synthetic cancellation"}
    monkeypatch.setattr(window.pipeline, "process_single_document", process)
    window.files_selected(["synthetic.png"])
    window.process_documents()
    try:
        window.stop_processing()
        assert not window.process_btn.isEnabled()
        assert window.worker_thread.isInterruptionRequested()
    finally:
        release.set()
        loop = QEventLoop()
        window.worker_thread.finished.connect(loop.quit)
        QTimer.singleShot(1000, loop.quit)
        loop.exec()
        assert window.worker_thread.wait(1000)
        app.processEvents()
        window.close()
