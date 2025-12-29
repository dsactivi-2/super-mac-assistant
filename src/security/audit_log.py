"""
Audit Log System
Logs all actions for security review
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class AuditLogger:
    """
    Security audit logger
    Records ALL actions for later review
    """

    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            log_dir = os.path.expanduser("~/activi-dev-repos/super-mac-assistant/logs/audit")

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.current_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def log_action(self,
                   action: str,
                   agent: str,
                   trigger: str,
                   params: Dict,
                   result: Dict,
                   risk_level: str,
                   user_confirmed: bool = False):
        """
        Log an action

        Args:
            action: Action name
            agent: Which agent (supervisor/assistant)
            trigger: How was it triggered (siri/cli/slack/auto)
            params: Action parameters
            result: Execution result
            risk_level: low/medium/high/critical
            user_confirmed: Was user confirmation required/given
        """

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": agent,
            "trigger": trigger,
            "params": params,
            "result": {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "error": result.get("error")
            },
            "risk_level": risk_level,
            "user_confirmed": user_confirmed,
            "session_id": os.getpid()  # Process ID as session identifier
        }

        # Write to JSON Lines file
        with open(self.current_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_security_event(self,
                           event_type: str,
                           description: str,
                           severity: str = "info",
                           details: Optional[Dict] = None):
        """
        Log a security event (blocked action, suspicious input, etc.)

        Args:
            event_type: Type of event (blocked_action, prompt_injection, etc.)
            description: Human-readable description
            severity: info/warning/critical
            details: Additional details
        """

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "security_event",
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "details": details or {},
            "session_id": os.getpid()
        }

        with open(self.current_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_recent_logs(self, hours: int = 24) -> List[Dict]:
        """Get logs from last N hours"""
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)
        logs = []

        # Check today's log file
        if self.current_log_file.exists():
            with open(self.current_log_file, "r") as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        log_time = datetime.fromisoformat(log["timestamp"])
                        if log_time >= cutoff_time:
                            logs.append(log)
                    except:
                        continue

        # Check yesterday's log file if needed
        if hours > 12:
            yesterday_file = self.log_dir / f"audit_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}.jsonl"
            if yesterday_file.exists():
                with open(yesterday_file, "r") as f:
                    for line in f:
                        try:
                            log = json.loads(line)
                            log_time = datetime.fromisoformat(log["timestamp"])
                            if log_time >= cutoff_time:
                                logs.append(log)
                        except:
                            continue

        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)

    def get_stats(self, hours: int = 24) -> Dict:
        """Get statistics about recent activity"""
        logs = self.get_recent_logs(hours)

        stats = {
            "total_actions": len(logs),
            "by_risk_level": {},
            "by_agent": {},
            "by_trigger": {},
            "success_rate": 0,
            "security_events": 0
        }

        successful = 0

        for log in logs:
            # Count by risk level
            risk = log.get("risk_level", "unknown")
            stats["by_risk_level"][risk] = stats["by_risk_level"].get(risk, 0) + 1

            # Count by agent
            agent = log.get("agent", "unknown")
            stats["by_agent"][agent] = stats["by_agent"].get(agent, 0) + 1

            # Count by trigger
            trigger = log.get("trigger", "unknown")
            stats["by_trigger"][trigger] = stats["by_trigger"].get(trigger, 0) + 1

            # Count success
            if log.get("result", {}).get("success"):
                successful += 1

            # Count security events
            if log.get("type") == "security_event":
                stats["security_events"] += 1

        if len(logs) > 0:
            stats["success_rate"] = round((successful / len(logs)) * 100, 2)

        return stats

    def search_logs(self, query: str, hours: int = 24) -> List[Dict]:
        """Search logs by text query"""
        logs = self.get_recent_logs(hours)
        results = []

        query_lower = query.lower()

        for log in logs:
            log_str = json.dumps(log).lower()
            if query_lower in log_str:
                results.append(log)

        return results

    def export_report(self, hours: int = 24) -> str:
        """Export a human-readable report"""
        logs = self.get_recent_logs(hours)
        stats = self.get_stats(hours)

        report = []
        report.append("=" * 60)
        report.append("SUPER MAC ASSISTANT - AUDIT REPORT")
        report.append("=" * 60)
        report.append(f"Period: Last {hours} hours")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("STATISTICS")
        report.append("-" * 60)
        report.append(f"Total Actions: {stats['total_actions']}")
        report.append(f"Success Rate: {stats['success_rate']}%")
        report.append(f"Security Events: {stats['security_events']}")
        report.append("")

        report.append("By Risk Level:")
        for risk, count in stats["by_risk_level"].items():
            report.append(f"  {risk}: {count}")
        report.append("")

        report.append("By Agent:")
        for agent, count in stats["by_agent"].items():
            report.append(f"  {agent}: {count}")
        report.append("")

        report.append("By Trigger:")
        for trigger, count in stats["by_trigger"].items():
            report.append(f"  {trigger}: {count}")
        report.append("")

        report.append("RECENT ACTIONS")
        report.append("-" * 60)

        for log in logs[:20]:  # Show last 20
            timestamp = log.get("timestamp", "unknown")
            action = log.get("action", "unknown")
            agent = log.get("agent", "unknown")
            success = "✅" if log.get("result", {}).get("success") else "❌"

            report.append(f"{timestamp} | {success} | {agent} | {action}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    logger = AuditLogger()

    # Log a normal action
    logger.log_action(
        action="take_screenshot",
        agent="assistant",
        trigger="siri",
        params={},
        result={"success": True, "message": "Screenshot saved"},
        risk_level="low",
        user_confirmed=False
    )

    # Log a blocked action
    logger.log_security_event(
        event_type="blocked_action",
        description="Attempted to run shell command",
        severity="warning",
        details={"command": "rm -rf /", "reason": "CRITICAL risk level"}
    )

    # Get stats
    stats = logger.get_stats(hours=24)
    print(json.dumps(stats, indent=2))

    # Export report
    report = logger.export_report(hours=24)
    print(report)
