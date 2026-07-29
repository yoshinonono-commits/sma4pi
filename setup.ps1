# Sma4Py を Claude Code で開発できる状態にする（Windows / PowerShell）。
#
#   1. git リポジトリを初期化（まだなら）
#   2. Python 仮想環境 .venv を作成
#   3. 依存パッケージをインストール
#   4. 非GUIテストを実行して健全性を確認
#   5. Claude Code が入っていれば案内を出す
#
# 使い方（PowerShell）:
#   実行が制限されている場合は最初に一度だけ:
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   その後:
#     .\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Say($msg)  { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }

# --- Python の確認 --------------------------------------------------------
Say "Python を確認します"
$py = $null
foreach ($cand in @("python", "python3", "py")) {
    if (Get-Command $cand -ErrorAction SilentlyContinue) { $py = $cand; break }
}
if (-not $py) {
    Warn "Python が見つかりません。3.9 以上を入れてください: https://www.python.org/"
    exit 1
}
& $py --version

$okVer = & $py -c "import sys; print(1 if sys.version_info >= (3,9) else 0)"
if ($okVer.Trim() -ne "1") {
    Warn "Python 3.9 以上が必要です。"
    exit 1
}

# --- git 初期化 -----------------------------------------------------------
Say "git リポジトリを準備します"
if (Test-Path ".git") {
    Write-Host "既に git 管理下です。スキップします。"
} elseif (Get-Command git -ErrorAction SilentlyContinue) {
    git init -q
    # コミット用の名前・メールが未設定なら、このリポジトリだけに仮の値を入れる
    git config user.email 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        git config user.email "you@example.com"
        git config user.name "Sma4Py Developer"
        Warn "git の名前/メールが未設定だったので仮の値を入れました。"
        Write-Host '    後で: git config user.name "あなたの名前" / git config user.email "..."'
    }
    git add -A
    git commit -q -m "Initial commit: Sma4Py 散布図描画・最小二乗フィッティングツール"
    Write-Host "リポジトリを初期化し、最初のコミットを作りました。"
} else {
    Warn "git が見つかりません。https://git-scm.com/ から入れると Claude Code で履歴管理できます。"
}

# --- 仮想環境 -------------------------------------------------------------
Say "仮想環境 .venv を作成します"
if (-not (Test-Path ".venv")) {
    & $py -m venv .venv
}
$activate = ".\.venv\Scripts\Activate.ps1"
& $activate
python -m pip install --quiet --upgrade pip

# --- 依存インストール -----------------------------------------------------
Say "依存パッケージをインストールします（少し時間がかかります）"
pip install --quiet -r requirements.txt
Write-Host "インストール完了。"

# --- テスト ---------------------------------------------------------------
Say "非GUIテストを実行します"
python tests\test_features.py
if ($LASTEXITCODE -ne 0) {
    Warn "テストが失敗しました。上のログを確認してください。"
    exit 1
}
Write-Host "`nテスト成功。ロジック層は正常です。"

# --- Claude Code の案内 ---------------------------------------------------
Say "Claude Code の状態を確認します"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "claude コマンドが見つかりました:"
    claude --version
    Write-Host "`nこのフォルダで次を実行すれば、続きから開発できます:"
    Write-Host "    claude"
} else {
    Warn "Claude Code (claude コマンド) が見つかりません。"
    Write-Host @"

  ネイティブインストーラ（推奨・Node.js 不要）:
    Windows (PowerShell):
      irm https://claude.ai/install.ps1 | iex

  npm を使う場合（Node.js 22 以上が必要）:
      npm install -g @anthropic-ai/claude-code

  ※ Claude Code の利用には Pro / Max / Team / Enterprise / API のいずれかの
    アカウントが必要です（無料プラン不可）。
  インストール後、新しい PowerShell を開いてこのフォルダで claude を実行してください。
"@
}

Say "セットアップ完了"
Write-Host @"

これから:
  .\.venv\Scripts\Activate.ps1   # 仮想環境を有効化
  python -m sma4py               # アプリを起動
  claude                         # Claude Code で開発を続ける

"@
