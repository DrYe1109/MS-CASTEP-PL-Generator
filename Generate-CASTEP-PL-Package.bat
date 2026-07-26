@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "SKILL_ROOT=%~dp0"
set "LOCAL_CONFIG=%SKILL_ROOT%config\pl-skill.local.bat"

if not exist "%LOCAL_CONFIG%" (
  echo 未找到本机配置：
  echo   %LOCAL_CONFIG%
  echo 请先运行 Configure-CASTEP-PL-Skill.bat。
  pause
  exit /b 1
)

call "%LOCAL_CONFIG%"

if not defined PL_SKILL_PYTHON (
  echo 配置中缺少 PL_SKILL_PYTHON。请重新运行配置 BAT。
  pause
  exit /b 1
)

set /p "SOURCE_XSD=请输入源 XSD 完整路径: "
if not exist "%SOURCE_XSD%" (
  echo XSD 不存在：%SOURCE_XSD%
  pause
  exit /b 1
)

set /p "CALC_NAME=请输入计算名称（建议简短英文，例如 VC_ref）: "
if not defined CALC_NAME (
  echo 计算名称不能为空。
  pause
  exit /b 1
)

set /p "SPINS=请输入初始自旋，以空格分隔 [默认 1 3]: "
if not defined SPINS set "SPINS=1 3"

set /p "CORES=请输入核心数 [默认 %PL_SKILL_DEFAULT_CORES%]: "
if not defined CORES set "CORES=%PL_SKILL_DEFAULT_CORES%"

set "DEFAULT_OUTPUT=%PL_SKILL_OUTPUT_ROOT%\%CALC_NAME%"
set /p "OUTPUT_DIR=请输入输出目录 [默认 %DEFAULT_OUTPUT%]: "
if not defined OUTPUT_DIR set "OUTPUT_DIR=%DEFAULT_OUTPUT%"

echo.
echo 即将生成任务包：
echo   XSD    = %SOURCE_XSD%
echo   Name   = %CALC_NAME%
echo   Spins  = %SPINS%
echo   Cores  = %CORES%
echo   Output = %OUTPUT_DIR%
echo   Mode   = fixed spin, manual Gateway submission
echo.

"%PL_SKILL_PYTHON%" "%SKILL_ROOT%scripts\generate_castep_pl_package.py" ^
  --xsd "%SOURCE_XSD%" ^
  --output-dir "%OUTPUT_DIR%" ^
  --calculation-name "%CALC_NAME%" ^
  --spins %SPINS% ^
  --cores %CORES% ^
  --spin-mode fixed

if errorlevel 1 (
  echo.
  echo 生成失败。请检查上方错误；已有同名输出目录时请更换计算名称或目录。
  pause
  exit /b 1
)

echo.
echo 生成成功。请阅读输出目录中的 MANUAL_SUBMISSION.txt。
echo 必须在 Materials Studio 中手动按 Ctrl+F5 并选择 Gateway。
echo 本脚本没有提交任何计算任务。
pause
exit /b 0
