@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo [1/3] pip: requirements + requirements-build ...
python -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 (
  echo 请先安装 Python 3，并确保 pip 可用。
  exit /b 1
)

echo [2/3] npm install (electron 目录^) ...
cd electron
call npm install
if errorlevel 1 exit /b 1

echo [3/3] PyInstaller 解析核心 + text-ai-bridge + electron-builder 安装包（体积较大，请耐心等待^) ...
echo 若提示找不到 pyinstaller，请先执行: python -m pip install -r requirements-build.txt
call npm run dist
if errorlevel 1 exit /b 1

echo.
echo 完成。最终用户只需一个文件即可使用（内含 Electron + 解析核心，无需 Python/Node）：
echo   electron\dist-installer\CDXML Compound Parser-*-portable-x64.exe
echo 首次运行可能较慢（自解压）。绿色目录打包：在 electron 下执行 npm run dist:unpacked
echo   输出目录 electron\dist-installer\win-unpacked\ ，运行 CDXML Compound Parser.exe
echo 若需 NSIS 安装包：npm run dist:nsis （部分环境需管理员或开发者模式）
cd ..
endlocal
