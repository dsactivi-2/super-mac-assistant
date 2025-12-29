"""
Agent Identity System
Manages switching between SUPERVISOR and ASSISTANT modes
Each agent has its own personality, capabilities, and Slack identity
"""

from typing import Dict, Optional, List
from enum import Enum
import json


class AgentType(Enum):
    """Agent types"""
    SUPERVISOR = "supervisor"
    ASSISTANT = "assistant"


class AgentIdentity:
    """
    Represents an agent's identity and capabilities
    """

    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self._load_profile()

    def _load_profile(self):
        """Load agent profile based on type"""
        if self.agent_type == AgentType.SUPERVISOR:
            self.name = "ENGINEERING_LEAD_SUPERVISOR"
            self.short_name = "Supervisor"
            self.icon_emoji = ":robot_face:"
            self.color = "#FF6B6B"  # Red
            self.personality = "strategic, analytical, decisive"
            self.capabilities = [
                "Strategic Planning",
                "Task Delegation",
                "Quality Control",
                "Risk Assessment (STOP Score)",
                "Evidence-Based Verification"
            ]
            self.greeting = "Hallo! Ich bin der Engineering Lead Supervisor. Ich plane, delegiere und verifiziere."
            self.slack_username = "ENGINEERING_LEAD_SUPERVISOR"

        elif self.agent_type == AgentType.ASSISTANT:
            self.name = "CLOUD_ASSISTANT"
            self.short_name = "Assistant"
            self.icon_emoji = ":zap:"
            self.color = "#4ECDC4"  # Cyan
            self.personality = "efficient, thorough, proactive"
            self.capabilities = [
                "Code Implementation",
                "Bug Fixing",
                "Testing & Verification",
                "Evidence Collection",
                "Documentation"
            ]
            self.greeting = "Hey! Ich bin der Cloud Assistant. Ich setze um und liefere Ergebnisse."
            self.slack_username = "CLOUD_ASSISTANT"

    def get_slack_message_config(self) -> Dict:
        """Get Slack message configuration for this agent"""
        return {
            "username": self.slack_username,
            "icon_emoji": self.icon_emoji
        }

    def format_message(self, content: str, message_type: str = "info") -> str:
        """Format a message in the agent's style"""
        prefix_map = {
            "info": f"ℹ️ [{self.short_name}]",
            "success": f"✅ [{self.short_name}]",
            "error": f"❌ [{self.short_name}]",
            "warning": f"⚠️ [{self.short_name}]",
            "task": f"📋 [{self.short_name}]",
            "report": f"📊 [{self.short_name}]"
        }
        prefix = prefix_map.get(message_type, f"[{self.short_name}]")
        return f"{prefix} {content}"

    def get_introduction_message(self) -> str:
        """Get agent introduction message"""
        capabilities_str = "\n".join([f"• {cap}" for cap in self.capabilities])

        if self.agent_type == AgentType.SUPERVISOR:
            return f"""Hallo! {self.icon_emoji}

Ich bin der *{self.name}* des Code Cloud Agents Systems.

*Meine Rolle:*
🎯 Strategische Planung und Delegation
📋 Task-Analyse und Aufgabenverteilung
✅ Qualitätskontrolle und Verification
🛑 STOP-Score Evaluation (Risk Assessment)

*Meine Kernkompetenzen:*
{capabilities_str}

*Status:* 🟢 Bereit für Anweisungen

Wie kann ich helfen?"""

        else:  # ASSISTANT
            return f"""Hey! {self.icon_emoji}

Ich bin der *{self.name}* - dein ausführender Agent.

*Meine Aufgaben:*
⚡ Code-Implementierung (Frontend + Backend)
🔧 Bug-Fixes und Refactoring
🧪 Testing und Verification
📊 Evidence Collection

*Meine Tools:*
{capabilities_str}

*Status:* 🟢 Ready for execution

Warte auf Tasks!"""

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "type": self.agent_type.value,
            "name": self.name,
            "short_name": self.short_name,
            "icon_emoji": self.icon_emoji,
            "color": self.color,
            "personality": self.personality,
            "capabilities": self.capabilities,
            "slack_username": self.slack_username
        }


