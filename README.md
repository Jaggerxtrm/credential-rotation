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

### From GitHub (Recommended)
```bash
pip install git+https://github.com/Jaggerxtrm/credential-rotation.git
```

### Local Development Install
```bash
git clone https://github.com/Jaggerxtrm/credential-rotation.git
cd credential-rotation
pip install -e .
```

📖 **Detailed Installation Guide:** See [INSTALLATION.md](INSTALLATION.md) for Docker integration and troubleshooting.

## Quick Start

### 1. Set Up Accounts

Configure your Qwen accounts (the system supports any number of accounts):

```bash
account-qwen --setup
```

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

# Add a new account
account-qwen --add

# Remove an account
account-qwen --remove 3

# Switch to specific account
account-qwen --switch 3

# Switch to next account (round-robin)
account-qwen --switch-next

# View usage statistics
account-qwen --stats
```

## Architecture

The system operates by managing physical file swapping in `~/.qwen/oauth_creds.json`.

- **`AccountManager`**: Core logic for listing, switching, and Sync-Back logic.
- **`QwenWrapper`**: Wraps CLI execution to catch errors and trigger rotation.

## Credential Storage

Credentials are stored in `~/.qwen/`:

```
~/.qwen/
├── accounts/
│   ├── oauth_creds_1.json    # Account 1
│   ├── oauth_creds_2.json    # Account 2
│   └── ...
├── oauth_creds.json          # Active account (Physical copy)
├── state.yaml                # Rotation state
└── rotation.log              # Audit log
```

## Docker Usage

Mount the `.qwen` directory to share credentials. Use the `:Z` flag for Podman/SELinux compatibility:

```yaml
services:
  app:
    image: your-app
    volumes:
      - ~/.qwen:/root/.qwen:rw,Z
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## References

- [Design Document](docs/qwen-design.md)
- [Docker PoC](examples/docker-service-poc/README.md)