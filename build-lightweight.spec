# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MoneyPulse using local HTTP model providers.

This configuration intentionally excludes the optional in-process Transformers stack.
Only the input notice is bundled from input/. User documents must never enter the build.
"""

import os
import sys
from pathlib import Path

main_script = "main.py"
added_files = [
    ("input/README.txt", "input"),
    ("LICENSE", "."),
    ("src/gui/resources/Inter.ttf", "src/gui/resources"),
    ("src/gui/resources/Inter-OFL.txt", "src/gui/resources"),
]
hidden_imports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "pytesseract",
    "cv2",
    "numpy",
    "PIL",
    "PIL.Image",
    "pdf2image",
    "requests",
    "yaml",
    "qtawesome",
    "qdarkstyle",
]

if sys.platform == "win32":
    # Resolve DLLs from the build interpreter, wheels, and Windows only.
    # A Poppler directory on PATH can otherwise contribute its incompatible
    # icuuc.dll in place of the Windows ICU library required by Qt.
    windows_dir = Path(os.environ["SystemRoot"])
    os.environ["PATH"] = os.pathsep.join(
        map(str, [windows_dir / "System32", windows_dir, Path(sys.executable).parent, sys.base_prefix])
    )

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch", "transformers", "sentence_transformers", "pandas", "pyqtgraph",
        "qtpy.QtDataVisualization",
    ],
    noarchive=False,
)
if sys.platform == "win32":
    # OCR uses Poppler for PDF and the app has no QML, virtual keyboard,
    # or video workflow. Qt and OpenCV hooks also collect these plugins.
    unused_binaries = {
        "qpdf.dll", "qt6pdf.dll",
        "qtvirtualkeyboardplugin.dll", "qt6virtualkeyboard.dll",
        "qt6qml.dll", "qt6qmlmeta.dll", "qt6qmlmodels.dll",
        "qt6qmlworkerscript.dll", "qt6quick.dll",
    }
    a.binaries = [
        entry for entry in a.binaries
        if Path(entry[0]).name.lower() not in unused_binaries
        and not Path(entry[0]).name.lower().startswith("opencv_videoio_ffmpeg")
    ]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MoneyPulse-Local",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/app_icon.ico" if Path("resources/app_icon.ico").exists() else None,
)
