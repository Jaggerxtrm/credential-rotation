"""
Qwen Account Rotation Manager

This module provides atomic account switching with file locking for
safe credential rotation across multiple Qwen OAuth accounts.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Final

import yaml

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TOTAL_ACCOUNTS: Final[int] = 5
DEFAULT_QWEN_DIR: Final[Path] = Path.home() / ".qwen"
DEFAULT_LOCK_FILE: Final[str] = "/tmp/qwen_rotation.lock"
ACCOUNTS_DIR_NAME: Final[str] = "accounts"
OAUTH_CREDS_FILE: Final[str] = "oauth_creds.json"
STATE_FILE: Final[str] = "state.yaml"
ROTATION_LOG: Final[str] = "rotation.log"


class SwitchReason(Enum):
    """Reason for account switch."""
    AUTO_QUOTA = "auto_quota"
    MANUAL = "manual"
    TEST = "test"


@dataclass
class AccountStats:
    """Statistics for a single account."""
    switches_count: int = 0
    last_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "switches_count": self.switches_count,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AccountStats:
        if data is None:
            return cls()
        return cls(
            switches_count=data.get("switches_count", 0),
            last_used=data.get("last_used"),
        )


@dataclass
class RotationState:
    """Complete rotation state."""
    current_index: int = 1
    total_accounts: int = DEFAULT_TOTAL_ACCOUNTS
    last_switch: str | None = None
    switches_total: int = 0
    accounts: dict[str, AccountStats] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_index": self.current_index,
            "total_accounts": self.total_accounts,
            "last_switch": self.last_switch,
            "switches_total": self.switches_total,
            "accounts": {
                k: v.to_dict() for k, v in self.accounts.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RotationState:
        accounts = {
            k: AccountStats.from_dict(v)
            for k, v in data.get("accounts", {}).items()
        }
        return cls(
            current_index=data.get("current_index", 1),
            total_accounts=data.get("total_accounts", DEFAULT_TOTAL_ACCOUNTS),
            last_switch=data.get("last_switch"),
            switches_total=data.get("switches_total", 0),
            accounts=accounts,
        )


class LockError(Exception):
    """Raised when lock acquisition fails."""
    pass


class AccountNotFoundError(Exception):
    """Raised when target account credentials don't exist."""
    pass


