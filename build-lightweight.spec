# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MoneyPulse using local HTTP model providers.

This configuration intentionally excludes the optional in-process Transformers stack.
It has not been verified as a distributable binary by the current modernization pass.
"""

from pathlib import Path

block_cipher = None
main_script = "main.py"
added_files = [("input", "input"), ("README.md", "."), ("LICENSE", ".")]
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

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "transformers", "sentence_transformers", "pandas", "pyqtgraph"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MoneyPulse-Local",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
