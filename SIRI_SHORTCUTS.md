# 🎤 Siri Shortcuts für Super Mac Assistant

Verbinde Siri mit dem Super Mac Assistant für **Voice Commands**!

---

## 📋 Voraussetzungen

- ✅ Super Mac Assistant läuft (Daemon oder manual)
- ✅ Backend läuft (`npm run backend:dev`)
- ✅ macOS Shortcuts App installiert

---

## 🚀 Shortcuts erstellen

### Shortcut 1: **"Supervisor Command"**

Für Befehle an den ENGINEERING_LEAD_SUPERVISOR.

**Schritte:**

1. Öffne **Shortcuts.app**
2. Klicke auf **"+"** (Neuer Shortcut)
3. Benenne ihn: **"Supervisor Command"**
4. Füge folgende Aktionen hinzu:

```
1. [Frage nach Eingabe]
   - Frage: "Was soll der Supervisor tun?"
   - Eingabetyp: Text

2. [Shell-Skript ausführen]
   - Shell: /bin/bash
   - Eingabe: Als Argument übergeben
   - Skript:
     cd /Users/dsselmanovic/activi-dev-repos/super-mac-assistant
     source venv/bin/activate
     python3 -c "
     import sys
     from src.core import SuperMacAssistant
     from src.agents.agent_identity import AgentType

     assistant = SuperMacAssistant()
     assistant.agent_manager.switch_to(AgentType.SUPERVISOR)
     result = assistant.process_command(sys.argv[1], voice=True)
     print(result['message'])
     " "$1"

3. [Diktat]
   - Text: Shell-Skript-Ergebnis
```

**Aktivieren:**
- Settings → Siri & Search → "Supervisor Command" aktivieren
- Siri-Phrase: **"Hey Siri, Supervisor Command"**

---

### Shortcut 2: **"Assistant Command"**

Für Befehle an den CLOUD_ASSISTANT.

**Schritte:**

1. Öffne **Shortcuts.app**
2. Klicke auf **"+"** (Neuer Shortcut)
3. Benenne ihn: **"Assistant Command"**
4. Füge folgende Aktionen hinzu:

```
1. [Frage nach Eingabe]
   - Frage: "Was soll der Assistant tun?"
   - Eingabetyp: Text

2. [Shell-Skript ausführen]
   - Shell: /bin/bash
   - Eingabe: Als Argument übergeben
   - Skript:
     cd /Users/dsselmanovic/activi-dev-repos/super-mac-assistant
     source venv/bin/activate
     python3 -c "
     import sys
     from src.core import SuperMacAssistant
     from src.agents.agent_identity import AgentType

     assistant = SuperMacAssistant()
     assistant.agent_manager.switch_to(AgentType.ASSISTANT)
     result = assistant.process_command(sys.argv[1], voice=True)
     print(result['message'])
     " "$1"

3. [Diktat]
   - Text: Shell-Skript-Ergebnis
```

**Aktivieren:**
- Settings → Siri & Search → "Assistant Command" aktivieren
- Siri-Phrase: **"Hey Siri, Assistant Command"**

---

### Shortcut 3: **"Agent Status"**

Zeigt den Status des Systems.

**Schritte:**

1. Öffne **Shortcuts.app**
2. Klicke auf **"+"** (Neuer Shortcut)
3. Benenne ihn: **"Agent Status"**
4. Füge folgende Aktion hinzu:

```
1. [Shell-Skript ausführen]
   - Shell: /bin/bash
   - Skript:
     cd /Users/dsselmanovic/activi-dev-repos/super-mac-assistant
     source venv/bin/activate
     python3 -c "
     from src.core import SuperMacAssistant
     import json

     assistant = SuperMacAssistant()
     status = assistant.get_status()
     agent = status['current_agent']

     print(f\"Agent: {agent['name']}\")
     print(f\"Backend: {'✅' if status['backend_available'] else '❌'}\")
     print(f\"Slack: {'✅' if status['slack_enabled'] else '❌'}\")
     "

2. [Diktat]
   - Text: Shell-Skript-Ergebnis
```

**Aktivieren:**
- Settings → Siri & Search → "Agent Status" aktivieren
- Siri-Phrase: **"Hey Siri, Agent Status"**

