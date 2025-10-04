@echo off
chcp 65001 >nul
call venv\Scripts\activate.bat

:MENU
cls
echo ============================================================
echo   视频下载工具
echo ============================================================
echo.

set "URL="
set /p "URL=粘贴视频链接 (q=退出): "
if /i "%URL%"=="q" exit
if "%URL%"=="" goto MENU

echo.
echo [下载中...]
if not exist "input" mkdir input

yt-dlp -o "input/%%(title)s.%%(ext)s" -f "bv*[ext=mp4]+ba/b" "%URL%"

echo.
if %ERRORLEVEL% EQU 0 (
    echo [完成] 已保存到 input\
) else (
    echo [失败] 下载失败
)

echo.
set /p "C=继续? [Y/N]: "
if /i "%C%"=="Y" goto MENU

echo.
timeout /t 2 >nul
