"""
Executor - Role2 Deterministic Action Execution
NO LLM in execution path - purely policy-driven

Flow:
1. Receive action request
2. Validate via PolicyValidator
3. Handle confirmation if needed (Risk 2)
4. Execute deterministically
5. Audit log everything
"""

import os
import subprocess
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from .validator import PolicyValidator, ValidationResult, ValidationResponse


class ConfirmationManager:
    """
    Manages pending confirmations for Risk 2 actions
    Implements TTL-based challenge/response
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Args:
            ttl_seconds: Time-to-live for confirmations (from policy)
        """
        self.ttl_seconds = ttl_seconds
        self.pending = {}  # {challenge_id: {timestamp, action, args, ...}}

    def create_challenge(self, action_name: str, args: Dict,
                        validation_response: ValidationResponse) -> str:
        """
        Create confirmation challenge
        Returns: challenge_id
        """
        challenge_id = str(uuid.uuid4())

        self.pending[challenge_id] = {
            'timestamp': datetime.now(),
            'action': action_name,
            'args': args,
            'description': validation_response.action_metadata.get('description', ''),
            'risk_level': validation_response.risk_level
        }

        return challenge_id

    def confirm_challenge(self, challenge_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Confirm a challenge
        Returns: (is_valid, action_data)
        """
        if challenge_id not in self.pending:
            return (False, None)

        challenge = self.pending[challenge_id]

        # Check TTL
        age = (datetime.now() - challenge['timestamp']).total_seconds()
        if age > self.ttl_seconds:
            del self.pending[challenge_id]
            return (False, None)

        # Valid - return action data and remove challenge
        action_data = {
            'action': challenge['action'],
            'args': challenge['args']
        }

        del self.pending[challenge_id]
        return (True, action_data)

    def get_pending_challenge(self, challenge_id: str) -> Optional[Dict]:
        """Get challenge details without confirming"""
        return self.pending.get(challenge_id)

    def cleanup_expired(self):
        """Remove expired challenges"""
        now = datetime.now()
        expired = [
            cid for cid, challenge in self.pending.items()
            if (now - challenge['timestamp']).total_seconds() > self.ttl_seconds
        ]

        for cid in expired:
            del self.pending[cid]


class ActionExecutor:
    """
    Deterministic action executor
    NO LLM - only executes validated actions
    """

    def __init__(self, validator: PolicyValidator, audit_logger):
        """
        Args:
            validator: PolicyValidator instance
            audit_logger: AuditLogger instance (from src/security/audit_log.py)
        """
        self.validator = validator
        self.audit_logger = audit_logger

        # Get TTL from policy
        ttl = validator.policy.get('confirm_ttl', 300)
        self.confirmation_manager = ConfirmationManager(ttl_seconds=ttl)

    def execute(self, action_name: str, args: Dict[str, Any],
               trigger: str = "cli", agent: str = "executor") -> Dict:
        """
        Main execution entry point

        Args:
            action_name: Action to execute
            args: Action arguments
            trigger: How was action triggered (siri/cli/slack/auto)
            agent: Which agent requested (supervisor/assistant)

        Returns:
            Execution result dict
        """
        # 1. Validate action
        validation = self.validator.validate_action(action_name, args)

        # 2. Handle validation result
        if validation.result == ValidationResult.DENIED:
            # Log denied action
            self.audit_logger.log_security_event(
                event_type="blocked_action",
                description=f"Action '{action_name}' was denied",
                severity="warning",
                details={
                    "action": action_name,
                    "args": args,
                    "reason": validation.reason,
                    "violations": validation.violations
                }
            )

            return {
                'success': False,
                'error': validation.reason,
                'risk_level': validation.risk_level,
                'violations': validation.violations
            }

        elif validation.result == ValidationResult.PENDING_CONFIRMATION:
            # Create confirmation challenge
            challenge_id = self.confirmation_manager.create_challenge(
                action_name, args, validation
            )

            return {
                'success': False,
                'requires_confirmation': True,
                'challenge_id': challenge_id,
                'action': action_name,
                'description': validation.action_metadata.get('description', ''),
                'risk_level': validation.risk_level,
                'ttl_seconds': self.confirmation_manager.ttl_seconds,
                'message': f"⚠️  Confirmation required (Risk {validation.risk_level})"
            }

        elif validation.result == ValidationResult.ALLOWED:
            # Execute immediately (Risk 0 or Risk 1)
            return self._execute_action(
                action_name, args, validation, trigger, agent
            )

    def confirm_and_execute(self, challenge_id: str, trigger: str = "cli",
                          agent: str = "executor") -> Dict:
        """
        Confirm a pending action and execute it

        Args:
            challenge_id: Challenge ID from previous execute() call
            trigger: How was confirmation triggered
            agent: Which agent confirmed

        Returns:
            Execution result
        """
        # Validate challenge
        is_valid, action_data = self.confirmation_manager.confirm_challenge(challenge_id)

        if not is_valid:
            return {
                'success': False,
                'error': 'Invalid or expired challenge ID'
            }

        action_name = action_data['action']
        args = action_data['args']

        # Re-validate (policy might have changed)
        validation = self.validator.validate_action(action_name, args)

        if validation.result != ValidationResult.ALLOWED:
            # Should not happen, but be safe
            if validation.result == ValidationResult.PENDING_CONFIRMATION:
                validation.result = ValidationResult.ALLOWED  # User confirmed

        # Execute
        return self._execute_action(
            action_name, args, validation, trigger, agent, user_confirmed=True
        )

    def _execute_action(self, action_name: str, args: Dict,
                       validation: ValidationResponse, trigger: str,
                       agent: str, user_confirmed: bool = False) -> Dict:
        """
        Actually execute the action (deterministic implementations)
        """
        try:
            # Route to appropriate handler
            if action_name == 'status_overview':
                result = self._action_status_overview(args)

            elif action_name == 'list_tasks':
                result = self._action_list_tasks(args)

            elif action_name == 'get_task_details':
                result = self._action_get_task_details(args)

            elif action_name == 'check_backend_health':
                result = self._action_check_backend_health(args)

            elif action_name == 'get_agent_mode':
                result = self._action_get_agent_mode(args)

            elif action_name == 'tail_log':
                result = self._action_tail_log(args)

            elif action_name == 'take_screenshot':
                result = self._action_take_screenshot(args)

            elif action_name == 'open_app':
                result = self._action_open_app(args)

            elif action_name == 'open_vscode_project':
                result = self._action_open_vscode_project(args)

            elif action_name == 'create_task':
                result = self._action_create_task(args)

            elif action_name == 'send_chat_message':
                result = self._action_send_chat_message(args)

            elif action_name == 'send_slack_notification':
                result = self._action_send_slack_notification(args)

            elif action_name == 'create_github_issue':
                result = self._action_create_github_issue(args)

            elif action_name == 'git_commit':
                result = self._action_git_commit(args)

            elif action_name == 'git_push':
                result = self._action_git_push(args)

            elif action_name == 'restart_service':
                result = self._action_restart_service(args)

            elif action_name == 'sleep_mac':
                result = self._action_sleep_mac(args)

            elif action_name == 'backup_now':
                result = self._action_backup_now(args)

            else:
                result = {
                    'success': False,
                    'error': f'Action {action_name} not implemented'
                }

            # Record execution for rate limiting
            self.validator.record_execution(action_name, result.get('success', False))

            # Audit log
            self.audit_logger.log_action(
                action=action_name,
                agent=agent,
                trigger=trigger,
                params=args,
                result=result,
                risk_level=f"risk_{validation.risk_level}",
                user_confirmed=user_confirmed
            )

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }

            # Log error
            self.audit_logger.log_action(
                action=action_name,
                agent=agent,
                trigger=trigger,
                params=args,
                result=error_result,
                risk_level=f"risk_{validation.risk_level}",
                user_confirmed=user_confirmed
            )

            return error_result

    # ==========================================================================
    # ACTION IMPLEMENTATIONS (Deterministic)
    # ==========================================================================

    def _action_status_overview(self, args: Dict) -> Dict:
        """Get system status overview"""
        # Check backend health
        backend_status = self._action_check_backend_health({})

        # Get agent mode
        agent_mode = self._action_get_agent_mode({})

        # Get recent logs summary
        logs_path = os.path.expanduser(
            "~/activi-dev-repos/super-mac-assistant/logs/audit"
        )

        log_count = 0
        if os.path.exists(logs_path):
            log_count = len(list(Path(logs_path).glob("*.jsonl")))

        return {
            'success': True,
            'backend': backend_status.get('status', 'unknown'),
            'agent_mode': agent_mode.get('mode', 'unknown'),
            'audit_log_files': log_count,
            'timestamp': datetime.now().isoformat()
        }

    def _action_list_tasks(self, args: Dict) -> Dict:
        """List tasks from backend"""
        # Import backend client
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            status_filter = args.get('status', 'all')
            # list_tasks returns Dict with 'data' key
            result = client.list_tasks(status=status_filter if status_filter != 'all' else None)

            tasks = result.get('data', []) if isinstance(result, dict) else result

            return {
                'success': True,
                'tasks': tasks,
                'count': len(tasks) if tasks else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_get_task_details(self, args: Dict) -> Dict:
        """Get task details"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            task_id = args['task_id']
            # Use get_task() method (exists in backend_client.py)
            result = client.get_task(task_id)

            # Extract task data
            task = result.get('data') if isinstance(result, dict) and 'data' in result else result

            return {
                'success': True,
                'task': task
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_check_backend_health(self, args: Dict) -> Dict:
        """Check backend health"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            # Use connect() method which checks /health endpoint
            is_connected = client.connect()

            if is_connected:
                return {
                    'success': True,
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'unreachable',
                    'error': 'Backend not reachable'
                }
        except Exception as e:
            return {
                'success': False,
                'status': 'unreachable',
                'error': str(e)
            }

    def _action_get_agent_mode(self, args: Dict) -> Dict:
        """Get current agent mode"""
        # TODO: Implement agent mode detection
        return {
            'success': True,
            'mode': 'dual',  # supervisor + assistant
            'available': ['supervisor', 'assistant']
        }

    def _action_tail_log(self, args: Dict) -> Dict:
        """Show last N lines from log"""
        log_type = args.get('log_type', 'audit')
        lines = args.get('lines', 50)

        logs_dir = os.path.expanduser(
            "~/activi-dev-repos/super-mac-assistant/logs"
        )

        if log_type == 'audit':
            log_path = Path(logs_dir) / 'audit' / f'audit_{datetime.now().strftime("%Y%m%d")}.jsonl'
        else:
            log_path = Path(logs_dir) / f'{log_type}.log'

        if not log_path.exists():
            return {
                'success': False,
                'error': f'Log file not found: {log_path}'
            }

        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), str(log_path)],
                capture_output=True,
                text=True
            )

            return {
                'success': True,
                'lines': result.stdout,
                'log_file': str(log_path)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_take_screenshot(self, args: Dict) -> Dict:
        """Take a screenshot"""
        desktop = os.path.expanduser('~/Desktop')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshot_{timestamp}.png'
        filepath = os.path.join(desktop, filename)

        try:
            subprocess.run(
                ['screencapture', '-x', filepath],
                check=True
            )

            return {
                'success': True,
                'filepath': filepath,
                'message': f'Screenshot saved to {filepath}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_open_app(self, args: Dict) -> Dict:
        """Open an application"""
        app_name = args['app_name']

        try:
            subprocess.run(
                ['open', '-a', app_name],
                check=True
            )

            return {
                'success': True,
                'message': f'Opened {app_name}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_open_vscode_project(self, args: Dict) -> Dict:
        """Open VS Code with project"""
        project = args['project']

        # Map project names to paths
        repos_root = os.path.expanduser('~/activi-dev-repos')
        project_path = os.path.join(repos_root, project)

        if not os.path.exists(project_path):
            return {
                'success': False,
                'error': f'Project not found: {project_path}'
            }

        try:
            subprocess.run(
                ['open', '-a', 'Visual Studio Code', project_path],
                check=True
            )

            return {
                'success': True,
                'message': f'Opened {project} in VS Code'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_create_task(self, args: Dict) -> Dict:
        """Create task in backend"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            task = client.create_task(
                title=args['title'],
                description=args.get('description', ''),
                priority=args.get('priority', 'medium'),
                assignee=args.get('assignee', 'cloud_assistant')
            )

            return {
                'success': True,
                'task': task,
                'message': f"Task created: {task.get('id')}"
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_send_chat_message(self, args: Dict) -> Dict:
        """Send message to AI agent"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            response = client.send_chat_message(
                message=args['message'],
                agent_name=args['agent']
            )

            return {
                'success': True,
                'response': response.get('response', ''),
                'agent': args['agent']
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_send_slack_notification(self, args: Dict) -> Dict:
        """Send Slack notification"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            result = client.send_slack_notification(
                message=args['message']
            )

            return {
                'success': True,
                'message': 'Slack notification sent',
                'timestamp': result.get('ts')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_create_github_issue(self, args: Dict) -> Dict:
        """Create GitHub issue"""
        try:
            from src.api.backend_client import BackendAPIClient
            client = BackendAPIClient()

            issue = client.github_create_issue(
                repo=args['repo'],
                title=args['title'],
                body=args.get('body', ''),
                labels=args.get('labels', [])
            )

            return {
                'success': True,
                'issue': issue,
                'url': issue.get('html_url'),
                'number': issue.get('number')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_git_commit(self, args: Dict) -> Dict:
        """Create git commit"""
        repo_path = os.path.expanduser(args['repo_path'])
        message = args['message']

        try:
            # git add -A
            subprocess.run(
                ['git', '-C', repo_path, 'add', '-A'],
                check=True,
                capture_output=True
            )

            # git commit
            result = subprocess.run(
                ['git', '-C', repo_path, 'commit', '-m', message],
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ['git', '-C', repo_path, 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True
            )

            commit_hash = hash_result.stdout.strip()

            return {
                'success': True,
                'commit_hash': commit_hash,
                'message': result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr if e.stderr else str(e)
            }

    def _action_git_push(self, args: Dict) -> Dict:
        """Push to git remote"""
        repo_path = os.path.expanduser(args['repo_path'])
        branch = args.get('branch')

        try:
            cmd = ['git', '-C', repo_path, 'push']
            if branch:
                cmd.extend(['origin', branch])

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            return {
                'success': True,
                'message': result.stdout or result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr if e.stderr else str(e)
            }

    def _action_restart_service(self, args: Dict) -> Dict:
        """Restart a service"""
        service = args['service']

        # Map service names to restart commands
        if service == 'backend':
            # TODO: Implement backend restart
            return {
                'success': False,
                'error': 'Backend restart not yet implemented'
            }
        else:
            return {
                'success': False,
                'error': f'Unknown service: {service}'
            }

    def _action_sleep_mac(self, args: Dict) -> Dict:
        """Put Mac to sleep"""
        try:
            subprocess.run(
                ['pmset', 'sleepnow'],
                check=True
            )

            return {
                'success': True,
                'message': 'Mac going to sleep'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_backup_now(self, args: Dict) -> Dict:
        """Trigger Time Machine backup"""
        try:
            result = subprocess.run(
                ['tmutil', 'startbackup'],
                capture_output=True,
                text=True
            )

            return {
                'success': True,
                'message': 'Time Machine backup started',
                'output': result.stdout
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Example usage
if __name__ == "__main__":
    # Import audit logger
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from src.security.audit_log import AuditLogger

    # Create instances
    validator = PolicyValidator()
    audit_logger = AuditLogger()
    executor = ActionExecutor(validator, audit_logger)

    print("=" * 60)
    print("EXECUTOR TEST")
    print("=" * 60)

    # Test 1: Low-risk action (execute immediately)
    print("\n1. Testing low-risk action (status_overview):")
    result = executor.execute('status_overview', {}, trigger='cli', agent='test')
    print(f"   Success: {result.get('success')}")
    print(f"   Backend: {result.get('backend')}")

    # Test 2: High-risk action (require confirmation)
    print("\n2. Testing high-risk action (git_push):")
    result = executor.execute('git_push', {
        'repo_path': '~/activi-dev-repos/super-mac-assistant'
    }, trigger='cli', agent='test')
    print(f"   Success: {result.get('success')}")
    print(f"   Requires confirmation: {result.get('requires_confirmation')}")
    print(f"   Challenge ID: {result.get('challenge_id')}")

    if result.get('requires_confirmation'):
        challenge_id = result['challenge_id']

        # Simulate user confirmation
        print("\n   Simulating user confirmation...")
        confirm_result = executor.confirm_and_execute(
            challenge_id, trigger='cli', agent='test'
        )
        print(f"   Confirmed execution success: {confirm_result.get('success')}")

    # Test 3: Blocked action
    print("\n3. Testing blocked action (run_shell_command):")
    result = executor.execute('run_shell_command', {
        'command': 'echo hello'
    }, trigger='cli', agent='test')
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")

    print("\n" + "=" * 60)
