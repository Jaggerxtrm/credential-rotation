"""
Tests for Qwen credential rotation.

Copy the full test suite from the original project.
"""

from credential_rotation.qwen.manager import AccountManager, RotationState

def test_basic_import():
    """Test that basic imports work."""
    assert AccountManager is not None
    assert RotationState is not None

def test_rotation_state_creation():
    """Test creating a rotation state."""
    state = RotationState(current_index=1, total_accounts=5)
    assert state.current_index == 1
    assert state.total_accounts == 5
    assert state.switches_total == 0
