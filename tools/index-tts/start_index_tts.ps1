# IndexTTS 便携式启动脚本
Write-Host "Starting IndexTTS..." -ForegroundColor Green
Write-Host ""

# 检查workenv中的Python是否存在
if (-not (Test-Path "workenv\install\python.exe")) {
    Write-Host "Error: workenv\install\python.exe not found!" -ForegroundColor Red
    Write-Host "Please make sure the workenv directory is properly set up." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 使用workenv中的Python运行webui.py
Write-Host "Using workenv Python to run IndexTTS..." -ForegroundColor Yellow
& "workenv\install\python.exe" webui.py @args

Write-Host ""
Write-Host "IndexTTS has stopped." -ForegroundColor Green
Read-Host "Press Enter to exit"

