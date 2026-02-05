# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dynamic account discovery: `AccountManager` now scans `~/.qwen/accounts/` for available credentials instead of using a fixed count.
- Non-sequential rotation support: System can now rotate between accounts with gaps in IDs (e.g., 1, 3, 5).
- CLI command `--add`: Interactively add a single new account to the rotation.
- CLI command `--remove <index>`: Safely remove a specific account.
- Docker Service PoC: Comprehensive example in `examples/docker-service-poc` demonstrating "Qwen-as-a-Service" architecture with Podman support.
- Centralization Guide: `CENTRALIZATION_GUIDE.md` detailing strategies for microservices integration.

### Changed
- Refactored `AccountManager` to use relative symlinks for portable host/container compatibility.
- Updated `switch_next` logic to use available IDs list instead of modular arithmetic on fixed range.
- `setup_accounts` is now idempotent and aware of existing accounts.

### Fixed
- Fixed permission issues in Docker/Podman by implementing SELinux-compatible volume mounts (`:Z`).
