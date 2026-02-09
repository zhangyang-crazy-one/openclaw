#!/bin/bash
# Stagehand Skill Installation Script

echo "========================================"
echo "🚀 Installing Stagehand Skill"
echo "========================================"
echo ""

# Set MiniMax API Key
read -p "Enter your MiniMax API Key: " MINIMAX_API_KEY
export MINIMAX_API_KEY="$MINIMAX_API_KEY"

echo ""
echo "📦 Installing Python dependencies..."

# Install Python packages
pip install stagehand playwright -q

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers..."
playwright install chromium 2>/dev/null || echo "⚠️  Playwright browsers may already be installed"

echo ""
echo "📦 Installing npm dependencies..."

# Install npm packages
if [ -d "node_modules" ]; then
    rm -rf node_modules
fi

npm install vercel-minimax-ai-provider -q 2>/dev/null || {
    echo "⚠️  npm install failed, trying pnpm..."
    pnpm add vercel-minimax-ai-provider -q 2>/dev/null || {
        echo "⚠️  Could not install vercel-minimax-ai-provider"
        echo "   Please install manually: npm install vercel-minimax-ai-provider"
    }
}

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Configuration:"
echo "   export MINIMAX_API_KEY=\"$MINIMAX_API_KEY\""
echo "   export MINIMAX_API_BASE=\"https://api.minimax.io/v1\""
echo ""
echo "🧪 Testing installation..."
python3 scripts/test_integration.py

echo ""
echo "📚 Usage:"
echo "   /stagehand navigate <url>   - Navigate to a URL"
echo "   /stagehand act <instruction>  - Perform an action"
echo "   /stagehand extract <query>   - Extract structured data"
echo "   /stagehand observe <query>   - Observe page elements"
echo "   /stagehand agent <task>      - Run autonomous workflow"
