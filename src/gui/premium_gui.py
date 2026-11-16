import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QFontDatabase, QTextCursor
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
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import qdarkstyle
import qtawesome as qta

from src.config import load_config, save_config
from src.llm_detector import LLMProviderDetector, RECOMMENDED_MODEL
from src.pipeline import DocumentPipeline


WORKSPACE_STYLE = """
QMainWindow, QWidget#workspace {
    background-color: #0f1722;
    color: #e4edf4;
}
QMenuBar, QStatusBar {
    background-color: #0c131d;
    color: #adbdcb;
}
QMenuBar::item {
    background-color: transparent;
    padding: 4px 9px;
}
QMenuBar::item:selected {
    background-color: #233346;
}
QWidget#workspaceHeader {
    background-color: #111c29;
    border-bottom: 1px solid #263648;
}
QWidget#workspaceHeader QLabel, QWidget#resultsPanel QLabel {
    background-color: transparent;
}
QLabel#workspaceTitle {
    color: #f4f8fb;
    font-size: 25px;
    font-weight: 700;
}
QLabel#workspaceSubtitle {
    color: #a3b5c6;
    font-size: 13px;
}
QLabel#brandMark {
    background-color: #143c3b;
    border-radius: 11px;
}
QScrollArea#workflowPanel, QWidget#workflowControls,
QWidget#workflowControls QGroupBox, QWidget#resultsPanel {
    background-color: #162130;
    border: 0;
}
QScrollArea#workflowPanel, QWidget#resultsPanel {
    border-radius: 12px;
}
QWidget#workflowControls QGroupBox {
    margin-top: 19px;
    padding-top: 4px;
    font-weight: 600;
}
QWidget#workflowControls QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    color: #d7e3ee;
    padding: 0;
    background-color: #162130;
}
QLabel#documentDrop {
    border: 1px dashed #426479;
    border-radius: 8px;
    padding: 10px;
    background-color: #1a2b3b;
    color: #c5dfed;
}
QWidget#workspace QPushButton {
    background-color: #233447;
    color: #e6eff6;
    border: 1px solid transparent;
    border-radius: 7px;
    min-height: 22px;
    padding: 5px 10px;
    font-weight: 600;
}
QWidget#workspace QPushButton:hover:enabled {
    background-color: #30465c;
}
QWidget#workspace QPushButton:focus:enabled {
    border-color: #90e1d1;
}
QWidget#workspace QPushButton:disabled {
    background-color: #1c2b3b;
    color: #92a3b3;
}
QWidget#workspace QPushButton#processDocuments:enabled {
    background-color: #76e0c3;
    color: #092b2a;
}
QWidget#workspace QPushButton#processDocuments:hover:enabled {
    background-color: #98eed7;
}
QWidget#workspace QPushButton#processDocuments:focus:enabled {
    border-color: #eefffa;
}
QLabel#resultsTitle {
    color: #f1f6fb;
    font-size: 21px;
    font-weight: 700;
}
QWidget#workspace QComboBox, QWidget#workspace QTextEdit,
QWidget#workspace QTreeWidget, QWidget#workspace QListWidget {
    background-color: #101a27;
    color: #e1ecf4;
    border: 1px solid #2b3d50;
    border-radius: 7px;
    padding: 5px 7px;
    selection-background-color: #264c59;
    selection-color: #ffffff;
}
QWidget#workspace QTabWidget::pane {
    border: 0;
    background-color: #162130;
    top: -1px;
}
QWidget#workspace QTabBar::tab {
    background-color: #162130;
    color: #aec1d1;
    border: 0;
    border-bottom: 2px solid #293c4f;
    padding: 10px;
    margin-right: 3px;
}
QWidget#workspace QTabBar::tab:selected {
    color: #9be9d6;
    border-bottom-color: #76e0c3;
    font-weight: 700;
}
QWidget#workspace QTabBar::tab:hover {
    background-color: #1d2e40;
}
QWidget#workspace QHeaderView::section {
    background-color: #1e3042;
    color: #d7e6f1;
    border: 0;
    padding: 6px 8px;
    font-weight: 600;
}
"""


class DocumentProcessorWorker(QThread):
    """Process documents off the UI thread."""

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


