"""
FinanceGuard - Multi-Layer Finance Data Protection

Layer 1: OS-Level Isolation
  - Finance data on encrypted DMG volume
  - Volume unmounted by default
  - Only manual mounting allowed (NO automation)

Layer 2: Policy Enforcement (via validator.py)
  - Block keywords (invoice, banking, etc.)
  - Block paths (/Volumes/Finance, ~/Banking, etc.)
  - Block apps (Banking, Lexoffice, etc.)
  - Block domains (paypal.com, stripe.com, etc.)

Layer 3: Runtime Detection
  - Check if Finance volume is mounted
  - Alert if suspicious activity detected
  - Log all finance-related access attempts
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class FinanceVolumeGuard:
    """
    OS-Level Finance Volume Protection
    Ensures Finance volume remains unmounted
    """

    def __init__(self, volume_name: str = "Finance"):
        """
        Args:
            volume_name: Name of the Finance volume
        """
        self.volume_name = volume_name
        self.mount_point = f"/Volumes/{volume_name}"

    def is_mounted(self) -> bool:
        """Check if Finance volume is mounted"""
        return os.path.exists(self.mount_point) and os.path.ismount(self.mount_point)

    def get_mount_status(self) -> Dict:
        """Get detailed mount status"""
        mounted = self.is_mounted()

        status = {
            'mounted': mounted,
            'volume_name': self.volume_name,
            'mount_point': self.mount_point,
            'timestamp': datetime.now().isoformat()
        }

        if mounted:
            # Get mount info
            try:
                result = subprocess.run(
                    ['mount'],
                    capture_output=True,
                    text=True
                )

                # Find Finance volume in mount output
                for line in result.stdout.split('\n'):
                    if self.mount_point in line:
                        status['mount_info'] = line.strip()
                        break

            except Exception as e:
                status['error'] = str(e)

        return status

    def force_unmount(self) -> Tuple[bool, str]:
        """
        EMERGENCY: Force unmount Finance volume
        Only used in security incidents

        Returns:
            (success, message)
        """
        if not self.is_mounted():
            return (True, "Volume not mounted")

        try:
            # Try graceful unmount first
            result = subprocess.run(
                ['diskutil', 'unmount', self.mount_point],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return (True, "Volume unmounted successfully")

            # If graceful failed, try force
            result = subprocess.run(
                ['diskutil', 'unmount', 'force', self.mount_point],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return (True, "Volume force unmounted")
            else:
                return (False, f"Unmount failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            return (False, "Unmount timeout - volume may be in use")
        except Exception as e:
            return (False, str(e))

    def create_encrypted_volume(self, size_mb: int = 1024,
                               password: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create encrypted DMG for Finance data
        (Manual operation - not automated)

        Args:
            size_mb: Size in megabytes
            password: Encryption password (will prompt if not provided)

        Returns:
            (success, message)
        """
        dmg_path = os.path.expanduser(f"~/Documents/{self.volume_name}.dmg")

        if os.path.exists(dmg_path):
            return (False, f"DMG already exists: {dmg_path}")

        try:
            cmd = [
                'hdiutil', 'create',
                '-size', f'{size_mb}m',
                '-fs', 'APFS',
                '-volname', self.volume_name,
                '-encryption', 'AES-256',
                dmg_path
            ]

            if password:
                cmd.extend(['-passphrase', password])
            else:
                # Will prompt user for password
                cmd.append('-stdinpass')

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return (True, f"Encrypted volume created: {dmg_path}")
            else:
                return (False, f"Creation failed: {result.stderr}")

        except Exception as e:
            return (False, str(e))


