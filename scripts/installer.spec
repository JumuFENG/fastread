# -*- mode: python ; coding: utf-8 -*-
import os
import sys

SPEC_DIR = os.path.abspath('scripts' if os.path.isfile('main.py') else '.')
ROOT = os.path.dirname(SPEC_DIR)


def _version_file():
    try:
        sys.path.insert(0, os.path.join(ROOT, 'app'))
        from lofig import VERSION
    except Exception:
        VERSION = '1.0.0'
    try:
        parts = [int(x) for x in VERSION.split('.')]
    except ValueError:
        parts = [1, 0, 0]
    filevers = tuple((parts + [0, 0, 0])[:4])
    out = os.path.join(ROOT, 'build', 'version_info.txt')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'FastRead'),
           StringStruct('FileDescription', 'FastRead 安装程序'),
           StringStruct('FileVersion', '{VERSION}'),
           StringStruct('InternalName', 'fastread_installer'),
           StringStruct('OriginalFilename', 'fastread_installer.exe'),
           StringStruct('ProductName', 'FastRead'),
           StringStruct('ProductVersion', '{VERSION}')]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""")
    return out

a = Analysis(
    [os.path.join(SPEC_DIR, 'installer.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'main.py'), '.'),
        (os.path.join(ROOT, 'desktop.py'), '.'),
        (os.path.join(ROOT, 'app'), 'app'),
        (os.path.join(ROOT, 'templates'), 'templates'),
        (os.path.join(ROOT, 'static'), 'static'),
        (os.path.join(ROOT, 'requirements.txt'), '.'),
        (os.path.join(SPEC_DIR, 'win_service.py'), 'scripts'),
        (os.path.join(ROOT, 'res', 'icon.ico'), 'res'),
        (os.path.join(ROOT, 'res', 'icon.png'), 'res'),
    ],
    hiddenimports=['PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='fastread_installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['ucrtbase.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, 'res', 'icon.ico'),
    version=_version_file(),
    uac_admin=True,
)