---

### Shortcut 4: **"Quick Screenshot"**

Macht einen Screenshot und benachrichtigt via Slack.

**Schritte:**

1. Öffne **Shortcuts.app**
2. Klicke auf **"+"** (Neuer Shortcut)
3. Benenne ihn: **"Quick Screenshot"**
4. Füge folgende Aktion hinzu:

```
1. [Shell-Skript ausführen]
   - Shell: /bin/bash
   - Skript:
     cd /Users/dsselmanovic/activi-dev-repos/super-mac-assistant
     source venv/bin/activate
     python3 -c "
     from src.core import SuperMacAssistant

     assistant = SuperMacAssistant()
     result = assistant.process_command('screenshot', voice=True)
     print(result['message'])
     "

2. [Diktat]
   - Text: Shell-Skript-Ergebnis
```

**Aktivieren:**
- Settings → Siri & Search → "Quick Screenshot" aktivieren
- Siri-Phrase: **"Hey Siri, Quick Screenshot"**

---

## 🎙️ Beispiel-Kommandos

### Supervisor Commands

```
"Hey Siri, Supervisor Command"
→ "Erstelle einen Plan für das neue Feature"

"Hey Siri, Supervisor Command"
→ "Analysiere das Risiko dieser Änderung"

"Hey Siri, Supervisor Command"
→ "Delegiere Task an den Assistant"
```

### Assistant Commands

```
"Hey Siri, Assistant Command"
→ "Implementiere die Login-Funktion"

"Hey Siri, Assistant Command"
→ "Fixe den Bug in der API"

"Hey Siri, Assistant Command"
→ "Führe die Tests aus"
```

### Status & Utility

```
"Hey Siri, Agent Status"
→ Zeigt aktuellen Status

"Hey Siri, Quick Screenshot"
→ Macht Screenshot und sendet Notification
```

---

## 🔧 Troubleshooting

### "Shortcuts konnte nicht ausgeführt werden"

**Lösung:**
1. Überprüfe Dateipfade in den Shell-Skripten
2. Stelle sicher, dass venv aktiviert ist
3. Teste das Python-Skript manuell:
   ```bash
   cd ~/activi-dev-repos/super-mac-assistant
   source venv/bin/activate
   python3 src/core.py
   ```

### "Backend not available"

**Lösung:**
1. Starte Backend:
   ```bash
   cd ~/activi-dev-repos/Optimizecodecloudagents
   npm run backend:dev
   ```
2. Prüfe ob Port 3000 läuft:
   ```bash
   lsof -i :3000
   ```

### "Permission denied"

**Lösung:**
1. Settings → Privacy & Security → Automation
2. Erlaube Shortcuts Zugriff auf Terminal
3. Erlaube Shortcuts Zugriff auf Python

---

## 🎯 Fortgeschrittene Nutzung

### Direkter Befehl ohne Eingabe

Für häufige Commands kannst du Shortcuts ohne Eingabe-Prompt erstellen:

**Beispiel: "Deploy Backend"**

```bash
cd /Users/dsselmanovic/activi-dev-repos/super-mac-assistant
source venv/bin/activate
python3 -c "
from src.core import SuperMacAssistant
from src.agents.agent_identity import AgentType

assistant = SuperMacAssistant()
assistant.agent_manager.switch_to(AgentType.SUPERVISOR)
result = assistant.process_command('Deploy backend to production', voice=True)
print(result['message'])
"
```

Siri-Phrase: **"Hey Siri, Deploy Backend"**

---

## 📱 iOS Integration (Optional)

Du kannst die gleichen Shortcuts auch auf iPhone/iPad erstellen!

1. Öffne Shortcuts App auf iOS
2. Erstelle gleiche Shortcuts
3. Verwende SSH statt lokale Shell:

```
ssh user@mac-ip "cd ~/activi-dev-repos/super-mac-assistant && ..."
```

---

## ✅ Fertig!

Jetzt kannst du deinen Mac per Stimme steuern und mit den Cloud Agents kommunizieren! 🎉

**Test:**
- "Hey Siri, Agent Status"
- "Hey Siri, Supervisor Command" → "Zeige mir den Status"
- "Hey Siri, Quick Screenshot"
