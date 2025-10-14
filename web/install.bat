@echo off
echo ========================================
echo TransVox Web Frontend Installation
echo ========================================
echo.

echo [1/4] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found!
echo.

echo [2/4] Installing dependencies...
call npm install
if errorlevel 1 (
    echo Error: Failed to install dependencies!
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo [3/4] Creating .env.local file...
if not exist .env.local (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo .env.local created!
) else (
    echo .env.local already exists, skipping...
)
echo.

echo [4/4] Installation complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Make sure the backend server is running on port 8000
echo 2. Run: npm run dev
echo 3. Open: http://localhost:3000
echo.
echo ========================================
pause


