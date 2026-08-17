# Sma4Py

散布図の作図と最小二乗フィッティングのためのデスクトップアプリ。
Sma4Win の操作感を参考にしたオリジナル実装で、元ソフトのコードは一切含みません。

Windows / macOS / Linux で動きます。

## セットアップ

```bash
pip install -r requirements.txt
python -m sma4py
```

Python 3.9 以上が必要です。

## 使い方の流れ

1. **データ** → **データファイルを開く** でテキストファイルを選ぶ
2. 出てきたダイアログで X 軸・Y 軸にとる列を指定する(誤差列も指定可)
3. **グラフ** → **グラフの設定** で軸ラベルや範囲を整える
4. **解析** → **最小二乗フィッティング** で式と初期値を入れて実行
5. **挿入** → **任意関数の重ね書き** / **テキスト注釈** で仕上げる
6. **ファイル** → **画像として書き出す** で PNG / PDF / SVG / EPS 出力

データファイルは空白・タブ・カンマ区切りに自動対応します。`#` 始まりの行と
ヘッダ行は自動で読み飛ばします。

## 軸ラベルの記法

Sma4Win と同じ記法が使えます。

| 記法 | 意味 |
|---|---|
| `%I` | イタリック(斜体)開始 |
| `%R` | ローマン(立体)に戻す |
| `%G` | ギリシャ文字開始 |
| `%A` | ギリシャ文字解除 |
| `^` | 上付き開始 |
| `_` | 下付き開始 |
| `@` | 上付き・下付き解除 |

例:

| 入力 | 表示 |
|---|---|
| `%II%R / A` | *I* / A |
| `%I%Gl%A%R / nm` | *λ* / nm |
| `N / m^2@` | N / m² |
| `%GD%RT_1@ / K` | ΔT₁ / K |

設定ダイアログの入力欄の下に変換結果がリアルタイムで出ます。

## 数式変換

系列の設定ダイアログで X 値・Y 値を変換できます。空欄なら変換しません。

- 使える名前: `x`, `y`, `i`(点番号), `pi`, `e`
- 関数: `sin cos tan exp log log10 sqrt abs floor ceil sign erf jn yn`
- 微積分: `diff(y)` (数値微分), `integ(y)` (累積積分)

例: `x*3`、`log10(y)`、`diff(y)`、`y/max(y,1e-12)`

> `eval` は使っていますが、AST を検証して許可した名前以外を弾いています。
> `__import__` などは実行できません。

## フィッティング

プリセット(直線・2次・指数・ガウス・ローレンツなど)から選ぶか、自分で式を書きます。

- パラメータ名をカンマ区切りで入れると、初期値の入力欄が自動で並びます
- 実行すると収束値・標準誤差・χ²・R² が出ます
- 収束値は初期値欄に書き戻されるので、そのまま追い込めます
- 誤差列を読み込んでいれば重み付きフィットもできます

Sma4Win で落ちがちだった `a+b*exp(c*x)` のようなモデルも、初期値の検算を
事前に行ってからソルバに渡すので、無限大や NaN が出る場合はクラッシュせず
メッセージで知らせます。

## マウス操作

| 操作 | 動き |
|---|---|
| 左ドラッグ | 囲んだ範囲を拡大 |
| 右ドラッグ | 平行移動 |
| ホイール | カーソル位置を中心に拡大縮小 |
| ダブルクリック | 全体表示に戻す (**表示** → **全体を表示**、`Ctrl+0` でも可) |
| 注釈を左ドラッグ | その注釈を動かす |

拡大した範囲は軸設定に書き戻されるので、保存しても再描画しても保たれます。
何も操作していないときはカーソル位置の座標がステータスバーに出ます。

## 任意関数の重ね書き

**挿入** → **任意関数の重ね書き** (`Ctrl+K`)。データが無くても `y = f(x)` を描けます。

- 「描画範囲をデータに合わせる」を on にすると、実データの x 範囲へ自動追従します
- off なら x 最小・最大・分割数を自分で決められます
- 使える関数は数式変換と同じ

## テキスト注釈

