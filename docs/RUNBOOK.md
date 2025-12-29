# 📖 Runbook - Common Commands & Troubleshooting

**Quick reference for daily operations and problem-solving**

---

## 🚀 Quick Commands

### System Control

```bash
# Status check
python3 src/security/kill_switch.py status

# Pause (reversible)
python3 src/security/kill_switch.py pause

# Resume
python3 src/security/kill_switch.py resume

# Emergency stop (requires restart)
python3 src/security/kill_switch.py kill

# Reset after kill
python3 src/security/kill_switch.py reset
```

### Daemon Control

```bash
# Start
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Restart
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist && \
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Check if running
launchctl list | grep supermacassistant
ps aux | grep daemon.py
```

### Logs

```bash
# View audit log (last 24h)
python3 -c "from src.security.audit_log import AuditLogger; print(AuditLogger().export_report(hours=24))"

# View daemon stdout
tail -f ~/activi-dev-repos/super-mac-assistant/logs/stdout.log

# View daemon errors
tail -f ~/activi-dev-repos/super-mac-assistant/logs/stderr.log

# Search audit logs
python3 -c "from src.security.audit_log import AuditLogger; results = AuditLogger().search_logs('git_push', hours=168); print(f'Found {len(results)} matches')"

# Get audit stats
python3 -c "from src.security.audit_log import AuditLogger; import json; print(json.dumps(AuditLogger().get_stats(hours=24), indent=2))"
```

### FinanceGuard

```bash
# Check status
python3 -c "from src.security.finance_guard import FinanceGuard; import yaml; policy = yaml.safe_load(open('policy/policy.yaml')); print(FinanceGuard(policy['finance_guard']).get_status())"

# Security check
python3 -c "from src.security.finance_guard import FinanceGuard; import yaml; policy = yaml.safe_load(open('policy/policy.yaml')); status = FinanceGuard(policy['finance_guard']).check_system_security(); print(f'Secure: {status[\"secure\"]}, Violations: {status[\"violations\"]}')"

# Emergency lockdown
python3 -c "from src.security.finance_guard import FinanceGuard; from src.security.audit_log import AuditLogger; import yaml; policy = yaml.safe_load(open('policy/policy.yaml')); FinanceGuard(policy['finance_guard']).emergency_lockdown(AuditLogger())"
```

### Testing

```bash
# Run integration tests
cd ~/activi-dev-repos/super-mac-assistant
python3 tests/test_integration.py

# Test policy validator
python3 executor/validator.py

# Test FinanceGuard
python3 src/security/finance_guard.py

# Test specific action
python3 -c "
from executor.validator import PolicyValidator
from executor.executor import ActionExecutor
from src.security.audit_log import AuditLogger

executor = ActionExecutor(PolicyValidator(), AuditLogger())
result = executor.execute('status_overview', {})
print(result)
"
```

---

## 🔍 Troubleshooting

### Problem: Daemon won't start

**Symptoms:**
- `launchctl load` fails
- `ps aux | grep daemon.py` shows nothing
- Siri shortcuts don't work

**Diagnosis:**
```bash
# Check LaunchAgent status
launchctl list | grep supermacassistant

# Check stderr log
tail -50 ~/activi-dev-repos/super-mac-assistant/logs/stderr.log

# Try starting manually
cd ~/activi-dev-repos/super-mac-assistant
source venv/bin/activate
python3 src/daemon.py
# Watch for errors
```

**Common Causes & Fixes:**

1. **Python environment not activated**
   ```bash
   # Fix LaunchAgent to use venv python
   # Edit plist, change <ProgramArguments>
   vi ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   ```

2. **Missing dependencies**
   ```bash
   cd ~/activi-dev-repos/super-mac-assistant
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Kill switch is set to 'killed'**
   ```bash
   python3 src/security/kill_switch.py status
   # If killed:
   python3 src/security/kill_switch.py reset
   ```

4. **Port already in use**
   ```bash
   # Check what's on port (if daemon uses one)
   lsof -i :PORT
   # Kill old process
   kill PID
   ```

### Problem: Siri shortcuts don't work

**Symptoms:**
- Siri says "There was a problem with the app"
- Shortcuts return error
- Actions not executing

**Diagnosis:**
```bash
# 1. Check if daemon running
ps aux | grep daemon.py

# 2. Check backend connection
curl http://localhost:3000/health

# 3. Check kill switch
python3 src/security/kill_switch.py status

# 4. Test action directly
python3 -c "
from executor.validator import PolicyValidator
from executor.executor import ActionExecutor
from src.security.audit_log import AuditLogger

executor = ActionExecutor(PolicyValidator(), AuditLogger())
result = executor.execute('status_overview', {})
print(result)
"
```

**Common Causes & Fixes:**

1. **Daemon not running**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   ```

2. **Backend not running**
   ```bash
   cd ~/activi-dev-repos/Optimizecodecloudagents
   npm run dev
   ```

3. **Kill switch paused/killed**
   ```bash
   python3 src/security/kill_switch.py resume
   ```

