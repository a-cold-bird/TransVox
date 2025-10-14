chcp 65001
@echo off
REM TransVox 一键启动脚本 - Windows
REM 同时启动后端和前端服务

echo ================================================
echo TransVox 启动脚本
echo ================================================
echo.

echo [0/3] 清理旧进程和端口...
echo.

REM 杀掉占用 8000 端口的进程（后端）
echo 正在检查端口 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 发现占用端口 8000 的进程 PID: %%a，正在终止...
    taskkill /F /PID %%a >nul 2>&1
)

REM 杀掉占用 3000 端口的进程（前端）
echo 正在检查端口 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo 发现占用端口 3000 的进程 PID: %%a，正在终止...
    taskkill /F /PID %%a >nul 2>&1
)

echo 端口清理完成
echo.

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境，请先运行安装脚本
    echo 运行: python -m venv venv
    pause
    exit /b 1
)

echo [1/2] 启动后端服务...
echo.
start "TransVox Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && echo [后端] 正在启动... && uvicorn api_server:app --host 0.0.0.0 --port 8000"

REM 等待后端启动
echo 等待后端初始化（8秒）...
timeout /t 8 /nobreak >nul

echo.
echo [2/2] 启动前端服务...
echo.

REM 检查前端目录是否存在
if not exist "web" (
    echo [错误] 未找到 web 目录
    pause
    exit /b 1
)

REM 检查 node_modules 是否存在
if not exist "web\node_modules" (
    echo [警告] 未找到 node_modules，正在安装依赖...
    cd web
    call npm install
    cd ..
)

start "TransVox Frontend" cmd /k "cd web && echo [前端] 正在启动... && npm run dev"

echo.
echo ================================================
echo 服务启动完成！
echo ================================================
echo.
echo 后端 API 文档: http://localhost:8000/docs
echo 前端界面:     http://localhost:3000
echo.
echo 提示：
echo - 如需停止服务，请关闭对应的命令行窗口
echo - 后端启动可能需要 1-2 分钟（首次启动更慢）
echo - 前端启动通常需要 10-30 秒
echo.
echo 按任意键退出此窗口...
pause >nul
