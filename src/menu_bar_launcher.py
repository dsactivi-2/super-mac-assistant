#!/usr/bin/env python3
"""
Super Mac Assistant - Menu Bar Launcher

Starts the Menu Bar App as a standalone application.

Usage:
    python3 src/menu_bar_launcher.py

Or via Terminal:
    cd ~/activi-dev-repos/super-mac-assistant
    source venv/bin/activate
    python3 src/menu_bar_launcher.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ui.menu_bar import run_menu_bar_app


if __name__ == "__main__":
    print("🤖 Starting Super Mac Assistant Menu Bar...")
    print("   Look for the robot icon in your menu bar!")
    print("   Press Ctrl+C to stop")
    print()

    try:
        run_menu_bar_app()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
