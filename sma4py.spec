# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 用の spec ファイル。

Windows で以下を実行すると dist\\Sma4Py.exe (単体exe) が作られる。

    pyinstaller sma4py.spec --noconfirm

build.bat から呼ばれる想定。このファイル自体はビルド成果物ではなく
ソース管理対象なので、.gitignore の `*.spec` から明示的に除外している。

PySide6 / matplotlib / scipy は、PyInstaller の自動検出だけでは
プラグインや遅延 import が漏れやすいため、下記を明示的に拾っている。

- PySide6: Qt プラットフォームプラグイン (platforms/qwindows.dll 等) や
  スタイル・イメージフォーマットのプラグインは collect_all で丸ごと同梱する。
- matplotlib: フォント等の mpl-data 一式に加え、canvas.py が実行時に
  遅延 import している Qt 用バックエンド (backend_qtagg) と、
  画像書き出し(PNG/PDF/SVG/EPS)で使うバックエンドを個別に追加する。
- scipy: fitting.py の curve_fit (scipy.optimize) に加えて、
  expression.py が遅延 import する scipy.special (erf/jn/yn) と
  scipy.integrate (cumulative_trapezoid, diff/integ用) は
  C拡張の取りこぼしが起きやすいので collect_submodules で網羅する。
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# --- PySide6 -----------------------------------------------------------
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")
datas += pyside6_datas
binaries += pyside6_binaries
hiddenimports += pyside6_hiddenimports

# --- matplotlib ----------------------------------------------------------
mpl_datas, mpl_binaries, mpl_hiddenimports = collect_all("matplotlib")
datas += mpl_datas
binaries += mpl_binaries
hiddenimports += mpl_hiddenimports
hiddenimports += [
    # canvas.py が実行時に import するQt用の描画バックエンド
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_qt5agg",
    # 画像書き出し(ファイル → PNG/PDF/SVG/EPS)で使うバックエンド
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_pdf",
    "matplotlib.backends.backend_svg",
    "matplotlib.backends.backend_ps",
]

# --- scipy -----------------------------------------------------------
# scipy.optimize.curve_fit (fitting.py) と、expression.py が遅延 import する
# scipy.special / scipy.integrate はいずれも Cython製の拡張を動的に
# 読み込むため、通常の静的解析では見落とされやすい。
hiddenimports += collect_submodules("scipy.optimize")
hiddenimports += collect_submodules("scipy.special")
hiddenimports += collect_submodules("scipy.integrate")

a = Analysis(
    ["sma4py/__main__.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# a.binaries / a.datas をここで EXE に渡すことで単体 exe (--onefile 相当) になる。
# onedir にしたい場合は exclude_binaries=True にして COLLECT() を別途呼ぶこと。
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Sma4Py",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --noconsole 相当。GUIアプリなのでコンソール窓を出さない
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="sma4py.ico",  # アイコンファイルを用意したらここに指定する
)
