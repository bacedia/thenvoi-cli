# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for thenvoi-cli

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all rich submodules including unicode data
rich_hiddenimports = collect_submodules('rich')

a = Analysis(
    ['src/thenvoi_cli/cli.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('rich'),
    hiddenimports=[
        'thenvoi_cli',
        'thenvoi_cli.commands',
        'thenvoi_cli.commands.config',
        'thenvoi_cli.commands.run',
        'thenvoi_cli.commands.status',
        'thenvoi_cli.commands.rooms',
        'thenvoi_cli.commands.participants',
        'thenvoi_cli.commands.peers',
        'thenvoi_cli.commands.adapters',
        'thenvoi_cli.commands.test',
        'thenvoi_cli.commands.agents',
        'thenvoi_cli.config_manager',
        'thenvoi_cli.adapter_registry',
        'thenvoi_cli.sdk_client',
        'thenvoi_cli.process_manager',
        'thenvoi_cli.output',
        'thenvoi_cli.exceptions',
        'thenvoi_cli.logging_config',
        'typer',
        'typer.main',
        'typer.core',
        'click',
        'rich',
        'rich.console',
        'rich.table',
        'rich.logging',
        'rich._unicode_data',
        'yaml',
        'httpx',
        'thenvoi_rest',
    ] + rich_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy optional dependencies from binary
        'langgraph',
        'langchain',
        'anthropic',
        'openai',
        'crewai',
        'parlant',
        'a2a_sdk',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='thenvoi-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
