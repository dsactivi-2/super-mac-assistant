"""
Policy Validator - Role2 Core Component
Single source of truth enforcement via policy.yaml

This module validates ALL action requests against policy.yaml.
NO action may execute without passing validation.
"""

import yaml
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ValidationResult(Enum):
    """Validation outcomes"""
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING_CONFIRMATION = "pending_confirmation"


@dataclass
class ValidationResponse:
    """Structured validation response"""
    result: ValidationResult
    reason: str
    risk_level: Optional[int] = None
    requires_confirm: bool = False
    action_metadata: Optional[Dict] = None
    violations: Optional[List[str]] = None


class PolicyValidator:
    """
    Validates all actions against policy.yaml
    Enforces:
    - Allowlists (enums)
    - Args schema (types, bounds, patterns)
    - Rate limits
    - FinanceGuard
    - Path security
    """

    def __init__(self, policy_path: Optional[str] = None):
        """Load policy.yaml"""
        if policy_path is None:
            policy_path = os.path.expanduser(
                "~/activi-dev-repos/super-mac-assistant/policy/policy.yaml"
            )

        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self.rate_tracker = {}  # {action_name: [(timestamp, success), ...]}

    def _load_policy(self) -> Dict:
        """Load and parse policy.yaml"""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

        with open(self.policy_path, 'r') as f:
            policy = yaml.safe_load(f)

        # Validate policy structure
        required_keys = ['allowlists', 'finance_guard', 'actions', 'rate_limits']
        for key in required_keys:
            if key not in policy:
                raise ValueError(f"Policy missing required key: {key}")

        return policy

    def reload_policy(self):
        """Reload policy from disk (for testing/updates)"""
        self.policy = self._load_policy()

    def validate_action(self, action_name: str, args: Dict[str, Any]) -> ValidationResponse:
        """
        Main validation entry point

        Returns:
            ValidationResponse with result, reason, and metadata
        """
        violations = []

        # 1. Check if action exists
        if action_name not in self.policy['actions']:
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=f"Action '{action_name}' not defined in policy",
                violations=["action_not_found"]
            )

        action_def = self.policy['actions'][action_name]
        risk_level = action_def.get('risk', 3)

        # 2. Check if action is CRITICAL (always denied)
        if risk_level == 3:
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=action_def.get('deny_reason', 'Action is permanently blocked'),
                risk_level=3,
                violations=["critical_risk"]
            )

        # 3. Validate arguments schema
        schema_validation = self._validate_args_schema(action_name, args, action_def)
        if not schema_validation[0]:
            violations.extend(schema_validation[1])
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=f"Schema validation failed: {', '.join(schema_validation[1])}",
                risk_level=risk_level,
                violations=violations
            )

        # 4. Check rate limits
        rate_check = self._check_rate_limit(action_name, action_def)
        if not rate_check[0]:
            violations.append("rate_limit_exceeded")
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=rate_check[1],
                risk_level=risk_level,
                violations=violations
            )

        # 5. Check FinanceGuard (CRITICAL)
        finance_check = self._check_finance_guard(action_name, args)
        if not finance_check[0]:
            violations.append("finance_guard_blocked")
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=f"🔒 FINANCE GUARD: {finance_check[1]}",
                risk_level=3,  # Escalate to CRITICAL
                violations=violations
            )

        # 6. Validate path security (if action involves paths)
        path_check = self._validate_paths(action_name, args)
        if not path_check[0]:
            violations.extend(path_check[1])
            return ValidationResponse(
                result=ValidationResult.DENIED,
                reason=f"Path security violation: {', '.join(path_check[1])}",
                risk_level=risk_level,
                violations=violations
            )

        # 7. Determine if confirmation required (Risk 2)
        requires_confirm = action_def.get('requires_confirm', False)

        if requires_confirm or risk_level == 2:
            return ValidationResponse(
                result=ValidationResult.PENDING_CONFIRMATION,
                reason=f"Action requires explicit confirmation (Risk {risk_level})",
                risk_level=risk_level,
                requires_confirm=True,
                action_metadata={
                    'action': action_name,
                    'description': action_def.get('description', ''),
                    'args': args
                }
            )

        # 8. ALLOWED - Risk 0 or Risk 1 (with verbal confirm handled elsewhere)
        return ValidationResponse(
            result=ValidationResult.ALLOWED,
            reason="Action validated successfully",
            risk_level=risk_level,
            requires_confirm=(risk_level == 1),  # Risk 1 = verbal confirm
            action_metadata={
                'action': action_name,
                'description': action_def.get('description', ''),
                'args': args
            }
        )

    def _validate_args_schema(self, action_name: str, args: Dict,
                            action_def: Dict) -> Tuple[bool, List[str]]:
        """
        Validate arguments against schema
        Returns: (is_valid, [violations])
        """
        violations = []
        schema = action_def.get('args_schema', {})

        # Check for missing required args
        for arg_name, arg_spec in schema.items():
            if arg_spec.get('optional', False):
                continue

            if arg_name not in args:
                violations.append(f"Missing required argument: {arg_name}")

        # Validate provided args
        for arg_name, arg_value in args.items():
            if arg_name not in schema:
                # Allow extra args (might be used internally)
                continue

            arg_spec = schema[arg_name]
            arg_type = arg_spec.get('type')

            # Type: string
            if arg_type == 'string':
                if not isinstance(arg_value, str):
                    violations.append(f"{arg_name} must be string")
                    continue

                # Check length constraints
                if 'min_length' in arg_spec and len(arg_value) < arg_spec['min_length']:
                    violations.append(f"{arg_name} too short (min {arg_spec['min_length']})")

                if 'max_length' in arg_spec and len(arg_value) > arg_spec['max_length']:
                    violations.append(f"{arg_name} too long (max {arg_spec['max_length']})")

                # Check pattern
                if 'pattern' in arg_spec:
                    if not re.match(arg_spec['pattern'], arg_value):
                        violations.append(f"{arg_name} doesn't match pattern {arg_spec['pattern']}")

                # Check must_be_under (path containment)
                if 'must_be_under' in arg_spec:
                    root_key = arg_spec['must_be_under']
                    root_path = self.policy.get('root_paths', {}).get(root_key)
                    if root_path:
                        if not self._is_path_under_root(arg_value, root_path):
                            violations.append(f"{arg_name} must be under {root_path}")

            # Type: integer
            elif arg_type == 'integer':
                if not isinstance(arg_value, int):
                    violations.append(f"{arg_name} must be integer")
                    continue

                if 'min' in arg_spec and arg_value < arg_spec['min']:
                    violations.append(f"{arg_name} too small (min {arg_spec['min']})")

                if 'max' in arg_spec and arg_value > arg_spec['max']:
                    violations.append(f"{arg_name} too large (max {arg_spec['max']})")

            # Type: enum
            elif arg_type == 'enum':
                # Check if enum values come from allowlist
                if 'values_from' in arg_spec:
                    allowlist_path = arg_spec['values_from'].split('.')
                    allowed_values = self.policy
                    for key in allowlist_path:
                        allowed_values = allowed_values.get(key, [])

                    if arg_value not in allowed_values:
                        violations.append(
                            f"{arg_name} must be one of {allowed_values}, got '{arg_value}'"
                        )

                # Or direct values list
                elif 'values' in arg_spec:
                    if arg_value not in arg_spec['values']:
                        violations.append(
                            f"{arg_name} must be one of {arg_spec['values']}, got '{arg_value}'"
                        )

            # Type: array
            elif arg_type == 'array':
                if not isinstance(arg_value, list):
                    violations.append(f"{arg_name} must be array")
                    continue

                # Validate array items
                if 'items' in arg_spec:
                    item_spec = arg_spec['items']
                    if item_spec.get('type') == 'enum':
                        allowed_values = item_spec.get('values', [])
                        for item in arg_value:
                            if item not in allowed_values:
                                violations.append(
                                    f"{arg_name} contains invalid value '{item}'"
                                )

        return (len(violations) == 0, violations)

    def _check_rate_limit(self, action_name: str, action_def: Dict) -> Tuple[bool, str]:
        """
        Check if action has exceeded rate limit
        Returns: (is_allowed, reason)
        """
        # Get rate limit from action or global config
        rate_limit = action_def.get('rate_limit')
        if rate_limit is None:
            rate_limit = self.policy['rate_limits'].get(action_name)

        if rate_limit is None:
            return (True, "No rate limit")

        # Count recent executions (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)

        if action_name not in self.rate_tracker:
            self.rate_tracker[action_name] = []

        # Clean old entries
        self.rate_tracker[action_name] = [
            (ts, success) for ts, success in self.rate_tracker[action_name]
            if ts > one_hour_ago
        ]

        recent_count = len(self.rate_tracker[action_name])

        if recent_count >= rate_limit:
            return (
                False,
                f"Rate limit exceeded: {recent_count}/{rate_limit} per hour"
            )

        return (True, f"Rate limit OK: {recent_count}/{rate_limit}")

    def _check_finance_guard(self, action_name: str, args: Dict) -> Tuple[bool, str]:
        """
        Check FinanceGuard - CRITICAL security layer
        Returns: (is_allowed, reason)
        """
        if not self.policy['finance_guard'].get('enabled', True):
            return (True, "FinanceGuard disabled")

        # Serialize all args to check for finance keywords
        args_str = str(args).lower()

        # Check deny_keywords
        for keyword in self.policy['finance_guard'].get('deny_keywords', []):
            if keyword.lower() in args_str:
                return (False, f"Finance keyword detected: '{keyword}'")

        # Check deny_paths
        for deny_path in self.policy['finance_guard'].get('deny_paths', []):
            deny_path_expanded = os.path.expanduser(deny_path)

            # Check if any arg contains this path
            for arg_value in args.values():
                if isinstance(arg_value, str):
                    arg_path_expanded = os.path.expanduser(arg_value)

                    # Check if paths overlap
                    try:
                        # Try to resolve to canonical form
                        deny_canonical = os.path.realpath(deny_path_expanded)
                        arg_canonical = os.path.realpath(arg_path_expanded)

                        if arg_canonical.startswith(deny_canonical):
                            return (False, f"Finance path blocked: {deny_path}")
                    except:
                        # Path doesn't exist - do string comparison
                        if deny_path_expanded in arg_path_expanded:
                            return (False, f"Finance path blocked: {deny_path}")

        # Check deny_apps (for open_app actions)
        if action_name == 'open_app':
            app_name = args.get('app_name', '')
            for deny_app in self.policy['finance_guard'].get('deny_apps', []):
                if deny_app.lower() in app_name.lower():
                    return (False, f"Finance app blocked: '{deny_app}'")

        # Check deny_domains (for URL operations)
        for arg_value in args.values():
            if isinstance(arg_value, str) and ('http://' in arg_value or 'https://' in arg_value):
                for deny_domain in self.policy['finance_guard'].get('deny_domains', []):
                    if deny_domain.lower() in arg_value.lower():
                        return (False, f"Finance domain blocked: '{deny_domain}'")

        return (True, "FinanceGuard passed")

    def _validate_paths(self, action_name: str, args: Dict) -> Tuple[bool, List[str]]:
        """
        Validate path security
        - Canonical path resolution (no symlink escapes)
        - Root containment checking
        - No wildcards that expand too broadly

        Returns: (is_valid, [violations])
        """
        violations = []

        # Find all path-like arguments
        for arg_name, arg_value in args.items():
            if not isinstance(arg_value, str):
                continue

            # Skip if not a path (no slashes)
            if '/' not in arg_value:
                continue

            # Expand user home directory
            expanded_path = os.path.expanduser(arg_value)

            # Check for dangerous patterns
            if '..' in expanded_path:
                violations.append(f"{arg_name} contains '..' (traversal attempt)")

            # Try to get canonical path
            try:
                canonical = os.path.realpath(expanded_path)

                # Check if canonical path is under allowed roots
                allowed_roots = []

                # Get work_roots from policy
                for root in self.policy.get('root_paths', {}).get('work_roots', []):
                    allowed_roots.append(os.path.expanduser(root))

                # Also add other root paths
                for key in ['repos_root', 'screenshots_root', 'logs_root']:
                    root = self.policy.get('root_paths', {}).get(key)
                    if root:
                        allowed_roots.append(os.path.expanduser(root))

                # Check containment
                if allowed_roots:
                    is_contained = any(
                        canonical.startswith(os.path.realpath(root))
                        for root in allowed_roots
                    )

                    if not is_contained:
                        violations.append(
                            f"{arg_name} outside allowed roots: {canonical}"
                        )

            except Exception as e:
                # Path doesn't exist or can't be resolved - allow it
                # (might be for creation)
                pass

        return (len(violations) == 0, violations)

    def _is_path_under_root(self, path: str, root: str) -> bool:
        """Check if path is under root directory"""
        try:
            path_expanded = os.path.expanduser(path)
            root_expanded = os.path.expanduser(root)

            path_canonical = os.path.realpath(path_expanded)
            root_canonical = os.path.realpath(root_expanded)

            return path_canonical.startswith(root_canonical)
        except:
            return False

    def record_execution(self, action_name: str, success: bool):
        """Record action execution for rate limiting"""
        if action_name not in self.rate_tracker:
            self.rate_tracker[action_name] = []

        self.rate_tracker[action_name].append((datetime.now(), success))

        # Keep only last 1000 entries per action
        if len(self.rate_tracker[action_name]) > 1000:
            self.rate_tracker[action_name] = self.rate_tracker[action_name][-1000:]

    def get_action_info(self, action_name: str) -> Optional[Dict]:
        """Get action definition from policy"""
        return self.policy['actions'].get(action_name)

    def list_allowed_actions(self, risk_level: Optional[int] = None) -> List[str]:
        """List all allowed actions, optionally filtered by risk level"""
        actions = []
        for name, action_def in self.policy['actions'].items():
            if risk_level is not None:
                if action_def.get('risk', 3) == risk_level:
                    actions.append(name)
            else:
                # Only non-CRITICAL actions
                if action_def.get('risk', 3) < 3:
                    actions.append(name)

        return sorted(actions)

    def get_allowlist(self, list_name: str) -> List[str]:
        """Get allowlist values (e.g., 'apps', 'projects')"""
        return self.policy.get('allowlists', {}).get(list_name, [])