**挿入** → **テキスト注釈** (`Ctrl+T`)。軸ラベルと同じ Sma4 記法が使えます。

- 座標系は「グラフ枠に対する相対位置 (0〜1)」と「データ座標」から選べます
  - 相対位置なら、拡大しても枠内の同じ場所に留まります
  - データ座標なら、データと一緒に動きます
- データ座標のときは引き出し線(矢印)を付けられます
- **グラフ上で文字を直接ドラッグして動かせます**(数値入力は不要)

## ファイル構成

```
sma4py/
├── __main__.py     起動エントリ
├── mainwindow.py   メインウィンドウ、メニュー、項目パネル
├── dialogs.py      各ダイアログ(列選択/軸設定/系列設定/フィット/関数/注釈)
├── interaction.py  マウス操作(拡大・平行移動・注釈のドラッグ)
├── canvas.py       matplotlib への描画と Qt 埋め込み
├── model.py        Series / FitCurve / FunctionCurve / Annotation / Document
├── data_io.py      テキストファイルの読み込み
├── expression.py   数式変換の安全な評価
├── fitting.py      最小二乗フィッティング
└── notation.py     Sma4 記法 → mathtext 変換
```

ビルド関連のファイルは次の通りです。

```
Sma4Py.spec               PyInstaller の同梱設定(hiddenimports / datas)
run_sma4py.py             ビルド時の起動スクリプト
build.bat                 Windows でビルド → dist\Sma4Py-windows-x64.zip
build.sh                  macOS / Linux でビルド → dist/Sma4Py-macos-*.zip など
THIRD_PARTY_NOTICES.md    同梱ライブラリのライセンス表記(配布物に同梱される)
.github/workflows/build.yml  GitHub Actions で Windows / macOS 版をビルド
```

グラフは `.s4p` (JSON) で保存され、データも一緒に埋め込まれます。
保存形式は version 2 ですが、version 1 のファイルもそのまま開けます。

## 単体実行ファイルにする (exe 化)

Python を入れていない人にも渡せる、単体で動く実行ファイルを作れます。
PyInstaller を使いますが、必要なものは `requirements.txt` に入っているので
個別のインストールは不要です。

出力は **onedir 形式**（フォルダ一式）です。1 個の実行ファイルに固める onefile
形式ではありません。理由は[後述](#なぜ-onefile-ではなく-onedir-なのか)します。

### Windows

```bat
build.bat
```

`dist\Sma4Py\Sma4Py.exe` ができ、`dist\Sma4Py-windows-x64.zip` にまとまります。
**配布するのは zip のほうです。** exe だけ取り出しても、同じフォルダの DLL を
参照するため動きません。

### macOS

```bash
bash build.sh
```

`dist/Sma4Py.app` と `dist/Sma4Py-macos-<arch>.zip` ができます。
`open dist/Sma4Py.app` で起動します。

初回起動で「開発元を確認できないため開けません」と出たら、署名していない
`.app` が Gatekeeper に止められています。Finder で右クリック →「開く」を選べば
以降は普通に起動できます (配布先でも同じ操作が必要です)。

### Linux

```bash
bash build.sh
```

`dist/Sma4Py/Sma4Py` と `dist/Sma4Py-linux-<arch>.zip` ができます。

### ⚠️ 実行ファイルはビルドした OS 専用です

**PyInstaller はクロスコンパイルできません。** 作られる実行ファイルには、その
OS 用の Python 本体・Qt・各種バイナリがそのまま詰め込まれるためです。

| 配布したい相手 | ビルドする場所 | 作られるもの |
|---|---|---|
| Windows | Windows 上で `build.bat` | `Sma4Py-windows-x64.zip` |
| macOS | macOS 上で `bash build.sh` | `Sma4Py-macos-<arch>.zip` |
| Linux | Linux 上で `bash build.sh` | `Sma4Py-linux-<arch>.zip` |

- Windows で作った `.exe` は macOS / Linux では動きません。逆も同じです。
- macOS では **CPU アーキテクチャも引き継ぎます**。Apple Silicon で作った `.app` は
  Intel Mac では動きません (その逆は Rosetta 経由で動きます)。両対応が要る場合は
  それぞれの Mac でビルドしてください。

### Mac しか無くても Windows 版を作れます

上の制約への対処として、**GitHub Actions の Windows ランナー**でビルドする
ワークフローを用意してあります ([`.github/workflows/build.yml`](.github/workflows/build.yml))。

```bash
git tag v0.1.0
git push origin v0.1.0
```

タグを push すると Windows と macOS の両方でビルドが走り、Release が作られて
zip が添付されます。ビルドだけ試したいときは、GitHub の **Actions** タブから
**Run workflow** を押してください（この場合は Release を作らず、Artifacts に
成果物が置かれます）。

### 配布するときの注意

**1. Windows では SmartScreen の警告が出ます**

署名していない実行ファイルなので、受け取った人の環境で
「Windows によって PC が保護されました」と表示され、既定でブロックされます。
不具合ではないため、配布時に次の手順を案内してください。

> 「詳細情報」をクリック →「実行」を押す

消すにはコード署名証明書（有料）が必要です。

**2. ウイルス対策ソフトの誤検知**

PyInstaller で作った実行ファイルは誤検知されることがあります。onedir 形式は
onefile より起きにくいとされていますが、ゼロにはなりません。

**3. Python を入れていない環境で必ず試してください**

ビルドしたマシンには Python も Qt も入っているため、そこでの動作確認は
当てになりません。

**4. ライセンス表記を同梱してください**

`THIRD_PARTY_NOTICES.md` が zip に入ります。**PySide6 と Qt は LGPL v3** で、
配布時に条件が付きます。詳しくは
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) を参照してください。

