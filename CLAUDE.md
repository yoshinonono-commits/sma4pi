# Sma4Py — Claude Code 向けプロジェクトガイド

散布図の作図と最小二乗フィッティングのためのデスクトップアプリ。
Sma4Win の操作感を参考にしたオリジナル実装で、元ソフトのコードは一切含まない。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate        # Windows は .venv\Scripts\activate
pip install -r requirements.txt
```

## 実行とテスト

```bash
python -m sma4py               # アプリを起動 (GUI)
python tests/test_features.py  # 非GUIの機能テスト (17項目)
```

テストは matplotlib の Agg バックエンドで動くので、GUI 環境が無くても走る。
コードを変更したら、まず `python tests/test_features.py` が通ることを確認する。

## アーキテクチャ

GUI 層 (PySide6) とロジック層 (numpy/scipy/matplotlib) を分離している。
**ロジック層は PySide6 に依存しない**ので、GUI 無しでテストできる。この境界は保つこと。

```
sma4py/
├── __main__.py     起動エントリ (python -m sma4py)
├── mainwindow.py   [GUI] メインウィンドウ、メニュー、項目パネル
├── dialogs.py      [GUI] 各ダイアログ(列選択/軸設定/系列設定/フィット/関数/注釈)
├── interaction.py  [GUI寄り] マウス操作。matplotlib のみ依存、PySide6 非依存
├── canvas.py       描画。matplotlib の Axes に Document を描く + Qt埋め込み補助
├── model.py        [純ロジック] Series/FitCurve/FunctionCurve/Annotation/Document
├── data_io.py      [純ロジック] テキストファイルの読み込み
├── expression.py   [純ロジック] 数式変換の安全な評価 (AST検証つき eval)
├── fitting.py      [純ロジック] 最小二乗フィッティング (scipy.curve_fit)
└── notation.py     [純ロジック] Sma4記法 → matplotlib mathtext 変換
```

データの流れ: `data_io` が読む → `model.Series` に入る → `canvas.render()` が
`model.Document` を matplotlib の Axes に描く → `mainwindow` が全体を束ねる。

## 設計上の約束ごと

- **ロジック層に PySide6 を import しない。** テスト可能性を保つための境界。
- **`expression.py` の eval は必ず AST 検証を通す。** `_ALLOWED_NODES` と許可名の
  ホワイトリストで、`__import__` などを弾いている。関数を足すときは `FUNCS` に登録する。
- **保存形式 `.s4p` は JSON。** `Document.to_dict` / `from_dict` が担当。
  フィールドを足すときは両方を更新し、`from_dict` は古いファイル(version 1)も
  開けるよう `dict.get(..., 既定値)` で読むこと。現在は version 2。
- **UI 文言・コメントは日本語。** 既存のトーンに合わせる。
- **matplotlib は `layout="constrained"` を使う。** `tight_layout` は使わない。

## よくある作業の入り口

- フィット関数のプリセットを増やす → `fitting.py` の `PRESETS`
- 多重ピークの形状を増やす → `fitting.py` の `PEAK_SHAPES`
- 数式変換で使える関数を増やす → `expression.py` の `FUNCS`
- Sma4記法の記号を増やす → `notation.py`
- 新しい描画要素(系列以外)を足す → `model.py` にデータクラス追加 →
  `canvas.render()` に描画追加 → `to_dict`/`from_dict` 対応 →
  `mainwindow` にメニューとダイアログ

## まだ手を付けていない候補

subplot対応、フィット曲線の再編集。

## 注意

このリポジトリに Sma4Win のソースやバイナリを取り込まないこと。あくまで独立実装。
