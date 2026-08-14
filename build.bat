@echo off
REM build.bat - sma4py.spec を使って Windows 用の単体exe (dist\Sma4Py.exe) を作る。
REM
REM 前提: リポジトリのルートに .venv が作成済みであること (setup.ps1 を先に実行)。
REM 使い方:
REM     build.bat
REM
REM 実行時依存 (requirements.txt) とビルド依存 (requirements-dev.txt) の
REM 両方をインストールしてから PyInstaller を走らせる。

setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [build.bat] .venv が見つかりません。先に setup.ps1 を実行してください。
    exit /b 1
)

echo [build.bat] 仮想環境を有効化します...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [build.bat] venv の有効化に失敗しました。
    exit /b 1
)

echo [build.bat] 依存パッケージをインストールします (requirements.txt + requirements-dev.txt)...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
pip install -r requirements.txt -r requirements-dev.txt
if errorlevel 1 (
    echo [build.bat] pip install に失敗しました。
    exit /b 1
)

echo [build.bat] 前回のビルド成果物を削除します...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [build.bat] PyInstaller でビルドします (単体exe / コンソール窓なし)...
pyinstaller sma4py.spec --noconfirm
if errorlevel 1 (
    echo [build.bat] ビルドに失敗しました。上のログを確認してください。
    exit /b 1
)

if not exist "dist\Sma4Py.exe" (
    echo [build.bat] dist\Sma4Py.exe が見つかりません。ビルドは失敗している可能性があります。
    exit /b 1
)

echo.
echo [build.bat] 完了しました: dist\Sma4Py.exe
echo [build.bat] 初回起動はやや時間がかかります。数百MB程度のサイズになります。

endlocal
