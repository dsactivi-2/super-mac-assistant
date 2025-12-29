# 🚀 Super Mac Assistant

**Lokaler Mac-Agent der mit Siri kommuniziert, deinen Laptop steuert und mit den Code Cloud Agents verknüpft ist.**

---

## 🌟 Features

### 🎤 Siri Integration
- Sprachbefehle an Supervisor oder Assistant
- "Hey Siri, Supervisor Command" → "Deploy backend"
- Natürliche Sprache, keine CLI nötig

### 🤖 Dual Agent System
- **ENGINEERING_LEAD_SUPERVISOR**: Plant, delegiert, verifiziert
- **CLOUD_ASSISTANT**: Implementiert, testet, liefert

### 💻 Lokale Mac-Steuerung
- Screenshots machen
- Apps öffnen
- Terminal Commands ausführen
- Sleep Mode aktivieren

### 🔗 Backend Integration
- WebSocket + REST API zu localhost:3000
- Task Management
- Chat mit 8 AI Agents
- GitHub/Linear/Slack Integration

### 🔄 Autostart
- LaunchAgent für Boot-Start
- Läuft unsichtbar im Hintergrund
- Menu Bar Icon für Kontrolle

---

## 📦 Installation

### Voraussetzungen

- macOS 10.14+
- Python 3.8+
- Code Cloud Agents Backend (localhost:3000)

### Setup

```bash
cd ~/activi-dev-repos/super-mac-assistant
chmod +x setup.sh
./setup.sh
```

Das Setup-Script:
1. ✅ Erstellt Python venv
2. ✅ Installiert Dependencies
3. ✅ Testet Backend-Verbindung
4. ✅ Installiert LaunchAgent (optional)

---

## 🚀 Nutzung

### 1. Manuell starten

```bash
cd ~/activi-dev-repos/super-mac-assistant
source venv/bin/activate
python3 src/core.py
```

### 2. Als Daemon starten

```bash
python3 src/daemon.py
```

### 3. Mit Siri (Empfohlen!)

Siehe: **[SIRI_SHORTCUTS.md](SIRI_SHORTCUTS.md)**

