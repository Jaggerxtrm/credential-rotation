# Gemini Context: credential-rotation

## Project Overview
**credential-rotation** is a Python package designed to automatically rotate OAuth credentials for CLI tools, specifically targeting the `qwen` CLI. It manages usage quotas by switching between multiple accounts in a round-robin fashion when a quota exhaustion error is detected.

## Key Features
- **Automatic Rotation:** Switches accounts upon detecting quota errors.
- **Round-Robin Strategy:** Cycles through available accounts.
- **Atomic Operations:** Uses `os.replace` for safe credential swapping.
- **Persistence:** Maintains state in `~/.qwen/state.yaml`.

## Architecture
The system operates by managing a symlink at `~/.qwen/oauth_creds.json` that points to the currently active account file in `~/.qwen/accounts/`.

- **`AccountManager`**: Core logic for listing, switching, and locking accounts.
- **`QwenWrapper`**: Wraps CLI execution to catch errors and trigger rotation.

## Setup & Installation

### Prerequisites
- Python 3.10 or higher.
- `hatchling` for building (optional, handled by pip).

### Installation
```bash
# Install for usage
pip install .

# Install for development
pip install -e ".[dev,qwen]"
```

## Development Workflow

### Key Commands
| Command | Description |
| :--- | :--- |
| `account-qwen --setup` | Interactive setup for multiple Qwen accounts. |
| `account-qwen --list` | List all configured accounts and their status. |
| `account-qwen --stats` | View usage statistics. |
| `pytest` | Run the test suite. |
| `ruff check .` | Run linting checks. |
| `mypy .` | Run type checking. |

### Configuration
- **Project Config:** `pyproject.toml`
- **User Data:** `~/.qwen/` (contains credentials, logs, and state)

## Codebase Structure
- `src/credential_rotation/`: Main package source.
  - `qwen/cli.py`: Entry point for `account-qwen` tool.
  - `qwen/manager.py`: Logic for account management and file operations.
  - `qwen/wrapper.py`: Wrapper for executing CLI commands with retry logic.
- `tests/`: Test suite (uses `pytest`).

## Testing & Quality
- **Tests:** Run `pytest` to execute unit and integration tests.
- **Linting:** Use `ruff` for code style enforcement.
- **Typing:** Use `mypy` for static type checking.
