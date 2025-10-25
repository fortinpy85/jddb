# CI/CD Pipeline Fix Strategy - 2025-10-24

## Current Status

**Pipeline Run**: 18793947322 (commit 88dd992f)
**Status**: ❌ FAILED
**Time**: October 24, 2025 22:45 UTC

## Root Cause #1: Ruff Version Mismatch (CRITICAL)

**Problem**: Pre-commit uses Ruff v0.6.9, Poetry uses Ruff v0.13.1 - different formatting

**Evidence**:
- `.pre-commit-config.yaml`: `rev: v0.6.9`
- `backend/pyproject.toml`: `ruff = "^0.13.1"`
- 8 test files reformatted locally → CI/CD says need reformatting → endless loop

**Impact**: ALL backend test jobs fail at "Run linting" (Python 3.9, 3.10, 3.11, 3.12)

**Fix**: Update .pre-commit-config.yaml to v0.13.1

## Root Cause #2: Frontend TypeScript Errors

**Problem**: 8 TypeScript compilation errors across 6 files

**Errors**:
1. unified-dev-server.ts - Missing @types/bun, parameter type annotations (4 errors)
2. vite.config.ts - Invalid 'compress' in TerserOptions (1 error)
3. AIJobWriter.tsx - Type assertion needed (1 error)
4. SectionEditor.test.tsx - HTMLElement cast needed (1 error)
5. compare.spec.ts - Null check needed (1 error)

**Fix**: Install @types/bun and fix type errors in each file

## Root Cause #3: Performance Test Import Error

**Problem**: `ModuleNotFoundError: No module named 'src'` in seed_performance_data.py

**Fix**: Change imports from `src.jd_ingestion` to `jd_ingestion`

## Fix Order

### 1. Ruff Version Alignment (15 minutes)
```bash
# Edit .pre-commit-config.yaml: change v0.6.9 to v0.13.1
cd backend
poetry run pre-commit autoupdate
poetry run pre-commit clean
poetry run pre-commit run --all-files
cd ..
git add .pre-commit-config.yaml backend/tests/
git commit -m "fix: align Ruff to v0.13.1"
git push
```

### 2. Frontend TypeScript (30 minutes)
```bash
npm install --save-dev @types/bun
# Fix 6 TypeScript files
bunx tsc --noEmit  # verify
git add src/ tests/ unified-dev-server.ts vite.config.ts package*.json
git commit -m "fix: resolve 8 TypeScript errors"
git push
```

### 3. Performance Test (10 minutes)
```bash
# Fix backend/scripts/seed_performance_data.py imports
git add backend/scripts/seed_performance_data.py
git commit -m "fix: correct module imports in seed script"
git push
```

## Expected Result

✅ All backend tests pass (4 Python versions)
✅ Frontend tests pass type checking
✅ Performance tests complete
✅ Full CI/CD pipeline green
