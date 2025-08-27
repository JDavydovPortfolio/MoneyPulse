@echo off
echo Building MerchantProcessor - Two Versions
echo.
echo This will create:
echo   1. MerchantProcessor-Lite.exe (~100 MB) - Basic OCR only
echo   2. MerchantProcessor-Full.exe (~2.5 GB) - With AI features
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo ========================================
echo Building LITE version (no AI) ~100 MB
echo ========================================
pyinstaller build-lightweight.spec

if exist dist\MerchantProcessor-Lite.exe (
    echo ✅ Lite version built successfully!
    for %%I in (dist\MerchantProcessor-Lite.exe) do echo Size: %%~zI bytes
) else (
    echo ❌ Lite version failed!
)

echo.
echo ========================================
echo Building FULL version (with AI) ~2.5 GB
echo ========================================
pyinstaller build-merchant.spec

if exist dist\MerchantProcessor.exe (
    echo ✅ Full version built successfully!
    for %%I in (dist\MerchantProcessor.exe) do echo Size: %%~zI bytes
) else (
    echo ❌ Full version failed!
)

echo.
echo ========================================
echo BUILD SUMMARY
echo ========================================
if exist dist\MerchantProcessor-Lite.exe (
    echo ✅ Lite: Basic OCR + GUI (~100 MB)
) else (
    echo ❌ Lite: Failed to build
)

if exist dist\MerchantProcessor.exe (
    echo ✅ Full: OCR + AI + GUI (~2.5 GB)  
) else (
    echo ❌ Full: Failed to build
)

echo.
echo Most users should use the Lite version unless they need AI parsing!
echo.
pause