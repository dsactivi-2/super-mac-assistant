# 🛠️ Contributing to Super Mac Assistant

**How to safely add new features and actions**

> ⚠️ **CRITICAL**: Every new action is a potential security risk. Follow this guide exactly.

---

## 🎯 Before You Start

### 1. Read Required Documentation

- [ ] [SECURITY.md](./SECURITY.md) - Understand security model
- [ ] [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - Understand system design
- [ ] [docs/POLICY_GUIDE.md](./docs/POLICY_GUIDE.md) - Understand policy.yaml

### 2. Ask These Questions

1. **Is this action absolutely necessary?**
   - Principle: Minimize attack surface
   - Prefer read-only operations

2. **What's the worst that could happen?**
   - Data loss?
   - Privacy breach?
   - System compromise?

3. **Can this be exploited via prompt injection?**
   - Remember: Role1 uses LLM (can be tricked)
   - Role2 must validate everything

4. **Does it touch finance/banking/sensitive data?**
   - If yes → ⛔ **STOP** → Discuss with security team

---

## 📋 Process: Adding a New Action

### Step 1: Define in Policy (**REQUIRED**)

**File**: `policy/policy.yaml`

```yaml
actions:
  your_new_action:
    risk: 1 # 0=low, 1=medium, 2=high, 3=blocked
    description: "Clear description of what it does"
    args_schema:
      arg_name:
        type: enum # Use enums, NOT free strings!
        values_from: allowlists.your_list
      another_arg:
        type: string
        min_length: 1
        max_length: 100
        pattern: "^[a-zA-Z0-9_-]+$" # Regex validation
    rate_limit: 20 # Per hour
    requires_confirm: false # true for Risk 2
    returns: "What this action returns"
```

**Risk Level Guidelines:**

- **Risk 0 (LOW)**: Read-only, no side effects
  - Examples: get_status, list_tasks, check_health
  - Execute immediately

- **Risk 1 (MEDIUM)**: Can disrupt work but no data loss
  - Examples: open_app, take_screenshot, send_message
  - Verbal confirmation in voice UI

- **Risk 2 (HIGH)**: Can modify data or system state
  - Examples: git_commit, git_push, restart_service
  - Explicit confirmation required (challenge/response)

- **Risk 3 (CRITICAL)**: Too dangerous, always blocked
  - Examples: run_shell_command, delete_files, sudo
  - **NEVER** set to Risk 0-2

### Step 2: Add to Allowlists (**If Needed**)

If your action targets specific apps/projects/etc., add them to allowlists:

```yaml
allowlists:
  your_list:
    - "allowed_value_1"
    - "allowed_value_2"
    # NO wildcards, NO patterns, ONLY explicit values
```

**Rules:**

- ✅ Explicit strings only
- ❌ NO wildcards (`*`, `.*`)
- ❌ NO path patterns (`**/*.txt`)
- ❌ NO regex in allowlists

### Step 3: Implement in Executor

**File**: `executor/executor.py`

Add your implementation in `ActionExecutor._execute_action()`:

```python
def _execute_action(self, action_name: str, args: Dict, ...):
    # ... existing code ...

    elif action_name == 'your_new_action':
        result = self._action_your_new_action(args)

    # ... rest of code ...

def _action_your_new_action(self, args: Dict) -> Dict:
    """
    Your action implementation

    RULES:
    - Must be DETERMINISTIC (no randomness, no LLM calls)
    - Must validate all inputs (already done by validator)
    - Must return Dict with 'success' and 'message' or 'error'
    - Must handle exceptions gracefully
    """
    try:
        # Get validated args
        arg_value = args['arg_name']

        # Do the work (deterministically!)
        # ...

        return {
            'success': True,
            'message': 'Action completed successfully',
            'result_data': '...'  # Optional
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

**Common Pitfalls:**

- ❌ **DON'T** call LLM in executor
- ❌ **DON'T** use free-form string arguments
- ❌ **DON'T** access paths outside allowed roots
- ❌ **DON'T** execute shell commands with user input
- ✅ **DO** validate everything (done by validator)
- ✅ **DO** return consistent Dict format
- ✅ **DO** handle errors gracefully

### Step 4: Add Tests

**File**: `tests/test_your_action.py`

```python
def test_your_action():
    """Test your new action"""
    validator = PolicyValidator()
    audit_logger = AuditLogger()
    executor = ActionExecutor(validator, audit_logger)

    # Test 1: Valid input
    result = executor.execute('your_new_action', {
        'arg_name': 'valid_value'
    }, trigger='test', agent='test')

    assert result['success'], "Should succeed with valid input"

    # Test 2: Invalid input (should be caught by validator)
    result = executor.execute('your_new_action', {
        'arg_name': 'invalid_value'
    }, trigger='test', agent='test')

    assert not result['success'], "Should fail with invalid input"

    # Test 3: Edge cases
    # ...
```

**Required Tests:**

1. ✅ Valid input succeeds
2. ✅ Invalid input denied
3. ✅ Edge cases handled
4. ✅ Error handling works
5. ✅ Rate limiting enforced
6. ✅ FinanceGuard blocks if applicable

### Step 5: Update Documentation

1. **README.md**: Add to action list with example
2. **SIRI_SHORTCUTS.md**: Add voice command example (if applicable)
3. **docs/POLICY_GUIDE.md**: Document args_schema

---

## 🔐 Security Checklist

Before submitting your change, verify:

### Input Validation

- [ ] All inputs validated against schema (types, bounds, enums)
- [ ] No free-form strings that could be code/commands
- [ ] Paths validated (canonical, containment, no traversal)
- [ ] No user input directly in shell commands

### Risk Assessment

- [ ] Risk level correctly assigned
- [ ] Rate limit set appropriately
- [ ] Confirmation required if Risk 2
- [ ] Not Risk 3 (if so, remove it!)

### FinanceGuard

- [ ] Does NOT access finance paths
- [ ] Does NOT use finance keywords
- [ ] Does NOT open finance apps
- [ ] Does NOT access finance domains
- [ ] If it might → add to deny lists

### Implementation

- [ ] Deterministic (no LLM, no randomness in Role2)
- [ ] Error handling present
- [ ] Returns consistent format
- [ ] No secrets in code (use env vars)
- [ ] Audit logged automatically (done by executor)

### Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done
- [ ] Edge cases covered
- [ ] Error cases handled

---

## 🚫 Common Mistakes

### ❌ Adding Free-Form String Arguments

**BAD:**

```yaml
create_file:
  args_schema:
    path:
      type: string # User can pass ANYTHING!
```

**GOOD:**

```yaml
create_file:
  args_schema:
    filename:
      type: string
      pattern: "^[a-zA-Z0-9_-]+\\.txt$" # Limited pattern
      max_length: 100
    directory:
      type: enum
      values_from: allowlists.allowed_dirs # From allowlist!
```

### ❌ Shell Command Injection

**BAD:**

```python
# NEVER DO THIS!
subprocess.run(f"open {user_input}", shell=True)
```

**GOOD:**

```python
# Use list form, validate input first
subprocess.run(['open', validated_path], shell=False)
```

### ❌ Missing Error Handling

**BAD:**

```python
def _action_something(self, args):
    result = do_something(args['value'])  # Can throw!
    return {'success': True}
```

**GOOD:**

```python
def _action_something(self, args):
    try:
        result = do_something(args['value'])
        return {'success': True, 'result': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### ❌ Calling LLM in Executor (Role2)

**BAD:**

```python
# In executor.py - WRONG!
def _action_analyze(self, args):
    response = anthropic_client.messages.create(...)  # NO!
```

**GOOD:**

```python
# In researcher.py - CORRECT
def analyze_with_llm(self, text):
    response = self.client.messages.create(...)
    # Then pass structured request to executor
```

---

## 📝 Pull Request Template

```markdown
## Description

[Clear description of what this adds/changes]

## Type of Change

- [ ] New action
- [ ] Bug fix
- [ ] Documentation
- [ ] Security improvement

## Risk Assessment

- Risk Level: [0/1/2/3]
- Could this lead to data loss? [Yes/No - explain]
- Could this be exploited via prompt injection? [Yes/No - explain]
- Does this touch sensitive data? [Yes/No - explain]

## Checklist

- [ ] Added to policy.yaml with correct risk level
- [ ] Implemented in executor.py (deterministic)
- [ ] Added tests (all passing)
- [ ] Updated documentation
- [ ] Reviewed by security-conscious person
- [ ] FinanceGuard not affected (or properly handled)
- [ ] No secrets in code

## Testing

[Describe how you tested this]

## Screenshots (if applicable)

[Add screenshots of Siri usage, etc.]
```

---

## 🎓 Examples

### Example 1: Adding "list_projects" (Low Risk)

**1. policy.yaml:**

```yaml
actions:
  list_projects:
    risk: 0 # Read-only
    description: "List all projects in repos directory"
    args_schema: {}
    returns: "Array of project names"
```

**2. executor.py:**

```python
def _action_list_projects(self, args: Dict) -> Dict:
    """List all projects"""
    repos_root = os.path.expanduser('~/activi-dev-repos')

    try:
        projects = [
            d for d in os.listdir(repos_root)
            if os.path.isdir(os.path.join(repos_root, d))
            and not d.startswith('.')
        ]

        return {
            'success': True,
            'projects': projects,
            'count': len(projects)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Example 2: Adding "open_browser_url" (Medium Risk)

**1. Add to allowlists in policy.yaml:**

```yaml
allowlists:
  allowed_domains:
    - "github.com"
    - "linear.app"
    - "slack.com"
```

**2. Define action:**

```yaml
actions:
  open_browser_url:
    risk: 1 # Can disrupt work
    description: "Open URL in default browser"
    args_schema:
      domain:
        type: enum
        values_from: allowlists.allowed_domains
      path:
        type: string
        pattern: "^[a-zA-Z0-9/_-]+$"
        optional: true
    rate_limit: 20
    returns: "Success status"
```

**3. Implement:**

```python
def _action_open_browser_url(self, args: Dict) -> Dict:
    """Open URL in browser"""
    domain = args['domain']
    path = args.get('path', '')

    url = f"https://{domain}/{path}".rstrip('/')

    try:
        subprocess.run(['open', url], check=True)
        return {
            'success': True,
            'message': f'Opened {url}',
            'url': url
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## 🔄 Review Process

1. **Self-Review**: Go through security checklist
2. **Code Review**: Another developer reviews
3. **Security Review**: If Risk 1+ or touches sensitive areas
4. **Test**: Run full test suite
5. **Deploy**: Merge to main

---

## 📞 Questions?

- **Security Question**: Always ask! Better safe than sorry.
- **Design Question**: Check [ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **Policy Question**: See [POLICY_GUIDE.md](./docs/POLICY_GUIDE.md)

---

**🔒 Remember: Every new action increases the attack surface. Be conservative!**

Made with ❤️ & 🔒 by Denis Selmanovic & Claude Sonnet 4.5
