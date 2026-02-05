# Publishing Guide

This guide covers how to publish the `credential-rotation` package to PyPI and GitHub.

## Prerequisites

1. **PyPI Account:** Create an account at https://pypi.org/account/register/
2. **API Token:** Create an API token at https://pypi.org/manage/account/token/
3. **GitHub Repository:** Create a new repository at https://github.com/new
4. **Install Tools:**
   ```bash
   pip install build twine hatchling
   ```

## Version Management

### Bump Version

1. Update version in `pyproject.toml`:
   ```toml
   [project]
   name = "credential-rotation"
   version = "0.2.0"  # Update this
   ```

2. Update version in `src/credential_rotation/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

3. Commit the changes:
   ```bash
   git add pyproject.toml src/credential_rotation/__init__.py
   git commit -m "chore: bump version to 0.2.0"
   ```

## Publishing to PyPI

### 1. Clean Previous Builds
```bash
rm -rf dist/ build/ *.egg-info
```

### 2. Build the Package
```bash
python -m build
```

This creates:
- `dist/credential_rotation-0.1.0-py3-none-any.whl` (wheel)
- `dist/credential-rotation-0.1.0.tar.gz` (source)

### 3. Check the Package
```bash
twine check dist/*
```

### 4. Upload to TestPyPI (Optional)
First, register at https://test.pypi.org/account/register/

```bash
twine upload --repository testpypi dist/*
```

Install from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ credential-rotation
```

### 5. Upload to PyPI
```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: `pypi-...` (your API token)

### 6. Verify
Visit https://pypi.org/project/credential-rotation/

## Publishing to GitHub

### 1. Add Remote (first time only)
```bash
git remote add origin https://github.com/dawid/credential-rotation.git
```

### 2. Push to GitHub
```bash
git push -u origin main
```

### 3. Create Release
1. Go to https://github.com/dawid/credential-rotation/releases
2. Click "Draft a new release"
3. Tag version: `v0.1.0`
4. Release title: `v0.1.0 - Initial Release`
5. Describe changes
6. Click "Publish release"

## Complete Release Workflow

```bash
# 1. Bump version
vim pyproject.toml
vim src/credential_rotation/__init__.py

# 2. Commit changes
git add -A
git commit -m "chore: bump version to 0.2.0"

# 3. Create git tag
git tag v0.2.0
git push origin main --tags

# 4. Build package
rm -rf dist/ build/ *.egg-info
python -m build

# 5. Upload to PyPI
twine upload dist/*

# 6. Create GitHub release
# Go to https://github.com/dawid/credential-rotation/releases/new
# Tag: v0.2.0 (will be pre-selected)
```

## Post-Release Checklist

- [ ] Verify package installs from PyPI: `pip install credential-rotation`
- [ ] Verify CLI command works: `account-qwen --version`
- [ ] Update GitHub Releases page
- [ ] Update CHANGELOG.md (if exists)

## Troubleshooting

### "File already exists" error
You're trying to upload a version that already exists. Bump the version number.

### "Invalid or non-existent authentication information"
Your ~/.pypirc is misconfigured or token is expired. Use API token instead:
```bash
twine upload dist/* --username __token__ --password pypi-...
```

### "403 Forbidden" from PyPI
The package name is already taken. Choose a different name or contact the owner.

### Build fails with "module not found"
Make sure you're using hatchling as build backend:
```bash
pip install hatchling
```

## Continuous Deployment (Optional)

### GitHub Actions Workflow

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: read
  id-token: write

jobs:
  pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

Set `PYPI_API_TOKEN` in GitHub repository secrets.

## Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (0.x.x → 1.0.0): Breaking changes
- **MINOR** (0.1.x → 0.2.0): New features (backward compatible)
- **PATCH** (0.1.0 → 0.1.1): Bug fixes

Example:
```
0.1.0 → 0.1.1  # Bug fix
0.1.1 → 0.2.0  # Add OpenAI support
0.2.0 → 1.0.0  # Breaking API change
```
