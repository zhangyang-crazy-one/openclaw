#!/bin/bash
# Stagehand Browser Automation - Startup Script

# Set MiniMax API Key
export MINIMAX_API_KEY="${MINIMAX_API_KEY:-your-api-key-here}"
export MINIMAX_API_BASE="${MINIMAX_API_BASE:-https://api.minimax.io/v1}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import stagehand" 2>/dev/null; then
    echo "Installing Stagehand..."
    pip install stagehand
fi

if ! python3 -c "import vercel_minimax_ai_provider" 2>/dev/null; then
    echo "Installing MiniMax provider..."
    # Try npm first (TypeScript)
    if command -v pnpm &> /dev/null; then
        pnpm add vercel-minimax-ai-provider
    elif command -v npm &> /dev/null; then
        npm add vercel-minimax-ai-provider
    else
        echo "WARNING: npm/pnpm not found. Install manually: npm install vercel-minimax-ai-provider"
    fi
fi

# Install Playwright browsers if needed
if ! python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "Installing Playwright..."
    pip install playwright
    playwright install chromium
elif ! command -v playwright &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Run the script
echo "Starting Stagehand with MiniMax..."
python3 "$(dirname "$0")/stagehand_browser.py" "$@"
