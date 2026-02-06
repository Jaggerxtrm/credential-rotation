# Installation Guide

This guide covers how to install and use `credential-rotation` in various environments.

## Primary Installation Methods

### From GitHub
This is the recommended way to get the latest features and fixes.
```bash
pip install git+https://github.com/Jaggerxtrm/credential-rotation.git
```

### Local Development Install
Use this method if you want to modify the code or contribute.
```bash
git clone https://github.com/Jaggerxtrm/credential-rotation.git
cd credential-rotation
pip install -e .
```

## Verify Installation

```bash
# Check CLI is available
account-qwen --list
```

## Initial Setup

After installation, configure your Qwen accounts:

```bash
account-qwen --setup
```

Follow the interactive prompts to set up as many accounts as you need.

## Docker Integration

Docker integration has been tested and verified. Use the following volume mount to share credentials between the host and containers.

### docker-compose.yml Example

```yaml
services:
  qwen-service:
    image: your-qwen-image
    volumes:
      # ===== CRITICAL: Mount Qwen credentials =====
      # Use :rw,Z for read-write with SELinux/Podman context
      - ~/.qwen:/root/.qwen:rw,Z
```

**Important Notes:**
- The system uses a **Sync-Back** strategy: when an account is rotated, the current credentials are saved back to their original slot. This ensures that refreshed tokens are never lost.
- Volume mounts must be `rw` (read-write).

## Troubleshooting

### "command not found: account-qwen"

If the CLI is not in your PATH, try:
```bash
# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
# Then refresh your shell
hash -r # Bash
rehash  # Zsh
```

### "ModuleNotFoundError: No module named 'qwen_credential'"

If you see this error, you likely have an old version installed. Run:
```bash
pip uninstall qwen-credential credential-rotation
pip install -e .
```

## Next Steps

- Read [README.md](README.md) for usage examples.
- Check [CENTRALIZATION_GUIDE.md](CENTRALIZATION_GUIDE.md) for microservices architecture.