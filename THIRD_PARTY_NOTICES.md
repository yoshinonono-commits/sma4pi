# 第三者ソフトウェアのライセンス表記

Sma4Py の配布物（`Sma4Py.exe` / `Sma4Py.app` を含むフォルダ）には、以下の
ソフトウェアが同梱されています。それぞれの権利は各著作権者に帰属します。

| ソフトウェア | ライセンス | 入手先 |
|---|---|---|
| Python | PSF License | https://www.python.org/ |
| PySide6 (Qt for Python) | **LGPL v3** | https://www.qt.io/qt-for-python |
| Qt | **LGPL v3** | https://www.qt.io/ |
| NumPy | BSD 3-Clause | https://numpy.org/ |
| SciPy | BSD 3-Clause | https://scipy.org/ |
| matplotlib | matplotlib License (BSD 系) | https://matplotlib.org/ |

正式なライセンス全文は、各パッケージが配布物の中に同梱しています
（`_internal/` 以下の各パッケージのフォルダを参照してください）。

## LGPL について

**PySide6 と Qt は LGPL v3 で提供されています。** LGPL は、これらを組み込んだ
アプリケーションを配布する際に、利用者が Qt の部分を自分でビルドしたものに
差し替えられる状態を保つことを求めています。

Sma4Py の配布物は **onedir 形式**（1 個の実行ファイルに固めず、ライブラリを
独立したファイルとしてフォルダ内に並べる形式）でビルドしています。Qt の
ライブラリファイルはフォルダ内にそのまま置かれているため、差し替えが可能です。

ビルド設定は [`Sma4Py.spec`](Sma4Py.spec) にあり、同じものを誰でも再現できます。

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --clean Sma4Py.spec
```

商用ライセンスでの利用や、LGPL の要件について判断が必要な場合は、
Qt 社の案内 (https://www.qt.io/licensing/) と専門家にご確認ください。
この文書は情報提供であり、法的助言ではありません。

## Sma4Py 本体について

Sma4Py 自体は Sma4Win の操作感を参考にしたオリジナル実装で、
Sma4Win のソースコードやバイナリは一切含みません。
