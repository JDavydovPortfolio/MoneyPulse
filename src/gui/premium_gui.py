import os
import sys
from datetime import datetime
from typing import Dict, List

import qdarkstyle
import qtawesome as qta
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import load_config, save_config
from src.llm_detector import LLMProviderDetector, RECOMMENDED_MODEL
from src.pipeline import DocumentPipeline


class DocumentProcessorWorker(QThread):
    """Process documents away from the UI thread."""

    progress_updated = Signal(int, int, str)
    document_processed = Signal(dict)
    processing_completed = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, pipeline: DocumentPipeline, files: List[str]):
        super().__init__()
        self.pipeline = pipeline
        self.files = files
        self.processed_documents = []

    def run(self):
        try:
            for index, file_path in enumerate(self.files):
                self.progress_updated.emit(
                    index,
                    len(self.files),
                    f"Processing {os.path.basename(file_path)}",
                )
                result = self.pipeline.process_single_document(file_path)
                self.processed_documents.append(result)
                self.document_processed.emit(result)
                if self.isInterruptionRequested():
                    break
            self.processing_completed.emit(self.processed_documents)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class DropArea(QLabel):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(150)
        self.setText(
            "Drag & Drop Financial Documents Here\n\n"
            "Supported: PDF, PNG, JPG, JPEG\n\n"
            "OCR • Local AI • Source Grounding • Validation"
        )
        self._normal_style()

    def _normal_style(self):
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #2E7D32;
                border-radius: 8px;
                padding: 25px;
                font-size: 14px;
                background-color: rgba(46, 125, 50, 0.08);
                color: #2E7D32;
            }
            QLabel:hover {
                background-color: rgba(46, 125, 50, 0.12);
                border-color: #1B5E20;
            }
            """
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                """
                QLabel {
                    border: 2px solid #2E7D32;
                    border-radius: 8px;
                    padding: 25px;
                    font-size: 14px;
                    background-color: rgba(46, 125, 50, 0.15);
                    color: #2E7D32;
                }
                """
            )

    def dragLeaveEvent(self, event):
        self._normal_style()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                files.append(path)
        if files:
            self.files_dropped.emit(files)
            self.setText(f"{len(files)} file(s) selected")
        else:
            self.setText("No supported files found")
        self._normal_style()


class PremiumDocumentProcessor(QMainWindow):
    """MoneyPulse desktop workflow for source-grounded document extraction and review."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MoneyPulse - MCA Underwriting Document Intelligence")
        self.setMinimumSize(1400, 900)
        self.setWindowIcon(qta.icon("fa5s.chart-line", color="#2E7D32"))

        self.selected_files = []
        self.processed_documents = []
        self.worker_thread = None
        self.processing_active = False

        self.setup_pipeline()
        self.setup_ui()
        self.setup_connections()
        self.setup_menu_bar()
        QTimer.singleShot(1000, self.test_system_components)

    def setup_pipeline(self):
        config = {
            "llm_provider": "ollama",
            "model": RECOMMENDED_MODEL,
            "tesseract_path": None,
        }
        try:
            config.update(load_config())
        except (ValueError, OSError) as exc:
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"Saved configuration could not be loaded; using defaults.\n{exc}",
            )
        try:
            self.pipeline = DocumentPipeline(output_dir="output", config=config)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize processing pipeline:\n{exc}",
            )
            raise

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.addWidget(self.create_control_panel(), 1)
        main_layout.addWidget(self.create_results_panel(), 2)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to process merchant documents")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_control_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        file_group = QGroupBox("Document Upload")
        file_layout = QVBoxLayout(file_group)
        self.drop_area = DropArea()
        file_layout.addWidget(self.drop_area)

        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setIcon(qta.icon("fa5s.folder-open", color="white"))
        self.browse_btn.clicked.connect(self.browse_files)
        file_layout.addWidget(self.browse_btn)

        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.setIcon(qta.icon("fa5s.trash", color="white"))
        self.clear_btn.clicked.connect(self.clear_selection)
        file_layout.addWidget(self.clear_btn)
        layout.addWidget(file_group)

        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)
        self.process_btn = QPushButton("Process Documents")
        self.process_btn.setIcon(qta.icon("fa5s.play", color="white"))
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.process_documents)
        process_layout.addWidget(self.process_btn)

        self.stop_btn = QPushButton("Stop Processing")
        self.stop_btn.setIcon(qta.icon("fa5s.stop", color="white"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        process_layout.addWidget(self.stop_btn)
        layout.addWidget(process_group)

        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        self.export_csv_btn = QPushButton("Export CSV Summary")
        self.export_csv_btn.setIcon(qta.icon("fa5s.file-csv", color="white"))
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)

        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.setIcon(qta.icon("fa5s.external-link-alt", color="white"))
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        export_layout.addWidget(self.open_folder_btn)
        layout.addWidget(export_group)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(110)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        test_btn = QPushButton("Test System")
        test_btn.setIcon(qta.icon("fa5s.check-circle", color="white"))
        test_btn.clicked.connect(self.test_system_components)
        status_layout.addWidget(test_btn)
        layout.addWidget(status_group)

        layout.addStretch()
        return widget

    def create_results_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Document results"))

        self.result_selector = QComboBox()
        self.result_selector.setPlaceholderText("Process documents to inspect results")
        self.result_selector.currentIndexChanged.connect(self.show_selected_result)
        layout.addWidget(self.result_selector)

        self.tab_widget = QTabWidget()

        self.ocr_preview = QTextEdit()
        self.ocr_preview.setReadOnly(True)
        self.ocr_preview.setPlaceholderText("OCR extracted text will appear here...")
        self.tab_widget.addTab(self.ocr_preview, "OCR Preview")

        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["Field", "Value", "Status"])
        self.data_tree.setAlternatingRowColors(True)
        self.data_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.data_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.data_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tab_widget.addTab(self.data_tree, "Extracted Data")

        self.underwriting_tree = QTreeWidget()
        self.underwriting_tree.setHeaderLabels(["Reviewed Metric", "Value", "Status"])
        self.underwriting_tree.setAlternatingRowColors(True)
        self.underwriting_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.underwriting_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.underwriting_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tab_widget.addTab(self.underwriting_tree, "Derived Metrics")

        self.validation_list = QListWidget()
        self.tab_widget.addTab(self.validation_list, "Validation Results")

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.tab_widget.addTab(self.log_text, "Processing Log")

        layout.addWidget(self.tab_widget)
        return widget

    def setup_connections(self):
        self.drop_area.files_dropped.connect(self.files_selected)

    def setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction(qta.icon("fa5s.folder-open"), "Open Files", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_files)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction(qta.icon("fa5s.times"), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("Settings")
        self.config_action = QAction(qta.icon("fa5s.cog"), "Configuration", self)
        self.config_action.triggered.connect(self.show_configuration)
        settings_menu.addAction(self.config_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction(qta.icon("fa5s.info-circle"), "About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)",
        )
        if files:
            self.files_selected(files)

    def files_selected(self, files: List[str]):
        if self.processing_active:
            return
        self.selected_files = files
        self.process_btn.setEnabled(True)
        self.drop_area.setText(f"{len(files)} file(s) selected")
        self.clear_results()
        self.status_bar.showMessage(f"{len(files)} files selected")
        self.log_message(f"Selected {len(files)} files for processing")

    def clear_selection(self):
        if self.processing_active:
            return
        self.selected_files = []
        self.process_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)
        self.drop_area.setText(
            "Drag & Drop Financial Documents Here\n\nSupported: PDF, PNG, JPG, JPEG"
        )
        self.clear_results()
        self.status_bar.showMessage("Ready to process merchant documents")

    def clear_results(self):
        self.ocr_preview.clear()
        self.data_tree.clear()
        self.underwriting_tree.clear()
        self.validation_list.clear()
        self.processed_documents = []
        self.result_selector.clear()
        self.export_csv_btn.setEnabled(False)

    def set_processing_active(self, active):
        self.processing_active = active
        self.process_btn.setEnabled(not active and bool(self.selected_files))
        self.browse_btn.setEnabled(not active)
        self.clear_btn.setEnabled(not active)
        self.drop_area.setAcceptDrops(not active)
        self.config_action.setEnabled(not active)
        self.stop_btn.setEnabled(active)
        self.export_csv_btn.setEnabled(not active and bool(self.processed_documents))

    def process_documents(self):
        if self.processing_active or not self.selected_files:
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)
        self.clear_results()
        self.set_processing_active(True)

        self.worker_thread = DocumentProcessorWorker(self.pipeline, self.selected_files)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.document_processed.connect(self.document_processed)
        self.worker_thread.processing_completed.connect(self.processing_completed)
        self.worker_thread.error_occurred.connect(self.processing_error)
        self.worker_thread.finished.connect(lambda: self.set_processing_active(False))
        self.worker_thread.start()
        self.log_message(f"Started processing {len(self.selected_files)} documents")

    def stop_processing(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("Stopping after the current document finishes")
            self.log_message("Stop requested; waiting for the current document")

    def update_progress(self, current: int, total: int, message: str):
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"{message} ({current}/{total})")

    def document_processed(self, result: Dict):
        filename = result.get("source_file", "Unknown")
        if result.get("processing_status") == "completed":
            self.log_message(f"Completed: {filename}")
            self.update_results_display(result)
        else:
            self.log_message(f"Failed: {filename} - {result.get('error', 'Unknown error')}")

    def processing_completed(self, processed_documents: List[Dict]):
        self.processed_documents = processed_documents
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.result_selector.blockSignals(True)
        self.result_selector.clear()
        for document in processed_documents:
            status = document.get("validation_status", document.get("processing_status", "unknown"))
            self.result_selector.addItem(f"{document.get('source_file', 'Unknown')} — {status}")
        self.result_selector.blockSignals(False)

        if processed_documents:
            self.result_selector.setCurrentIndex(len(processed_documents) - 1)
            self.show_selected_result(len(processed_documents) - 1)

        successful = sum(
            1 for doc in processed_documents if doc.get("processing_status") == "completed"
        )
        failed = len(processed_documents) - successful
        self.status_bar.showMessage(
            f"Processing completed: {successful} successful, {failed} failed"
        )
        self.log_message(f"Processing completed: {successful} successful, {failed} failed")
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Processed {len(processed_documents)} documents\n\n"
            f"Successful: {successful}\nFailed: {failed}\n\n"
            "Results saved to output folder.",
        )

    def processing_error(self, error_message: str):
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Processing failed")
        self.log_message(f"Processing error: {error_message}")
        QMessageBox.critical(self, "Processing Error", f"Processing failed:\n{error_message}")

    def show_selected_result(self, index):
        if 0 <= index < len(self.processed_documents):
            self.update_results_display(self.processed_documents[index])

    def update_results_display(self, result: Dict):
        self.ocr_preview.setPlainText(result.get("extracted_text", ""))
        self.data_tree.clear()
        self.underwriting_tree.clear()
        self.validation_list.clear()

        if result.get("processing_status") == "failed":
            self.validation_list.addItem(
                f"Processing failed: {result.get('error', 'Unknown error')}"
            )
            return

        merchant_item = QTreeWidgetItem(["Merchant Information", "", ""])
        self.data_tree.addTopLevelItem(merchant_item)
        merchant_name = result.get("merchant_name", "")
        merchant_item.addChild(
            QTreeWidgetItem(["Name", merchant_name, "Present" if merchant_name else "Missing"])
        )
        ein_ssn = result.get("ein_or_ssn", "")
        merchant_item.addChild(
            QTreeWidgetItem(["EIN/SSN", ein_ssn, "Present" if ein_ssn else "Not provided"])
        )

        address_item = QTreeWidgetItem(["Address", "", ""])
        self.data_tree.addTopLevelItem(address_item)
        address = result.get("address", {}) or {}
        for field in ("street", "city", "state", "zip"):
            value = address.get(field, "")
            address_item.addChild(
                QTreeWidgetItem([field.title(), str(value), "Present" if value else "Not provided"])
            )

        contact_item = QTreeWidgetItem(["Contact Information", "", ""])
        self.data_tree.addTopLevelItem(contact_item)
        contact = result.get("contact_info", {}) or {}
        for field in ("phone", "email"):
            value = contact.get(field, "")
            contact_item.addChild(
                QTreeWidgetItem([field.title(), str(value), "Present" if value else "Not provided"])
            )

        application_item = QTreeWidgetItem(["Application", "", ""])
        self.data_tree.addTopLevelItem(application_item)
        for field in ("document_type", "requested_amount"):
            value = result.get(field, "")
            application_item.addChild(
                QTreeWidgetItem(
                    [field.replace("_", " ").title(), str(value), "Present" if value else "Not provided"]
                )
            )

        business_item = QTreeWidgetItem(["Business Information", "", ""])
        self.data_tree.addTopLevelItem(business_item)
        for field, value in (result.get("business_info", {}) or {}).items():
            business_item.addChild(
                QTreeWidgetItem(
                    [field.replace("_", " ").title(), str(value), "Present" if value else "Not provided"]
                )
            )
        self.data_tree.expandAll()

        self._populate_underwriting(result.get("underwriting", {}) or {})
        self._populate_validation(result)

    def _populate_underwriting(self, underwriting: Dict):
        status = underwriting.get("status", "awaiting_review") if underwriting else "awaiting_review"
        if status != "calculated":
            self.underwriting_tree.addTopLevelItem(
                QTreeWidgetItem(
                    [
                        "Derived calculations",
                        "Awaiting human review",
                        "Not calculated",
                    ]
                )
            )
            return

        inputs_item = QTreeWidgetItem(["Reviewed Inputs", "", "Approved"])
        self.underwriting_tree.addTopLevelItem(inputs_item)
        for key, value in (underwriting.get("inputs", {}) or {}).items():
            display = "Not available" if value is None else str(value)
            inputs_item.addChild(
                QTreeWidgetItem([key.replace("_", " ").title(), display, "Reviewed"])
            )

        metrics_item = QTreeWidgetItem(["Derived Ratios", "", "Calculated"])
        self.underwriting_tree.addTopLevelItem(metrics_item)
        for key, value in (underwriting.get("metrics", {}) or {}).items():
            display = "Not available" if value is None else str(value)
            metrics_item.addChild(
                QTreeWidgetItem([key.replace("_", " ").title(), display, ""])
            )
        self.underwriting_tree.expandAll()

    def _populate_validation(self, result: Dict):
        validation_status = result.get("validation_status", "unknown")
        review_state = result.get("review_state", "unreviewed")

        status_item = QListWidgetItem(f"Overall Status: {validation_status.upper()}")
        status_item.setIcon(
            qta.icon(
                "fa5s.check-circle" if validation_status == "passed" else "fa5s.exclamation-triangle"
            )
        )
        self.validation_list.addItem(status_item)

        review_item = QListWidgetItem(
            f"Review State: {review_state.replace('_', ' ').title()}"
        )
        review_item.setIcon(qta.icon("fa5s.user-check"))
        self.validation_list.addItem(review_item)
        self.validation_list.addItem(
            "Compare extracted values with the source document before downstream use."
        )

        issues = result.get("flagged_issues", []) or []
        if issues:
            self.validation_list.addItem(QListWidgetItem(""))
            header_item = QListWidgetItem("Flagged Issues:")
            header_item.setIcon(qta.icon("fa5s.flag"))
            self.validation_list.addItem(header_item)
            for issue in issues:
                issue_item = QListWidgetItem(f"• {issue}")
                issue_item.setIcon(qta.icon("fa5s.exclamation-circle"))
                self.validation_list.addItem(issue_item)
        else:
            self.validation_list.addItem(QListWidgetItem(""))
            no_issues = QListWidgetItem("✅ No validation issues found")
            no_issues.setIcon(qta.icon("fa5s.check"))
            self.validation_list.addItem(no_issues)

    def export_csv(self):
        if not self.processed_documents:
            QMessageBox.warning(self, "Warning", "No processed documents to export")
            return
        try:
            csv_file = self.pipeline.crm.generate_csv_summary(self.processed_documents)
            QMessageBox.information(
                self,
                "Export Complete",
                f"CSV summary exported successfully!\n\nFile: {csv_file}",
            )
            self.log_message(f"CSV summary exported: {csv_file}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV:\n{exc}")

    def open_output_folder(self):
        import platform
        import subprocess

        output_path = os.path.abspath("output")
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", output_path])
            elif platform.system() == "Darwin":
                subprocess.run(["open", output_path])
            else:
                subprocess.run(["xdg-open", output_path])
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{exc}")

    def test_system_components(self):
        self.status_text.clear()
        self.status_text.append("Testing system components...\n")
        for component, result in self.pipeline.test_system_components().items():
            icon = "✅" if result["status"] == "ok" else "❌"
            self.status_text.append(f"{icon} {component.upper()}: {result['details']}")
        self.status_text.append("\nTest completed.")

    def show_configuration(self):
        if self.processing_active:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("MoneyPulse Configuration")
        dialog.setModal(True)
        dialog.resize(560, 420)
        layout = QVBoxLayout(dialog)
        detector = LLMProviderDetector()

        model_group = QGroupBox("Local Model Settings")
        model_layout = QFormLayout(model_group)
        provider_combo = QComboBox()
        provider_combo.addItem("Transformers (in-process)", "transformers")
        provider_combo.addItem("Ollama (recommended)", "ollama")
        provider_combo.addItem("LM Studio", "lm_studio")
        provider_combo.addItem("llama.cpp", "llama_cpp")

        current_provider = self.pipeline.config.get("llm_provider", "ollama")
        for index in range(provider_combo.count()):
            if provider_combo.itemData(index) == current_provider:
                provider_combo.setCurrentIndex(index)
                break

        host_edit = QLineEdit(
            self.pipeline.config.get("llm_host")
            or self.pipeline.config.get("ollama_host", "")
        )
        model_edit = QLineEdit(self.pipeline.config.get("model", RECOMMENDED_MODEL))
        provider_defaults = {
            "transformers": "",
            "ollama": "http://localhost:11434",
            "lm_studio": "http://localhost:1234",
            "llama_cpp": "http://localhost:8080",
        }

        def sync_provider_fields():
            provider_id = provider_combo.currentData()
            current_host = host_edit.text().strip()
            known_hosts = {value for value in provider_defaults.values() if value}
            if provider_id == "transformers":
                host_edit.clear()
                host_edit.setEnabled(False)
                host_edit.setPlaceholderText("Not used for in-process Transformers")
            else:
                host_edit.setEnabled(True)
                if not current_host or current_host in known_hosts:
                    host_edit.setText(provider_defaults[provider_id])
                host_edit.setPlaceholderText(provider_defaults[provider_id])

        provider_combo.currentIndexChanged.connect(sync_provider_fields)
        sync_provider_fields()

        def detect_local_ai():
            config = detector.detect_recommended_config(provider_ids=("ollama", "lm_studio"))
            if not config:
                QMessageBox.warning(
                    dialog,
                    "No Local AI Detected",
                    "MoneyPulse could not find a running Ollama or LM Studio server with an available model.\n\n"
                    "Recommended setup: Qwen3 8B through Ollama, or a compatible Qwen3 8B GGUF loaded in LM Studio. "
                    "Qwen3 4B is a lighter option for lower-memory systems.",
                )
                return
            for index in range(provider_combo.count()):
                if provider_combo.itemData(index) == config["llm_provider"]:
                    provider_combo.setCurrentIndex(index)
                    break
            host_edit.setText(config["llm_host"])
            model_edit.setText(config["model"])
            QMessageBox.information(
                dialog,
                "Local AI Detected",
                f"Provider: {config['llm_provider']}\nModel: {config['model']}",
            )

        detect_button = QPushButton("Auto-detect Ollama / LM Studio")
        detect_button.clicked.connect(detect_local_ai)
        model_layout.addRow("Provider:", provider_combo)
        model_layout.addRow("Host:", host_edit)
        model_layout.addRow("Model:", model_edit)
        model_layout.addRow("", detect_button)
        layout.addWidget(model_group)

        note = QLabel(
            "Recommended local default: Qwen3 8B. The model proposes structured fields from OCR text; "
            "MoneyPulse checks proposed values against the source and does not use the model to invent missing financial facts."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.Accepted:
            return

        new_config = {
            "llm_provider": provider_combo.currentData(),
            "llm_host": host_edit.text().strip(),
            "model": model_edit.text().strip(),
        }
        try:
            self.pipeline.update_config(new_config)
        except Exception as exc:
            QMessageBox.warning(self, "Configuration Error", str(exc))
            return

        try:
            save_config(self.pipeline.config)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(
                self,
                "Settings Not Saved",
                f"Settings apply for this session but could not be saved.\n{exc}",
            )
        self.log_message(
            f"Configuration updated: {new_config['llm_provider']} / {new_config['model']}"
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "About MoneyPulse",
            """
            <h3>MoneyPulse</h3>
            <p>MCA underwriting document intelligence</p>
            <ul>
              <li>OCR extraction from merchant documents</li>
              <li>Local AI structured-field extraction</li>
              <li>Source-grounded deterministic validation</li>
              <li>Analyst/underwriter review of extracted values</li>
              <li>Review-gated derived ratios and optional downstream integration</li>
            </ul>
            <p><b>Local-first by design.</b> OCR and model inference can remain on the operator's machine or private network.</p>
            """,
        )

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertPlainText(f"[{timestamp}] {message}\n")
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Document processing is still running. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.stop_processing()
                self.worker_thread.finished.connect(self.close)
                event.ignore()
            else:
                event.ignore()
        else:
            event.accept()


def launch_application():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    custom_style = """
    QMainWindow { background: #1e1e1e; }
    QPushButton {
        background-color: #2E7D32;
        border: 1px solid #1B5E20;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        color: white;
    }
    QPushButton:hover { background-color: #388E3C; }
    QPushButton:pressed { background-color: #1B5E20; }
    QPushButton:disabled { background: #666666; color: #999999; }
    QGroupBox {
        border: 1px solid #2E7D32;
        border-radius: 6px;
        margin: 8px;
        padding: 12px;
        font-weight: 500;
        color: #2E7D32;
    }
    QTextEdit, QListWidget, QTreeWidget {
        border: 1px solid #2E7D32;
        border-radius: 4px;
        padding: 8px;
        background: #1a1a1a;
        selection-background-color: #2E7D32;
    }
    QProgressBar { border: 1px solid #2E7D32; border-radius: 4px; text-align: center; }
    QProgressBar::chunk { background-color: #2E7D32; border-radius: 3px; }
    QStatusBar { background: #1e1e1e; border-top: 1px solid #2E7D32; color: #2E7D32; }
    """
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6() + custom_style)
    app.setApplicationName("MoneyPulse")
    app.setOrganizationName("MoneyPulse")
    window = PremiumDocumentProcessor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_application()
