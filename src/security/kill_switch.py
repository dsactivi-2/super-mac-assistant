"""
Kill Switch / Panic Button
Emergency stop for all operations
"""

import os
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


class KillSwitch:
    """
    Emergency kill switch
    Can pause/stop all operations immediately
    """

    def __init__(self):
        self.state_file = Path(os.path.expanduser("~/activi-dev-repos/super-mac-assistant/.killswitch"))
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize as active if file doesn't exist
        if not self.state_file.exists():
            self._write_state("active")

    def _write_state(self, state: str):
        """Write state to file"""
        with open(self.state_file, "w") as f:
            f.write(f"{state}\n{datetime.now().isoformat()}")

    def _read_state(self) -> dict:
        """Read current state"""
        if not self.state_file.exists():
            return {"state": "active", "timestamp": datetime.now()}

        try:
            with open(self.state_file, "r") as f:
                lines = f.read().strip().split("\n")
                state = lines[0]
                timestamp = datetime.fromisoformat(lines[1]) if len(lines) > 1 else datetime.now()
                return {"state": state, "timestamp": timestamp}
        except:
            return {"state": "active", "timestamp": datetime.now()}

    def is_active(self) -> bool:
        """Check if system is active (not paused/killed)"""
        state = self._read_state()
        return state["state"] == "active"

    def is_paused(self) -> bool:
        """Check if system is paused"""
        state = self._read_state()
        return state["state"] == "paused"

    def is_killed(self) -> bool:
        """Check if system is killed"""
        state = self._read_state()
        return state["state"] == "killed"

    def pause(self):
        """Pause all operations"""
        self._write_state("paused")
        print("🚨 SUPER MAC ASSISTANT PAUSED")
        print("   All operations are suspended")
        print("   Use 'resume' to continue")

    def resume(self):
        """Resume operations after pause"""
        self._write_state("active")
        print("✅ SUPER MAC ASSISTANT RESUMED")

    def kill(self):
        """
        EMERGENCY STOP
        Requires manual restart
        """
        self._write_state("killed")
        print("🛑 EMERGENCY STOP ACTIVATED")
        print("   Super Mac Assistant is now KILLED")
        print("   Manual restart required")
        print("")
        print("To restart:")
        print("  python3 src/daemon.py")

    def reset(self):
        """Reset kill switch (for restart)"""
        self._write_state("active")
        print("🔄 Kill switch reset")

    def get_status(self) -> dict:
        """Get current status"""
        state_data = self._read_state()

        return {
            "active": self.is_active(),
            "paused": self.is_paused(),
            "killed": self.is_killed(),
            "state": state_data["state"],
            "since": state_data["timestamp"].isoformat()
        }

    def check_or_block(self):
        """
        Check kill switch and block if not active
        Raise exception if paused/killed
        """
        if self.is_killed():
            raise SystemExit("🛑 System is KILLED. Restart required.")

        if self.is_paused():
            raise RuntimeError("⏸️  System is PAUSED. Operations blocked.")

        # Active - continue
        return True


class PanicPhrase:
    """
    Detect panic phrases in voice commands
    """

    PANIC_PHRASES = [
        "stop everything",
        "emergency stop",
        "kill switch",
        "stop immediately",
        "abort everything",
        "cancel all",
        "panic",
        "stopp alles",  # German
        "notfall stop",
        "abbrechen",
    ]

    @classmethod
    def detect(cls, text: str) -> bool:
        """Check if text contains panic phrase"""
        text_lower = text.lower()

        for phrase in cls.PANIC_PHRASES:
            if phrase in text_lower:
                return True

        return False

    @classmethod
    def handle_panic(cls, text: str, kill_switch: KillSwitch):
        """Handle panic phrase if detected"""
        if cls.detect(text):
            print("\n" + "="*60)
            print("🚨 PANIC PHRASE DETECTED")
            print("="*60)
            print(f"Input: {text}")
            print("")
            print("Activating emergency stop...")
            kill_switch.pause()  # Pause instead of kill (allows resume)
            print("")
            print("="*60)
            return True

        return False


class ConfirmationDialog:
    """
    Request user confirmation for high-risk actions
    """

    @staticmethod
    def confirm_action(action_name: str, description: str, risk_level: str) -> bool:
        """
        Ask user to confirm action

        Args:
            action_name: Name of the action
            description: What the action does
            risk_level: low/medium/high/critical

        Returns:
            bool: True if confirmed, False otherwise
        """

        print("\n" + "="*60)
        print(f"⚠️  CONFIRMATION REQUIRED ({risk_level.upper()} RISK)")
        print("="*60)
        print(f"Action: {action_name}")
        print(f"Description: {description}")
        print("")
        print("Do you want to proceed?")
        print("  - Type 'yes' or 'confirm' to proceed")
        print("  - Type 'no' or 'cancel' to abort")
        print("  - Type 'pause' to pause the assistant")
        print("="*60)

        while True:
            response = input("> ").strip().lower()

            if response in ["yes", "confirm", "y", "ja"]:
                print("✅ Confirmed. Proceeding...")
                return True

            elif response in ["no", "cancel", "n", "nein"]:
                print("❌ Cancelled.")
                return False

            elif response == "pause":
                kill_switch = KillSwitch()
                kill_switch.pause()
                return False

            else:
                print("Invalid response. Please type 'yes', 'no', or 'pause'")


# Example usage & CLI
if __name__ == "__main__":
    import sys

    kill_switch = KillSwitch()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "pause":
            kill_switch.pause()

        elif command == "resume":
            kill_switch.resume()

        elif command == "kill":
            kill_switch.kill()

        elif command == "reset":
            kill_switch.reset()

        elif command == "status":
            status = kill_switch.get_status()
            print(f"Status: {status['state']}")
            print(f"Since: {status['since']}")

        else:
            print("Usage: python kill_switch.py [pause|resume|kill|reset|status]")

    else:
        status = kill_switch.get_status()
        print(f"Kill Switch Status: {status['state']}")
        print(f"Since: {status['since']}")
