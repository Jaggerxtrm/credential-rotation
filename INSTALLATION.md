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

This section provides real-world integration examples based on successful implementations.

### Complete Integration Example

Here's a complete example from a production project (`omni-search-engine`):

#### Step 1: Add Dependency

```bash
# Add to requirements.txt or install
pip install credential-rotation
```

#### Step 2: Initialize Wrapper in Your Class

```python
# watcher.py (example)
from credential_rotation import QwenWrapper

class ShadowObserver:
    def __init__(self, vault_path: Path, log_file: str = "dev-log.md"):
        # ... existing init code ...

        # Initialize QwenWrapper with credential rotation
        self.qwen_wrapper = QwenWrapper(max_retries=5)
```

#### Step 3: Replace subprocess.run Calls

**BEFORE (direct qwen call):**
```python
qwen_result = subprocess.run(
    ["qwen", prompt, "--output-format", "text"],
    capture_output=True,
    text=True,
    timeout=45
)
ai_analysis = qwen_result.stdout.strip() if qwen_result.returncode == 0 else "Could not generate summary."
```

**AFTER (with credential rotation):**
```python
ai_analysis = self.qwen_wrapper.call_with_fallback(
    prompt,
    fallback_message="Could not generate summary.",
    timeout=45
)
```

#### Step 4: Update pyproject.toml (if using entry points)

```toml
[project]
name = "your-project"
dependencies = [
    # ... your other dependencies ...
    "credential-rotation>=0.1.0",
]
```

### Integration Patterns

#### Pattern 1: Wrapper Initialization

```python
from credential_rotation import QwenWrapper, AccountManager

# Option A: Simple wrapper with defaults
wrapper = QwenWrapper()

# Option B: Custom retry count
wrapper = QwenWrapper(max_retries=10)

# Option C: With custom account manager
manager = AccountManager(total_accounts=5)
wrapper = QwenWrapper(account_manager=manager, max_retries=5)
```

#### Pattern 2: Fallback Messages

```python
# For critical operations (fail loudly)
result = wrapper.call(prompt, timeout=45)
if not result.success:
    logger.error(f"Qwen failed: {result.error}")
    raise OperationFailedError("AI analysis unavailable")

# For non-critical operations (graceful degradation)
output = wrapper.call_with_fallback(
    prompt,
    fallback_message="Analysis unavailable",
    timeout=30
)
# Always returns a string, never raises
```

#### Pattern 3: Error Handling

```python
result = wrapper.call("Your prompt")

if result.success:
    print(f"Success: {result.output}")
    print(f"Attempts: {result.attempts}")
    print(f"Accounts tried: {result.accounts_tried}")
else:
    if "quota exhausted" in (result.error or "").lower():
        print("All accounts quota exhausted")
    else:
        print(f"Error: {result.error}")
```

### Script Integration

For standalone scripts that use qwen:

```python
#!/usr/bin/env python3
"""Analyze code with Qwen CLI and credential rotation."""

import sys
from credential_rotation import QwenWrapper

def main(prompt: str) -> int:
    wrapper = QwenWrapper()
    result = wrapper.call_with_fallback(
        prompt,
        fallback_message="Analysis failed",
        timeout=60
    )

    print(result)
    return 0 if result.success else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: analyze.py <prompt>")
        sys.exit(1)

    sys.exit(main(" ".join(sys.argv[1:])))
```

### Testing Integration

When writing tests for code using credential rotation:

```python
import pytest
from unittest.mock import Mock, patch
from credential_rotation import QwenWrapper

def test_qwen_call_with_mock():
    """Test qwen call with mocked subprocess."""
    # Mock the subprocess to avoid real API calls
    def mock_run(*args, **kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = "Mocked response"
        result.stderr = ""
        return result

    with patch('subprocess.run', side_effect=mock_run):
        wrapper = QwenWrapper()
        result = wrapper.call("test prompt")

    assert result.success
    assert result.output == "Mocked response"

def test_quota_rotation():
    """Test automatic account switching on quota error."""
    call_count = [0]

    def mock_run(*args, **kwargs):
        call_count[0] += 1
        result = Mock()
        # First call: quota error
        if call_count[0] == 1:
            result.returncode = 1
            result.stderr = "quota exhausted"
            result.stdout = ""
        # Second call: success
        else:
            result.returncode = 0
            result.stderr = ""
            result.stdout = "Success"
        return result

    with patch('subprocess.run', side_effect=mock_run):
        wrapper = QwenWrapper()
        result = wrapper.call("test prompt")

    assert result.success
    assert result.attempts == 2
```

## Docker Integration

Docker integration has been tested and verified in production. Here's the complete setup.

### Complete docker-compose.yml Example

This is the production configuration from `omni-search-engine`:

```yaml
services:
  your-app:
    build: .
    container_name: your-app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OBSIDIAN_VAULT_PATH=/vault
      - WATCH_MODE=true
    volumes:
      # Mount your application code
      - .:/app:z
      # Mount the vault
      - ${VAULT_PATH:-/home/user/vault}:/vault:rw,Z
      # Persist database data
      - chroma_data:/data/chromadb
      # ===== CRITICAL: Mount Qwen credentials =====
      - ~/.qwen:/root/.qwen:rw,Z
    stdin_open: true
    tty: false
    command: ["python", "server.py", "--sse"]
    ports:
      - "8765:8765"

volumes:
  chroma_data:
```

