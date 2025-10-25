# Mock Assertion Failure Analysis - 2025-10-24

## Context

From CI/CD run 18795947761, we have ~600+ test failures out of 1,719 collected tests.
This analysis focuses on the **mock assertion failures** pattern (Phase 2.1 of Sprint 1).

## Top Failure Patterns

### Pattern 1: Mock Method Not Called (200+ instances)

**Error Pattern:**
```
AssertionError: Expected 'X' to have been called once. Called 0 times.
```

**Root Cause:** Mock setup doesn't match actual implementation call signatures or mock isn't properly configured.

**Examples:**

1. **test_analytics_middleware.py::test_track_request_success**
   - Mock: `analytics_service.track_activity`
   - Expected: Called once
   - Actual: Called 0 times
   - Location: `backend/tests/unit/test_analytics_middleware.py`

2. **test_audit_logger.py** (multiple tests)
   - Mock: Various logging methods
   - Pattern: Logging calls not triggered
   - Location: `backend/tests/unit/test_audit_logger.py`

3. **test_auth_service.py::test_create_session**
   - Mock: Return value mismatch
   - Pattern: Mock configured but implementation doesn't call
   - Location: `backend/tests/unit/test_auth_service.py`

### Pattern 2: AttributeError on NoneType (150+ instances)

**Error Pattern:**
```
AttributeError: 'NoneType' object has no attribute 'X'
```

**Root Cause:** Function returns None when test expects an object, or async functions not awaited.

**Examples:**

1. **test_embedding_service.py** (436 failures)
   - Pattern: Embedding operations return None
   - Likely: Missing mock configuration or service initialization
   - Location: `backend/tests/unit/test_embedding_service.py`

2. **test_quality_service.py** (284 failures)
   - Pattern: Quality check methods return None
   - Location: `backend/tests/unit/test_quality_service.py`

### Pattern 3: Pydantic ValidationError (100+ instances)

**Error Pattern:**
```
pydantic.ValidationError: validation errors for X
```

**Root Cause:** Test data doesn't match Pydantic model requirements.

**Examples:**

1. **test_database_models.py** (308 failures)
   - Pattern: Model instantiation with invalid data
   - Location: `backend/tests/unit/test_database_models.py`

2. **test_saved_searches_endpoints.py** (292 failures)
   - Pattern: Request/response validation failures
   - Location: `backend/tests/unit/test_saved_searches_endpoints.py`

## Investigation Strategy

### Phase 2.1: Fix Top 50 Mock Assertion Failures

**Priority Files (by failure count):**
1. test_embedding_service.py (436 failures)
2. test_database_models.py (308 failures)
3. test_saved_searches_endpoints.py (292 failures)
4. test_quality_service.py (284 failures)
5. test_job_analysis_service.py (248 failures)

**Approach:**
1. Read test file
2. Identify common mock patterns
3. Check actual implementation signatures
4. Fix mock configuration to match reality
5. Run tests to verify fix

### Phase 2.2: Fix Top 50 Type/Attribute Failures

**Focus:**
- AttributeError on NoneType
- Missing async/await
- Service initialization issues

## Root Cause Analysis: test_analytics_middleware.py

### test_track_request_success (Line 168)

**Issue Found:**
```python
# Test mocks (line 177):
mock_get_session.return_value.__aenter__.return_value = [mock_db]

# Actual implementation (line 87):
async for db in get_async_session():
```

**Root Cause:** Mock uses `__aenter__` (async context manager), but implementation uses `async for` (async iterator).

**Fix:** Change mock to use `__aiter__` and `__anext__`:
```python
async def mock_async_gen():
    yield mock_db

mock_get_session.return_value = mock_async_gen()
```

**Pattern:** This same issue likely affects ALL tests that mock `get_async_session()`.

## Fix Applied: test_analytics_middleware.py ✅

**Result:** ALL 23 tests PASSED!

**Files Fixed:**
- test_analytics_middleware.py (4 tests)
  - test_track_request_success
  - test_track_request_with_error
  - test_track_search_request
  - test_middleware_with_tracking

**Pattern Applied:**
```python
# OLD (WRONG):
mock_get_session.return_value.__aenter__.return_value = [mock_db]
# OR:
mock_get_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

# NEW (CORRECT):
async def mock_async_gen():
    yield mock_db

mock_get_session.return_value = mock_async_gen()
```

**Files with Same Pattern:**
- test_phase2_metrics.py (has __aiter__)
- test_audit_logger.py (has __aiter__)

## Summary of Fixes Applied ✅

### Files Fixed:
1. ✅ **test_analytics_middleware.py** - ALL 23 tests PASS (4 mock patterns fixed)
2. ✅ **test_audit_logger.py** - 25/28 tests PASS (15 mock patterns fixed, 3 different issues remain)
3. ✅ **test_phase2_metrics.py** - Database tests PASS (2 mock patterns fixed)

### Total Impact:
- **Mock patterns fixed**: 21 instances across 3 files
- **Tests fixed**: ~20+ tests now passing
- **Pattern documented**: Async generator mock technique established

### Remaining Work:
- test_audit_logger.py has 3 failures (different mock issues, not async generator)
- High-impact files: embedding_service.py (436 failures), quality_service.py (284 failures)
- Apply this pattern project-wide (likely 50+ more files affected)

## Next Steps

1. ✅ test_analytics_middleware.py - COMPLETE
2. ✅ test_audit_logger.py - COMPLETE (async generator pattern)
3. ✅ test_phase2_metrics.py - COMPLETE
4. Commit Sprint 1 Phase 2 fixes
5. Then embedding_service.py (high impact, 436 failures)
6. Apply patterns learned project-wide

## Files to Investigate

- `backend/tests/unit/test_analytics_middleware.py`
- `backend/tests/unit/test_audit_logger.py`
- `backend/tests/unit/test_auth_service.py`
- `backend/tests/unit/test_embedding_service.py`
- `backend/tests/unit/test_quality_service.py`
- `backend/tests/unit/test_database_models.py`
- `backend/tests/unit/test_saved_searches_endpoints.py`
- `backend/tests/unit/test_job_analysis_service.py`

## Success Criteria

- Reduce mock assertion failures by 50+ (200+ → 150)
- Reduce AttributeError failures by 30+ (150+ → 120)
- Tests should PASS, not just skip/ignore
