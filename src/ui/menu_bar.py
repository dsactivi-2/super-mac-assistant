"""
Super Mac Assistant - Menu Bar App
macOS Status Bar application using rumps

Accessibility IDs follow OTOP standard:
- Menu items have unique identifiers for UI automation
- Format: supermac.menubar.{section}.{item}
"""

import rumps
import threading
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core import SuperMacAssistant
from src.agents.agent_identity import AgentType


class SuperMacMenuBarApp(rumps.App):
    """
    Menu Bar App for Super Mac Assistant

    Provides quick access to:
    - Agent switching (Supervisor/Assistant)
    - Quick commands
    - Status display
    - Backend connection status
    """

    # OTOP Accessibility ID prefix
    ACCESSIBILITY_PREFIX = "supermac.menubar"

    def __init__(self):
        # Initialize with robot icon
        super().__init__(
            name="Super Mac Assistant",
            icon=None,  # Will use title instead
            title="🤖",
            quit_button=None  # Custom quit button
        )

        # Initialize assistant in background
        self.assistant = None
        self.loading = True

        # Build menu
        self._build_menu()

        # Start assistant initialization in background
        threading.Thread(target=self._init_assistant, daemon=True).start()

    def _build_menu(self):
        """Build the menu structure with accessibility IDs"""

        # Status section
        self.status_item = rumps.MenuItem(
            title="Status: Starting...",
            callback=None,
            key=""  # supermac.menubar.status.display
        )
        self.status_item.set_callback(None)  # Not clickable

        # Agent section
        self.agent_header = rumps.MenuItem(
            title="--- Agent ---",
            callback=None
        )

        self.supervisor_item = rumps.MenuItem(
            title="Switch to Supervisor",
            callback=self.switch_to_supervisor,
            key="1"  # supermac.menubar.agent.supervisor
        )

        self.assistant_item = rumps.MenuItem(
            title="Switch to Assistant",
            callback=self.switch_to_assistant,
            key="2"  # supermac.menubar.agent.assistant
        )

        self.current_agent_item = rumps.MenuItem(
            title="Current: Loading...",
            callback=None
        )

        # Quick Actions section
        self.actions_header = rumps.MenuItem(
            title="--- Quick Actions ---",
            callback=None
        )

        self.screenshot_item = rumps.MenuItem(
            title="Take Screenshot",
            callback=self.take_screenshot,
            key="s"  # supermac.menubar.action.screenshot
        )

        self.status_check_item = rumps.MenuItem(
            title="Check Status",
            callback=self.check_status,
            key="c"  # supermac.menubar.action.status
        )

        # Backend section
        self.backend_header = rumps.MenuItem(
            title="--- Backend ---",
            callback=None
        )

        self.backend_status_item = rumps.MenuItem(
            title="Backend: Checking...",
            callback=None
        )

        self.reconnect_item = rumps.MenuItem(
            title="Reconnect",
            callback=self.reconnect_backend,
            key="r"  # supermac.menubar.backend.reconnect
        )

        # Slack section
        self.slack_header = rumps.MenuItem(
            title="--- Slack ---",
            callback=None
        )

        self.slack_toggle_item = rumps.MenuItem(
            title="Notifications: Off",
            callback=self.toggle_slack,
            key="n"  # supermac.menubar.slack.toggle
        )

        # Quit
        self.quit_item = rumps.MenuItem(
            title="Quit Super Mac Assistant",
            callback=self.quit_app,
            key="q"  # supermac.menubar.app.quit
        )

        # Build menu
        self.menu = [
            self.status_item,
            None,  # Separator
            self.agent_header,
            self.current_agent_item,
            self.supervisor_item,
            self.assistant_item,
            None,  # Separator
            self.actions_header,
            self.screenshot_item,
            self.status_check_item,
            None,  # Separator
            self.backend_header,
            self.backend_status_item,
            self.reconnect_item,
            None,  # Separator
            self.slack_header,
            self.slack_toggle_item,
            None,  # Separator
            self.quit_item
        ]

    def _init_assistant(self):
        """Initialize the assistant in background thread"""
        try:
            self.assistant = SuperMacAssistant()
            self.loading = False
            self._update_status()
        except Exception as e:
            self.status_item.title = f"Error: {str(e)[:30]}"
            self.loading = False

    def _update_status(self):
        """Update all status displays"""
        if not self.assistant:
            return

        # Update status
        self.status_item.title = "Status: Ready"
        self.title = "🤖" if self.assistant.backend_available else "🔴"

        # Update agent
        agent = self.assistant.get_current_agent()
        self.current_agent_item.title = f"Current: {agent.short_name}"

        # Update backend status
        if self.assistant.backend_available:
            self.backend_status_item.title = "Backend: Connected"
        else:
            self.backend_status_item.title = "Backend: Offline"

        # Update Slack
        if self.assistant.slack_enabled:
            self.slack_toggle_item.title = "Notifications: On"
        else:
            self.slack_toggle_item.title = "Notifications: Off"

    # ===== Menu Callbacks =====

    @rumps.clicked("Switch to Supervisor")
    def switch_to_supervisor(self, sender):
        """Switch to Supervisor agent"""
        if not self.assistant:
            rumps.notification(
                title="Super Mac Assistant",
                subtitle="Error",
                message="Assistant not initialized",
                sound=False
            )
            return

        result = self.assistant.switch_agent("supervisor")
        if result.get("success"):
            self._update_status()
            rumps.notification(
                title="Super Mac Assistant",
                subtitle="Agent Switched",
                message="Now using: SUPERVISOR",
                sound=False
            )

    @rumps.clicked("Switch to Assistant")
    def switch_to_assistant(self, sender):
        """Switch to Assistant agent"""
        if not self.assistant:
            return

        result = self.assistant.switch_agent("assistant")
        if result.get("success"):
            self._update_status()
            rumps.notification(
                title="Super Mac Assistant",
                subtitle="Agent Switched",
                message="Now using: ASSISTANT",
                sound=False
            )

    @rumps.clicked("Take Screenshot")
    def take_screenshot(self, sender):
        """Take a screenshot"""
        if not self.assistant:
            return

        result = self.assistant._take_screenshot()
        if result.get("success"):
            rumps.notification(
                title="Super Mac Assistant",
                subtitle="Screenshot Saved",
                message=result.get("output", "Screenshot taken"),
                sound=True
            )
        else:
            rumps.notification(
                title="Super Mac Assistant",
                subtitle="Screenshot Failed",
                message=result.get("error", "Unknown error"),
                sound=True
            )

    @rumps.clicked("Check Status")
    def check_status(self, sender):
        """Check and display system status"""
        if not self.assistant:
            return

        status = self.assistant.get_status()
        agent = status.get("current_agent", {})

        message = f"""
Agent: {agent.get('name', 'Unknown')}
Backend: {'Connected' if status.get('backend_available') else 'Offline'}
Slack: {'Enabled' if status.get('slack_enabled') else 'Disabled'}
"""
        rumps.notification(
            title="Super Mac Assistant",
            subtitle="System Status",
            message=message.strip(),
            sound=False
        )

    @rumps.clicked("Reconnect")
    def reconnect_backend(self, sender):
        """Attempt to reconnect to backend"""
        if not self.assistant:
            return

        self.backend_status_item.title = "Backend: Connecting..."

        def reconnect():
            if self.assistant.backend.connect():
                self.assistant.backend_available = True
                self._update_status()
                rumps.notification(
                    title="Super Mac Assistant",
                    subtitle="Backend",
                    message="Successfully reconnected!",
                    sound=True
                )
            else:
                self.assistant.backend_available = False
                self._update_status()
                rumps.notification(
                    title="Super Mac Assistant",
                    subtitle="Backend",
                    message="Connection failed",
                    sound=True
                )

        threading.Thread(target=reconnect, daemon=True).start()

    @rumps.clicked("Notifications: Off")
    @rumps.clicked("Notifications: On")
    def toggle_slack(self, sender):
        """Toggle Slack notifications"""
        if not self.assistant:
            return

        if self.assistant.slack_enabled:
            self.assistant.disable_slack_notifications()
        else:
            self.assistant.enable_slack_notifications()

        self._update_status()

    @rumps.clicked("Quit Super Mac Assistant")
    def quit_app(self, sender):
        """Quit the application"""
        rumps.quit_application()


def run_menu_bar_app():
    """Entry point for the Menu Bar App"""
    app = SuperMacMenuBarApp()
    app.run()


if __name__ == "__main__":
    run_menu_bar_app()