class AccountManager:
    """
    Manages Qwen account rotation with physical file swapping.

    This class provides thread-safe account switching using:
    - File locking (flock) to prevent race conditions
    - Physical file copy (sync-back) to survive Qwen CLI overwrites
    - Persistent state tracking in state.yaml
    - Audit logging to rotation.log
    """

    def __init__(
        self,
        qwen_dir: Path | None = None,
        total_accounts: int = DEFAULT_TOTAL_ACCOUNTS,
    ) -> None:
        """
        Initialize the AccountManager.
        """
        self.qwen_dir = qwen_dir or DEFAULT_QWEN_DIR
        self.total_accounts = total_accounts
        self.state_file = self.qwen_dir / STATE_FILE
        self.lock_file = Path(DEFAULT_LOCK_FILE)
        self.accounts_dir = self.qwen_dir / ACCOUNTS_DIR_NAME
        self.creds_file = self.qwen_dir / OAUTH_CREDS_FILE
        self.log_file = self.qwen_dir / ROTATION_LOG

    def get_state(self) -> RotationState:
        """Read current rotation state."""
        if not self.state_file.exists():
            return RotationState(total_accounts=self.total_accounts)

        try:
            with open(self.state_file, "r") as f:
                data = yaml.safe_load(f) or {}
            return RotationState.from_dict(data)
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Failed to read state file: {e}")
            return RotationState(total_accounts=self.total_accounts)

    def _write_state(self, state: RotationState) -> None:
        """Write state file atomically."""
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            if not self.qwen_dir.exists():
                self.qwen_dir.mkdir(parents=True, exist_ok=True)
                
            with open(temp_file, "w") as f:
                yaml.dump(state.to_dict(), f, default_flow_style=False)
            os.replace(temp_file, self.state_file)
        except (IOError, OSError) as e:
            logger.error(f"Failed to write state file: {e}")
            if temp_file.exists(): temp_file.unlink()
            raise

    def _discover_account_ids(self) -> list[int]:
        """Discover available account IDs."""
        if not self.accounts_dir.exists():
            return []
        ids = []
        for f in self.accounts_dir.glob("oauth_creds_*.json"):
            try:
                parts = f.stem.split("_")
                if len(parts) >= 3:
                    ids.append(int(parts[-1]))
            except (ValueError, IndexError):
                continue
        return sorted(ids)

    def _swap_credentials(self, target_index: int, current_index: int | None = None) -> None:
        """
        Physically swap credentials. 
        Saves current file back to its slot (sync-back) and loads the new one.
        """
        # 1. Sync-back: Save current active file to its slot
        if current_index is not None and self.creds_file.exists():
            # Don't sync if it's a symlink (cleanup legacy)
            if not self.creds_file.is_symlink():
                current_slot = self.accounts_dir / f"oauth_creds_{current_index}.json"
                try:
                    shutil.copy2(self.creds_file, current_slot)
                    logger.debug(f"Synced credentials back to account{current_index}")
                except Exception as e:
                    logger.error(f"Failed to sync-back credentials: {e}")
            else:
                # Remove legacy symlink to allow physical copy
                self.creds_file.unlink()

        # 2. Activate: Copy target account to main slot
        target_slot = self.accounts_dir / f"oauth_creds_{target_index}.json"
        if not target_slot.exists():
            raise AccountNotFoundError(f"Account {target_index} source file not found")

        temp_active = self.creds_file.with_suffix(".json.tmp")
        try:
            shutil.copy2(target_slot, temp_active)
            os.replace(temp_active, self.creds_file)
            logger.debug(f"Activated account{target_index}")
        except Exception as e:
            if temp_active.exists(): temp_active.unlink()
            raise OSError(f"Failed to activate credentials: {e}")

    def _update_account_stats(self, state: RotationState, index: int) -> None:
        account_key = f"account{index}"
        if account_key not in state.accounts:
            state.accounts[account_key] = AccountStats()
        stats = state.accounts[account_key]
        stats.switches_count += 1
        stats.last_used = datetime.now().isoformat()

    def _log_switch(self, from_idx: int, to_idx: int, reason: SwitchReason) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "event": "account_switch",
            "from": from_idx,
            "to": to_idx,
            "reason": reason.value,
        }
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError:
            pass

    def _with_lock(self, func) -> Any:
        lock_fd = None
        try:
            lock_fd = open(self.lock_file, "w")
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
            return func()
        except (IOError, OSError) as e:
            raise LockError(f"Could not acquire lock: {e}")
        finally:
            if lock_fd:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()

    def switch_to(self, index: int, reason: SwitchReason = SwitchReason.MANUAL) -> bool:
        def _do_switch() -> bool:
            state = self.get_state()
            current_index = state.current_index
            self._swap_credentials(index, current_index)
            state.current_index = index
            state.last_switch = datetime.now().isoformat()
            state.switches_total += 1
            self._update_account_stats(state, index)
            self._write_state(state)
            self._log_switch(current_index, index, reason)
            return True
        return self._with_lock(_do_switch)

    def switch_next(self, reason: SwitchReason = SwitchReason.AUTO_QUOTA) -> tuple[bool, int]:
        def _do_switch() -> tuple[bool, int]:
            state = self.get_state()
            current_index = state.current_index
            available_ids = self._discover_account_ids()
            if not available_ids:
                raise AccountNotFoundError("No accounts found")

            try:
                current_pos = available_ids.index(current_index)
                next_pos = (current_pos + 1) % len(available_ids)
                next_index = available_ids[next_pos]
                wrapped = next_pos == 0
            except ValueError:
                next_index = available_ids[0]
                wrapped = True

            self._swap_credentials(next_index, current_index)
            state.current_index = next_index
            state.last_switch = datetime.now().isoformat()
            state.switches_total += 1
            self._update_account_stats(state, next_index)
            state.total_accounts = len(available_ids)
            self._write_state(state)
            self._log_switch(current_index, next_index, reason)
            return (not wrapped, next_index)
        return self._with_lock(_do_switch)

    def list_accounts(self) -> dict[str, dict[str, Any]]:
        state = self.get_state()
        result = {}
        available_ids = self._discover_account_ids()
        for i in available_ids:
            account_key = f"account{i}"
            creds_file = self.accounts_dir / f"oauth_creds_{i}.json"
            stats = state.accounts.get(account_key, AccountStats())
            result[account_key] = {
                "index": i,
                "active": i == state.current_index,
                "exists": True,
                "switches_count": stats.switches_count,
                "last_used": stats.last_used,
            }
        return result

    def get_stats(self) -> dict[str, Any]:
        state = self.get_state()
        accounts = self.list_accounts()
        most_used = max(accounts.items(), key=lambda x: x[1]["switches_count"], default=("none", {"switches_count": 0}))
        return {
            "accounts": {k: v["switches_count"] for k, v in accounts.items()},
            "total_switches": state.switches_total,
            "last_switch": state.last_switch,
            "current_account": f"account{state.current_index}",
            "most_used_account": most_used[0],
            "most_used_count": most_used[1]["switches_count"],
        }


def create_initial_state(qwen_dir: Path | None = None, total_accounts: int = DEFAULT_TOTAL_ACCOUNTS) -> RotationState:
    manager = AccountManager(qwen_dir=qwen_dir, total_accounts=total_accounts)
    state = RotationState(total_accounts=total_accounts)
    manager._write_state(state)
    return state
