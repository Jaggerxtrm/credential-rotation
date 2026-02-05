"""
Credential Rotation - Automatic OAuth credential rotation for CLI tools

This package provides automatic credential rotation for CLI tools that have
quota limits, supporting round-robin rotation across multiple accounts.

Supported tools:
- Qwen CLI (qwen)
"""

__version__ = "0.1.0"

from credential_rotation.qwen.manager import (
    AccountManager,
    AccountNotFoundError,
    AccountStats,
    LockError,
    RotationState,
    SwitchReason,
    create_initial_state,
)

from credential_rotation.qwen.wrapper import (
    QwenWrapper,
    WrapperResult,
    CallResult,
    QUOTA_PATTERNS,
)

__all__ = [
    # Version
    "__version__",
    # AccountManager
    "AccountManager",
    "AccountNotFoundError",
    "AccountStats",
    "LockError",
    "RotationState",
    "SwitchReason",
    "create_initial_state",
    # QwenWrapper
    "QwenWrapper",
    "WrapperResult",
    "CallResult",
    "QUOTA_PATTERNS",
]
