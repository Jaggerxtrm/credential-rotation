# credential-rotation

Automatic OAuth credential rotation for CLI tools with quota limits.

## Overview

This package provides automatic credential rotation for CLI tools that have usage quota limits. When a tool reports quota exhaustion, the system automatically switches to the next available account in a round-robin fashion.

**Currently Supported:**
- Qwen CLI (`qwen`)

**Planned Support:**
- OpenAI CLI
- Anthropic Claude CLI
- Generic pattern for any CLI tool

## Installation

### From PyPI (when published)
```bash
pip install credential-rotation
```

### From GitHub
```bash
pip install git+https://github.com/dawid/credential-rotation.git
```

### Development Install
```bash
git clone https://github.com/dawid/credential-rotation.git
cd credential-rotation
pip install -e ".[dev,qwen]"
```

## Quick Start

### 1. Set Up Multiple Accounts

First, configure multiple Qwen accounts:

```bash
account-qwen --setup
```

This will guide you through:
1. Opening a new terminal for each account (5 accounts recommended)
2. Running `qwen` to initiate OAuth login
3. Completing the browser authentication
4. Saving credentials automatically

### 2. Use in Your Code

```python
from credential_rotation import QwenWrapper

# Create wrapper with automatic rotation
wrapper = QwenWrapper(max_retries=5)

# Call with automatic fallback
result = wrapper.call_with_fallback(
    "Analyze this code",
    fallback_message="Analysis unavailable",
    timeout=45
)

if result:
    print(result)
else:
    print("All accounts exhausted")
```

### 3. Manual Account Management

```bash
# List all accounts with status
account-qwen --list

# Switch to specific account
account-qwen --switch 3

# Switch to next account (round-robin)
account-qwen --switch-next

# View usage statistics
account-qwen --stats
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Application                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QwenWrapper                                │
│  • Executes CLI command                                        │
│  • Detects quota errors                                        │
│  • Calls AccountManager.switch_next() on quota error           │
│  • Retries with new account                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ switches
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AccountManager                             │
│  • Atomic symlink update (os.replace)                          │
│  • File locking (fcntl.flock)                                  │
│  • State persistence (state.yaml)                              │
│  • Audit logging (rotation.log)                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ updates
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ~/.qwen/ structure                            │
│  ├── accounts/                                                  │
│  │   ├── oauth_creds_1.json                                   │
│  │   ├── oauth_creds_2.json                                   │
│  │   └── ...                                                   │
│  ├── oauth_creds.json → symlink to active account              │
│  ├── state.yaml                                                │
│  └── rotation.log                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Credential Storage

Credentials are stored in `~/.qwen/`:

```
~/.qwen/
├── accounts/
│   ├── oauth_creds_1.json    # Account 1
│   ├── oauth_creds_2.json    # Account 2
│   ├── oauth_creds_3.json    # Account 3
│   ├── oauth_creds_4.json    # Account 4
│   └── oauth_creds_5.json    # Account 5
├── oauth_creds.json          # Symlink to current account
├── state.yaml                # Rotation state
└── rotation.log              # Audit log
```

## API Reference

### QwenWrapper

```python
from credential_rotation import QwenWrapper

wrapper = QwenWrapper(max_retries=5)

# Basic call with automatic rotation
result = wrapper.call(prompt, timeout=45)

# Call with fallback message
output = wrapper.call_with_fallback(
    prompt,
    fallback_message="Fallback text",
    timeout=30
)
```

**Returns:**
- `WrapperResult(success=bool, output=str, error=str|None, attempts=int)`

### AccountManager

```python
from credential_rotation import AccountManager

manager = AccountManager()

# Switch to specific account
manager.switch_to(3)

# Switch to next account (round-robin)
switched, next_index = manager.switch_next()

# List all accounts
accounts = manager.list_accounts()

# Get statistics
stats = manager.get_stats()
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=credential_rotation --cov-report=html
```

## Docker Usage

Mount the `.qwen` directory to share credentials:

```yaml
services:
  app:
    image: your-app
    volumes:
      - ~/.qwen:/root/.qwen:ro
```

## Security

- **Atomic Operations:** Uses `os.replace()` for atomic symlink updates
- **File Locking:** Uses `fcntl.flock()` to prevent concurrent modifications
- **Audit Trail:** All switches logged to `rotation.log`
- **No Hardcoded Secrets:** All credentials externalized to user directory

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Roadmap

- [ ] OpenAI CLI support
- [ ] Anthropic Claude CLI support
- [ ] Per-account quota tracking
- [ ] Configurable backoff strategies
- [ ] Webhook notifications
- [ ] Dashboard/monitoring UI

## References

- [Design Document](docs/qwen-design.md)
- [Original Implementation](https://github.com/dawid/omni-search-engine/tree/feature/qwen-credential-rolling)
