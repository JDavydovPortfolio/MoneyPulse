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


def test_batch_results_are_selectable_and_ocr_remains_plain_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()
    from test_crm_submit import validated_document
    first = validated_document()
    first.update(source_file="first.png", processing_status="completed", extracted_text="<b>Untrusted source</b>")
    second = {"source_file": "second.pdf", "processing_status": "failed", "error": "No text"}
    window.processing_completed([first, second])
    assert window.result_selector.count() == 2
    assert "No text" in window.validation_list.item(0).text()
    window.result_selector.setCurrentIndex(0)
    assert window.ocr_preview.toPlainText() == "<b>Untrusted source</b>"
    assert window.data_tree.topLevelItem(3).child(1).text(1) == "$75000"
    window.close()
    app.processEvents()


def test_selection_and_reentry_are_blocked_during_processing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()
    window.files_selected(["first.png"])
    window.set_processing_active(True)
    window.files_selected(["second.png"])
    window.clear_selection()
    window.process_documents()
    assert window.selected_files == ["first.png"]
    assert window.worker_thread is None
    assert not window.config_action.isEnabled()
    assert not window.browse_btn.isEnabled()
    window.set_processing_active(False)
    assert window.process_btn.isEnabled()
    window.close()
    app.processEvents()
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
