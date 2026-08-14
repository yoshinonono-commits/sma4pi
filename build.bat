@echo off
rem ---------------------------------------------------------------------------
rem Sma4Py を Windows 用の単体 exe にビルドする。
rem
rem 使い方: このファイルをダブルクリックするか、コマンドプロンプトで
rem             build.bat
rem
rem 出力: dist\Sma4Py.exe (1ファイル、コンソール窓なし)
rem
rem PowerShell の setup.ps1 と違い .bat にしてあるのは、実行ポリシーの変更
rem (Set-ExecutionPolicy) 無しにダブルクリックで走らせられるようにするため。
rem ---------------------------------------------------------------------------
setlocal

rem ログの日本語が化けないよう UTF-8 のコードページにする
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ==^> Python を確認します

rem .venv があればそれを使う (setup.ps1 が作るもの)
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
    echo 仮想環境 .venv を使います。
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [!] Python が見つかりません。3.9 以上を入れてください: https://www.python.org/
        goto :fail
    )
    set "PY=python"
    echo [!] .venv が見つかりません。システムの python を使います。
    echo     先に setup.ps1 を実行して仮想環境を作るのを勧めます。
)

"%PY%" --version
if errorlevel 1 goto :fail

echo.
echo ==^> 依存パッケージを確認します（PyInstaller 含む）

"%PY%" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [!] 依存パッケージのインストールに失敗しました。
    goto :fail
)

echo インストール完了。

echo.
echo ==^> 以前のビルド結果を掃除します

if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"

echo.
echo ==^> PyInstaller でビルドします（数分かかります）

"%PY%" -m PyInstaller --noconfirm --clean Sma4Py.spec
if errorlevel 1 (
    echo.
    echo [!] ビルドに失敗しました。上のログを確認してください。
    goto :fail
)

if not exist "dist\Sma4Py.exe" (
    echo.
    echo [!] ビルドは終わりましたが dist\Sma4Py.exe がありません。
    goto :fail
)

echo.
echo ==^> 完成
echo.
echo     dist\Sma4Py.exe
echo.
echo この exe は Windows 専用です。macOS や Linux では動きません
echo （そちらで配布したい場合は、その OS 上で build.sh を実行してください）。
echo.

rem ダブルクリック起動でも結果を読めるように止める
pause
endlocal
exit /b 0

:fail
echo.
pause
endlocal
exit /b 1
