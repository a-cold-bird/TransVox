@echo off
echo ========================================
echo TransVox Web - Setup Testing
echo ========================================
echo.

echo [Test 1/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Node.js is not installed!
    goto :error
) else (
    node --version
    echo [PASS] Node.js is installed
)
echo.

echo [Test 2/6] Checking npm installation...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] npm is not installed!
    goto :error
) else (
    npm --version
    echo [PASS] npm is installed
)
echo.

echo [Test 3/6] Checking package.json...
if not exist package.json (
    echo [FAIL] package.json not found!
    goto :error
) else (
    echo [PASS] package.json found
)
echo.

echo [Test 4/6] Checking critical dependencies...
if not exist node_modules (
    echo [WARN] node_modules not found, dependencies not installed yet
    echo Run 'npm install' to install dependencies
) else (
    echo [PASS] node_modules folder exists
)
echo.

echo [Test 5/6] Checking configuration files...
set files_ok=1

if not exist tsconfig.json (
    echo [FAIL] tsconfig.json not found
    set files_ok=0
) else (
    echo [PASS] tsconfig.json found
)

if not exist next.config.js (
    echo [FAIL] next.config.js not found
    set files_ok=0
) else (
    echo [PASS] next.config.js found
)

if not exist tailwind.config.ts (
    echo [FAIL] tailwind.config.ts not found
    set files_ok=0
) else (
    echo [PASS] tailwind.config.ts found
)

if %files_ok%==0 goto :error
echo.

echo [Test 6/6] Checking environment file...
if not exist .env.local (
    echo [WARN] .env.local not found
    echo Creating default .env.local...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo [PASS] .env.local created
) else (
    echo [PASS] .env.local exists
)
echo.

echo ========================================
echo All Tests Passed!
echo ========================================
echo.
echo You can now:
echo 1. Install dependencies: npm install
echo 2. Run development server: npm run dev
echo 3. Build for production: npm run build
echo.
goto :end

:error
echo.
echo ========================================
echo Tests Failed!
echo ========================================
echo Please check the errors above and fix them.
echo.
pause
exit /b 1

:end
pause


