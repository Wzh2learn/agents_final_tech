@echo off
echo ========================================
echo 启动建账规则助手 Web 服务
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查环境变量
if "%SILICONFLOW_API_KEY%"=="" (
    echo [ERROR] 未设置 SILICONFLOW_API_KEY 环境变量
    echo 请在 .env 文件中配置或设置系统环境变量
    pause
    exit /b 1
)

REM 启动服务
echo [INFO] 启动 Flask Web 服务 (端口 5000)...
echo [INFO] WebSocket 服务将自动在端口 5001 启动
echo.
python src/web/app.py

pause
