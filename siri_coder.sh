#!/bin/bash
#############################################################################
# Super Mac Assistant - Siri Coder Script
# Frage direkt den Coder-Agenten
#############################################################################

PROJECT_DIR="$HOME/activi-dev-repos/super-mac-assistant"
cd "$PROJECT_DIR"
source venv/bin/activate
python3 src/siri_assistant.py --agent coder "$@"
