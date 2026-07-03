@echo off
chcp 65001 > nul
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   支払い管理システム Ver.1.0  起動中...      ║
echo  ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: 必要パッケージのインストール確認
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo  必要パッケージをインストールしています...
    pip install -r requirements.txt
    echo.
)

echo  ブラウザで自動的に開きます...
echo  終了するには Ctrl+C を押してください。
echo.
streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause