@echo off
setlocal

echo Building MoneyPulse variants.
echo The local-provider variant requires requirements-build.txt.
echo The Transformers variant additionally requires requirements-transformers.txt.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller build-lightweight.spec
if errorlevel 1 exit /b 1

echo.
echo Building optional Transformers-enabled variant...
pyinstaller build-merchant.spec
if errorlevel 1 exit /b 1

echo.
echo Build commands completed. Verify both executables on the target Windows system before release.
