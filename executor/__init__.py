"""
Executor Package - Role2 Deterministic Execution
NO LLM in execution path
"""

import sentry_sdk

sentry_sdk.init(
    dsn="https://d6b039fa51435d431953a1fab781592a@o4510621142024192.ingest.de.sentry.io/4510627954163792",
    send_default_pii=True,
    traces_sample_rate=1.0,
)

from .validator import PolicyValidator, ValidationResult, ValidationResponse
from .executor import ActionExecutor, ConfirmationManager

__all__ = [
    'PolicyValidator',
    'ValidationResult',
    'ValidationResponse',
    'ActionExecutor',
    'ConfirmationManager'
]
