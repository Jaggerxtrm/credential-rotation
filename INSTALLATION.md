# Installation Guide

This guide covers how to install and use `credential-rotation` in various environments.

## Quick Install

### From PyPI (Recommended)
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

## Verify Installation

```bash
# Check CLI is available
account-qwen --version

# Or check Python import
python -c "from credential_rotation import __version__; print(__version__)"
```

Expected output:
```
credential-rotation 0.1.0
```

## Initial Setup

After installation, configure your Qwen accounts:

```bash
account-qwen --setup
```

Follow the interactive prompts:
1. You'll be asked to set up 5 accounts (default)
2. For each account, open a NEW terminal
3. Run `qwen` in that terminal
4. Complete OAuth in browser
5. Return here and press ENTER
6. Repeat for all 5 accounts

## Project Integration

### Method 1: Direct Import

```python
from credential_rotation import QwenWrapper

# In your __init__ or setup
wrapper = QwenWrapper(max_retries=5)

# When calling qwen
result = wrapper.call_with_fallback(
    "Your prompt here",
    fallback_message="Analysis unavailable",
    timeout=45
)
```

### Method 2: With Existing subprocess calls

Replace this:
```python
qwen_result = subprocess.run(
    ["qwen", prompt, "--output-format", "text"],
    capture_output=True,
    text=True,
    timeout=45
)
output = qwen_result.stdout.strip()
```

With this:
```python
from credential_rotation import QwenWrapper

wrapper = QwenWrapper()
output = wrapper.call_with_fallback(
    prompt,
    fallback_message="Could not generate summary.",
    timeout=45
)
```

## Docker Integration

### Method 1: Mount ~/.qwen directory

```yaml
# docker-compose.yml
services:
  your-app:
    image: your-app
    volumes:
      - ~/.qwen:/root/.qwen:ro
```

### Method 2: Install in Dockerfile

```dockerfile
FROM python:3.12-slim

# Install credential-rotation
RUN pip install credential-rotation

# Copy your app
COPY . /app
WORKDIR /app

# Mount point for credentials
VOLUME ["/root/.qwen"]

CMD ["python", "app.py"]
```

## System Requirements

- Python 3.10 or higher
- qwen CLI installed (`npm install -g @qwen-code/qwen-code`)
- ~1MB disk space for package
- Credentials stored in `~/.qwen/`

## Troubleshooting

### "command not found: account-qwen"

The CLI is not in your PATH. Try:
```bash
# Check pip location
pip show credential-rotation

# Reinstall with user flag
pip install --user credential-rotation

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

### "ModuleNotFoundError: No module named 'credential_rotation'"

Python can't find the package. Try:
```bash
# Reinstall
pip uninstall credential-rotation
pip install credential-rotation

# Or with full path
python -m pip install credential-rotation
```

### "Qwen CLI not found"

Install the qwen CLI first:
```bash
npm install -g @qwen-code/qwen-code
```

### "No such file or directory: ~/.qwen/oauth_creds.json"

You haven't set up accounts yet:
```bash
account-qwen --setup
```

### "All accounts exhausted"

All 5 accounts have hit quota limits. You need to:
1. Wait for quota to reset (usually daily/monthly)
2. Add more accounts (edit state.yaml)
3. Check rotation log: `cat ~/.qwen/rotation.log`

## Uninstallation

```bash
# Remove package
pip uninstall credential-rotation

# Remove credentials (optional, keeps your accounts)
rm -rf ~/.qwen

# Or keep credentials for future use
ls ~/.qwen/  # Check what's there
```

## Upgrading

```bash
# Check current version
pip show credential-rotation

# Upgrade to latest
pip install --upgrade credential-rotation

# Upgrade to specific version
pip install credential-rotation==0.2.0
```

## Offline Installation

For air-gapped environments:

1. On internet-connected machine:
   ```bash
   pip download credential-rotation -d ./packages
   ```

2. Transfer `packages/` directory to target machine

3. Install offline:
   ```bash
   pip install --no-index --find-links=./packages credential-rotation
   ```

## Next Steps

- Read [README.md](README.md) for usage examples
- See [PUBLISHING.md](PUBLISHING.md) for release workflow
- Check [GitHub Issues](https://github.com/dawid/credential-rotation/issues) for known problems
