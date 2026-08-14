#!/usr/bin/env bash
#
# Sma4Py をビルドする（macOS では .app バンドル、Linux では単体実行ファイル）。
#
# 使い方:  bash build.sh
#
# 出力:
#   macOS  -> dist/Sma4Py.app   (コンソール窓なし)
#   Linux  -> dist/Sma4Py       (1ファイル、コンソール窓なし)
#
# Windows 用の exe はこのスクリプトでは作れない。PyInstaller はクロス
# コンパイルできないので、Windows 上で build.bat を実行すること。
#
set -euo pipefail

cd "$(dirname "$0")"
say() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$1"; }

case "$(uname -s)" in
  Darwin) TARGET="app" ;;
  Linux)  TARGET="bin" ;;
  *)      warn "未対応の OS です: $(uname -s)"; exit 1 ;;
esac

# --- Python の確認 --------------------------------------------------------
say "Python を確認します"
if [ -x ".venv/bin/python" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  PY=python
  echo "仮想環境 .venv を使います。"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
  warn ".venv が見つかりません。システムの python3 を使います。"
  echo "    先に bash setup.sh を実行して仮想環境を作るのを勧めます。"
else
  warn "Python が見つかりません。3.9 以上を入れてください: https://www.python.org/"
  exit 1
fi
"$PY" --version

# --- 依存インストール -----------------------------------------------------
say "依存パッケージを確認します（PyInstaller 含む）"
"$PY" -m pip install --quiet -r requirements.txt
echo "インストール完了。"

# --- 掃除 -----------------------------------------------------------------
say "以前のビルド結果を掃除します"
rm -rf build dist

# --- ビルド ---------------------------------------------------------------
say "PyInstaller でビルドします（数分かかります）"
"$PY" -m PyInstaller --noconfirm --clean Sma4Py.spec

# --- 確認 -----------------------------------------------------------------
if [ "$TARGET" = "app" ]; then
  OUT="dist/Sma4Py.app"
else
  OUT="dist/Sma4Py"
fi

if [ ! -e "$OUT" ]; then
  warn "ビルドは終わりましたが $OUT がありません。上のログを確認してください。"
  exit 1
fi

say "完成"
echo ""
echo "    $OUT"
echo ""

if [ "$TARGET" = "app" ]; then
  cat <<'EOF'
起動:
    open dist/Sma4Py.app

初回起動時に「開発元を確認できないため開けません」と出る場合:
  署名していない .app なので Gatekeeper に止められている。
  Finder で .app を右クリック → 「開く」 を選べば以降は普通に起動できる。
  （配布先でも同じ操作が必要。コマンドで外すなら:
     xattr -dr com.apple.quarantine dist/Sma4Py.app ）

この .app は macOS 専用で、ビルドしたマシンの CPU アーキテクチャ
(Apple Silicon / Intel) 向けになる。Windows 用の exe が要る場合は
Windows 上で build.bat を実行すること。
EOF
else
  cat <<'EOF'
起動:
    ./dist/Sma4Py

この実行ファイルは Linux 専用。Windows 用の exe は Windows 上で
build.bat を、macOS 用の .app は macOS 上でこのスクリプトを実行して作ること。
EOF
fi
echo ""
