# Changelog

All notable changes to the MoneyPulse project will be documented in this file.

## [v1.0.0] - 2025-08-06

### Initial Release

#### Added
- **Standalone Windows Executable** - `MoneyPulse.exe` (~2.5 GB)
  - No Python installation required
  - All dependencies bundled (PySide6, PyTorch, OpenCV, Tesseract, etc.)
  - Ready-to-run on any Windows 10/11 (64-bit) machine
- **Premium GUI Interface** - Professional PySide6 application with dark theme
- **Advanced OCR Processing** - Tesseract integration for PDF and image text extraction
- **AI-Powered Document Parsing** - Local LLM processing with Ollama/LM Studio support
- **Smart Validation Engine** - Business rule validation with error flagging
- **CRM Integration** - Clean JSON/CSV output ready for CRM systems
- **100% Offline Processing** - Documents never leave your computer
- **Multi-threaded Performance** - Progress tracking and optimized processing

#### Technical Features
- **Document Types Supported**: Merchant applications, W-9 forms, voided checks, bank statements
- **File Formats**: PDF (multi-page), PNG, JPG, JPEG
- **Output Formats**: JSON (structured data), CSV (Excel-friendly summaries)
- **Logging**: Comprehensive application and processing logs
- **Build System**: PyInstaller configuration for executable creation

#### Distribution
- **EXE Download**: Available in GitHub Releases
- **Source Code**: Available for developers and customization
- **Build Scripts**: Automated building with `build.bat`

### Developer Tools
- **PyInstaller Spec**: `build-merchant.spec` for consistent builds
- **Requirements**: Complete Python dependencies list
- **Documentation**: Comprehensive README with installation and usage guide

---

## Future Releases

### Planned Features
- Sample document templates
- Additional LLM provider support
- Enhanced validation rules
- Cloud storage integration options
- Multi-language OCR support

### Version Numbering
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)