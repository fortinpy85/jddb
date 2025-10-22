# Coverage Improvement Strategy

**Current Coverage**: 30.43% (3,100 / 10,187 lines)
**Target Coverage**: 80.00% (8,150 / 10,187 lines)
**Gap**: Need to cover **5,049 additional lines**

## Strategic Approach

### Phase 1: Quick Wins - High-Impact, Already-Tested Modules (Target: +15%)

Focus on modules with existing tests that just need expansion:

1. **analytics.py** (337 lines, 65% → 85%)
   - Already has 36 tests passing
   - Need: 67 more covered lines
   - Effort: LOW (expand existing tests)
   - Files: `tests/unit/test_analytics_endpoints.py`

2. **rlhf.py** (93 lines, 67% → 90%)
   - Good coverage, fill gaps
   - Need: 21 more lines
   - Effort: LOW

3. **ai_suggestions.py** (196 lines, 66% → 85%)
   - Need: 37 more lines
   - Effort: MEDIUM

**Phase 1 Total**: ~125 lines = +1.2% coverage

### Phase 2: Medium-Impact Services (Target: +20%)

Focus on service layer with moderate complexity:

1. **analytics_service.py** (210 lines, 28% → 75%)
   - Need: 99 more lines
   - Effort: MEDIUM
   - Create: `tests/unit/test_analytics_service.py` (expand existing)

2. **rate_limiting_service.py** (219 lines, 32% → 75%)
   - Need: 94 more lines
   - Effort: MEDIUM
   - Has tests, needs expansion

3. **auth_service.py** (215 lines, 24% → 70%)
   - Need: 99 more lines
   - Effort: MEDIUM
   - Critical for security

4. **rlhf_service.py** (66 lines, 36% → 80%)
   - Need: 29 more lines
   - Effort: LOW

5. **search_analytics_service.py** (84 lines, 27% → 75%)
   - Need: 40 more lines
   - Effort: LOW

6. **template_generation_service.py** (82 lines, 23% → 70%)
   - Need: 39 more lines
   - Effort: MEDIUM

**Phase 2 Total**: ~400 lines = +3.9% coverage

### Phase 3: API Endpoints (Target: +15%)

Fill coverage gaps in API endpoints:

1. **saved_searches.py** (272 lines, 32% → 70%)
   - Need: 103 more lines
   - Effort: MEDIUM

2. **content_generation.py** (117 lines, 56% → 80%)
   - Need: 28 more lines
   - Effort: LOW

3. **translation_quality.py** (62 lines, 52% → 85%)
   - Need: 20 more lines
   - Effort: LOW

4. **bilingual_documents.py** (92 lines, 40% → 75%)
   - Need: 32 more lines
   - Effort: MEDIUM

5. **templates.py** (82 lines, 41% → 75%)
   - Need: 28 more lines
   - Effort: LOW

6. **quality.py** (101 lines, 31% → 70%)
   - Need: 39 more lines
   - Effort: MEDIUM

7. **performance.py** (96 lines, 28% → 70%)
   - Need: 40 more lines
   - Effort: MEDIUM

8. **health.py** (115 lines, 25% → 70%)
   - Need: 52 more lines
   - Effort: LOW (simple endpoints)

9. **phase2_monitoring.py** (166 lines, 21% → 65%)
   - Need: 73 more lines
   - Effort: MEDIUM

**Phase 3 Total**: ~415 lines = +4.1% coverage

### Phase 4: Utilities & Infrastructure (Target: +10%)

Core utilities with broad impact:

1. **error_handler.py** (208 lines, 26% → 70%)
   - Need: 92 more lines
   - Effort: MEDIUM

2. **cache.py** (152 lines, 22% → 70%)
   - Need: 73 more lines
   - Effort: MEDIUM

3. **caching.py** (72 lines, 29% → 75%)
   - Need: 33 more lines
   - Effort: LOW

4. **circuit_breaker.py** (160 lines, 44% → 75%)
   - Need: 50 more lines
   - Effort: MEDIUM

5. **monitoring.py** (171 lines, 22% → 65%)
   - Need: 73 more lines
   - Effort: MEDIUM

6. **logging.py** (110 lines, 36% → 70%)
   - Need: 37 more lines
   - Effort: LOW