**Important Notes:**
- The `~/.qwen:/root/.qwen:rw,Z` mount includes:
  - `accounts/` - All credential files
  - `oauth_creds.json` - Active account symlink
  - `state.yaml` - Rotation state
  - `rotation.log` - Audit trail
- Use `:rw,Z` for read-write with SELinux context
- The mount is from the host's user directory to root's home in container

### Dockerfile Configuration

No special Dockerfile changes needed - just install the package:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install qwen CLI globally
RUN npm install -g @qwen-code/qwen-code

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install credential rotation
RUN pip install credential-rotation

# Copy application
COPY . /app
WORKDIR /app

# Create directory for credentials (optional, volume mount handles this)
RUN mkdir -p /root/.qwen

CMD ["python", "server.py"]
```

### Verify Docker Setup

After starting containers, verify credential access:

```bash
# Check credentials are mounted
podman exec your-app ls -la /root/.qwen/

# Check current state
podman exec your-app cat /root/.qwen/state.yaml

# Test CLI in container
podman exec your-app python -m qwen_credential.account_qwen --list

# Test account switching
podman exec your-app python -m qwen_credential.account_qwen --switch 1
```

### Multi-Stage Dockerfile (Optimized)

For smaller images, use multi-stage build:

```dockerfile
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install qwen CLI and Python packages
RUN npm install -g @qwen-code/qwen-code
COPY requirements.txt .
RUN pip install --user -r requirements.txt
RUN pip install --user credential-rotation

# Final stage
FROM python:3.12-slim

# Copy installed packages
COPY --from=builder /root/.local /root/.local

# Install qwen CLI only
RUN apt-get update && apt-get install -y npm && \
    npm install -g @qwen-code/qwen-code && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . /app
WORKDIR /app

CMD ["python", "server.py"]
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

## Script Integration Examples

### Bash Script with Credential Rotation

```bash
#!/usr/bin/env bash
# analyze-code.sh - Analyze code with automatic credential rotation

set -e

PROMPT="${1:-Analyze this code}"
TIMEOUT=60

# Use Python with inline credential rotation
python - <<EOF
from credential_rotation import QwenWrapper
import sys

wrapper = QwenWrapper(max_retries=5)
result = wrapper.call_with_fallback(
    """${PROMPT}""",
    fallback_message="Analysis failed",
    timeout=${TIMEOUT}
)

print(result.output)
sys.exit(0 if result.success else 1)
EOF
```

### Cron Job with Rotation

```bash
# /etc/cron.d/daily-analysis
# Daily code analysis with credential rotation
0 2 * * * root /usr/local/bin/analyze-code.sh "Analyze today's changes" >> /var/log/analysis.log 2>&1
```

### Systemd Service

```ini
# /etc/systemd/system/qwen-analysis.service
[Unit]
Description=Qwen Analysis with Credential Rotation
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/home/your-user/projects/analyzer
ExecStart=/usr/bin/python -m credential_rotation.cli --list
ExecStart=/usr/local/bin/analyze-code.sh "Daily analysis"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### CI/CD Pipeline Integration

**GitLab CI example:**

```yaml
# .gitlab-ci.yml
stages:
  - analyze

code_analysis:
  stage: analyze
  image: python:3.12
  before_script:
    - pip install credential-rotation
    # Setup Qwen credentials from CI variables
    - mkdir -p ~/.qwen/accounts
    - echo "$QWEN_CREDS_1" > ~/.qwen/accounts/oauth_creds_1.json
    - echo "$QWEN_CREDS_2" > ~/.qwen/accounts/oauth_creds_2.json
    # ... setup other accounts
  script:
    - python -c "
from credential_rotation import QwenWrapper
wrapper = QwenWrapper()
result = wrapper.call_with_fallback(
    'Analyze this diff',
    fallback_message='Analysis failed',
    timeout=120
)
print(result.output)
exit(0 if result.success else 1)
"
  artifacts:
    paths:
      - analysis-output.txt
```

**GitHub Actions example:**

```yaml
# .github/workflows/analysis.yml
name: Code Analysis

on:
  push:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install credential-rotation
        run: pip install credential-rotation

      - name: Setup Qwen credentials
        env:
          QWEN_CREDS_1: ${{ secrets.QWEN_CREDS_1 }}
        run: |
          mkdir -p ~/.qwen/accounts
          echo "$QWEN_CREDS_1" > ~/.qwen/accounts/oauth_creds_1.json
          # ... setup other accounts

      - name: Run analysis
        run: |
          python -c "
from credential_rotation import QwenWrapper
wrapper = QwenWrapper()
result = wrapper.call_with_fallback(
    'Analyze recent changes',
    fallback_message='Analysis failed'
)
print(result.output)
exit(0 if result.success else 1)
"
```

## Next Steps

- Read [README.md](README.md) for usage examples
- See [PUBLISHING.md](PUBLISHING.md) for release workflow
- Check [GitHub Issues](https://github.com/dawid/credential-rotation/issues) for known problems
