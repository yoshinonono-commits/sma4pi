"""PyInstaller でビルドするときの起動スクリプト。

`python -m sma4py` は sma4py をパッケージとして読み込むので、__main__.py の中の
`from .mainwindow import MainWindow` のような相対インポートが解決できる。
一方 PyInstaller はエントリを「ただのスクリプト」として実行するため、
sma4py/__main__.py を直接指定すると __package__ が空になり

    ImportError: attempted relative import with no known parent package

で落ちる。そこで、パッケージとして import し直すだけのこのファイルを噛ませる。
"""

from sma4py.__main__ import main

if __name__ == "__main__":
    main()