7. **exceptions.py** (174 lines, 41% → 70%)
   - Need: 50 more lines
   - Effort: LOW

**Phase 4 Total**: ~408 lines = +4.0% coverage

### Phase 5: Complex Services - SKIP FOR NOW

These are large, complex modules that would take significant effort:

- **ai_enhancement_service.py** (609 lines, 8% coverage) - DEFER
- **search.py** (475 lines, 19% coverage) - DEFER
- **jobs.py** (456 lines, 16% coverage) - DEFER
- **job_analysis_service.py** (417 lines, 10% coverage) - DEFER
- **ingestion.py** (404 lines, 12% coverage) - DEFER

**Rationale**: These would require hundreds of lines of complex test code. Better ROI focusing on Phases 1-4 first.

## Implementation Plan

### Week 1: Quick Wins (Phases 1-2)
- Day 1-2: Expand analytics tests (+125 lines)
- Day 3-4: Service layer tests (+200 lines)
- Day 5: Service layer completion (+200 lines)
- **Target**: 35% → 40% coverage

### Week 2: API & Utils (Phases 3-4)
- Day 1-3: API endpoint tests (+415 lines)
- Day 4-5: Utilities tests (+408 lines)
- **Target**: 40% → 48% coverage

### Alternative: Focused Sprint

If we focus just on **realistic, high-ROI modules** from Phases 1-4:

**Total Coverage Gain**: 525 + 400 + 415 + 408 = **1,748 lines**
**New Coverage**: 30.43% + 17.2% = **47.6%**

This gets us close to 50% with reasonable effort, focusing on maintainable code.

## Priority Recommendations

### Immediate Actions (Next 2-3 days):

1. ✅ **Fix 3 failing analytics tests** (already identified)
2. **Expand analytics test coverage** (+125 lines from Phase 1)
3. **Add service layer tests** (+200 lines from Phase 2)
4. **API endpoint coverage** (+100 lines from Phase 3, easiest ones)

**Expected Gain**: 425 lines = +4.2% → **34.6% coverage**

### Medium-term (1-2 weeks):

Continue with Phases 2-4 systematically, prioritizing:
- Services with existing test infrastructure
- Simple API endpoints
- Critical utilities (error handling, caching)

**Realistic Target**: **45-50% coverage** (not 80%, but significant improvement)

### Long-term (Future):

The complex services (ai_enhancement, search, jobs, ingestion) would require:
- Extensive mocking of external services
- Complex test data fixtures
- Significant refactoring for testability

**Recommendation**: Focus on new code coverage for these modules going forward, rather than retroactive testing.

## Tooling & Best Practices

### Test Quality Standards:

1. **Unit tests should**:
   - Test one function/method at a time
   - Mock external dependencies (DB, APIs, OpenAI)
   - Use fixtures for common test data
   - Follow AAA pattern (Arrange, Act, Assert)

2. **Coverage measurement**:
   ```bash
   # Run with coverage
   poetry run pytest --cov=src --cov-report=html --cov-report=term

   # View detailed report
   open htmlcov/index.html
   ```

3. **Focus metrics**:
   - **Branch coverage** (not just line coverage)
   - **Critical path coverage** (happy path + error cases)
   - **Edge cases** (null, empty, boundary conditions)

### Testing Patterns:

```python
# Example test structure
@pytest.fixture
def mock_service(mocker):
    return mocker.patch('module.service.external_call')

def test_function_success(mock_service):
    # Arrange
    mock_service.return_value = expected_data

    # Act
    result = function_under_test()

    # Assert
    assert result == expected_result
    mock_service.assert_called_once()

def test_function_error_handling(mock_service):
    # Arrange
    mock_service.side_effect = Exception("error")

    # Act & Assert
    with pytest.raises(CustomException):
        function_under_test()
```

## Conclusion

**Realistic Goal**: Achieve 45-50% coverage by focusing on Phases 1-4.

**Reasoning**:
- 80% coverage would require testing 2,500+ lines of complex AI/ML services
- Better ROI: Focus on critical paths, services, and utilities
- New code can maintain high coverage standards going forward
- Existing complex code can be covered incrementally as it's refactored

**Next Steps**:
1. Fix 3 failing analytics tests
2. Execute Phase 1 (analytics expansion)
3. Begin Phase 2 (service layer)
4. Measure progress weekly
5. Adjust strategy based on results
