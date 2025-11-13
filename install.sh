#!/bin/bash

# Quick dependency installer for AI Trading Bot

echo "==================================="
echo "  Installing Dependencies"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed${NC}"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}[OK] Python and Node.js found${NC}"
echo ""

# Install backend dependencies
echo -e "${YELLOW}[1/2] Installing Python dependencies...${NC}"
cd backend
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install Python dependencies${NC}"
    echo "Try running: pip3 install --upgrade pip"
    exit 1
fi
touch .dependencies_installed
cd ..
echo -e "${GREEN}[OK] Python dependencies installed${NC}"
echo ""

# Install frontend dependencies
echo -e "${YELLOW}[2/2] Installing Node.js dependencies...${NC}"
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install Node.js dependencies${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}[OK] Node.js dependencies installed${NC}"
echo ""

echo -e "${GREEN}==================================="
echo "  Installation Complete!"
echo "===================================${NC}"
echo ""
echo "You can now run: ./start.sh"
echo ""
