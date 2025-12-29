#!/bin/bash
###############################################################################
# Super Mac Assistant Setup Script
###############################################################################

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        SUPER MAC ASSISTANT SETUP                         ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo "📦 Project Directory: $PROJECT_DIR"
echo ""

# Step 1: Create logs directory
echo "1️⃣  Creating logs directory..."
mkdir -p logs
echo "   ✅ logs/ created"
echo ""

# Step 2: Create Python virtual environment
echo "2️⃣  Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ venv created"
else
    echo "   ℹ️  venv already exists"
fi
echo ""

# Step 3: Activate venv and install dependencies
echo "3️⃣  Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Step 4: Create __init__.py files
echo "4️⃣  Creating __init__.py files..."
touch src/__init__.py
touch src/api/__init__.py
touch src/agents/__init__.py
touch src/ui/__init__.py
touch src/plugins/__init__.py
touch src/utils/__init__.py
echo "   ✅ __init__.py files created"
echo ""

# Step 5: Test backend connection
echo "5️⃣  Testing backend connection..."
python3 -c "
from src.api.backend_client import BackendAPIClient
client = BackendAPIClient()
if client.connect():
    print('   ✅ Backend connected')
else:
    print('   ⚠️  Backend not running. Start it with:')
    print('      cd ~/activi-dev-repos/Optimizecodecloudagents && npm run backend:dev')
"
echo ""

# Step 6: Install LaunchAgent
echo "6️⃣  Installing LaunchAgent (Autostart)..."
echo ""
echo "   Do you want to enable autostart? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    # Copy plist to LaunchAgents
    cp com.step2job.supermacassistant.plist ~/Library/LaunchAgents/

    # Load the agent
    launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist 2>/dev/null
    launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

    echo "   ✅ LaunchAgent installed and loaded"
    echo "   🔄 Super Mac Assistant will start automatically on boot"
else
    echo "   ⏭️  Skipped autostart setup"
fi
echo ""

# Step 7: Summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETE                                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 NEXT STEPS:"
echo ""
echo "1. Start the Menu Bar App (recommended):"
echo "   source venv/bin/activate"
echo "   python3 src/menu_bar_launcher.py"
echo ""
echo "2. Or start CLI mode:"
echo "   source venv/bin/activate"
echo "   python3 src/core.py"
echo ""
echo "3. Or run as daemon:"
echo "   python3 src/daemon.py"
echo ""
echo "4. Configure Siri Shortcuts:"
echo "   Open: Shortcuts.app"
echo "   See: SIRI_SHORTCUTS.md"
echo ""
echo "5. Start backend (if not running):"
echo "   cd ~/activi-dev-repos/Optimizecodecloudagents"
echo "   npm run backend:dev"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
