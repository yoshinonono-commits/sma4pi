#!/usr/bin/env bash
#
# Sma4Py を Claude Code で開発できる状態にする（macOS / Linux）。
#
#   1. git リポジトリを初期化（まだなら）
#   2. Python 仮想環境 .venv を作成
#   3. 依存パッケージをインストール
#   4. 非GUIテストを実行して健全性を確認
#   5. Claude Code が入っていれば案内を出す
#
# 使い方:  bash setup.sh
#
set -euo pipefail

cd "$(dirname "$0")"
say() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$1"; }

# --- Python の確認 --------------------------------------------------------
say "Python を確認します"
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  warn "Python が見つかりません。3.9 以上を入れてください: https://www.python.org/"
  exit 1
fi
"$PY" --version

# バージョンが 3.9 以上か確認
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  warn "Python 3.9 以上が必要です。"
  exit 1
fi

# --- git 初期化 -----------------------------------------------------------
say "git リポジトリを準備します"
if ! command -v git >/dev/null 2>&1; then
  warn "git が見つかりません。https://git-scm.com/ から入れると履歴管理できます。（スキップ）"
elif [ -d .git ]; then
  echo "既に git 管理下です。スキップします。"
else
  git init -q
  # コミット用の名前・メールが未設定なら、このリポジトリだけに仮の値を入れる
  if ! git config user.email >/dev/null 2>&1; then
    git config user.email "you@example.com"
    git config user.name "Sma4Py Developer"
    warn "git の名前/メールが未設定だったので仮の値を入れました。"
    echo "    後で: git config user.name \"あなたの名前\" / git config user.email \"...\""
  fi
  git add -A
  git commit -q -m "Initial commit: Sma4Py 散布図描画・最小二乗フィッティングツール"
  echo "リポジトリを初期化し、最初のコミットを作りました。"
fi

# --- 仮想環境 -------------------------------------------------------------
say "仮想環境 .venv を作成します"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip

# --- 依存インストール -----------------------------------------------------
say "依存パッケージをインストールします（少し時間がかかります）"
pip install --quiet -r requirements.txt
echo "インストール完了。"

# --- テスト ---------------------------------------------------------------
say "非GUIテストを実行します"
if python tests/test_features.py; then
  echo ""
  echo "テスト成功。ロジック層は正常です。"
else
  warn "テストが失敗しました。上のログを確認してください。"
  exit 1
fi

# --- Claude Code の案内 ---------------------------------------------------
say "Claude Code の状態を確認します"
if command -v claude >/dev/null 2>&1; then
  echo "claude コマンドが見つかりました:"
  claude --version || true
  echo ""
  echo "このフォルダで次を実行すれば、続きから開発できます:"
  echo "    claude"
else
  warn "Claude Code (claude コマンド) が見つかりません。"
  cat <<'EOF'

  ネイティブインストーラ（推奨・Node.js 不要）:
    macOS / Linux:
      curl -fsSL https://claude.ai/install.sh | bash

  npm を使う場合（Node.js 22 以上が必要）:
      npm install -g @anthropic-ai/claude-code

  ※ Claude Code の利用には Pro / Max / Team / Enterprise / API のいずれかの
    アカウントが必要です（無料プラン不可）。
  インストール後、新しいターミナルを開いてこのフォルダで `claude` を実行してください。
EOF
fi

say "セットアップ完了"
cat <<EOF

これから:
  source .venv/bin/activate     # 仮想環境を有効化
  python -m sma4py              # アプリを起動
  claude                        # Claude Code で開発を続ける

EOF