class AgentManager:
    """
    Manages agent switching and state
    """

    def __init__(self, default_agent: AgentType = AgentType.SUPERVISOR):
        self.current_agent: AgentIdentity = AgentIdentity(default_agent)
        self.agent_history: List[Dict] = []

    def switch_to(self, agent_type: AgentType) -> AgentIdentity:
        """Switch to a different agent"""
        old_agent = self.current_agent.name
        self.current_agent = AgentIdentity(agent_type)

        # Log switch
        self.agent_history.append({
            "from": old_agent,
            "to": self.current_agent.name,
            "timestamp": self._get_timestamp()
        })

        print(f"🔄 Switched from {old_agent} to {self.current_agent.name}")
        return self.current_agent

    def get_supervisor(self) -> AgentIdentity:
        """Get supervisor agent"""
        return AgentIdentity(AgentType.SUPERVISOR)

    def get_assistant(self) -> AgentIdentity:
        """Get assistant agent"""
        return AgentIdentity(AgentType.ASSISTANT)

    def is_supervisor(self) -> bool:
        """Check if current agent is supervisor"""
        return self.current_agent.agent_type == AgentType.SUPERVISOR

    def is_assistant(self) -> bool:
        """Check if current agent is assistant"""
        return self.current_agent.agent_type == AgentType.ASSISTANT

    def get_current_agent(self) -> AgentIdentity:
        """Get current agent"""
        return self.current_agent

    def process_command(self, command: str) -> Dict:
        """
        Process a command with the current agent's context
        Returns structured response
        """
        # Parse command intent
        command_lower = command.lower()

        # Agent-specific behavior
        if self.is_supervisor():
            return self._process_as_supervisor(command)
        else:
            return self._process_as_assistant(command)

    def _process_as_supervisor(self, command: str) -> Dict:
        """Process command as supervisor"""
        command_lower = command.lower()

        # Planning keywords
        if any(word in command_lower for word in ["plan", "strategie", "wie", "analyse"]):
            return {
                "agent": "supervisor",
                "action": "plan",
                "message": "Ich analysiere die Anforderungen und erstelle einen Plan...",
                "needs_delegation": True
            }

        # Risk assessment keywords
        elif any(word in command_lower for word in ["risiko", "stop", "gefahr", "kritisch"]):
            return {
                "agent": "supervisor",
                "action": "risk_assessment",
                "message": "Ich bewerte das Risiko mit dem STOP-Score System...",
                "needs_approval": True
            }

        # Verification keywords
        elif any(word in command_lower for word in ["prüf", "verify", "check", "kontroll"]):
            return {
                "agent": "supervisor",
                "action": "verify",
                "message": "Ich verifiziere die Ergebnisse mit Evidence-Based Verification...",
                "needs_evidence": True
            }

        else:
            return {
                "agent": "supervisor",
                "action": "analyze",
                "message": "Verstanden. Lass mich das analysieren...",
                "needs_delegation": False
            }

    def _process_as_assistant(self, command: str) -> Dict:
        """Process command as assistant"""
        command_lower = command.lower()

        # Implementation keywords
        if any(word in command_lower for word in ["implement", "code", "bau", "erstell", "fix"]):
            return {
                "agent": "assistant",
                "action": "implement",
                "message": "Ich implementiere das jetzt...",
                "needs_execution": True
            }

        # Testing keywords
        elif any(word in command_lower for word in ["test", "prüf", "verify"]):
            return {
                "agent": "assistant",
                "action": "test",
                "message": "Ich führe die Tests durch...",
                "needs_evidence": True
            }

        # Bug fix keywords
        elif any(word in command_lower for word in ["bug", "fehler", "fix", "problem"]):
            return {
                "agent": "assistant",
                "action": "fix",
                "message": "Ich behebe den Fehler...",
                "needs_verification": True
            }

        else:
            return {
                "agent": "assistant",
                "action": "execute",
                "message": "Ich führe das aus...",
                "needs_execution": True
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "current_agent": self.current_agent.to_dict(),
            "is_supervisor": self.is_supervisor(),
            "is_assistant": self.is_assistant(),
            "history_count": len(self.agent_history)
        }


# Example usage
if __name__ == "__main__":
    manager = AgentManager()

    print("=== SUPERVISOR MODE ===")
    print(manager.get_current_agent().get_introduction_message())
    print()

    response = manager.process_command("Erstelle einen Plan für das neue Feature")
    print(f"Response: {response}")
    print()

    print("=== SWITCHING TO ASSISTANT ===")
    manager.switch_to(AgentType.ASSISTANT)
    print(manager.get_current_agent().get_introduction_message())
    print()

    response = manager.process_command("Implementiere die Login-Funktion")
    print(f"Response: {response}")
