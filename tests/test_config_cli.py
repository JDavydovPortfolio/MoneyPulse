import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from src import cli
from src.config import load_config, save_config


def test_config_roundtrip_and_desktop_restart(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {"llm_provider": "lm_studio", "llm_host": "http://localhost:1234", "model": "test-gemma"}
    save_config(config)
    assert load_config() == config
    from PySide6.QtWidgets import QApplication
    from src.gui.premium_gui import PremiumDocumentProcessor
    app = QApplication.instance() or QApplication([])
    window = PremiumDocumentProcessor()
    assert window.pipeline.llm.provider_id == "lm_studio"
    assert window.pipeline.llm.model == "test-gemma"
    assert window.pipeline.llm.provider.host == "http://localhost:1234"
    window.close()
    app.processEvents()


@pytest.mark.parametrize("text", ["[not, a, mapping]", "model: [one, two]", "llm_host: file:///tmp/private", "unexpected: value", "model: ["])
def test_invalid_config_is_explicitly_rejected(tmp_path, text):
    path = tmp_path / "config.yaml"
    path.write_text(text)
    with pytest.raises(ValueError):
        load_config(path)


def test_failed_save_preserves_previous_settings(tmp_path, monkeypatch):
    import src.config as settings
    path = tmp_path / "config.yaml"
    save_config({"model": "previous"}, path)
    monkeypatch.setattr(settings.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("read only")))
    with pytest.raises(OSError):
        save_config({"model": "replacement"}, path)
    assert load_config(path) == {"model": "previous"}
    assert not list(tmp_path.glob(".moneypulse-config-*"))


def test_cli_real_ocr_to_local_output(tmp_path, monkeypatch, capsys):
    from test_pipeline import _pipeline, _synthetic_image
    monkeypatch.chdir(tmp_path)
    image = tmp_path / "application.png"
    _synthetic_image(image)
    pipeline = _pipeline(tmp_path)
    monkeypatch.setattr(cli, "DocumentPipeline", lambda **kwargs: pipeline)
    assert cli.main(["process", str(image)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["destination"] == "local_only"
    assert summary["documents"][0]["review_state"] == "ready_for_review"
    assert summary["csv_file"]


def test_cli_failure_and_invalid_inputs_have_nonzero_exit(tmp_path, monkeypatch, capsys):
    from test_pipeline import _pipeline
    monkeypatch.chdir(tmp_path)
    assert cli.main(["process", "missing.pdf"]) == 2
    capsys.readouterr()
    path = tmp_path / "broken.png"
    path.write_text("not an image")
    pipeline = _pipeline(tmp_path)
    monkeypatch.setattr(cli, "DocumentPipeline", lambda **kwargs: pipeline)
    assert cli.main(["process", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["documents"][0]["processing_status"] == "failed"


def test_cli_does_not_process_when_provider_is_unavailable(tmp_path, monkeypatch, capsys):
    from test_pipeline import _pipeline
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "application.png"
    path.write_text("fixture")
    pipeline = _pipeline(tmp_path)
    monkeypatch.setattr(pipeline.llm, "test_connection", lambda: False)
    monkeypatch.setattr(pipeline, "process_single_document", lambda _: pytest.fail("processing must not start"))
    monkeypatch.setattr(cli, "DocumentPipeline", lambda **kwargs: pipeline)
    assert cli.main(["process", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["component_checks"]["llm"]["status"] == "error"
