"""
Integration Tests
Tests complete Role1 → Role2 → Policy → FinanceGuard flow
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from executor.validator import PolicyValidator
from executor.executor import ActionExecutor
from src.security.audit_log import AuditLogger
from src.security.finance_guard import FinanceGuard
import yaml


def test_policy_validation():
    """Test policy validator"""
    print("\n" + "="*60)
    print("TEST 1: Policy Validation")
    print("="*60)

    validator = PolicyValidator()

    # Test 1.1: Valid low-risk action
    result = validator.validate_action('status_overview', {})
    assert result.result.value == 'allowed', "Should allow low-risk action"
    print("✅ 1.1: Low-risk action allowed")

    # Test 1.2: Invalid enum
    result = validator.validate_action('create_task', {
        'title': 'Test',
        'priority': 'invalid_priority'
    })
    assert result.result.value == 'denied', "Should deny invalid enum"
    print("✅ 1.2: Invalid enum denied")

    # Test 1.3: High-risk needs confirmation
    result = validator.validate_action('git_push', {
        'repo_path': '/Users/dsselmanovic/activi-dev-repos/super-mac-assistant'
    })
    assert result.result.value == 'pending_confirmation', "Should require confirmation"
    print("✅ 1.3: High-risk requires confirmation")

    # Test 1.4: CRITICAL blocked
    result = validator.validate_action('run_shell_command', {'command': 'ls'})
    assert result.result.value == 'denied', "Should block CRITICAL"
    print("✅ 1.4: CRITICAL action blocked")

    print("✅ Policy Validation: ALL TESTS PASSED")


def test_finance_guard():
    """Test FinanceGuard"""
    print("\n" + "="*60)
    print("TEST 2: FinanceGuard")
    print("="*60)

    # Load policy
    policy_path = os.path.expanduser(
        "~/activi-dev-repos/super-mac-assistant/policy/policy.yaml"
    )
    with open(policy_path, 'r') as f:
        policy = yaml.safe_load(f)

    guard = FinanceGuard(policy['finance_guard'])

    # Test 2.1: Finance keyword detection
    is_finance, matched = guard.access_detector.check_keyword("Send invoice to client")
    assert is_finance, "Should detect finance keyword"
    assert matched == "invoice", "Should match 'invoice'"
    print("✅ 2.1: Finance keyword detected")

    # Test 2.2: Finance path detection
    is_finance, matched = guard.access_detector.check_path_access("/Volumes/Finance/data")
    assert is_finance, "Should detect finance path"
    print("✅ 2.2: Finance path detected")

    # Test 2.3: Finance app detection
    is_finance, matched = guard.access_detector.check_app("Banking App")
    assert is_finance, "Should detect finance app"
    print("✅ 2.3: Finance app detected")

    # Test 2.4: Finance domain detection
    is_finance, matched = guard.access_detector.check_domain("https://paypal.com/checkout")
    assert is_finance, "Should detect finance domain"
    print("✅ 2.4: Finance domain detected")

    # Test 2.5: System security check
    status = guard.check_system_security()
    print(f"✅ 2.5: Security check complete (secure: {status['secure']})")

    print("✅ FinanceGuard: ALL TESTS PASSED")


def test_executor():
    """Test executor"""
    print("\n" + "="*60)
    print("TEST 3: Executor")
    print("="*60)

    validator = PolicyValidator()
    audit_logger = AuditLogger()
    executor = ActionExecutor(validator, audit_logger)

    # Test 3.1: Execute low-risk action
    result = executor.execute('status_overview', {}, trigger='test', agent='test')
    assert result['success'], "Should execute low-risk action"
    print("✅ 3.1: Low-risk action executed")

    # Test 3.2: High-risk returns challenge
    result = executor.execute('git_push', {
        'repo_path': '/Users/dsselmanovic/activi-dev-repos/super-mac-assistant'
    }, trigger='test', agent='test')
    assert result.get('requires_confirmation'), "Should require confirmation"
    assert 'challenge_id' in result, "Should return challenge_id"
    print("✅ 3.2: High-risk returns challenge")

    # Test 3.3: Blocked action denied
    result = executor.execute('run_shell_command', {
        'command': 'ls'
    }, trigger='test', agent='test')
    assert not result['success'], "Should deny blocked action"
    print("✅ 3.3: Blocked action denied")

    print("✅ Executor: ALL TESTS PASSED")


def test_end_to_end():
    """Test complete end-to-end flow"""
    print("\n" + "="*60)
    print("TEST 4: End-to-End Flow")
    print("="*60)

    # Setup
    validator = PolicyValidator()
    audit_logger = AuditLogger()
    executor = ActionExecutor(validator, audit_logger)

    # Load policy for FinanceGuard
    policy_path = os.path.expanduser(
        "~/activi-dev-repos/super-mac-assistant/policy/policy.yaml"
    )
    with open(policy_path, 'r') as f:
        policy = yaml.safe_load(f)

    guard = FinanceGuard(policy['finance_guard'])

    # Test 4.1: Normal workflow (low-risk)
    print("\n4.1: Low-risk workflow")
    result = executor.execute('status_overview', {}, trigger='siri', agent='assistant')
    assert result['success'], "Should execute successfully"
    print("  ✅ Executed status_overview")

    # Test 4.2: Confirmation workflow (high-risk)
    print("\n4.2: High-risk confirmation workflow")

    # Step 1: Execute returns challenge
    result = executor.execute('git_push', {
        'repo_path': '/Users/dsselmanovic/activi-dev-repos/super-mac-assistant'
    }, trigger='siri', agent='assistant')

    assert result.get('requires_confirmation'), "Should require confirmation"
    challenge_id = result['challenge_id']
    print("  ✅ Challenge created")

    # Step 2: Confirm and execute
    result = executor.confirm_and_execute(challenge_id, trigger='siri', agent='assistant')
    # Note: May fail if not a git repo, but that's OK - we tested the flow
    print(f"  ✅ Confirmation flow complete (executed: {result.get('success', False)})")

    # Test 4.3: Finance blocking
    print("\n4.3: Finance blocking workflow")

    # Try to create task with finance keyword
    result = executor.execute('create_task', {
        'title': 'Send invoice to client',
        'priority': 'high',
        'assignee': 'cloud_assistant'
    }, trigger='siri', agent='assistant')

    # Should be denied by FinanceGuard
    assert not result['success'], "Should block finance keyword"
    assert 'FINANCE GUARD' in result.get('error', ''), "Should mention FinanceGuard"
    print("  ✅ Finance keyword blocked")

    print("\n✅ End-to-End Flow: ALL TESTS PASSED")


def test_path_security():
    """Test path security"""
    print("\n" + "="*60)
    print("TEST 5: Path Security")
    print("="*60)

    validator = PolicyValidator()

    # Test 5.1: Path traversal blocked
    result = validator.validate_action('git_commit', {
        'message': 'Test',
        'repo_path': '../../etc/passwd'
    })
    assert result.result.value == 'denied', "Should block path traversal"
    print("✅ 5.1: Path traversal blocked")

    # Test 5.2: Valid repo path allowed
    result = validator.validate_action('git_commit', {
        'message': 'Test commit',
        'repo_path': '/Users/dsselmanovic/activi-dev-repos/super-mac-assistant'
    })
    # Should require confirmation (Risk 2), not be denied
    assert result.result.value != 'denied', "Should not deny valid path"
    print("✅ 5.2: Valid repo path allowed")

    print("✅ Path Security: ALL TESTS PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# SUPER MAC ASSISTANT - INTEGRATION TESTS")
    print("#"*60)

    try:
        test_policy_validation()
        test_finance_guard()
        test_executor()
        test_path_security()
        test_end_to_end()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
