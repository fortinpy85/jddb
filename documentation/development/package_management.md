# Package Management Guide

This document outlines the package management strategy for the JDDB project, covering both frontend (JavaScript/TypeScript) and backend (Python) dependencies.

## Frontend Package Management (Bun)

The frontend of the JDDB project uses **Bun** as its primary package manager. Bun is a fast, all-in-one JavaScript runtime, bundler, and package manager.

### Installation

If you don't have Bun installed, you can install it globally using npm (which is typically pre-installed with Node.js):

```bash
npm install -g bun
```

### Common Commands

- **Install dependencies:**
  ```bash
bun install
  ```

- **Add a new dependency:**
  ```bash
bun add <package-name>
  ```

- **Add a new development dependency:**
  ```bash
bun add -d <package-name>
  ```

- **Run a script defined in `package.json`:**
  ```bash
bun run <script-name>
  ```

- **Run a local executable (e.g., `bunx` equivalent):**
  ```bash
bun <executable-name>
  ```

- **Upgrade all dependencies:**
  ```bash
bun update
  ```

- **Remove a dependency:**
  ```bash
bun remove <package-name>
  ```

### Lockfile

Bun uses `bun.lock` to ensure reproducible installations. This file should be committed to version control.

## Backend Package Management (Poetry)

The backend of the JDDB project uses **Poetry** for managing Python dependencies and virtual environments. Poetry provides a robust and reproducible way to handle Python projects.

### Installation

If you don't have Poetry installed, you can install it using pip:

```bash
pip install poetry
```

### Configuration (Python Version)

Ensure Poetry is configured to use a compatible Python version (currently Python 3.9 to 3.12 due to `spacy` compatibility):

```bash
# Replace C:\Python\Python312\python.exe with the actual path to your Python 3.12 executable
poetry env use C:\Python\Python312\python.exe
```

### Common Commands

- **Install dependencies:**
  Navigate to the `backend` directory and run:
  ```bash
cd backend
poetry install
  ```

- **Add a new dependency:**
  ```bash
poetry add <package-name>
  ```

- **Add a new development dependency:**
  ```bash
poetry add --group dev <package-name>
  ```

- **Run a script or command within the Poetry environment:**
  ```bash
poetry run <command>
# Example: poetry run pytest
# Example: poetry run python scripts/dev_server.py
  ```

- **Update dependencies:**
  ```bash
poetry update
  ```

- **Remove a dependency:**
  ```bash
poetry remove <package-name>
  ```

### Lockfile

Poetry uses `poetry.lock` to ensure reproducible installations. This file should be committed to version control.

### Handling `spacy` and `spacy-transformers`

Currently, there are known compatibility issues with `spacy` and `spacy-transformers` when using Poetry with Python 3.13. If you encounter issues, ensure you are using Python 3.12 or earlier. If the problem persists, you may need to install these specific packages using `pip` directly within the Poetry virtual environment after `poetry install`:

```bash
poetry run pip install spacy==3.8.7 spacy-transformers==1.3.9
```

This guide will be updated as compatibility issues are resolved or new best practices emerge.
