# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['flask', 'jinja2', 'werkzeug', 'pandas', 'numpy', 'openpyxl', 'xlsxwriter']
hiddenimports += collect_submodules('werkzeug')
hiddenimports += collect_submodules('jinja2')

# Minimal excludes - only things definitely not needed (prioritize performance over size)
excludes = [
    'tkinter', 'matplotlib', 'scipy', 'PIL', 'IPython', 
    'notebook', 'jupyter', 'pytest'
]

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('data', 'data')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=True,  # Keep .pyc files separate - faster startup (no archive extraction)
    optimize=2,  # Bytecode optimization (removes docstrings/asserts)
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Hypertrophy-Toolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX - improves startup time (no decompression needed)
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['static\\images\\favicon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX for faster startup
    upx_exclude=[],
    name='Hypertrophy-Toolbox',
)
