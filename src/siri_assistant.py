#!/usr/bin/env python3
"""
Super Mac Assistant - Siri Integration
Ermöglicht Sprachsteuerung über Siri Shortcuts

Verwendung:
    python3 siri_assistant.py "Deine Frage hier"
    python3 siri_assistant.py --agent coder "Wie erstelle ich eine REST API?"
"""

import sys
import os
import argparse
import subprocess

# Projektverzeichnis zum Path hinzufügen
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from src.api.backend_client import BackendAPIClient


class SiriAssistant:
    """Siri-kompatibler Assistent für Sprachbefehle"""

    AGENTS = {
        "supervisor": "emir",
        "emir": "emir",
        "planner": "planner",
        "berater": "berater",
        "designer": "designer",
        "coder": "coder",
        "tester": "tester",
        "security": "security",
        "docs": "docs"
    }

    def __init__(self):
        self.client = BackendAPIClient(
            base_url="http://localhost:3001",
            ws_url="ws://localhost:3001/ws"
        )
        self.current_agent = "emir"

    def speak(self, text: str):
        """Text über macOS Sprachausgabe vorlesen"""
        # Bereinige Text für Sprachausgabe
        clean_text = text.replace('"', '\\"').replace("'", "\\'")
        subprocess.run(["say", "-v", "Anna", clean_text], check=False)

    def ask(self, question: str, agent: str = None, speak_response: bool = True) -> str:
        """
        Stelle eine Frage an den Assistenten

        Args:
            question: Die Frage/Anfrage
            agent: Optional - welcher Agent antworten soll
            speak_response: Ob die Antwort vorgelesen werden soll

        Returns:
            Die Antwort als Text
        """
        # Agent auswählen
        if agent:
            agent_name = self.AGENTS.get(agent.lower(), "emir")
        else:
            agent_name = self.current_agent

        # Prüfe Backend-Verbindung
        if not self.client.connect():
            error_msg = "Das Backend ist nicht erreichbar. Bitte starte zuerst den Server."
            if speak_response:
                self.speak(error_msg)
            return error_msg

        # Sende Anfrage an Backend
        result = self.client.send_chat_message(
            message=question,
            agent_name=agent_name,
            user_id="siri_user"
        )

        if result.get("success"):
            data = result.get("data", {})
            response = data.get("content") or data.get("response") or data.get("message", "Keine Antwort erhalten.")

            # Kürze für Sprachausgabe (max 500 Zeichen)
            if speak_response:
                spoken_response = response[:500] + "..." if len(response) > 500 else response
                self.speak(spoken_response)

            return response
        else:
            error_msg = f"Fehler: {result.get('error', 'Unbekannter Fehler')}"
            if speak_response:
                self.speak("Es ist ein Fehler aufgetreten.")
            return error_msg

    def quick_action(self, action: str) -> str:
        """
        Führe eine Quick Action aus

        Actions:
            - status: Aktueller Status
            - tasks: Offene Aufgaben
            - help: Hilfe anzeigen
        """
        if action == "status":
            if self.client.connect():
                self.speak("Der Assistent ist bereit und das Backend ist verbunden.")
                return "Status: Ready, Backend: Connected"
            else:
                self.speak("Das Backend ist nicht erreichbar.")
                return "Status: Ready, Backend: Disconnected"

        elif action == "tasks":
            result = self.client.list_tasks()
            if result.get("success"):
                tasks = result.get("data", [])
                if tasks:
                    task_count = len(tasks)
                    self.speak(f"Du hast {task_count} offene Aufgaben.")
                    return f"{task_count} tasks: " + ", ".join([t.get("title", "Unbenannt") for t in tasks[:5]])
                else:
                    self.speak("Du hast keine offenen Aufgaben.")
                    return "Keine offenen Aufgaben"
            else:
                self.speak("Konnte Aufgaben nicht abrufen.")
                return "Fehler beim Abrufen der Aufgaben"

        elif action == "help":
            help_text = """
Du kannst mich fragen:
- Wie erstelle ich eine API?
- Erkläre mir React Hooks
- Hilf mir beim Debugging
- Erstelle einen Unit Test

Oder Quick Actions:
- Status prüfen
- Aufgaben anzeigen
"""
            self.speak("Ich kann dir bei der Programmierung helfen. Frag mich einfach was du wissen möchtest.")
            return help_text

        else:
            self.speak(f"Unbekannte Aktion: {action}")
            return f"Unbekannte Aktion: {action}"

    def set_agent(self, agent: str) -> str:
        """Wechsle den aktiven Agenten"""
        agent_lower = agent.lower()
        if agent_lower in self.AGENTS:
            self.current_agent = self.AGENTS[agent_lower]
            agent_names = {
                "emir": "Supervisor Emir",
                "planner": "Planner",
                "berater": "Berater",
                "designer": "Designer",
                "coder": "Coder",
                "tester": "Tester",
                "security": "Security",
                "docs": "Dokumentation"
            }
            name = agent_names.get(self.current_agent, self.current_agent)
            self.speak(f"Agent gewechselt zu {name}")
            return f"Agent: {name}"
        else:
            self.speak(f"Unbekannter Agent: {agent}")
            return f"Unbekannter Agent: {agent}. Verfügbar: supervisor, planner, berater, designer, coder, tester, security, docs"


def main():
    parser = argparse.ArgumentParser(description="Super Mac Assistant - Siri Integration")
    parser.add_argument("question", nargs="*", help="Deine Frage oder Anfrage")
    parser.add_argument("--agent", "-a", help="Agent auswählen (supervisor, coder, etc.)")
    parser.add_argument("--action", help="Quick Action (status, tasks, help)")
    parser.add_argument("--set-agent", help="Agent wechseln")
    parser.add_argument("--no-speak", action="store_true", help="Keine Sprachausgabe")

    args = parser.parse_args()
    assistant = SiriAssistant()

    # Quick Action
    if args.action:
        result = assistant.quick_action(args.action)
        print(result)
        return

    # Agent wechseln
    if args.set_agent:
        result = assistant.set_agent(args.set_agent)
        print(result)
        return

    # Frage stellen
    if args.question:
        question = " ".join(args.question)
        result = assistant.ask(
            question=question,
            agent=args.agent,
            speak_response=not args.no_speak
        )
        print(result)
    else:
        # Interaktiver Modus
        assistant.speak("Hallo! Wie kann ich dir helfen?")
        print("Super Mac Assistant - Siri Modus")
        print("Tippe deine Frage oder 'exit' zum Beenden:")

        while True:
            try:
                user_input = input("\n> ").strip()
                if user_input.lower() in ["exit", "quit", "q"]:
                    assistant.speak("Auf Wiedersehen!")
                    break
                if user_input:
                    result = assistant.ask(user_input, speak_response=not args.no_speak)
                    print(f"\n{result}")
            except KeyboardInterrupt:
                print("\n")
                assistant.speak("Auf Wiedersehen!")
                break


if __name__ == "__main__":
    main()
