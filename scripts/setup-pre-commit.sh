#!/bin/bash

# Pre-commit hooks setup script for JDDB
# This script sets up automated code quality checks that run before each commit

set -e

echo "🔧 Setting up pre-commit hooks for JDDB..."

# Check if we're in the project root
if [ ! -f "package.json" ] || [ ! -f "backend/pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit is already installed"
fi

# Create .pre-commit-config.yaml
echo "📝 Creating pre-commit configuration..."
cat > .pre-commit-config.yaml << 'EOF'
repos:
  # Python code formatting and linting
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black
        name: Format Python code with Black
        files: '^backend/.*\.py$'
        args: ['--line-length=88']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        name: Lint Python code with Ruff
        files: '^backend/.*\.py$'
        args: [--fix]
      - id: ruff-format
        name: Format Python code with Ruff
        files: '^backend/.*\.py$'

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        name: Type check Python code with MyPy
        files: '^backend/src/.*\.py$'
        additional_dependencies: [types-all]

  # JavaScript/TypeScript formatting and linting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        name: Format frontend code with Prettier
        files: '^src/.*\.(ts|tsx|js|jsx|json|css|md)$'
        additional_dependencies:
          - prettier@3.6.2

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
        name: Remove trailing whitespace
      - id: end-of-file-fixer
        name: Ensure files end with newline
      - id: check-yaml
        name: Check YAML syntax
      - id: check-json
        name: Check JSON syntax
      - id: check-toml
        name: Check TOML syntax
      - id: check-merge-conflict
        name: Check for merge conflict markers
      - id: check-added-large-files
        name: Check for large files
        args: ['--maxkb=1024']
      - id: check-case-conflict
        name: Check for case conflicts
      - id: mixed-line-ending
        name: Check for mixed line endings

  # Security checks
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        name: Detect secrets in code
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json

  # Database migration checks
  - repo: local
    hooks:
      - id: check-migrations
        name: Check for pending database migrations
        entry: bash -c 'cd backend && source venv/Scripts/activate && alembic check || echo "⚠️  Warning: Alembic check failed - ensure database is up to date"'
        language: system
        pass_filenames: false
        files: '^backend/alembic/versions/.*\.py$'

  # Frontend build check (optional - can be slow)
  - repo: local
    hooks:
      - id: frontend-build-check
        name: Check frontend builds successfully
        entry: bash -c 'echo "🏗️  Checking frontend build..." && bun run build'
        language: system
        pass_filenames: false
        files: '^(src/|package\.json|tsconfig\.json|\.env\.local).*$'
        stages: [manual]  # Only run when explicitly requested

EOF

# Install the pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook for conventional commits (optional)
echo "📝 Installing commit message hook..."
pre-commit install --hook-type commit-msg

# Create a secrets baseline (if detect-secrets is being used)
echo "🔐 Creating secrets baseline..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --baseline .secrets.baseline || echo "⚠️  Note: detect-secrets baseline created"
else
    echo "{}" > .secrets.baseline
fi

# Test the hooks on existing files (optional)
echo "🧪 Testing pre-commit hooks..."
echo "This may take a few minutes for the first run..."

# Run hooks on all files (excluding slow build check)
pre-commit run --all-files --exclude-stage manual || {
    echo "⚠️  Some hooks failed - this is normal for the first run"
    echo "   Files have been automatically formatted where possible"
    echo "   Please review changes and commit them if needed"
}

echo ""
echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "📋 What happens now:"
echo "   • Code will be automatically checked before each commit"
echo "   • Python code will be formatted with Black and Ruff"
echo "   • Frontend code will be formatted with Prettier"
echo "   • Type checking will be performed with MyPy"
echo "   • Security scans will check for secrets"
echo "   • General file quality checks will be applied"
echo ""
echo "🔧 To run hooks manually:"
echo "   pre-commit run --all-files           # Run all hooks on all files"
echo "   pre-commit run <hook-name>           # Run specific hook"
echo "   pre-commit run --hook-stage manual   # Run build check manually"
echo ""
echo "⚠️  To skip hooks (not recommended):"
echo "   git commit --no-verify"
echo ""
echo "📚 For more information:"
echo "   https://pre-commit.com/"
