@echo off
REM Build RawAccelProfileSwitcher.exe with PyInstaller (run on Windows).
setlocal

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt || goto :error

echo Building executable...
pyinstaller --noconfirm RawAccelProfileSwitcher.spec || goto :error

echo.
echo Done. Your executable is at: dist\RawAccelProfileSwitcher.exe
goto :eof

:error
echo.
echo Build failed.
exit /b 1
