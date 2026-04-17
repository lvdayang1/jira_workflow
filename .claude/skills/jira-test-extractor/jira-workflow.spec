# -*- coding: utf-8 -*-
"""PyInstaller spec file for jira-workflow CLI"""
import os
import sys

block_cipher = None

# Determine if we're in build mode or install mode
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    datas = []
    hiddenimports = []
else:
    datas = [
        ('src', 'src'),
        ('templates', 'templates'),
    ]
    hiddenimports = [
        'click',
        'openpyxl',
        'docx',
        'pptx',
        'PIL',
        'yaml',
        'requests',
        'PyPDF2',
        'pdfplumber',
        'pytesseract',
        'playwright',
        'jinja2',
    ]

a = Analysis(
    ['src/cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    win_prefer_remote=False,
    cipher=block_cipher,
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
    ],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='jira-workflow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