class FinanceAccessDetector:
    """
    Runtime detection of finance-related access
    Monitors and alerts on suspicious activity
    """

    def __init__(self, policy_guard_config: Dict):
        """
        Args:
            policy_guard_config: finance_guard section from policy.yaml
        """
        self.deny_paths = policy_guard_config.get('deny_paths', [])
        self.deny_keywords = policy_guard_config.get('deny_keywords', [])
        self.deny_apps = policy_guard_config.get('deny_apps', [])
        self.deny_domains = policy_guard_config.get('deny_domains', [])

        self.access_attempts = []  # Log of attempts

    def check_path_access(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if path accesses finance data

        Returns:
            (is_finance_access, matched_deny_path)
        """
        expanded_path = os.path.expanduser(path)

        for deny_path in self.deny_paths:
            deny_expanded = os.path.expanduser(deny_path)

            # Check if paths overlap
            if expanded_path.startswith(deny_expanded):
                self._log_attempt('path', path, deny_path)
                return (True, deny_path)

            if deny_expanded in expanded_path:
                self._log_attempt('path', path, deny_path)
                return (True, deny_path)

        return (False, None)

    def check_keyword(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if text contains finance keywords

        Returns:
            (contains_finance_keyword, matched_keyword)
        """
        text_lower = text.lower()

        for keyword in self.deny_keywords:
            if keyword.lower() in text_lower:
                self._log_attempt('keyword', text, keyword)
                return (True, keyword)

        return (False, None)

    def check_app(self, app_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if app is finance-related

        Returns:
            (is_finance_app, matched_deny_app)
        """
        app_lower = app_name.lower()

        for deny_app in self.deny_apps:
            if deny_app.lower() in app_lower:
                self._log_attempt('app', app_name, deny_app)
                return (True, deny_app)

        return (False, None)

    def check_domain(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL accesses finance domain

        Returns:
            (is_finance_domain, matched_deny_domain)
        """
        url_lower = url.lower()

        for deny_domain in self.deny_domains:
            if deny_domain.lower() in url_lower:
                self._log_attempt('domain', url, deny_domain)
                return (True, deny_domain)

        return (False, None)

    def _log_attempt(self, attempt_type: str, value: str, matched: str):
        """Log finance access attempt"""
        self.access_attempts.append({
            'timestamp': datetime.now().isoformat(),
            'type': attempt_type,
            'value': value,
            'matched': matched
        })

        # Keep only last 1000
        if len(self.access_attempts) > 1000:
            self.access_attempts = self.access_attempts[-1000:]

    def get_recent_attempts(self, minutes: int = 60) -> List[Dict]:
        """Get recent access attempts"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(minutes=minutes)

        return [
            attempt for attempt in self.access_attempts
            if datetime.fromisoformat(attempt['timestamp']) >= cutoff
        ]

    def get_stats(self) -> Dict:
        """Get access attempt statistics"""
        by_type = {}
        for attempt in self.access_attempts:
            attempt_type = attempt['type']
            by_type[attempt_type] = by_type.get(attempt_type, 0) + 1

        return {
            'total_attempts': len(self.access_attempts),
            'by_type': by_type,
            'recent_24h': len(self.get_recent_attempts(minutes=24*60))
        }


class FinanceGuard:
    """
    Complete Finance Protection System
    Combines OS-level + Policy + Runtime detection
    """

    def __init__(self, policy_guard_config: Dict, volume_name: str = "Finance"):
        """
        Args:
            policy_guard_config: finance_guard section from policy.yaml
            volume_name: Name of Finance volume
        """
        self.enabled = policy_guard_config.get('enabled', True)

        self.volume_guard = FinanceVolumeGuard(volume_name)
        self.access_detector = FinanceAccessDetector(policy_guard_config)

    def check_system_security(self) -> Dict:
        """
        Comprehensive security check

        Returns:
            {
                'secure': bool,
                'volume_mounted': bool,
                'recent_attempts': int,
                'violations': List[str]
            }
        """
        violations = []

        # Check if Finance volume is mounted (should NOT be)
        volume_status = self.volume_guard.get_mount_status()
        is_mounted = volume_status['mounted']

        if is_mounted:
            violations.append("Finance volume is mounted (security risk)")

        # Check recent access attempts
        recent_attempts = self.access_detector.get_recent_attempts(minutes=60)

        if len(recent_attempts) > 0:
            violations.append(f"{len(recent_attempts)} finance access attempts in last hour")

        return {
            'secure': len(violations) == 0,
            'volume_mounted': is_mounted,
            'recent_attempts': len(recent_attempts),
            'violations': violations,
            'timestamp': datetime.now().isoformat()
        }

    def emergency_lockdown(self, audit_logger) -> Dict:
        """
        EMERGENCY: Complete lockdown

        1. Unmount Finance volume (if mounted)
        2. Log security event
        3. Return status

        Returns:
            Lockdown result
        """
        results = []

        # 1. Unmount Finance volume
        if self.volume_guard.is_mounted():
            success, message = self.volume_guard.force_unmount()
            results.append({
                'action': 'unmount_finance_volume',
                'success': success,
                'message': message
            })
        else:
            results.append({
                'action': 'unmount_finance_volume',
                'success': True,
                'message': 'Volume was not mounted'
            })

        # 2. Log security event
        audit_logger.log_security_event(
            event_type="finance_guard_lockdown",
            description="Emergency lockdown activated",
            severity="critical",
            details={
                'results': results,
                'access_attempts': self.access_detector.get_stats()
            }
        )

        return {
            'success': True,
            'message': 'Emergency lockdown complete',
            'actions': results
        }

    def get_status(self) -> Dict:
        """Get complete FinanceGuard status"""
        return {
            'enabled': self.enabled,
            'volume': self.volume_guard.get_mount_status(),
            'access_attempts': self.access_detector.get_stats(),
            'security_check': self.check_system_security()
        }


# Example usage
if __name__ == "__main__":
    import sys
    import yaml

    # Load policy
    policy_path = os.path.expanduser(
        "~/activi-dev-repos/super-mac-assistant/policy/policy.yaml"
    )

    with open(policy_path, 'r') as f:
        policy = yaml.safe_load(f)

    finance_config = policy.get('finance_guard', {})

    print("=" * 60)
    print("FINANCE GUARD TEST")
    print("=" * 60)

    # Create FinanceGuard
    guard = FinanceGuard(finance_config)

    # Check status
    print("\n1. System Security Check:")
    status = guard.check_system_security()
    print(f"   Secure: {status['secure']}")
    print(f"   Volume mounted: {status['volume_mounted']}")
    print(f"   Recent attempts: {status['recent_attempts']}")
    if status['violations']:
        print(f"   Violations:")
        for v in status['violations']:
            print(f"     - {v}")

    # Test path detection
    print("\n2. Path Detection Test:")
    test_paths = [
        "/Users/dsselmanovic/Documents/Work/report.pdf",
        "/Volumes/Finance/invoices/2024.xlsx",
        "/Users/dsselmanovic/Finance/banking.csv"
    ]

    for path in test_paths:
        is_finance, matched = guard.access_detector.check_path_access(path)
        print(f"   {path}")
        print(f"     Finance: {is_finance}, Matched: {matched}")

    # Test keyword detection
    print("\n3. Keyword Detection Test:")
    test_texts = [
        "Please send me the report",
        "Create invoice for client ABC",
        "Check the banking transactions"
    ]

    for text in test_texts:
        is_finance, matched = guard.access_detector.check_keyword(text)
        print(f"   '{text}'")
        print(f"     Finance: {is_finance}, Matched: {matched}")

    # Get stats
    print("\n4. Access Attempt Statistics:")
    stats = guard.access_detector.get_stats()
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   By type: {stats['by_type']}")

    print("\n" + "=" * 60)
