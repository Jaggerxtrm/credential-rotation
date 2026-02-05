"""
Qwen Credential Rotation Module

This module provides credential rotation for the Qwen CLI.
"""

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
    "AccountManager",
    "AccountNotFoundError",
    "AccountStats",
    "LockError",
    "RotationState",
    "SwitchReason",
    "create_initial_state",
    "QwenWrapper",
    "WrapperResult",
    "CallResult",
    "QUOTA_PATTERNS",
]
