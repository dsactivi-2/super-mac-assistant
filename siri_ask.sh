#!/bin/bash
#############################################################################
# Super Mac Assistant - Siri Shortcut Script
# Dieses Script wird von Siri Shortcuts aufgerufen
#############################################################################

# Projektverzeichnis
PROJECT_DIR="$HOME/activi-dev-repos/super-mac-assistant"
cd "$PROJECT_DIR"

# Virtual Environment aktivieren
source venv/bin/activate

# Frage an den Assistenten senden
python3 src/siri_assistant.py "$@"
