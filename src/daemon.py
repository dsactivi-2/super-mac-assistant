"""
Super Mac Assistant Daemon
Runs in the background and listens for commands
"""

import os
import sys
import time
import signal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import SuperMacAssistant


class AssistantDaemon:
    """Background daemon for Super Mac Assistant"""

    def __init__(self):
        self.assistant = SuperMacAssistant()
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def start(self):
        """Start the daemon"""
        print("🚀 Super Mac Assistant Daemon starting...")

        self.running = True
        self.assistant.running = True

        # Enable Slack notifications
        self.assistant.enable_slack_notifications()

        # Connect WebSocket for real-time updates
        if self.assistant.backend_available:
            self.assistant.backend.connect_websocket()

        # Send startup notification
        agent = self.assistant.get_current_agent()
        startup_message = f"✅ Super Mac Assistant gestartet\n\nAgent: {agent.name}\nStatus: 🟢 Ready"

        if self.assistant.slack_enabled:
            self.assistant._notify_slack(
                agent_type="supervisor",
                message=startup_message
            )

        print(f"✅ Daemon gestartet")
        print(f"   Agent: {agent.name}")
        print(f"   Backend: {'✅ Connected' if self.assistant.backend_available else '❌ Offline'}")
        print(f"   Slack: {'✅ Enabled' if self.assistant.slack_enabled else '❌ Disabled'}")
        print("\n🎤 Bereit für Siri-Befehle...")

        # Main loop
        try:
            while self.running:
                time.sleep(10)  # Keep alive
        except KeyboardInterrupt:
            self._handle_shutdown()

    def _handle_shutdown(self, signum=None, frame=None):
        """Handle shutdown gracefully"""
        print("\n🛑 Shutting down Super Mac Assistant Daemon...")

        self.running = False
        self.assistant.running = False

        # Send shutdown notification
        if self.assistant.slack_enabled:
            self.assistant._notify_slack(
                agent_type="supervisor",
                message="⏸️  Super Mac Assistant wurde beendet"
            )

        # Disconnect WebSocket
        if self.assistant.backend_available:
            self.assistant.backend.disconnect_websocket()

        print("✅ Shutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    daemon = AssistantDaemon()
    daemon.start()
