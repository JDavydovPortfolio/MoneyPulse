@echo off
echo Building MerchantProcessor executable...
echo This may take several minutes...
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist MerchantProcessor.spec del MerchantProcessor.spec

REM Build with optimized settings
echo Starting PyInstaller build...
pyinstaller --onefile --windowed --name="MerchantProcessor" --exclude-module matplotlib --exclude-module IPython --exclude-module jupyter --exclude-module pytest --exclude-module tensorboard --exclude-module torch.utils.tensorboard main.py

if exist dist\MerchantProcessor.exe (
    echo.
    echo ✅ Build successful!
    echo 📁 Executable: dist\MerchantProcessor.exe
    echo 💾 Size: ~2.5 GB
    echo.
    echo The executable includes all dependencies and can run on any Windows machine.
) else (
    echo.
    echo ❌ Build failed! Check the output above for errors.
)

echo.
pause