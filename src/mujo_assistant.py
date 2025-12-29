#!/usr/bin/env python3
"""
MUJO - Dein persönlicher Sprachassistent
=========================================

Wecke ihn mit: "Hey Mujo" oder "Mujo"

Dann stelle deine Frage und er antwortet dir.

Verwendung:
    python3 mujo_assistant.py

Autor: Super Mac Assistant Team
"""

import sys
import os
import subprocess
import threading
import time
import signal

# Projektverzeichnis
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

try:
    import speech_recognition as sr
except ImportError:
    print("❌ SpeechRecognition nicht installiert. Führe aus:")
    print("   pip install SpeechRecognition pyaudio")
    sys.exit(1)

from src.api.backend_client import BackendAPIClient


class MujoAssistant:
    """
    Mujo - Dein persönlicher Coding-Assistent

    Hört auf "Hey Mujo" und beantwortet Programmier-Fragen.
    """

    # Wake words die den Assistenten aktivieren
    WAKE_WORDS = ["siri"]

    # Stopp-Wörter zum Beenden
    STOP_WORDS = ["stop", "beenden", "aufhören", "tschüss", "quit", "exit"]

    AGENTS = {
        "supervisor": "emir",
        "coder": "coder",
        "planner": "planner",
        "berater": "berater",
        "designer": "designer",
        "tester": "tester",
        "security": "security",
        "docs": "docs"
    }

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.client = BackendAPIClient(
            base_url="http://localhost:3001",
            ws_url="ws://localhost:3001/ws"
        )
        self.current_agent = "emir"
        self.running = False
        self.listening_for_command = False

        # Mikrofonkalibrierung
        print("🎤 Mikrofon wird kalibriert...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✅ Mikrofon bereit!")

    def speak(self, text: str, voice: str = "Anna"):
        """Text über macOS Sprachausgabe vorlesen"""
        try:
            # Bereinige Text für Sprachausgabe
            clean_text = str(text)
            # Entferne problematische Zeichen
            clean_text = clean_text.replace('"', ' ')
            clean_text = clean_text.replace("'", ' ')
            clean_text = clean_text.replace('`', ' ')
            clean_text = clean_text.replace('\\', ' ')
            clean_text = clean_text.replace('\n', '. ')
            clean_text = clean_text.replace('\r', ' ')
            # Kürze für Sprachausgabe
            if len(clean_text) > 500:
                clean_text = clean_text[:500] + "... und so weiter."

            print(f"🔊 Spreche: {clean_text[:50]}...")
            result = subprocess.run(
                ["say", "-v", voice, clean_text],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print(f"⚠️ Say Fehler: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Speak Fehler: {e}")

    def listen(self, timeout: int = 5, phrase_limit: int = 10) -> str:
        """
        Höre auf Spracheingabe

        Args:
            timeout: Sekunden warten auf Sprache
            phrase_limit: Max Sekunden für Phrase

        Returns:
            Erkannter Text oder leerer String
        """
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )

            # Google Speech Recognition (kostenlos)
            text = self.recognizer.recognize_google(audio, language="de-DE")
            return text.lower()

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"⚠️  Spracherkennung nicht verfügbar: {e}")
            return ""
        except Exception as e:
            print(f"⚠️  Fehler: {e}")
            return ""

    def check_wake_word(self, text: str) -> bool:
        """Prüft ob ein Wake Word erkannt wurde"""
        text_lower = text.lower()
        for wake_word in self.WAKE_WORDS:
            if wake_word in text_lower:
                return True
        return False

    def check_stop_word(self, text: str) -> bool:
        """Prüft ob ein Stopp-Wort erkannt wurde"""
        text_lower = text.lower()
        for stop_word in self.STOP_WORDS:
            if stop_word in text_lower:
                return True
        return False

    def extract_agent_from_text(self, text: str) -> tuple:
        """
        Extrahiert Agent aus Text
        z.B. "frag den coder wie..." → ("coder", "wie...")
        """
        text_lower = text.lower()

        agent_triggers = {
            "coder": ["coder", "programmierer", "entwickler"],
            "designer": ["designer", "design"],
            "tester": ["tester", "test"],
            "planner": ["planner", "planer", "planung"],
            "berater": ["berater", "beratung", "experte"],
            "security": ["security", "sicherheit"],
            "docs": ["docs", "dokumentation", "doku"]
        }

        for agent, triggers in agent_triggers.items():
            for trigger in triggers:
                if trigger in text_lower:
                    # Entferne den Trigger aus dem Text
                    for t in triggers:
                        text = text.lower().replace(f"frag den {t}", "")
                        text = text.lower().replace(f"frage den {t}", "")
                        text = text.lower().replace(t, "")
                    return (agent, text.strip())

        return (None, text)

    def ask_backend(self, question: str, agent: str = None) -> str:
        """Frage an das Backend senden"""
        agent_name = agent if agent else self.current_agent

        if not self.client.connect():
            return "Das Backend ist leider nicht erreichbar. Bitte starte zuerst den Server."

        result = self.client.send_chat_message(
            message=question,
            agent_name=agent_name,
            user_id="mujo_user"
        )

        if result.get("success"):
            data = result.get("data", {})
            response = data.get("content") or data.get("response") or data.get("message")
            return response if response else "Ich habe leider keine Antwort erhalten."
        else:
            return f"Es gab einen Fehler: {result.get('error', 'Unbekannt')}"

    def handle_command(self, text: str):
        """Verarbeite einen Befehl nach dem Wake Word"""
        print(f"📝 Befehl: {text}")

        # Prüfe auf Stopp-Wort
        if self.check_stop_word(text):
            self.speak("Auf Wiedersehen! Bis bald.")
            self.running = False
            return

        # Prüfe auf spezielle Befehle
        if "status" in text.lower():
            if self.client.connect():
                self.speak("Ich bin bereit und das Backend ist verbunden.")
            else:
                self.speak("Das Backend ist nicht erreichbar.")
            return

        if "hilfe" in text.lower() or "help" in text.lower():
            self.speak("""
                Du kannst mich alles zur Programmierung fragen.
                Zum Beispiel: Wie erstelle ich eine REST API?
                Oder: Erkläre mir React Hooks.
                Sage Stop oder Beenden um mich zu beenden.
            """)
            return

        # Extrahiere Agent aus Text
        agent, clean_text = self.extract_agent_from_text(text)

        if not clean_text or len(clean_text) < 5:
            self.speak("Was möchtest du wissen?")
            print("👂 Warte auf Frage...")
            follow_up = self.listen(timeout=8, phrase_limit=15)
            if follow_up and len(follow_up) > 3:
                clean_text = follow_up
            else:
                self.speak("Ich habe dich nicht verstanden.")
                return

        # Frage an Backend senden
        self.speak("Moment, ich denke nach...")
        response = self.ask_backend(clean_text, agent)

        print(f"🤖 Antwort: {response[:200]}...")
        self.speak(response)

    def run(self):
        """Hauptschleife - lauscht auf "Hey Mujo" """
        self.running = True

        print("")
        print("═" * 60)
        print("  🤖 SIRI - Dein persönlicher Coding-Assistent")
        print("═" * 60)
        print("")
        print("  Sage 'Hey Siri' um mich zu aktivieren")
        print("  Sage 'Stop' oder 'Beenden' um zu beenden")
        print("")
        print("  Beispiele:")
        print("    • 'Hey Siri, wie erstelle ich eine REST API?'")
        print("    • 'Siri, erkläre mir React Hooks'")
        print("    • 'Hey Siri, frag den Coder wie schreibe ich einen Test'")
        print("")
        print("═" * 60)
        print("")

        self.speak("Hallo! Ich bin dein Coding-Assistent. Sage Hey Siri wenn du mich brauchst.")

        while self.running:
            try:
                # Lausche im Hintergrund
                print("👂 Lausche... (sage 'Hey Siri')")
                text = self.listen(timeout=None, phrase_limit=15)

                if not text:
                    continue

                print(f"🎤 Gehört: {text}")

                # Prüfe auf Wake Word
                if self.check_wake_word(text):
                    # Entferne Wake Word aus Text
                    command = text.lower()
                    for wake_word in sorted(self.WAKE_WORDS, key=len, reverse=True):
                        command = command.replace(wake_word, "")
                    # Entferne auch "hey" falls übrig
                    command = command.replace("hey", "").strip()
                    # Entferne Satzzeichen am Anfang
                    command = command.lstrip(",. ")

                    if command and len(command) > 2:
                        # Befehl wurde zusammen mit Wake Word gesagt
                        self.handle_command(command)
                    else:
                        # Wake Word allein - warte auf Befehl
                        self.speak("Ja? Was kann ich für dich tun?")
                        print("👂 Warte auf Befehl...")

                        command = self.listen(timeout=8, phrase_limit=15)
                        if command:
                            self.handle_command(command)
                        else:
                            self.speak("Ich habe dich nicht gehört.")

                # Kurze Pause
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n👋 Beende...")
                self.speak("Auf Wiedersehen!")
                break
            except Exception as e:
                print(f"⚠️  Fehler: {e}")
                time.sleep(1)

        print("✅ Mujo beendet.")


def main():
    """Hauptfunktion"""
    # Signal Handler für sauberes Beenden
    def signal_handler(sig, frame):
        print("\n👋 Beende Mujo...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Starte Mujo
    mujo = MujoAssistant()
    mujo.run()


if __name__ == "__main__":
    main()