class SystemCheckWorker(QThread):
    results_ready = Signal(dict)

    def __init__(self, pipeline: DocumentPipeline, parent):
        super().__init__(parent)
        self.pipeline = pipeline

    def run(self):
        self.results_ready.emit(self.pipeline.test_system_components())


class DropArea(QLabel):
    files_dropped = Signal(list)
    EMPTY_TEXT = "Drop files here\nPDF, PNG, JPG, JPEG"

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(82)
        self.setText(self.EMPTY_TEXT)
        self.setObjectName("documentDrop")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

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


class PremiumDocumentProcessor(QMainWindow):
    """Desktop workflow for source-grounded merchant-document processing."""

    def __init__(self, data_dir=None):
        super().__init__()
        data_dir = Path(data_dir) if data_dir is not None else Path()
        self.config_path = data_dir / "config.yaml"
        self.output_dir = data_dir / "output"
        self.setWindowTitle("MoneyPulse - MCA Document Intelligence")
        self.setMinimumSize(1020, 640)
        self.resize(1180, 790)
        self.setWindowIcon(qta.icon("fa5s.chart-line", color="#9be9d6"))

        self.selected_files = []
        self.processed_documents = []
        self.worker_thread = None
        self.system_check_thread = None
        self.close_after_system_check = False
        self.processing_active = False

        self.setup_pipeline()
        self.setup_ui()
        self.setup_connections()
        self.setup_menu_bar()
        self.startup_check_timer = QTimer(self)
        self.startup_check_timer.setSingleShot(True)
        self.startup_check_timer.setInterval(1000)
        self.startup_check_timer.timeout.connect(self.test_system_components)
        self.startup_check_timer.start()

    def setup_pipeline(self):
        config = {
            "llm_provider": "ollama",
            "model": RECOMMENDED_MODEL,
            "tesseract_path": None,
        }
        try:
            config.update(load_config(self.config_path))
        except (ValueError, OSError) as exc:
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"Saved configuration could not be loaded; using defaults.\n{exc}",
            )
        self.pipeline = DocumentPipeline(output_dir=str(self.output_dir), config=config)

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("workspace")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 12, 20, 16)
        main_layout.setSpacing(14)

        header = QWidget()
        header.setObjectName("workspaceHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 11, 16, 11)
        mark = QLabel()
        mark.setObjectName("brandMark")
        mark.setFixedSize(44, 44)
        mark.setAlignment(Qt.AlignCenter)
        mark.setPixmap(qta.icon("fa5s.chart-line", color="#9be9d6").pixmap(22, 22))
        header_layout.addWidget(mark)
        header_layout.setSpacing(12)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        title = QLabel("MoneyPulse")
        title.setObjectName("workspaceTitle")
        identity.addWidget(title)
        subtitle = QLabel("Merchant document processing")
        subtitle.setObjectName("workspaceSubtitle")
        identity.addWidget(subtitle)
        header_layout.addLayout(identity)
        header_layout.addStretch()
        self.configuration_btn = QPushButton("Configuration")
        self.configuration_btn.setIcon(qta.icon("fa5s.cog", color="#9be9d6"))
        self.configuration_btn.setToolTip("Configure the local model provider")
        self.configuration_btn.clicked.connect(self.show_configuration)
        header_layout.addWidget(self.configuration_btn)
        main_layout.addWidget(header)

        content = QHBoxLayout()
        content.setSpacing(16)
        sidebar = QScrollArea()
        sidebar.setObjectName("workflowPanel")
        sidebar.setWidgetResizable(True)
        sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar.setMinimumWidth(292)
        sidebar.setMaximumWidth(372)
        sidebar.setWidget(self.create_control_panel())
        content.addWidget(sidebar, 1)
        content.addWidget(self.create_results_panel(), 2)
        main_layout.addLayout(content, 1)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to process merchant documents")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_control_panel(self):
        widget = QWidget()
        widget.setObjectName("workflowControls")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(11)

        file_group = QGroupBox("Documents")
        file_layout = QVBoxLayout(file_group)
        self.drop_area = DropArea()
        file_layout.addWidget(self.drop_area)
        file_actions = QHBoxLayout()

        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.clicked.connect(self.browse_files)
        file_actions.addWidget(self.browse_btn)

        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.clear_selection)
        file_actions.addWidget(self.clear_btn)
        file_layout.addLayout(file_actions)
        layout.addWidget(file_group)

        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)
        self.process_btn = QPushButton("Process Documents")
        self.process_btn.setObjectName("processDocuments")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.process_documents)
        process_layout.addWidget(self.process_btn)

        self.stop_btn = QPushButton("Stop Processing")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        process_layout.addWidget(self.stop_btn)
        layout.addWidget(process_group)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self.status_text = QTextEdit()
        self.status_text.setFixedHeight(110)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        self.test_btn = QPushButton("Test System")
        self.test_btn.clicked.connect(self.test_system_components)
        status_layout.addWidget(self.test_btn)
        layout.addWidget(status_group)

        layout.addStretch()
        return widget

    def create_results_panel(self):
        widget = QWidget()
        widget.setObjectName("resultsPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(10)
        review_header = QHBoxLayout()
        title = QLabel("Document review")
        title.setObjectName("resultsTitle")
        review_header.addWidget(title)
        review_header.addStretch()

        self.export_csv_btn = QPushButton("Export CSV Summary")
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self.export_csv)
        review_header.addWidget(self.export_csv_btn)

        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        review_header.addWidget(self.open_folder_btn)
        layout.addLayout(review_header)

        self.result_selector = QComboBox()
        self.result_selector.setAccessibleName("Processed document")
        self.result_selector.setPlaceholderText("Process documents to inspect results")
        self.result_selector.currentIndexChanged.connect(self.show_selected_result)
        layout.addWidget(self.result_selector)

        self.tab_widget = QTabWidget()

        self.ocr_preview = QTextEdit()
        self.ocr_preview.setReadOnly(True)
        self.ocr_preview.setPlaceholderText("Choose a file and click Process Documents to see its OCR text.")
        self.tab_widget.addTab(self.ocr_preview, "OCR Preview")

        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["Field", "Value", "Status"])
        self.data_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.data_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.data_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tab_widget.addTab(self.data_tree, "Extracted Data")

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
        open_action = QAction("Open Files", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_files)
        file_menu.addAction(open_action)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("Settings")
        self.config_action = QAction("Configuration", self)
        self.config_action.triggered.connect(self.show_configuration)
        settings_menu.addAction(self.config_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
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
        self.update_pipeline_actions()
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
        self.drop_area.setText(DropArea.EMPTY_TEXT)
        self.clear_results()
        self.status_bar.showMessage("Ready to process merchant documents")

    def clear_results(self):
        self.ocr_preview.clear()
        self.data_tree.clear()
        self.validation_list.clear()
        self.processed_documents = []
        self.result_selector.clear()
        self.export_csv_btn.setEnabled(False)

    def update_pipeline_actions(self):
        ready = not self.processing_active and self.system_check_thread is None
        self.process_btn.setEnabled(ready and bool(self.selected_files))
        self.config_action.setEnabled(ready)
        self.configuration_btn.setEnabled(ready)
        self.test_btn.setEnabled(ready)

    def set_processing_active(self, active):
        self.processing_active = active
        self.update_pipeline_actions()
        self.browse_btn.setEnabled(not active)
        self.clear_btn.setEnabled(not active)
        self.drop_area.setAcceptDrops(not active)
        self.stop_btn.setEnabled(active)
        self.export_csv_btn.setEnabled(not active and bool(self.processed_documents))

    def process_documents(self):
        if self.processing_active or self.system_check_thread is not None or not self.selected_files:
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
            self.update_results_display(result)

    def processing_completed(self, processed_documents: List[Dict]):
        self.processed_documents = processed_documents
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.result_selector.blockSignals(True)
        self.result_selector.clear()
        for document in processed_documents:
            status = document.get(
                "validation_status", document.get("processing_status", "unknown")
            )
            self.result_selector.addItem(
                f"{document.get('source_file', 'Unknown')} — {status}"
            )
        if processed_documents:
            index = next(
                (i for i, doc in enumerate(processed_documents) if doc.get("processing_status") == "failed"),
                len(processed_documents) - 1,
            )
            self.result_selector.setCurrentIndex(index)
            self.show_selected_result(index)
        self.result_selector.blockSignals(False)

        successful = sum(
            1
            for doc in processed_documents
            if doc.get("processing_status") == "completed"
        )
        failed = len(processed_documents) - successful
        self.status_bar.showMessage(
            f"Processing completed: {successful} successful, {failed} failed"
        )
        self.log_message(
            f"Processing completed: {successful} successful, {failed} failed"
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
        self.validation_list.clear()

        if result.get("processing_status") == "failed":
            self.validation_list.addItem(
                f"Processing failed: {result.get('error', 'Unknown error')}"
            )
            self.tab_widget.setCurrentWidget(self.validation_list)
            return

        merchant_item = QTreeWidgetItem(["Merchant Information", "", ""])
        self.data_tree.addTopLevelItem(merchant_item)
        merchant_name = result.get("merchant_name", "")
        merchant_item.addChild(
            QTreeWidgetItem(
                ["Name", merchant_name, "Present" if merchant_name else "Missing"]
            )
        )
        ein = result.get("ein_or_ssn", "")
        merchant_item.addChild(
            QTreeWidgetItem(
                ["EIN/SSN", ein, "Present" if ein else "Not provided"]
            )
        )

        address_item = QTreeWidgetItem(["Address", "", ""])
        self.data_tree.addTopLevelItem(address_item)
        for field in ("street", "city", "state", "zip"):
            value = (result.get("address", {}) or {}).get(field, "")
            address_item.addChild(
                QTreeWidgetItem(
                    [field.title(), str(value), "Present" if value else "Not provided"]
                )
            )

        contact_item = QTreeWidgetItem(["Contact Information", "", ""])
        self.data_tree.addTopLevelItem(contact_item)
        for field in ("phone", "email"):
            value = (result.get("contact_info", {}) or {}).get(field, "")
            contact_item.addChild(
                QTreeWidgetItem(
                    [field.title(), str(value), "Present" if value else "Not provided"]
                )
            )

        application_item = QTreeWidgetItem(["Application", "", ""])
        self.data_tree.addTopLevelItem(application_item)
        for field in ("document_type", "requested_amount"):
            value = result.get(field, "")
            application_item.addChild(
                QTreeWidgetItem(
                    [
                        field.replace("_", " ").title(),
                        str(value),
                        "Present" if value else "Not provided",
                    ]
                )
            )

        business_item = QTreeWidgetItem(["Business Information", "", ""])
        self.data_tree.addTopLevelItem(business_item)
        for field, value in (result.get("business_info", {}) or {}).items():
            business_item.addChild(
                QTreeWidgetItem(
                    [
                        field.replace("_", " ").title(),
                        str(value),
                        "Present" if value else "Not provided",
                    ]
                )
            )
        self.data_tree.expandAll()

        validation_status = result.get("validation_status", "unknown")
        review_state = result.get("review_state", "unreviewed")
        self.validation_list.addItem(
            QListWidgetItem(f"Overall Status: {validation_status.upper()}")
        )
        self.validation_list.addItem(
            QListWidgetItem(
                f"Review State: {review_state.replace('_', ' ').title()}"
            )
        )
        self.validation_list.addItem(
            "Compare extracted values with the source document before downstream use."
        )
        for issue in result.get("flagged_issues", []) or []:
            self.validation_list.addItem(QListWidgetItem(f"• {issue}"))

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
        output_path = str(self.output_dir.resolve())
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(output_path)):
            QMessageBox.warning(self, "Output Folder", f"Could not open {output_path}")

    def test_system_components(self):
        if self.processing_active:
            if not self.status_text.toPlainText():
                self.startup_check_timer.start()
            return
        if self.system_check_thread is not None:
            return
        self.startup_check_timer.stop()
        self.status_text.setPlainText("Testing system components...\n")
        self.system_check_thread = SystemCheckWorker(self.pipeline, self)
        self.system_check_thread.results_ready.connect(self.show_system_check_results)
        self.system_check_thread.finished.connect(self.finish_system_check)
        self.update_pipeline_actions()
        self.system_check_thread.start()

    def show_system_check_results(self, results):
        lines = ["Testing system components...", ""]
        for component, result in results.items():
            icon = "✅" if result["status"] == "ok" else "❌"
            lines.append(f"{icon} {component.upper()}: {result['details']}")
        lines.extend(("", "Test completed."))
        self.status_text.setPlainText("\n".join(lines))

    def finish_system_check(self):
        self.system_check_thread.deleteLater()
        self.system_check_thread = None
        self.update_pipeline_actions()
        if self.close_after_system_check:
            self.close()

    def show_configuration(self):
        if self.processing_active or self.system_check_thread is not None:
            return
        startup_check_pending = self.startup_check_timer.isActive()
        self.startup_check_timer.stop()

        dialog = QDialog(self)
        dialog.setWindowTitle("MoneyPulse Configuration")
        dialog.setModal(True)
        dialog.resize(520, 360)
        layout = QVBoxLayout(dialog)
        detector = LLMProviderDetector()

        group = QGroupBox("Local Model Settings")
        form = QFormLayout(group)
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
            known = {value for value in provider_defaults.values() if value}
            if provider_id == "transformers":
                host_edit.clear()
                host_edit.setEnabled(False)
            else:
                host_edit.setEnabled(True)
                if not current_host or current_host in known:
                    host_edit.setText(provider_defaults[provider_id])

        provider_combo.currentIndexChanged.connect(sync_provider_fields)
        sync_provider_fields()

        def detect_local_ai():
            config = detector.detect_recommended_config(
                provider_ids=("ollama", "lm_studio")
            )
            if not config:
                QMessageBox.warning(
                    dialog,
                    "No Local AI Detected",
                    "No running Ollama or LM Studio server with an available model was detected.\n\n"
                    "Recommended setup: Qwen3 8B through Ollama, or a compatible Qwen3 8B GGUF in LM Studio. "
                    "Qwen3 4B is a lighter option for lower-memory systems.",
                )
                return
            for index in range(provider_combo.count()):
                if provider_combo.itemData(index) == config["llm_provider"]:
                    provider_combo.setCurrentIndex(index)
                    break
            host_edit.setText(config["llm_host"])
            model_edit.setText(config["model"])

        detect_button = QPushButton("Auto-detect Ollama / LM Studio")
        detect_button.clicked.connect(detect_local_ai)

        form.addRow("Provider:", provider_combo)
        form.addRow("Host:", host_edit)
        form.addRow("Model:", model_edit)
        form.addRow("", detect_button)
        layout.addWidget(group)

        note = QLabel(
            "Recommended local default: Qwen3 8B. The model proposes structured fields from OCR text; "
            "MoneyPulse checks proposed values against the source and does not use the model to invent missing financial facts."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            if startup_check_pending:
                self.test_system_components()
            return

        new_config = {
            "llm_provider": provider_combo.currentData(),
            "llm_host": host_edit.text().strip(),
            "model": model_edit.text().strip(),
        }
        try:
            self.pipeline.update_config(new_config)
            save_config(self.pipeline.config, self.config_path)
        except Exception as exc:
            QMessageBox.warning(self, "Configuration Error", str(exc))
            if startup_check_pending:
                self.test_system_components()
            return
        self.log_message(
            f"Configuration updated: {new_config['llm_provider']} / {new_config['model']}"
        )
        self.test_system_components()

    def show_about(self):
        QMessageBox.about(
            self,
            "About MoneyPulse",
            """
            <h3>MoneyPulse</h3>
            <p>Local-first document intelligence for MCA underwriting operations.</p>
            <ul>
              <li>OCR extraction from merchant documents</li>
              <li>Local AI structured-field extraction</li>
              <li>Source grounding and deterministic validation</li>
              <li>Reviewable local output for analyst/underwriter workflows</li>
              <li>Optional downstream CRM integration</li>
            </ul>
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
        if self.system_check_thread is not None:
            self.close_after_system_check = True
            self.status_bar.showMessage("Finishing system checks before closing")
            event.ignore()
        elif self.worker_thread and self.worker_thread.isRunning():
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
            self.startup_check_timer.stop()
            event.accept()


def launch_application(data_dir=None):
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font_file = Path(__file__).resolve().parent / "resources" / "Inter.ttf"
    font_id = QFontDatabase.addApplicationFont(str(font_file))
    families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
    font = app.font()
    font.setFamilies(families + ["Segoe UI", "Arial"])
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6() + WORKSPACE_STYLE)
    app.setApplicationName("MoneyPulse")
    app.setOrganizationName("MoneyPulse")
    window = PremiumDocumentProcessor(data_dir=data_dir)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_application()
