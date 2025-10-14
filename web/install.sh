#!/bin/bash

echo "========================================"
echo "TransVox Web Frontend Installation"
echo "========================================"
echo ""

echo "[1/4] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo "Node.js found: $(node --version)"
echo ""

echo "[2/4] Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies!"
    exit 1
fi
echo "Dependencies installed successfully!"
echo ""

echo "[3/4] Creating .env.local file..."
if [ ! -f .env.local ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo ".env.local created!"
else
    echo ".env.local already exists, skipping..."
fi
echo ""

echo "[4/4] Installation complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo "1. Make sure the backend server is running on port 8000"
echo "2. Run: npm run dev"
echo "3. Open: http://localhost:3000"
echo ""
echo "========================================"


