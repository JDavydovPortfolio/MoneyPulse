@echo off
REM Build script for Merchant Document Processor
REM This script builds the EXE using PyInstaller

echo Building Merchant Document Processor...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Cleaning previous builds...
echo.

REM Build the executable
echo Building executable...
pyinstaller build-merchant.spec

REM Check if build was successful
if exist "dist\MerchantProcessor.exe" (
    echo.
    echo =====================================
    echo    BUILD SUCCESSFUL!
    echo =====================================
    echo.
    echo Executable created: dist\MerchantProcessor.exe
    echo File size: 
    dir "dist\MerchantProcessor.exe" | find "MerchantProcessor.exe"
    echo.
    echo To run the application:
    echo   1. Double-click dist\MerchantProcessor.exe
    echo   2. Or run: .\dist\MerchantProcessor.exe
    echo.
) else (
    echo.
    echo =====================================
    echo    BUILD FAILED!
    echo =====================================
    echo.
    echo Check the output above for errors.
    echo Make sure all dependencies are installed:
    echo   pip install -r requirements.txt
    echo.
)

pause