# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller の spec ファイル。

    pyinstaller Sma4Py.spec

で単体実行ファイルを作る。build.bat (Windows) / build.sh (macOS) は
どちらも最終的にこのファイルを呼ぶので、同梱設定はここ一箇所にまとまっている。

なぜ spec が要るのか
--------------------
PyInstaller は「ソースを静的に読んで import を追う」方式で同梱物を決める。
そのため *実行時にしか分からない依存* は取りこぼす。Sma4Py には次の3種類があり、
どれも取りこぼすと「ビルドは成功するのに起動すると落ちる」形で表面化する:

  1. 関数の中に隠れた import
     canvas.py の make_canvas() が matplotlib.backends.backend_qtagg を
     関数内で import している。静的解析では追えない。
  2. 文字列から決まる import
     fig.savefig(path) は拡張子を見て backend_pdf / backend_svg / backend_ps を
     動的に読み込む。ソース上に import 文が存在しない。
  3. Python ではなくデータとして必要なもの
     matplotlib のフォント (mpl-data) や scipy のコンパイル済み拡張。

以下の hiddenimports / datas は、この3つを明示的に埋めるためのもの。
"""

import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# spec 実行時は __file__ が無いので、PyInstaller が渡す SPECPATH を使う
PROJECT_ROOT = Path(SPECPATH).resolve()  # noqa: F821


def _read_version():
    """sma4py/__init__.py から __version__ を取り出す。

    import せずにテキストとして読む。ビルド環境で sma4py を import すると
    依存の解決順によっては失敗しうるため、副作用の無い方法にしてある。
    """
    init_py = PROJECT_ROOT / "sma4py" / "__init__.py"
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']',
                  init_py.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else "0.0.0"


VERSION = _read_version()
APP_NAME = "Sma4Py"


# --- hiddenimports: 静的解析で追えない import ------------------------------

hiddenimports = []

# PySide6: 実際に使っているサブモジュールを明示する。
# (mainwindow.py / dialogs.py が QtCore・QtGui・QtWidgets を使用)
hiddenimports += [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

# matplotlib のバックエンド。
# backend_qtagg は canvas.py:make_canvas() の *関数内* import なので静的解析では
# 見つからない。qt_compat は「どの Qt バインディングを使うか」を実行時に決める
# 部分で、これも明示しないと落ちることがある。
hiddenimports += [
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.qt_compat",
]

# 画像書き出し (mainwindow.py の「画像として書き出す」= PNG/PDF/SVG/EPS)。
# savefig() が拡張子から選ぶので、ソースには import 文が現れない。
hiddenimports += [
    "matplotlib.backends.backend_pdf",   # .pdf
    "matplotlib.backends.backend_svg",   # .svg
    "matplotlib.backends.backend_ps",    # .eps
]

# scipy: fitting.py が使うのは curve_fit だけだが、scipy.optimize は内部で
# コンパイル済み拡張を動的に読み込むため、サブモジュールごと入れるのが確実。
# tests は実行時に使わないうえ pytest を引き込むので外す（サイズ削減）。
hiddenimports += collect_submodules(
    "scipy.optimize",
    filter=lambda name: "tests" not in name.split("."),
)

# scipy が実行時に遅延ロードする低レベル部分。PyInstaller が取りこぼしやすい
# 定番で、抜けると「ImportError: DLL load failed」等になる。
hiddenimports += [
    "scipy._lib.messagestream",
    "scipy.special._ufuncs_cxx",
    "scipy.linalg.cython_blas",
    "scipy.linalg.cython_lapack",
    "scipy.sparse.csgraph._validation",
]


# --- datas: Python コードではないが必要なファイル --------------------------

datas = []

# matplotlib の mpl-data 一式。フォント (fonts/ttf) と matplotlibrc が入る。
# canvas.py:setup_japanese_font() が mathtext.fontset = "cm" を設定するので、
# Computer Modern のフォントファイルが無いと数式ラベルの描画で落ちる。
datas += collect_data_files("matplotlib", excludes=["**/tests/**"])

# scipy の付属データ (.pyi や一部の設定ファイル)。
datas += collect_data_files("scipy", excludes=["**/tests/**"])


# --- excludes: 入れたくないもの --------------------------------------------
#
# 特に他の Qt バインディングの除外は重要。matplotlib の qt_compat は
# 「見つかったバインディング」を使うため、環境に PyQt5 等が残っていると
# それを巻き込んで同梱し、実行時に PySide6 と衝突して起動しなくなる。
excludes = [
    "PyQt5",
    "PyQt6",
    "PySide2",
    "tkinter",           # Tk バックエンドは使わない (サイズ削減)
    "matplotlib.backends.backend_tkagg",
    "pytest",
    "IPython",
    "jupyter",
    "notebook",
]


a = Analysis(  # noqa: F821
    ["run_sma4py.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821


# --- 実行ファイルの作り方は OS ごとに変える --------------------------------
#
# Windows / Linux: 1ファイルの実行ファイル (onefile)。配布が楽。
# macOS: .app バンドルを作る。.app は「中身がディレクトリの塊」という形式なので
#        onefile ではなく onedir (COLLECT) で組んでから BUNDLE でくるむ。

if sys.platform == "darwin":
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,       # 実体は COLLECT 側に置く
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,               # --noconsole 相当
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,            # ビルドした Mac のアーキテクチャに従う
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(  # noqa: F821
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=APP_NAME,
    )

    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.sma4py.app",
        version=VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            # Retina で文字がぼやけないようにする
            "NSHighResolutionCapable": True,
            # 注: .s4p を Finder からダブルクリックして開く機能 (CFBundleDocumentTypes)
            # は入れていない。アプリ側が起動引数を読んでファイルを開く実装を
            # 持っていないため、宣言しても「アプリが起動するだけ」になるので。
        },
    )
else:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,               # --noconsole 相当
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
