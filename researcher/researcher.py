"""
Researcher - Role1 LLM-based Planning
CAN use LLM for understanding and planning
CANNOT execute actions - must pass to Role2 (Executor)

Separation of Concerns:
- Role1: Understand intent, plan actions (can be wrong)
- Role2: Validate against policy, execute (deterministic)
"""

import os
import json
from typing import Dict, List, Any, Optional
from anthropic import Anthropic


class ActionPlanner:
    """
    LLM-based action planner
    Translates natural language → structured action requests
    """

    def __init__(self, allowed_actions: List[str], allowlists: Dict[str, List[str]]):
        """
        Args:
            allowed_actions: List of allowed action names (from policy)
            allowlists: Dict of allowlists (apps, projects, etc.) from policy
        """
        self.allowed_actions = allowed_actions
        self.allowlists = allowlists

        # Initialize Anthropic client
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)

    def plan(self, user_request: str, context: Optional[Dict] = None) -> Dict:
        """
        Plan actions for user request

        Args:
            user_request: Natural language request
            context: Optional context (current state, recent actions, etc.)

        Returns:
            {
                'success': bool,
                'plan': List[Dict],  # List of action requests
                'reasoning': str,    # Why this plan
                'confidence': float  # 0-1
            }
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user message
        user_message = self._build_user_message(user_request, context)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            plan_data = self._extract_json(response_text)

            if not plan_data:
                return {
                    'success': False,
                    'error': 'Failed to parse LLM response',
                    'raw_response': response_text
                }

            return {
                'success': True,
                'plan': plan_data.get('actions', []),
                'reasoning': plan_data.get('reasoning', ''),
                'confidence': plan_data.get('confidence', 0.5),
                'raw_response': response_text
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return f"""You are an AI assistant that translates user requests into structured action plans.

IMPORTANT CONSTRAINTS:
1. You can ONLY use these actions: {', '.join(self.allowed_actions)}
2. All action arguments must come from allowlists (no free-form strings)
3. You are Role1 (Planner) - you CANNOT execute actions
4. Role2 (Executor) will validate your plan against policy.yaml
5. If you're unsure, suggest low-risk read-only actions first

AVAILABLE ALLOWLISTS:
{json.dumps(self.allowlists, indent=2)}

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "actions": [
    {{
      "action": "action_name",
      "args": {{
        "arg1": "value1",
        "arg2": "value2"
      }},
      "reason": "why this action is needed"
    }}
  ],
  "reasoning": "overall plan explanation",
  "confidence": 0.8  // 0-1, how confident you are
}}

RULES:
- Use ONLY actions from the allowed list
- Use ONLY values from allowlists for enum arguments
- Start with read-only actions when exploring
- Be conservative - suggest confirmation for risky actions
- If request is unclear, ask for clarification (suggest status_overview)
- NEVER suggest actions that access finance, banking, or sensitive data
"""

    def _build_user_message(self, user_request: str, context: Optional[Dict]) -> str:
        """Build user message with request and context"""
        message = f"User request: {user_request}\n\n"

        if context:
            message += "Context:\n"
            for key, value in context.items():
                message += f"- {key}: {value}\n"
            message += "\n"

        message += "Plan the actions needed to fulfill this request. Return JSON only."

        return message

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response"""
        # Try to find JSON in response
        import re

        # Look for JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass

        # Try parsing entire response
        try:
            return json.loads(text)
        except:
            pass

        return None