```
"Hey Siri, Supervisor Command"
→ "Erstelle einen Deployment-Plan"

"Hey Siri, Assistant Command"
→ "Implementiere die Login-Funktion"

"Hey Siri, Agent Status"
→ Zeigt Status
```

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────┐
│  SIRI (Voice Commands)                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  macOS Shortcuts.app                    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  SUPER MAC ASSISTANT (Lokal)            │
│  ├─ Agent Manager (Supervisor/Assistan │
│  ├─ Backend API Client (WebSocket+REST)│
│  ├─ Local Mac Control (AppleScript)    │
│  └─ Slack Integration Proxy            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  CODE CLOUD AGENTS BACKEND              │
│  (localhost:3000)                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  INTEGRATIONS                           │
│  - Slack (mit Agent-Identitäten)       │
│  - GitHub                               │
│  - Linear                               │
└─────────────────────────────────────────┘
```

---

## 🎯 Agent Modi

### ENGINEERING_LEAD_SUPERVISOR 🤖

**Rolle:** Strategische Planung, Delegation, Qualitätskontrolle

**Capabilities:**
- Strategische Planung
- Task Delegation
- Risk Assessment (STOP Score)
- Evidence-Based Verification

**Beispiel Commands:**
```bash
"Erstelle einen Plan für Feature X"
"Analysiere das Risiko dieser Änderung"
"Delegiere Task an den Assistant"
"Verifiziere die Implementierung"
```

### CLOUD_ASSISTANT ⚡

**Rolle:** Code-Implementierung, Testing, Execution

**Capabilities:**
- Code Implementation
- Bug Fixing
- Testing & Verification
- Evidence Collection
- Documentation

**Beispiel Commands:**
```bash
"Implementiere die Login-Funktion"
"Fixe den Bug in api/auth.ts"
"Führe alle Tests aus"
"Erstelle einen Screenshot als Evidence"
```

---

## 📡 API Endpoints

### Backend API Client

```python
from src.api.backend_client import BackendAPIClient

client = BackendAPIClient()

# Tasks
client.create_task("Implement login")
client.list_tasks(status="pending")
client.get_task(task_id)

# Chat
client.send_chat_message("Hello", agent_name="emir")
client.get_chat_history()

# GitHub
client.github_create_issue("owner/repo", "Bug fix")

# Linear
client.linear_create_issue("Feature request")

# Slack (via agents)
client.send_slack_message_as_agent("supervisor", user_id, "Message")
```

---

## 🛠️ Development

### Projekt-Struktur

```
super-mac-assistant/
├── src/
│   ├── api/
│   │   └── backend_client.py      # Backend API Client
│   ├── agents/
│   │   └── agent_identity.py      # Agent System
│   ├── core.py                    # Main Core
│   ├── daemon.py                  # Background Daemon
│   ├── ui/                        # Menu Bar App (TODO)
│   ├── plugins/                   # Mac Control Plugins
│   └── utils/                     # Utilities
├── setup.sh                       # Setup Script
├── requirements.txt               # Dependencies
├── com.step2job.supermacassistant.plist  # LaunchAgent
├── SIRI_SHORTCUTS.md             # Siri Setup Guide
└── README.md                      # This file
```

### Agent wechseln

```python
from src.core import SuperMacAssistant
from src.agents.agent_identity import AgentType

assistant = SuperMacAssistant()

# Switch to Supervisor
assistant.agent_manager.switch_to(AgentType.SUPERVISOR)

# Switch to Assistant
assistant.agent_manager.switch_to(AgentType.ASSISTANT)

# Get current
agent = assistant.get_current_agent()
print(agent.name)  # "ENGINEERING_LEAD_SUPERVISOR"
```

---

## 🔧 Configuration

### Backend URL

Default: `http://localhost:3000`

Ändern:
```python
assistant = SuperMacAssistant(backend_url="http://your-server:3000")
```

### Slack User ID

In `src/core.py`:
```python
self.user_id = "U0904E3AAR5"  # Deine Slack User ID
```

### Slack Notifications

```python
assistant.enable_slack_notifications()   # Enable
assistant.disable_slack_notifications()  # Disable
```

---

## 📊 Status prüfen

### CLI

```bash
python3 -c "
from src.core import SuperMacAssistant
assistant = SuperMacAssistant()
print(assistant.get_status())
"
```

### Via Siri

```
"Hey Siri, Agent Status"
```

---

## 🐛 Troubleshooting

### Backend nicht erreichbar

```bash
# Start Backend
cd ~/activi-dev-repos/Optimizecodecloudagents
npm run backend:dev

# Check Port
lsof -i :3000
```

### LaunchAgent läuft nicht

```bash
# Unload & Reload
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Check Status
launchctl list | grep supermacassistant

# View Logs
tail -f ~/activi-dev-repos/super-mac-assistant/logs/stdout.log
```

### Siri Shortcuts funktionieren nicht

1. Settings → Privacy & Security → Automation
2. Erlaube **Shortcuts** Zugriff auf **Terminal**
3. Teste Shell-Skript manuell

---

## 🎉 Example Workflow

### Scenario: Neues Feature implementieren

1. **Siri:** "Hey Siri, Supervisor Command"
2. **Du:** "Erstelle einen Plan für User-Authentication"
3. **Supervisor:** Analysiert, erstellt Task, delegiert
4. **Siri:** "Hey Siri, Assistant Command"
5. **Du:** "Implementiere den Login-Endpoint"
6. **Assistant:** Schreibt Code, testet, sammelt Evidence
7. **Supervisor:** Verifiziert, sendet Slack-Notification

---

## 📝 TODO

- [ ] Menu Bar App (UI)
- [ ] Screenshot-Upload zu Slack
- [ ] Code Diff Analysis
- [ ] Git Integration
- [ ] Auto-PR Creation
- [ ] iOS Companion App

---

## 🤝 Contributing

Dieses Projekt ist Teil des **Code Cloud Agents** Ecosystems.

---

## 📄 License

Proprietary - Step2Job GmbH

---

**Made with ❤️ by Denis Selmanovic & Claude Sonnet 4.5**

🤖 Generated with [Claude Code](https://claude.com/claude-code)
