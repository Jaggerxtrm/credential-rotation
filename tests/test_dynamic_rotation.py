
import pytest
from pathlib import Path
from credential_rotation.qwen.manager import AccountManager

def test_discovery_and_non_sequential_rotation(tmp_path):
    """Test that discovery works with gaps in IDs."""
    # Setup mock .qwen directory
    qwen_dir = tmp_path / ".qwen"
    accounts_dir = qwen_dir / "accounts"
    accounts_dir.mkdir(parents=True)
    
    # Create accounts 1 and 3 (gap at 2)
    (accounts_dir / "oauth_creds_1.json").write_text("{}")
    (accounts_dir / "oauth_creds_3.json").write_text("{}")
    
    manager = AccountManager(qwen_dir=qwen_dir)
    
    # Test discovery
    ids = manager._discover_account_ids()
    assert ids == [1, 3]
    
    # Test rotation from 1 to 3
    success, next_index = manager.switch_next()
    assert next_index == 3
    assert success is True
    
    # Test rotation from 3 back to 1 (wrap)
    success, next_index = manager.switch_next()
    assert next_index == 1
    assert success is False # Wrapped
    
def test_switch_to_non_existent_fails(tmp_path):
    """Test that switching to a non-existent account raises error."""
    qwen_dir = tmp_path / ".qwen"
    (qwen_dir / "accounts").mkdir(parents=True)
    
    manager = AccountManager(qwen_dir=qwen_dir)
    with pytest.raises(Exception): # AccountNotFoundError
        manager.switch_to(5)
