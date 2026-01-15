# 🚀 Operations Guide

**Production deployment, monitoring, and incident response**

---

## 📋 Table of Contents

1. [Deployment](#deployment)
2. [Daemon Management](#daemon-management)
3. [Monitoring](#monitoring)
4. [Backup & Recovery](#backup--recovery)
5. [Incident Response](#incident-response)
6. [Maintenance](#maintenance)

---

## 🔧 Deployment

### Initial Setup

**Prerequisites:**

- macOS 11.0 or later
- Python 3.8+
- ANTHROPIC_API_KEY set in environment
- Backend running on localhost:3000

**Installation:**

```bash
cd ~/activi-dev-repos/super-mac-assistant

# Run setup script
chmod +x setup.sh
./setup.sh

# Answer prompts:
# - Backend URL: http://localhost:3000
# - Install LaunchAgent? yes (for auto-start)
```

### Configuration

**Environment Variables:**

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional
export BACKEND_URL="http://localhost:3000"
export BACKEND_WS_URL="ws://localhost:3000/ws"
```

**Add to ~/.zshrc or ~/.bashrc:**

```bash
# Super Mac Assistant
export ANTHROPIC_API_KEY="sk-ant-..."
```

### LaunchAgent Setup (Auto-Start)

**Install:**

```bash
# Copy plist
cp launchd/com.step2job.supermacassistant.plist ~/Library/LaunchAgents/

# Load
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Verify
launchctl list | grep supermacassistant
```

**Uninstall:**

```bash
# Unload
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Remove
rm ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

---

## 🔄 Daemon Management

### Start Daemon

**Method 1: LaunchAgent (recommended)**

```bash
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

**Method 2: Manual**

```bash
cd ~/activi-dev-repos/super-mac-assistant
source venv/bin/activate
python3 src/daemon.py &
```

### Stop Daemon

**Method 1: LaunchAgent**

```bash
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

**Method 2: Kill Switch**

```bash
python3 src/security/kill_switch.py kill
```

**Method 3: Find and kill process**

```bash
# Find PID
ps aux | grep daemon.py

# Kill
kill <PID>
```

### Restart Daemon

```bash
# Via LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist

# Or
kill <PID>
# LaunchAgent will auto-restart
```

### Check Status

```bash
# Is daemon running?
launchctl list | grep supermacassistant

# Or
ps aux | grep daemon.py

# Check kill switch state
python3 src/security/kill_switch.py status
```

---

## 📊 Monitoring

### Health Checks

**Quick Health Check:**

```bash
cd ~/activi-dev-repos/super-mac-assistant
python3 -c "
from executor.validator import PolicyValidator
from executor.executor import ActionExecutor
from src.security.audit_log import AuditLogger

executor = ActionExecutor(PolicyValidator(), AuditLogger())
result = executor.execute('status_overview', {})
print(result)
"
```

**Expected Output:**

```json
{
  "success": true,
  "backend": "healthy",
  "agent_mode": "dual",
  "audit_log_files": 3,
  "timestamp": "2025-12-27T..."
}
```

### Log Files

**Locations:**

```
~/activi-dev-repos/super-mac-assistant/logs/
├── audit/
│   └── audit_YYYYMMDD.jsonl  # Security audit logs
├── stdout.log                 # Daemon stdout
├── stderr.log                 # Daemon stderr
└── daemon.log                 # Daemon events
```

**View Audit Log:**

```bash
# Last 50 lines
python3 -c "
from src.security.audit_log import AuditLogger
print(AuditLogger().export_report(hours=24))
"

# Or directly
tail -50 ~/activi-dev-repos/super-mac-assistant/logs/audit/audit_$(date +%Y%m%d).jsonl
```

**View Daemon Logs:**

```bash
# Stdout
tail -f ~/activi-dev-repos/super-mac-assistant/logs/stdout.log

# Stderr (errors)
tail -f ~/activi-dev-repos/super-mac-assistant/logs/stderr.log
```

### Metrics to Monitor

**Daily Checks:**

- [ ] Daemon is running
- [ ] Backend is reachable
- [ ] No error spikes in stderr.log
- [ ] Audit log files being created

**Weekly Checks:**

- [ ] Review audit log report
- [ ] Check disk space (logs grow)
- [ ] Review security events
- [ ] Check rate limiting stats

**Commands:**

```bash
# Disk space
du -sh ~/activi-dev-repos/super-mac-assistant/logs/

# Audit stats
python3 -c "
from src.security.audit_log import AuditLogger
import json
stats = AuditLogger().get_stats(hours=168)  # 1 week
print(json.dumps(stats, indent=2))
"

# Security events
python3 -c "
from src.security.audit_log import AuditLogger
logger = AuditLogger()
events = [log for log in logger.get_recent_logs(hours=168)
          if log.get('type') == 'security_event']
print(f'Security events: {len(events)}')
for event in events[-10:]:  # Last 10
    print(f\"  {event['timestamp']}: {event['event_type']} - {event['description']}\")
"
```

### Alerts

**Set up alerts for:**

1. **Security Events**: Any `type == 'security_event'` in audit log
2. **Daemon Crashes**: Process not running
3. **High Error Rate**: Many failed actions
4. **Finance Access Attempts**: FinanceGuard triggers
5. **Disk Space**: Logs directory > 1GB

**Example cron job for alerts:**

```bash
# Check every hour
0 * * * * /path/to/check_health.sh
```

**check_health.sh:**

```bash
#!/bin/bash
cd ~/activi-dev-repos/super-mac-assistant
source venv/bin/activate

# Check if daemon running
if ! pgrep -f "daemon.py" > /dev/null; then
    echo "ALERT: Super Mac Assistant daemon not running" | mail -s "SMA Alert" your@email.com
fi

# Check for security events (last hour)
SECURITY_EVENTS=$(python3 -c "
from src.security.audit_log import AuditLogger
events = [log for log in AuditLogger().get_recent_logs(hours=1)
          if log.get('type') == 'security_event']
print(len(events))
")

if [ "$SECURITY_EVENTS" -gt 0 ]; then
    echo "ALERT: $SECURITY_EVENTS security events in last hour" | mail -s "SMA Security Alert" your@email.com
fi
```

---

## 💾 Backup & Recovery

### What to Backup

**Critical Files:**

```
~/activi-dev-repos/super-mac-assistant/
├── policy/policy.yaml          # ⚠️ CRITICAL
├── logs/audit/*.jsonl          # ⚠️ CRITICAL (compliance)
├── .env                        # If using (contains secrets)
└── launchd/*.plist             # Configuration
```

### Time Machine

**Included (from policy.yaml):**

- `/Users/dsselmanovic/activi-dev-repos` (including super-mac-assistant)
- `/Users/dsselmanovic/Documents/Work`

**Excluded:**

- `/Volumes/Finance` (separate backup)
- `**/node_modules`
- `**/.git/objects`
- `**/venv`

**Trigger Backup:**

```bash
# Immediate backup
tmutil startbackup

# Wait for completion
tmutil startbackup --block

# Check status
tmutil status
```

### iCloud Sync

**Enabled for:**

- `/Users/dsselmanovic/Documents/Work`

**Excluded:**

- `/Users/dsselmanovic/Finance`

### Manual Backup

```bash
# Backup critical files
DATE=$(date +%Y%m%d)
BACKUP_DIR=~/Desktop/sma_backup_$DATE

mkdir -p $BACKUP_DIR
cp -r ~/activi-dev-repos/super-mac-assistant/policy $BACKUP_DIR/
cp -r ~/activi-dev-repos/super-mac-assistant/logs/audit $BACKUP_DIR/
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### Recovery

**Restore from backup:**

```bash
# Extract backup
tar -xzf sma_backup_YYYYMMDD.tar.gz

# Restore policy
cp -r sma_backup_YYYYMMDD/policy ~/activi-dev-repos/super-mac-assistant/

# Restore audit logs (if needed)
cp -r sma_backup_YYYYMMDD/audit ~/activi-dev-repos/super-mac-assistant/logs/

# Restart daemon
launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

---

## 🚨 Incident Response

See [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) for detailed procedures.

**Quick Reference:**

### Suspicious Activity

```bash
# 1. PAUSE immediately
python3 src/security/kill_switch.py pause

# 2. Review audit log
python3 -c "from src.security.audit_log import AuditLogger; print(AuditLogger().export_report(hours=24))"

# 3. Check FinanceGuard
python3 -c "
from src.security.finance_guard import FinanceGuard
import yaml
with open('policy/policy.yaml') as f:
    policy = yaml.safe_load(f)
guard = FinanceGuard(policy['finance_guard'])
print(guard.get_status())
"

# 4. If OK → Resume, if NOT OK → Kill
python3 src/security/kill_switch.py resume  # or kill
```

### Daemon Crash

```bash
# 1. Check logs
tail -100 ~/activi-dev-repos/super-mac-assistant/logs/stderr.log

# 2. Check kill switch
python3 src/security/kill_switch.py status

# 3. Restart if safe
python3 src/security/kill_switch.py reset
launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

### Finance Access Attempt

```bash
# 1. Check FinanceGuard status
python3 -c "
from src.security.finance_guard import FinanceGuard
import yaml
with open('policy/policy.yaml') as f:
    policy = yaml.safe_load(f)
guard = FinanceGuard(policy['finance_guard'])
status = guard.check_system_security()
print(f'Secure: {status[\"secure\"]}')
print(f'Violations: {status[\"violations\"]}')
"

# 2. Emergency lockdown if needed
python3 -c "
from src.security.finance_guard import FinanceGuard
from src.security.audit_log import AuditLogger
import yaml
with open('policy/policy.yaml') as f:
    policy = yaml.safe_load(f)
guard = FinanceGuard(policy['finance_guard'])
result = guard.emergency_lockdown(AuditLogger())
print(result)
"
```

---

## 🔧 Maintenance

### Weekly Tasks

**1. Audit Log Review** (15 min)

```bash
# Generate weekly report
python3 -c "
from src.security.audit_log import AuditLogger
print(AuditLogger().export_report(hours=168))
" > weekly_audit_$(date +%Y%m%d).txt

# Review for:
# - Unusual patterns
# - Security events
# - Failed actions
```

**2. Log Rotation** (5 min)

```bash
# Compress old audit logs
cd ~/activi-dev-repos/super-mac-assistant/logs/audit
find . -name "audit_*.jsonl" -mtime +7 -exec gzip {} \;

# Delete compressed logs older than 90 days
find . -name "audit_*.jsonl.gz" -mtime +90 -delete
```

**3. Update Check** (5 min)

```bash
cd ~/activi-dev-repos/super-mac-assistant
git fetch
git status

# If updates available:
# git pull (after reviewing changes!)
# launchctl unload ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
# launchctl load ~/Library/LaunchAgents/com.step2job.supermacassistant.plist
```

### Monthly Tasks

**1. Security Review** (30 min)

- Review all security events
- Check FinanceGuard logs
- Verify backups working
- Test kill switch
- Review policy.yaml for needed changes

**2. Cleanup** (15 min)

```bash
# Clear old logs
find ~/activi-dev-repos/super-mac-assistant/logs -name "*.log" -mtime +30 -delete

# Check disk usage
du -sh ~/activi-dev-repos/super-mac-assistant/logs/
```

### Quarterly Tasks

**1. Penetration Test** (60 min)

- Try to bypass FinanceGuard
- Test prompt injection resistance
- Verify rate limits work
- Test all risk levels

**2. Dependency Updates** (30 min)

```bash
cd ~/activi-dev-repos/super-mac-assistant
source venv/bin/activate

# Check outdated packages
pip list --outdated

# Update (carefully!)
pip install --upgrade package_name

# Test thoroughly after updates
python3 tests/test_integration.py
```

---

## 📚 Related Documentation

- [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) - Detailed incident procedures
- [AUDIT_GUIDE.md](./AUDIT_GUIDE.md) - Audit log analysis
- [RUNBOOK.md](./RUNBOOK.md) - Common issues and fixes

---

**🔒 Operations Security: Trust but verify. Always.**

Made with ❤️ & 🔒 by Denis Selmanovic & Claude Sonnet 4.5
