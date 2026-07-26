@echo off
setlocal
chcp 65001 >nul
set "SKILL_ROOT=%~dp0"

echo ============================================================
echo MS CASTEP PL Generator - 本机环境配置
echo ============================================================
echo 此脚本只检查环境并生成本机配置，不会启动或提交 CASTEP 作业。
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass ^
  -File "%SKILL_ROOT%scripts\configure-castep-pl-skill.ps1"

if errorlevel 1 (
  echo.
  echo 配置失败。请根据上方提示修正 Python 或路径后重试。
  pause
  exit /b 1
)

echo.
echo 配置完成。下一步运行 Generate-CASTEP-PL-Package.bat。
pause
exit /b 0
