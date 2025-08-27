# -*- mode: python ; coding: utf-8 -*-
# MoneyPulse Build Configuration
# Enterprise Financial Document Processing Solution

import sys
from pathlib import Path

block_cipher = None

# Define the main script
main_script = 'main.py'

# Data files to include
added_files = [
    ('input', 'input'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Hidden imports for enterprise application
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'pytesseract',
    'cv2',
    'PIL',
    'PIL.Image',
    'pdf2image',
    'requests',
    'numpy',
    'qtawesome',
    'qdarkstyle',
    'pyqtgraph',
    'pathlib',
    'datetime',
    'json',
    'csv',
    'logging',
    'typing',
]

# Analysis phase
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
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create enterprise executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MoneyPulse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application for professional use
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Will add professional icon later
    version=None,
)