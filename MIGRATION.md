# Claude Code への移行ガイド

このプロジェクトをローカルに置いて、Claude Code で開発を続けるための手順。

## 「移す」とは何をすることか

今このプロジェクトは chat の中で生成されたファイル群。これを開発可能にするには、
次の3つが必要になる。付属のセットアップスクリプトがまとめて面倒を見る。

1. **ローカルに置く** — フォルダをダウンロードして好きな場所に展開する
2. **開発環境を作る** — git 初期化、Python 仮想環境、依存パッケージ
3. **Claude Code を入れて起動する** — このフォルダで `claude` を実行

## 手順

### 1. ダウンロードして展開

このフォルダ（`sma4py`）を丸ごとダウンロードし、作業用の場所に置く。

### 2. セットアップスクリプトを実行

**macOS / Linux:**
```bash
cd sma4py
bash setup.sh
```

**Windows (PowerShell):**
```powershell
cd sma4py
# 実行が制限されている場合、最初に一度だけ:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

スクリプトがやること:
- Python 3.9 以上があるか確認
- git リポジトリを初期化して最初のコミットを作成（git があれば）
- 仮想環境 `.venv` を作成
- `requirements.txt` の依存をインストール
- 非GUIテスト（`tests/test_features.py`、13項目）を実行して健全性を確認
- Claude Code が入っているか確認し、無ければインストール方法を案内

### 3. Claude Code を入れる（未インストールなら）

Claude Code は現在ネイティブバイナリで配布されており、Node.js は不要。

**macOS / Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://claude.ai/install.ps1 | iex
```

npm 経由（Node.js 22 以上が必要）でも入る:
```bash
npm install -g @anthropic-ai/claude-code
```

利用には Pro / Max / Team / Enterprise / API のいずれかのアカウントが必要
（無料プランは不可）。インストール後は**新しいターミナル**を開くこと（PATH の反映のため）。

最新の入れ方は公式を参照:
https://docs.claude.com/en/docs/claude-code/overview

### 4. Claude Code で開発を始める

```bash
cd sma4py
claude
```

起動すると Claude Code が同梱の `CLAUDE.md` を読み、プロジェクト構成・設計上の
約束ごと・作業の入り口を把握した状態から始まる。たとえばこう頼める:

- 「Undo/Redo を実装して」
- 「フィット関数に Voigt 関数のプリセットを足して」
- 「データ点を表形式で編集できるダイアログを追加して」
- 「まず tests/test_features.py が通ることを確認してから進めて」

## セットアップ後の手動コマンド

```bash
source .venv/bin/activate        # 仮想環境を有効化 (Win: .venv\Scripts\activate)
python -m sma4py                 # アプリ起動
python tests/test_features.py    # テスト
```

`make` が使えるなら `make run` / `make test` / `make setup` でも可。

## GitHub に上げたい場合

セットアップ後、ローカルには git 履歴ができている。リモートに上げるには:

```bash
git remote add origin https://github.com/<ユーザー名>/sma4py.git
git branch -M main
git push -u origin main
```

（先に GitHub 側で空のリポジトリを作っておく。認証は gh CLI か個人アクセストークンで。）

## うまくいかないとき

- **`claude` が command not found** → 新しいターミナルを開く。PATH は既存の
  シェルには反映されない。
- **PySide6 のインストールに失敗** → Python のバージョンを確認（3.9〜3.13 が無難）。
  Linux では稀にシステムライブラリが要る。
- **テストは通るが GUI が起動しない** → `python -m sma4py` のエラー全文を Claude Code
  にそのまま貼れば、環境依存の問題として切り分けてくれる。
- **git commit で identity エラー** → スクリプトが仮の名前/メールを入れて回避するが、
  後で `git config user.name` / `user.email` を自分の値に直しておくとよい。
