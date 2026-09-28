@echo off
setlocal

echo Creating MoneyPulse virtual environment...
python -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Desktop dependencies installed. Run:
echo   python main.py
echo.
echo Optional in-process Transformers support:
echo   python -m pip install -r requirements-transformers.txt
