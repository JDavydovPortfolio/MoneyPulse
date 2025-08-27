# -*- mode: python ; coding: utf-8 -*-

# Lightweight build - excludes heavy AI dependencies
# Results in ~100-200 MB executable instead of 2.5 GB

import sys
from pathlib import Path

block_cipher = None

# Define the main script
main_script = 'main.py'

# Data files to include
added_files = [
    ('input', 'input'),
]

# Minimal hidden imports (no PyTorch/Transformers)
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'pytesseract',
    'PIL',
    'PIL.Image',
    'pdf2image',
    'requests',
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
        # Exclude the heavy dependencies
        'torch',
        'torchvision', 
        'transformers',
        'sentence_transformers',
        'numpy',  # Only if not needed for other features
        'opencv-python',
        'cv2',
        'pandas',
        'pyqtgraph',
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'tensorboard',
        'torch.utils.tensorboard',
        'tensorflow',  # In case it's pulled in
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MerchantProcessor-Lite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app_icon.ico' if Path('resources/app_icon.ico').exists() else None,
)