@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 启动建账规则助手 Web 服务
echo ========================================
echo.

REM 设置项目根目录
set PROJECT_ROOT=%CD%
set PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 正在激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] 未找到 venv 虚拟环境，将使用系统 Python
)

REM 检查环境变量
if "%SILICONFLOW_API_KEY%"=="" (
    echo [ERROR] 未设置 SILICONFLOW_API_KEY 环境变量
    echo 请在 .env 文件中配置 SILICONFLOW_API_KEY=你的密钥
    echo.
    pause
    exit /b 1
)

REM 启动服务
echo [INFO] 启动服务 (PYTHONPATH=%PYTHONPATH%)...
echo [INFO] WebSocket 服务将自动在端口 5001 启动
echo.
python src/main.py -m http -p 5000

pause
