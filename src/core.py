"""
Super Mac Assistant Core
Combines Backend API Client + Agent Identity + Local Mac Control
"""

import os
import subprocess
from typing import Dict, Optional, List
from datetime import datetime

from src.api.backend_client import BackendAPIClient
from src.agents.agent_identity import AgentManager, AgentType, AgentIdentity


class SuperMacAssistant:
    """
    Main coordinator for Super Mac Assistant
    Bridges local Mac control with Cloud Agents backend
    """

    def __init__(self, backend_url: str = "http://localhost:3000"):
        print("🚀 Initializing Super Mac Assistant...")

        # Initialize components
        self.backend = BackendAPIClient(base_url=backend_url)
        self.agent_manager = AgentManager(default_agent=AgentType.SUPERVISOR)

        # State
        self.running = False
        self.user_id = "U0904E3AAR5"  # Denis's Slack ID
        self.slack_enabled = False

        # Connect to backend
        if self.backend.connect():
            print("✅ Backend connected")
            self.backend_available = True
        else:
            print("⚠️  Backend not available (offline mode)")
            self.backend_available = False

        print(f"✅ Super Mac Assistant initialized")
        print(f"   Current Agent: {self.agent_manager.get_current_agent().name}")

    # =========================================================================
    # AGENT MANAGEMENT
    # =========================================================================

    def switch_agent(self, agent_type: str) -> Dict:
        """Switch between supervisor and assistant"""
        if agent_type.lower() in ["supervisor", "super", "sup"]:
            self.agent_manager.switch_to(AgentType.SUPERVISOR)
        elif agent_type.lower() in ["assistant", "ass", "worker"]:
            self.agent_manager.switch_to(AgentType.ASSISTANT)
        else:
            return {"success": False, "error": f"Unknown agent type: {agent_type}"}

        return {
            "success": True,
            "current_agent": self.agent_manager.get_current_agent().name
        }

    def get_current_agent(self) -> AgentIdentity:
        """Get current agent"""
        return self.agent_manager.get_current_agent()

    # =========================================================================
    # COMMAND PROCESSING
    # =========================================================================

    def process_command(self, command: str, voice: bool = False) -> Dict:
        """
        Process a command (from Siri or CLI)
        Returns structured response
        """
        print(f"\n{'🎤' if voice else '⌨️'} Command: {command}")
        print(f"🤖 Agent: {self.agent_manager.get_current_agent().short_name}")

        # Let agent manager process command
        response = self.agent_manager.process_command(command)

        # Execute based on response
        if response.get("needs_delegation"):
            # Supervisor delegates to assistant
            return self._handle_delegation(command, response)

        elif response.get("needs_execution"):
            # Assistant executes task
            return self._handle_execution(command, response)

        elif response.get("needs_verification"):
            # Verify results
            return self._handle_verification(command, response)

        else:
            # General processing
            return self._handle_general(command, response)

    def _handle_delegation(self, command: str, context: Dict) -> Dict:
        """Handle task delegation (Supervisor → Assistant)"""
        print("📋 Supervisor: Creating task and delegating...")

        if not self.backend_available:
            return {
                "success": False,
                "message": "Backend not available. Cannot create task.",
                "agent": "supervisor"
            }

        # Create task in backend
        result = self.backend.create_task(
            title=command,
            description=f"Delegated by Supervisor via Mac Assistant",
            assignee="cloud_assistant"
        )

        if result.get("success"):
            task_data = result.get("data", {})
            task_id = task_data.get("id")
            stop_score = task_data.get("stopScore", 0)

            message = f"✅ Task erstellt und an Assistant delegiert\n"
            message += f"📋 Task ID: {task_id}\n"
            message += f"📊 STOP Score: {stop_score}"

            # Send Slack notification
            if self.slack_enabled:
                self._notify_slack("supervisor", message)

            return {
                "success": True,
                "message": message,
                "task_id": task_id,
                "stop_score": stop_score,
                "agent": "supervisor"
            }
        else:
            return {
                "success": False,
                "message": f"Fehler beim Erstellen der Task: {result.get('error')}",
                "agent": "supervisor"
            }

    def _handle_execution(self, command: str, context: Dict) -> Dict:
        """Handle task execution (Assistant)"""
        print("⚡ Assistant: Executing task...")

        # Parse command and execute
        result = self._execute_local_command(command)

        message = f"✅ Task ausgeführt\n"
        message += f"📊 Result: {result.get('output', 'OK')}"

        # Send Slack notification
        if self.slack_enabled:
            self._notify_slack("assistant", message)

        return {
            "success": True,
            "message": message,
            "result": result,
            "agent": "assistant"
        }

    def _handle_verification(self, command: str, context: Dict) -> Dict:
        """Handle verification"""
        print("🔍 Verifying...")

        # Collect evidence
        evidence = self._collect_evidence(command)

        message = f"✅ Verification abgeschlossen\n"
        message += f"📊 Evidence: {len(evidence)} items collected"

        return {
            "success": True,
            "message": message,
            "evidence": evidence,
            "agent": self.agent_manager.get_current_agent().short_name
        }

    def _handle_general(self, command: str, context: Dict) -> Dict:
        """Handle general command"""
        agent = self.agent_manager.get_current_agent()

        message = agent.format_message(context.get("message", "Verstanden."), "info")

        return {
            "success": True,
            "message": message,
            "agent": agent.short_name
        }

    # =========================================================================
    # LOCAL MAC CONTROL
    # =========================================================================

    def _execute_local_command(self, command: str) -> Dict:
        """Execute command on local Mac"""
        command_lower = command.lower()

        # Screenshot
        if "screenshot" in command_lower or "bildschirmfoto" in command_lower:
            return self._take_screenshot()

        # Open app
        elif "öffne" in command_lower or "open" in command_lower:
            app_name = self._extract_app_name(command)
            return self._open_app(app_name)

        # Terminal command
        elif "terminal" in command_lower or "command" in command_lower:
            cmd = self._extract_terminal_command(command)
            return self._run_terminal_command(cmd)

        # Sleep
        elif "sleep" in command_lower or "schlaf" in command_lower:
            return self._sleep_mac()

        else:
            return {"success": False, "error": "Unknown command type"}

    def _take_screenshot(self) -> Dict:
        """Take a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.expanduser(f"~/Desktop/{filename}")

            script = f'screencapture -x "{filepath}"'
            subprocess.run(script, shell=True, check=True)

            return {
                "success": True,
                "output": f"Screenshot gespeichert: {filepath}",
                "file": filepath
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _open_app(self, app_name: str) -> Dict:
        """Open a Mac application"""
        try:
            script = f'tell application "{app_name}" to activate'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "output": f"{app_name} geöffnet"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_terminal_command(self, cmd: str) -> Dict:
        """Run a terminal command"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sleep_mac(self) -> Dict:
        """Put Mac to sleep"""
        try:
            subprocess.run(['pmset', 'sleepnow'], check=True)
            return {
                "success": True,
                "output": "Mac geht in den Ruhemodus..."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # SLACK INTEGRATION
    # =========================================================================

    def _notify_slack(self, agent_type: str, message: str):
        """Send Slack notification as specific agent"""
        if not self.backend_available:
            return

        try:
            self.backend.send_slack_message_as_agent(
                agent_type=agent_type,
                user_id=self.user_id,
                message=message
            )
        except Exception as e:
            print(f"Slack notification failed: {e}")

    def enable_slack_notifications(self):
        """Enable Slack notifications"""
        self.slack_enabled = True
        print("✅ Slack notifications enabled")

    def disable_slack_notifications(self):
        """Disable Slack notifications"""
        self.slack_enabled = False
        print("⏸️  Slack notifications disabled")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _extract_app_name(self, command: str) -> str:
        """Extract app name from command"""
        # Simple extraction (can be improved with NLP)
        words = command.split()
        for i, word in enumerate(words):
            if word.lower() in ["öffne", "open", "starte", "start"]:
                if i + 1 < len(words):
                    return words[i + 1].capitalize()
        return "Finder"

    def _extract_terminal_command(self, command: str) -> str:
        """Extract terminal command"""
        # Extract everything after "terminal" or "command"
        for keyword in ["terminal", "command", "führe aus", "execute"]:
            if keyword in command.lower():
                parts = command.lower().split(keyword)
                if len(parts) > 1:
                    return parts[1].strip()
        return "echo 'No command found'"

    def _collect_evidence(self, context: str) -> List[Dict]:
        """Collect evidence for verification"""
        evidence = []

        # Screenshot evidence
        screenshot = self._take_screenshot()
        if screenshot.get("success"):
            evidence.append({
                "type": "screenshot",
                "file": screenshot.get("file"),
                "timestamp": datetime.now().isoformat()
            })

        # System info
        evidence.append({
            "type": "system_info",
            "agent": self.agent_manager.get_current_agent().name,
            "backend_status": "connected" if self.backend_available else "offline",
            "timestamp": datetime.now().isoformat()
        })

        return evidence

    def get_status(self) -> Dict:
        """Get system status"""
        return {
            "running": self.running,
            "backend_available": self.backend_available,
            "slack_enabled": self.slack_enabled,
            "current_agent": self.agent_manager.get_current_agent().to_dict(),
            "agent_status": self.agent_manager.get_status()
        }


# CLI Interface
if __name__ == "__main__":
    assistant = SuperMacAssistant()

    print("\n" + "="*60)
    print("🚀 SUPER MAC ASSISTANT")
    print("="*60)
    print(f"Current Agent: {assistant.get_current_agent().name}")
    print("\nCommands:")
    print("  - 'switch supervisor' / 'switch assistant'")
    print("  - 'screenshot' - Take a screenshot")
    print("  - 'open [app]' - Open an application")
    print("  - 'status' - Show system status")
    print("  - 'quit' - Exit")
    print("="*60 + "\n")

    while True:
        try:
            command = input(f"[{assistant.get_current_agent().short_name}] > ").strip()

            if not command:
                continue

            if command.lower() in ["quit", "exit", "q"]:
                print("👋 Bye!")
                break

            elif command.lower().startswith("switch"):
                agent_type = command.split()[1] if len(command.split()) > 1 else "supervisor"
                result = assistant.switch_agent(agent_type)
                print(f"✅ Switched to: {result.get('current_agent')}")

            elif command.lower() == "status":
                status = assistant.get_status()
                print(json.dumps(status, indent=2))

            else:
                result = assistant.process_command(command)
                print(f"\n{result.get('message', 'Done')}\n")

        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