### なぜ onefile ではなく onedir なのか

| | onefile | **onedir** (採用) |
|---|---|---|
| 配布物 | 実行ファイル 1 個 | フォルダ一式（zip で配る） |
| 起動速度 | 遅い。毎回一時フォルダへ展開する | 速い。展開済み |
| 誤検知 | されやすい | 比較的少ない |
| LGPL 対応 | しにくい | しやすい |

3 つ目と 4 つ目が決め手です。onefile は「自分自身を展開して実行する」挙動が
マルウェアと似ているため検知に引っかかりやすく、また Qt のライブラリを 1 つに
固めてしまうため、LGPL が求める「利用者が Qt 部分を差し替えられる状態」を
保ちにくくなります。

### 同梱設定について (`Sma4Py.spec`)

PyInstaller はソースの `import` 文を静的に読んで同梱物を決めるため、
実行時にしか分からない依存を取りこぼします。Sma4Py には次の 3 つがあり、
`Sma4Py.spec` で明示的に指定しています。

| 取りこぼす原因 | 該当箇所 | spec での対処 |
|---|---|---|
| 関数の中に隠れた import | `canvas.py` の `make_canvas()` が `backend_qtagg` を関数内で import | `hiddenimports` |
| 文字列から決まる import | `savefig()` が拡張子を見て PDF / SVG / EPS のバックエンドを選ぶ | `hiddenimports` |
| Python コードでないデータ | mathtext 用フォントなど matplotlib の `mpl-data` | `datas` |

環境に PyQt5 などが残っていると matplotlib がそちらを巻き込んで PySide6 と
衝突するため、他の Qt バインディングは `excludes` で外しています。

設定を変えたいときは spec を編集してから、次のように直接実行できます。

```bash
pyinstaller --noconfirm --clean Sma4Py.spec
```

なお、エントリに `sma4py/__main__.py` を直接指定するとビルドは通っても起動時に
`ImportError: attempted relative import with no known parent package` で落ちます。
PyInstaller はエントリをパッケージではなく単なるスクリプトとして実行するためで、
これを避けるために `run_sma4py.py` を挟んでいます。

## これから足せるもの

- 複数グラフの並べ表示 (subplot)
- 元に戻す / やり直し (Undo / Redo)
- データ点の直接編集(表形式のエディタ)
- フィット曲線の再編集(現状は再フィットが必要)
- 誤差棒の X 方向対応
