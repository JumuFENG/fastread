@echo off
rem 构建 fastread_installer.exe (Windows 安装器)
rem 依赖: python + pyinstaller (打包机需装 PyQt6)
setlocal
cd /d "%~dp0\.."

echo ==^> 安装构建依赖
python -m pip install pyinstaller PyQt6 || exit /b 1

echo ==^> PyInstaller 打包 (scripts\installer.spec)
python -m PyInstaller --noconfirm --clean scripts\installer.spec || exit /b 1

echo ==^> 完成: dist\fastread_installer.exe
endlocal
