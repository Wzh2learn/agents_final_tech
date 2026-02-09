@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 启动建账规则助手 Web 服务
echo ========================================
echo.

REM 设置项目根目录
set PROJECT_ROOT=%CD%
set PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src

REM 检查 Docker 容器状态
echo [INFO] 检查 Docker 数据库容器...
docker ps --filter "name=pgvector" --format "{{.Names}}" | findstr "pgvector" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pgvector 容器未运行，正在启动...
    docker start pgvector 2>nul || (
        echo [ERROR] 启动 pgvector 容器失败，请先运行：
        echo     docker run -d --name pgvector -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=vector_db -p 5432:5432 ankane/pgvector:latest
        pause
        exit /b 1
    )
    echo [INFO] pgvector 容器已启动
    timeout /t 3 /nobreak >nul
) else (
    echo [INFO] pgvector 容器运行正常
)

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 正在激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] 未找到 venv 虚拟环境，将使用系统 Python
)

REM 加载 .env 文件中的环境变量
if exist ".env" (
    echo [INFO] 正在加载 .env 文件...
    for /f "usebackq tokens=*" %%a in (".env") do (
        echo %%a | findstr "^#" >nul || (
            for /f "tokens=1,2 delims==" %%b in ("%%a") do (
                set "%%b=%%c"
            )
        )
    )
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
echo [INFO] 访问 http://localhost:5000
echo.
python src/main.py -m http -p 5000

pause
