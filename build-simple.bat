@echo off
setlocal

echo Building MoneyPulse local-provider desktop executable...
echo This build does not bundle the optional Transformers model stack.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller build-lightweight.spec
if errorlevel 1 (
    echo Build failed. Review the PyInstaller output above.
    exit /b 1
)

if exist dist\MoneyPulse-Local.exe (
    echo Build completed: dist\MoneyPulse-Local.exe
    echo Test the executable on the intended target system before distributing it.
) else (
    echo Build command completed but expected executable was not found.
    exit /b 1
)
