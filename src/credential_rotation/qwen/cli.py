#!/usr/bin/env python3
"""
account-qwen CLI - Qwen Account Rotation Management Utility

This script manages multiple Qwen OAuth accounts with automatic
round-robin rotation when quota is exhausted.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from textwrap import dedent

from credential_rotation.qwen.manager import (
    DEFAULT_QWEN_DIR,
    DEFAULT_TOTAL_ACCOUNTS,
    AccountManager,
    AccountNotFoundError,
    LockError,
    SwitchReason,
    create_initial_state,
)

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_success(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def print_warning(msg: str) -> None:
    print(f"{YELLOW}⚠{RESET} {msg}")


def print_error(msg: str) -> None:
    print(f"{RED}✗{RESET} {msg}")


def print_info(msg: str) -> None:
    print(f"{BLUE}ℹ{RESET} {msg}")


def print_header(msg: str) -> None:
    print(f"\n{BOLD}{BLUE}=== {msg} ==={RESET}\n")


def check_qwen_installed() -> bool:
    """Check if qwen CLI is installed and available in PATH."""
    return shutil.which("qwen") is not None


def get_qwen_creds_path() -> Path:
    """Get the default path for qwen credentials."""
    return DEFAULT_QWEN_DIR / "oauth_creds.json"


def _setup_single_account(index: int, total_label: str = "") -> bool:
    """
    Setup a single account interactively.
    
    Args:
        index: Account index.
        total_label: Optional label for progress (e.g., "/5").
        
    Returns:
        True if success, False otherwise.
    """
    print_header(f"Account {index}{total_label}")
    creds_path = get_qwen_creds_path()
    accounts_dir = DEFAULT_QWEN_DIR / "accounts"

    print("To add or update a Qwen account:")
    print(f"  1. Open a {BOLD}NEW terminal{RESET}")
    print(f"  2. Run: {BOLD}qwen{RESET}")
    print(f"  3. Complete the OAuth login in your browser")
    print(f"  4. When you see the qwen prompt, close that terminal")
    print(f"  5. Return here and press {BOLD}ENTER{RESET}\n")

    input("Press ENTER when you have completed the OAuth login...")

    # Verify credentials were created
    if not creds_path.exists():
        print_error(f"No credentials found at {creds_path}")
        retry = input("Try again? (y/N): ").strip().lower()
        if retry == "y":
            return _setup_single_account(index, total_label)
        return False

    # Move credentials to accounts directory
    target_creds = accounts_dir / f"oauth_creds_{index}.json"

    if target_creds.exists():
        sys.stdout.write(f"{YELLOW}⚠{RESET} Account {index} credentials already exist. Overwrite? (y/N): ")
        sys.stdout.flush()
        overwrite = input().strip().lower()
        if overwrite != "y":
            print_info(f"Skipping account {index}")
            return True

    shutil.move(str(creds_path), str(target_creds))
    print_success(f"Saved credentials as: {target_creds}")

    # Clean up any remaining oauth_creds.json (sometimes move doesn't clean up perfectly)
    if creds_path.exists():
        creds_path.unlink()
        
    return True


def setup_accounts(total_accounts: int = DEFAULT_TOTAL_ACCOUNTS) -> int:
    """
    Interactive setup for initial Qwen account credentials.
    """
    print_header(f"Qwen Account Rotation Setup ({total_accounts} accounts)")
    print_info("This will guide you through logging into multiple Qwen accounts.")

    if not check_qwen_installed():
        print_error("qwen CLI is not installed!")
        print("Install it with: npm install -g @qwen-code/qwen-code")
        return 1

    qwen_dir = DEFAULT_QWEN_DIR
    accounts_dir = qwen_dir / "accounts"

    if not accounts_dir.exists():
        accounts_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"Created accounts directory: {accounts_dir}")

    for i in range(1, total_accounts + 1):
        if not _setup_single_account(i, f"/{total_accounts}"):
            return 1

    print_header("Setup Complete!")
    print_info("Creating initial state...")
    create_initial_state(total_accounts=total_accounts)
    print_success("You can now use account-qwen to manage your accounts.")
    return 0


def add_account() -> int:
    """Add a new account to the rotation."""
    print_header("Add New Qwen Account")
    
    if not check_qwen_installed():
        print_error("qwen CLI is not installed!")
        return 1

    manager = AccountManager()
    existing_ids = manager._discover_account_ids()
    
    # Find the next ID
    new_id = 1
    while new_id in existing_ids:
        new_id += 1
        
    print_info(f"Adding new account as index {new_id}")
    if _setup_single_account(new_id):
        print_success(f"Account {new_id} added successfully.")
        return 0
    return 1


def remove_account(index: int) -> int:
    """Remove an account from the rotation."""
    manager = AccountManager()
    target_creds = manager.accounts_dir / f"oauth_creds_{index}.json"
    
    if not target_creds.exists():
        print_error(f"Account {index} not found at {target_creds}")
        return 1
        
    print_warning(f"Are you sure you want to remove account {index}? (y/N): ")
    confirm = input().strip().lower()
    if confirm == "y":
        target_creds.unlink()
        print_success(f"Removed account {index}")
        return 0
    
    print_info("Operation cancelled.")
    return 0


def list_accounts() -> int:
    """List all configured accounts and their status."""
    manager = AccountManager()
    accounts = manager.list_accounts()

    if not accounts:
        print_warning("No accounts configured. Run 'account-qwen --setup' or '--add'")
        return 0

    print_header("Qwen Accounts")
    for index_str, info in accounts.items():
        index = info["index"]
        active_marker = "*" if info["active"] else " "
        exists_marker = "✓" if info["exists"] else "✗"
        name = f"Account {index}"

        print(f"  {active_marker} [{index}] {name} {exists_marker}")

    print(f"\n({BOLD}*{RESET} = active account, {GREEN}✓{RESET} = credentials exist)")
    return 0


def switch_account(index: int | None = None) -> int:
    """Switch to specific or next account."""
    manager = AccountManager()

    try:
        if index is None:
            # Switch to next
            success, new_index = manager.switch_next(reason=SwitchReason.MANUAL)
            if not success:
                print_warning(f"Cycled back to the first available account ({new_index})")
            else:
                print_success(f"Switched to account {new_index}")
        else:
            # Switch to specific
            manager.switch_to(index)
            print_success(f"Switched to account {index}")
        return 0
    except (AccountNotFoundError, LockError, ValueError) as e:
        print_error(str(e))
        return 1


def show_stats() -> int:
    """Show usage statistics."""
    manager = AccountManager()
    stats = manager.get_stats()

    print_header("Usage Statistics")
    print(f"Total switches: {stats['total_switches']}")
    print(f"Last switch:    {stats['last_switch'] or 'Never'}")
    print(f"Current active: {stats['current_account']}")
    print(f"Most used:      {stats['most_used_account']} ({stats['most_used_count']} times)")

    print_header("Account Breakdown")
    for account, count in stats["accounts"].items():
        print(f"  {account}: {count} switches")

    return 0


def main() -> int:
    """Main entry point for account-qwen CLI."""
    parser = argparse.ArgumentParser(
        prog="account-qwen",
        description="Qwen Account Rotation Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""
            Examples:
              account-qwen --setup           Set up initial accounts
              account-qwen --add             Add a new account to the rotation
              account-qwen --remove 3        Remove account index 3
              account-qwen --list            List all accounts with status
              account-qwen --switch 3        Switch to account 3
              account-qwen --switch-next     Switch to next account (round-robin)
        """),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--setup",
        action="store_true",
        help="Interactive setup for initial configuration",
    )
    group.add_argument(
        "--add",
        action="store_true",
        help="Add a new account to the rotation",
    )
    group.add_argument(
        "--remove",
        metavar="INDEX",
        type=int,
        help="Remove a specific account by index",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List all configured accounts with status",
    )
    group.add_argument(
        "--switch",
        metavar="INDEX",
        type=int,
        help="Switch to specific account by index (1-based)",
    )
    group.add_argument(
        "--switch-next",
        action="store_true",
        help="Switch to next available account (round-robin)",
    )
    group.add_argument(
        "--stats",
        action="store_true",
        help="Display usage statistics",
    )

    args = parser.parse_args()

    # Route to appropriate handler
    if args.setup:
        return setup_accounts()
    elif args.add:
        return add_account()
    elif args.remove is not None:
        return remove_account(args.remove)
    elif args.list:
        return list_accounts()
    elif args.switch is not None:
        return switch_account(args.switch)
    elif args.switch_next:
        return switch_account(None)
    elif args.stats:
        return show_stats()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())