class Researcher:
    """
    Role1: LLM-based Researcher
    Plans actions but does NOT execute
    """

    def __init__(self, validator, executor):
        """
        Args:
            validator: PolicyValidator instance
            executor: ActionExecutor instance
        """
        self.validator = validator
        self.executor = executor

        # Get allowed actions and allowlists from policy
        allowed_actions = validator.list_allowed_actions()
        allowlists = validator.policy.get('allowlists', {})

        # Initialize planner
        self.planner = ActionPlanner(allowed_actions, allowlists)

        # Conversation history
        self.history = []

    def process_request(self, user_request: str, auto_execute: bool = False) -> Dict:
        """
        Process natural language request

        Args:
            user_request: User's natural language request
            auto_execute: If True, automatically execute low-risk actions

        Returns:
            {
                'success': bool,
                'plan': List[Dict],
                'results': List[Dict],  # If auto_execute=True
                'needs_confirmation': bool
            }
        """
        # Add to history
        self.history.append({
            'role': 'user',
            'content': user_request
        })

        # Build context from recent history
        context = self._build_context()

        # Plan actions
        plan_result = self.planner.plan(user_request, context)

        if not plan_result['success']:
            return {
                'success': False,
                'error': plan_result.get('error', 'Planning failed')
            }

        plan = plan_result['plan']
        reasoning = plan_result['reasoning']

        # Add plan to history
        self.history.append({
            'role': 'assistant',
            'content': f"Plan: {reasoning}",
            'plan': plan
        })

        response = {
            'success': True,
            'plan': plan,
            'reasoning': reasoning,
            'confidence': plan_result.get('confidence', 0.5)
        }

        # If auto_execute, execute low-risk actions
        if auto_execute:
            results = []
            needs_confirmation = []

            for action_request in plan:
                action_name = action_request['action']
                args = action_request.get('args', {})

                # Execute via Role2 (Executor)
                result = self.executor.execute(
                    action_name, args,
                    trigger='siri',  # Assuming voice trigger
                    agent='researcher'
                )

                if result.get('requires_confirmation'):
                    # High-risk action - needs confirmation
                    needs_confirmation.append({
                        'action': action_request,
                        'challenge_id': result['challenge_id'],
                        'description': result.get('description', '')
                    })
                else:
                    results.append({
                        'action': action_name,
                        'result': result
                    })

            response['results'] = results
            response['needs_confirmation'] = needs_confirmation

        return response

    def confirm_action(self, challenge_id: str) -> Dict:
        """
        Confirm a pending high-risk action

        Args:
            challenge_id: Challenge ID from previous execution

        Returns:
            Execution result
        """
        return self.executor.confirm_and_execute(
            challenge_id,
            trigger='siri',
            agent='researcher'
        )

    def _build_context(self) -> Dict:
        """Build context from recent history"""
        # Get last 5 interactions
        recent = self.history[-5:] if len(self.history) > 5 else self.history

        context = {
            'conversation_length': len(self.history),
            'recent_interactions': len(recent)
        }

        # Add recent user requests
        recent_requests = [
            h['content'] for h in recent
            if h['role'] == 'user'
        ]
        if recent_requests:
            context['recent_requests'] = recent_requests

        return context

    def get_capabilities(self) -> Dict:
        """Get available capabilities"""
        # Get allowed actions by risk level
        risk_0 = self.validator.list_allowed_actions(risk_level=0)
        risk_1 = self.validator.list_allowed_actions(risk_level=1)
        risk_2 = self.validator.list_allowed_actions(risk_level=2)

        return {
            'total_actions': len(self.validator.list_allowed_actions()),
            'low_risk': {
                'count': len(risk_0),
                'actions': risk_0
            },
            'medium_risk': {
                'count': len(risk_1),
                'actions': risk_1
            },
            'high_risk': {
                'count': len(risk_2),
                'actions': risk_2
            },
            'allowlists': self.validator.policy.get('allowlists', {})
        }


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    from executor.validator import PolicyValidator
    from executor.executor import ActionExecutor
    from src.security.audit_log import AuditLogger

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("⚠️  ANTHROPIC_API_KEY not set - skipping LLM test")
        print("   Set with: export ANTHROPIC_API_KEY=sk-...")
        sys.exit(0)

    # Create instances
    validator = PolicyValidator()
    audit_logger = AuditLogger()
    executor = ActionExecutor(validator, audit_logger)
    researcher = Researcher(validator, executor)

    print("=" * 60)
    print("RESEARCHER (Role1) TEST")
    print("=" * 60)

    # Show capabilities
    caps = researcher.get_capabilities()
    print(f"\nAvailable capabilities:")
    print(f"  Low-risk actions: {caps['low_risk']['count']}")
    print(f"  Medium-risk actions: {caps['medium_risk']['count']}")
    print(f"  High-risk actions: {caps['high_risk']['count']}")

    # Test request
    print("\n" + "-" * 60)
    print("Test request: 'Show me system status'")
    print("-" * 60)

    result = researcher.process_request(
        "Show me the system status and list recent tasks",
        auto_execute=True
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 0)}")

    if result.get('results'):
        print(f"\nExecuted {len(result['results'])} actions:")
        for r in result['results']:
            print(f"  - {r['action']}: {r['result'].get('success', False)}")

    if result.get('needs_confirmation'):
        print(f"\nActions needing confirmation: {len(result['needs_confirmation'])}")

    print("\n" + "=" * 60)
