# 📚 Super Mac Assistant - Documentation Index

**Complete documentation for safe operation and development**

---

## 🎯 Quick Start

1. **New User?** → Start with [README.md](../README.md)
2. **Setting up Siri?** → See [SIRI_SHORTCUTS.md](../SIRI_SHORTCUTS.md)
3. **Security concerns?** → Read [SECURITY.md](../SECURITY.md)
4. **Want to contribute?** → Check [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 📖 Documentation Structure

### 🟢 User Documentation

| Document                                  | Purpose                                 | When to read                    |
| ----------------------------------------- | --------------------------------------- | ------------------------------- |
| [README.md](../README.md)                 | Overview, installation, basic usage     | **START HERE**                  |
| [SIRI_SHORTCUTS.md](../SIRI_SHORTCUTS.md) | Voice control setup                     | After installation              |
| [SECURITY.md](../SECURITY.md)             | Security model, threats, best practices | **MUST READ** before production |
| [RUNBOOK.md](./RUNBOOK.md)                | Common commands, troubleshooting        | When things break               |

### 🟡 Developer Documentation

| Document                              | Purpose                           | When to read             |
| ------------------------------------- | --------------------------------- | ------------------------ |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | How to add new actions safely     | Before coding            |
| [ARCHITECTURE.md](./ARCHITECTURE.md)  | System design, data flow          | Understanding internals  |
| [OPERATIONS.md](./OPERATIONS.md)      | Deployment, monitoring, incidents | Production ops           |
| [POLICY_GUIDE.md](./POLICY_GUIDE.md)  | Policy.yaml reference             | Adding/modifying actions |

### 🔴 Security Documentation

| Document                                       | Purpose                               | When to read             |
| ---------------------------------------------- | ------------------------------------- | ------------------------ |
| [SECURITY.md](../SECURITY.md)                  | Complete security model               | **CRITICAL**             |
| [THREAT_MODEL.md](./THREAT_MODEL.md)           | Known threats and mitigations         | Security reviews         |
| [AUDIT_GUIDE.md](./AUDIT_GUIDE.md)             | Log review procedures                 | Weekly/incident response |
| [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) | What to do when security event occurs | During incidents         |

---

## 🗂️ By Task

### I want to...

#### Use the System

- **Get started** → [README.md](../README.md) → [SIRI_SHORTCUTS.md](../SIRI_SHORTCUTS.md)
- **Understand security** → [SECURITY.md](../SECURITY.md)
- **Fix a problem** → [RUNBOOK.md](./RUNBOOK.md)
- **Review audit logs** → [AUDIT_GUIDE.md](./AUDIT_GUIDE.md)

#### Develop

- **Add a new action** → [CONTRIBUTING.md](../CONTRIBUTING.md) → [POLICY_GUIDE.md](./POLICY_GUIDE.md)
- **Understand the code** → [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Run tests** → [TESTING.md](./TESTING.md)
- **Deploy changes** → [OPERATIONS.md](./OPERATIONS.md)

#### Operate in Production

- **Start/stop daemon** → [OPERATIONS.md](./OPERATIONS.md) § Daemon Management
- **Monitor health** → [OPERATIONS.md](./OPERATIONS.md) § Monitoring
- **Handle incident** → [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md)
- **Review security** → [AUDIT_GUIDE.md](./AUDIT_GUIDE.md)

---

## 📁 Code Structure

```
super-mac-assistant/
├── policy/
│   └── policy.yaml           # 🔐 SINGLE SOURCE OF TRUTH
│
├── executor/                 # Role2: Deterministic Execution
│   ├── validator.py          # Policy validation
│   └── executor.py           # Action execution
│
├── researcher/               # Role1: LLM Planning
│   └── researcher.py         # Natural language → actions
│
├── src/
│   ├── api/
│   │   └── backend_client.py # Backend API client
│   ├── security/
│   │   ├── action_allowlist.py   # (deprecated - use policy.yaml)
│   │   ├── audit_log.py          # Audit logging
│   │   ├── kill_switch.py        # Emergency stop
│   │   └── finance_guard.py      # Finance protection
│   ├── agents/
│   │   └── agent_identity.py     # Agent personalities
│   └── core.py               # Main coordinator
│
├── shortcuts/                # Siri Shortcuts
├── launchd/                  # Auto-start configuration
├── docs/                     # Documentation (you are here)
└── tests/                    # Test suite
```

---

## 🔑 Key Concepts

### 1. Role Separation

- **Role1 (Researcher)**: LLM-based, can be wrong, plans actions
- **Role2 (Executor)**: Deterministic, validates against policy, executes
- **NO LLM in execution path** ← Critical security property

### 2. Policy-First

- `policy/policy.yaml` is the **SINGLE SOURCE OF TRUTH**
- All actions must be defined in policy
- All targets must be in allowlists (NO free strings)

### 3. Risk Levels

- **Risk 0**: Read-only, execute immediately
- **Risk 1**: Can disrupt work, verbal confirmation
- **Risk 2**: Can modify data, explicit confirmation with challenge/response
- **Risk 3**: Too dangerous, ALWAYS DENIED

### 4. FinanceGuard

- **Multi-layer**: OS-level + Policy + Runtime detection
- **Finance volume**: Encrypted DMG, unmounted by default
- **Blocks**: Keywords, paths, apps, domains

### 5. Audit Everything

- All actions logged to `logs/audit/audit_YYYYMMDD.jsonl`
- 90-day retention
- Weekly reports
- Search and statistics

---

## 🚨 Emergency Contacts

### Kill Switch

```bash
# Pause all operations (reversible)
python3 src/security/kill_switch.py pause

# Resume
python3 src/security/kill_switch.py resume

# EMERGENCY STOP (requires restart)
python3 src/security/kill_switch.py kill
```

### Quick Health Check

```bash
# Check system status
python3 -c "from executor.executor import ActionExecutor; from executor.validator import PolicyValidator; from src.security.audit_log import AuditLogger; e = ActionExecutor(PolicyValidator(), AuditLogger()); print(e.execute('status_overview', {}))"
```

### Audit Log (Last 24h)

```bash
python3 -c "from src.security.audit_log import AuditLogger; print(AuditLogger().export_report(hours=24))"
```

---

## 📞 Support

- **Security Issue**: Pause system immediately → Review audit logs → See [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md)
- **Bug**: Check [RUNBOOK.md](./RUNBOOK.md) → File issue with logs
- **Feature Request**: Read [CONTRIBUTING.md](../CONTRIBUTING.md) → Discuss security implications

---

## 🔄 Document Versions

| Date       | Version | Changes                                               |
| ---------- | ------- | ----------------------------------------------------- |
| 2025-12-27 | 2.0     | Enterprise architecture with Role1/Role2, policy.yaml |
| 2024-XX-XX | 1.0     | Initial version with allowlist                        |

---

**🔒 Remember: Security is not optional - it's mandatory!**

Made with ❤️ & 🔒 by Denis Selmanovic & Claude Sonnet 4.5
