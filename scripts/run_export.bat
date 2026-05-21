@echo off
setlocal
cd /d %~dp0\..
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
    copy .env.example .env
    echo.
    echo Создан .env. Вставьте EGOV_API_KEY и запустите файл еще раз.
    pause
    exit /b 1
)
python -m eqazyna_excel.main --pages 5
pause