4. **Permissions issue**
   - System Preferences → Security & Privacy → Privacy
   - Check Accessibility, Automation permissions

5. **Shortcut misconfigured**
   - Open Shortcuts app
   - Check "Run Shell Script" action has correct path
   - Check "Get Contents of URL" has correct localhost:PORT

### Problem: Actions being denied unexpectedly

**Symptoms:**
- Actions return `"success": false`
- Error says "denied" or "blocked"
- Works sometimes, fails other times

**Diagnosis:**
```bash
# 1. Check audit log for denials
python3 -c "
from src.security.audit_log import AuditLogger
logger = AuditLogger()
events = [log for log in logger.get_recent_logs(hours=1)
          if log.get('type') == 'security_event']
for event in events:
    print(f\"{event['timestamp']}: {event['event_type']} - {event['description']}\")
"

# 2. Test action validation
python3 -c "
from executor.validator import PolicyValidator
validator = PolicyValidator()
result = validator.validate_action('action_name', {'arg': 'value'})
print(result)
"

# 3. Check rate limits
python3 -c "
from executor.validator import PolicyValidator
validator = PolicyValidator()
action_info = validator.get_action_info('action_name')
print(f\"Rate limit: {action_info.get('rate_limit', 'None')}\")
"
```

**Common Causes & Fixes:**

1. **Rate limit exceeded**
   ```bash
   # Wait 1 hour for rate limit to reset
   # OR increase limit in policy.yaml
   ```

2. **Invalid argument**
   ```bash
   # Check args_schema in policy.yaml
   # Ensure using values from allowlists
   ```

3. **FinanceGuard triggered**
   ```bash
   # Check if contains finance keywords/paths
   python3 -c "
   from src.security.finance_guard import FinanceGuard
   import yaml
   policy = yaml.safe_load(open('policy/policy.yaml'))
   guard = FinanceGuard(policy['finance_guard'])

   # Test your input
   is_finance, matched = guard.access_detector.check_keyword('your text')
   print(f'Finance: {is_finance}, Matched: {matched}')
   "
   ```

4. **Risk 2 needs confirmation**
   ```bash
   # High-risk actions require explicit confirmation
   # Check if action has risk: 2 in policy.yaml
   # Implement confirmation flow
   ```

### Problem: Backend connection failing

**Symptoms:**
- "Backend unreachable" errors
- `check_backend_health` fails
- Tasks/chat not working

**Diagnosis:**
```bash
# 1. Check if backend running
curl http://localhost:3000/health

# 2. Check backend process
ps aux | grep "node.*Optimizecodecloudagents"

# 3. Check port
lsof -i :3000

# 4. Check backend logs
cd ~/activi-dev-repos/Optimizecodecloudagents
tail -f logs/server.log
```

**Common Causes & Fixes:**

1. **Backend not started**
   ```bash
   cd ~/activi-dev-repos/Optimizecodecloudagents
   npm run dev
   ```

2. **Port conflict**
   ```bash
   # Kill process on port 3000
   lsof -i :3000
   kill PID

   # Restart backend
   npm run dev
   ```

3. **Wrong URL configured**
   ```bash
   # Check environment variable
   echo $BACKEND_URL

   # Should be: http://localhost:3000
   export BACKEND_URL="http://localhost:3000"
   ```

4. **Backend crashed**
   ```bash
   # Check backend error logs
   tail -100 ~/activi-dev-repos/Optimizecodecloudagents/logs/error.log

   # Restart
   npm run dev
   ```

### Problem: Finance volume accidentally mounted

**Symptoms:**
- FinanceGuard reports `volume_mounted: true`
- Security check fails
- Finance access attempts logged

**Immediate Action:**
```bash
# 1. PAUSE system immediately
python3 src/security/kill_switch.py pause

# 2. Emergency lockdown
python3 -c "
from src.security.finance_guard import FinanceGuard
from src.security.audit_log import AuditLogger
import yaml
policy = yaml.safe_load(open('policy/policy.yaml'))
result = FinanceGuard(policy['finance_guard']).emergency_lockdown(AuditLogger())
print(result)
"

# 3. Verify unmounted
ls /Volumes/ | grep Finance
# Should be empty

# 4. Review what happened
python3 -c "
from src.security.audit_log import AuditLogger
logger = AuditLogger()
events = logger.search_logs('finance', hours=24)
print(f'Found {len(events)} finance-related events')
"

# 5. If safe, resume
python3 src/security/kill_switch.py resume
```

### Problem: Audit logs growing too large

**Symptoms:**
- Disk space warnings
- Slow log queries
- Large logs directory

**Diagnosis:**
```bash
# Check size
du -sh ~/activi-dev-repos/super-mac-assistant/logs/
du -sh ~/activi-dev-repos/super-mac-assistant/logs/audit/

# Count log files
ls -l ~/activi-dev-repos/super-mac-assistant/logs/audit/ | wc -l
```

**Solutions:**

