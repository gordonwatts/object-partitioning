# Dev Container Setup

This directory contains the development container configuration for the atlas-object-partitioning project.

## Features

- **Python 3.13** - Latest Python version
- **Node.js 22+** - Modern Node.js with npm
- **@openai/codex** - Installed globally via npm
- **Non-root user** - Runs as `vscode` user for better security
- **Persistent pip cache** - Docker volume for faster package installations
- **ServiceX credentials** - Mounted read-only from workspace root

## Prerequisites

- Docker Desktop or Docker Engine installed
- VS Code with the Dev Containers extension
- `servicex.yaml` file in the workspace root (for ServiceX authentication)

## Getting Started

1. Open the project in VS Code
2. Press `F1` and select `Dev Containers: Reopen in Container`
3. VS Code will build the container and install dependencies
4. Wait for the `postCreateCommand` to complete (installs Python packages)

## What Gets Installed

### System Packages

- curl, ca-certificates, gnupg, git
- sudo (for non-root user access)

### Node.js Packages

- @openai/codex (global installation)

### Python Packages

All dependencies from `pyproject.toml` including:

- Production: typer, func_adl_servicex_xaodr25, servicex_analysis_utils, jinja2, pyarrow, hist
- Test/Dev: pytest, pytest-cov, flake8, black, coverage

## Configuration Details

### Mounted Volumes

- **servicex.yaml**: Read-only bind mount from workspace root to `/workspace/servicex.yaml`
- **pip cache**: Named Docker volume `atlas-object-partitioning-pip-cache` mounted at `/home/vscode/.cache/pip`

### VS Code Settings

- Python interpreter: `/usr/local/bin/python`
- Formatter: Black (line length 99)
- Linter: Flake8 (max line length 99)
- Testing: pytest enabled

### Commands

After the container starts, you can use:

```bash
# Run the CLI
atlas-object-partitioning --help

# Run tests
pytest

# Format code
black src tests

# Lint code
flake8 src tests

# Check installed packages
pip list
```

## Rebuilding the Container

If you modify the Dockerfile or devcontainer.json:

1. Press `F1`
2. Select `Dev Containers: Rebuild Container`

## Troubleshooting

### servicex.yaml not found

Ensure `servicex.yaml` exists in the workspace root. If it's located elsewhere, update the mount path in `devcontainer.json`:

```json
"mounts": [
  "source=/path/to/servicex.yaml,target=/workspace/servicex.yaml,type=bind,readonly",
  ...
]
```

### PATH issues

If commands like `pytest` or `atlas-object-partitioning` aren't found, ensure `/home/vscode/.local/bin` is in PATH. This is set in the Dockerfile but you can verify with:

```bash
echo $PATH
```

### Permission issues

The container runs as the `vscode` user (UID 1000) to avoid Windows file permission issues. If you encounter permission errors, ensure your Windows user can read/write the workspace directory.

## Manual Docker Build

To build and test the image manually without VS Code:

```powershell
# Build the image
docker build -f .devcontainer/Dockerfile -t atlas-object-partitioning-dev .

# Run with mounted workspace
docker run --rm -v "${PWD}:/workspace" -w /workspace atlas-object-partitioning-dev bash

# Test CLI
docker run --rm -v "${PWD}:/workspace" -w /workspace atlas-object-partitioning-dev \
  bash -c "pip install --user -e '.[test]' && atlas-object-partitioning --help"
```