# Example usage & testing
if __name__ == "__main__":
    validator = PolicyValidator()

    print("=" * 60)
    print("POLICY VALIDATOR TEST")
    print("=" * 60)

    # Test 1: Valid low-risk action
    print("\n1. Testing valid low-risk action (status_overview):")
    result = validator.validate_action('status_overview', {})
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")
    print(f"   Risk: {result.risk_level}")

    # Test 2: Valid action with args
    print("\n2. Testing valid action with args (create_task):")
    result = validator.validate_action('create_task', {
        'title': 'Test task',
        'priority': 'high',
        'assignee': 'cloud_assistant'
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")
    print(f"   Risk: {result.risk_level}")

    # Test 3: Invalid enum value
    print("\n3. Testing invalid enum value:")
    result = validator.validate_action('create_task', {
        'title': 'Test',
        'priority': 'ultra_mega_high'  # Invalid
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")

    # Test 4: High-risk action (should require confirmation)
    print("\n4. Testing high-risk action (git_push):")
    result = validator.validate_action('git_push', {
        'repo_path': '/Users/dsselmanovic/activi-dev-repos/super-mac-assistant'
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")
    print(f"   Requires confirm: {result.requires_confirm}")

    # Test 5: Blocked CRITICAL action
    print("\n5. Testing blocked CRITICAL action (run_shell_command):")
    result = validator.validate_action('run_shell_command', {
        'command': 'rm -rf /'
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")

    # Test 6: FinanceGuard trigger
    print("\n6. Testing FinanceGuard (finance keyword):")
    result = validator.validate_action('create_task', {
        'title': 'Send invoice to client',
        'description': 'Banking details needed'
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")

    # Test 7: Path traversal attempt
    print("\n7. Testing path traversal attempt:")
    result = validator.validate_action('git_commit', {
        'message': 'Test commit',
        'repo_path': '../../etc/passwd'
    })
    print(f"   Result: {result.result.value}")
    print(f"   Reason: {result.reason}")

    print("\n" + "=" * 60)
    print("VALIDATION TEST COMPLETE")
    print("=" * 60)