1. **Compress old logs**
   ```bash
   cd ~/activi-dev-repos/super-mac-assistant/logs/audit

   # Compress logs older than 7 days
   find . -name "audit_*.jsonl" -mtime +7 -exec gzip {} \;
   ```

2. **Delete old compressed logs**
   ```bash
   # Delete compressed logs older than 90 days (per policy)
   find . -name "audit_*.jsonl.gz" -mtime +90 -delete
   ```

3. **Reduce retention**
   ```yaml
   # In policy.yaml
   audit:
     retention_days: 60  # Reduce from 90
   ```

---

## 📋 Common Workflows

### Workflow: Add a new allowed app

**Steps:**
1. Edit policy.yaml
   ```yaml
   allowlists:
     apps:
       - "Visual Studio Code"
       - "Google Chrome"
       - "Your New App"  # Add here
   ```

2. Restart daemon
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   ```

3. Test
   ```python
   python3 -c "
   from executor.validator import PolicyValidator
   validator = PolicyValidator()
   apps = validator.get_allowlist('apps')
   print('Your New App' in apps)  # Should be True
   "
   ```

### Workflow: Investigate suspicious activity

**Steps:**
1. Pause system
   ```bash
   python3 src/security/kill_switch.py pause
   ```

2. Review last 24h of audit logs
   ```bash
   python3 -c "from src.security.audit_log import AuditLogger; print(AuditLogger().export_report(hours=24))" > audit_review.txt
   ```

3. Check security events
   ```bash
   python3 -c "
   from src.security.audit_log import AuditLogger
   events = [log for log in AuditLogger().get_recent_logs(hours=24)
             if log.get('type') == 'security_event']
   print(f'Security events: {len(events)}')
   for e in events:
       print(f\"  {e['timestamp']}: {e['event_type']}\")
   "
   ```

4. Check FinanceGuard
   ```bash
   python3 -c "
   from src.security.finance_guard import FinanceGuard
   import yaml
   policy = yaml.safe_load(open('policy/policy.yaml'))
   status = FinanceGuard(policy['finance_guard']).get_status()
   print(status)
   "
   ```

5. Decide: Resume or Kill
   ```bash
   # If safe:
   python3 src/security/kill_switch.py resume

   # If compromised:
   python3 src/security/kill_switch.py kill
   ```

### Workflow: Update policy.yaml safely

**Steps:**
1. Backup current policy
   ```bash
   cp policy/policy.yaml policy/policy.yaml.backup
   ```

2. Edit policy.yaml
   ```bash
   vi policy/policy.yaml
   ```

3. Validate syntax
   ```bash
   python3 -c "
   import yaml
   with open('policy/policy.yaml') as f:
       policy = yaml.safe_load(f)
   print('✅ Valid YAML')
   print(f'Actions: {len(policy[\"actions\"])}')
   "
   ```

4. Test with validator
   ```bash
   python3 executor/validator.py
   ```

5. Restart daemon
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
   ```

6. Verify changes
   ```bash
   python3 -c "
   from executor.validator import PolicyValidator
   validator = PolicyValidator()
   # Test your new action
   result = validator.validate_action('your_new_action', {})
   print(result)
   "
   ```

---

## 🔧 Useful One-Liners

```bash
# Count actions by risk level
python3 -c "from executor.validator import PolicyValidator; v = PolicyValidator(); print(f\"Risk 0: {len(v.list_allowed_actions(0))}, Risk 1: {len(v.list_allowed_actions(1))}, Risk 2: {len(v.list_allowed_actions(2))}\")"

# Get all security events today
python3 -c "from src.security.audit_log import AuditLogger; events = [log for log in AuditLogger().get_recent_logs(hours=24) if log.get('type') == 'security_event']; print(f'{len(events)} security events'); [print(f\"  {e['event_type']}\") for e in events]"

# Check if Finance volume exists
ls -la /Volumes/ | grep Finance || echo "Finance volume not found (good!)"

# Count successful vs failed actions today
python3 -c "from src.security.audit_log import AuditLogger; logs = AuditLogger().get_recent_logs(hours=24); success = sum(1 for l in logs if l.get('result', {}).get('success')); print(f'Success: {success}/{len(logs)} ({round(success/len(logs)*100 if logs else 0, 1)}%)')"

# Find all actions that accessed a specific path
python3 -c "from src.security.audit_log import AuditLogger; results = AuditLogger().search_logs('/path/to/check', hours=168); print(f'Found {len(results)} matches')"

# Get current rate limit usage for an action
python3 -c "from executor.validator import PolicyValidator; v = PolicyValidator(); v.rate_tracker['action_name'] = [...]; print(f'Used: {len(v.rate_tracker.get(\"action_name\", []))}')"
```

---

## 📚 Related Documentation

- [OPERATIONS.md](./OPERATIONS.md) - Full operations guide
- [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) - Security incidents
- [SECURITY.md](../SECURITY.md) - Security model

---

**💡 Pro Tip: Bookmark this page for quick reference!**

Made with ❤️ & 🔒 by Denis Selmanovic & Claude Sonnet 4.5
