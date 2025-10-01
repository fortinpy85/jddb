# Testing Guide for JDDB

This document provides comprehensive information about the testing setup and practices for the Job Description Database (JDDB) application.

## Overview

The JDDB project implements a multi-layered testing approach:

- **Backend Unit Tests**: Python/pytest for individual components
- **Backend Integration Tests**: Full API endpoint testing with database
- **Frontend Unit Tests**: Bun/React Testing Library for components
- **End-to-End Tests**: Playwright for full user workflows
- **Accessibility Tests**: WCAG compliance and keyboard navigation
- **Performance Tests**: Load times and responsiveness

## Test Structure

```
├── backend/tests/           # Backend Python tests
│   ├── conftest.py         # Pytest fixtures and configuration
│   ├── unit/               # Unit tests for individual components
│   │   ├── test_content_processor.py
│   │   └── test_embedding_service.py
│   └── integration/        # Integration tests for API endpoints
│       └── test_jobs_api.py
├── src/                    # Frontend tests alongside source
│   ├── test-setup.ts       # Test configuration for Bun
│   ├── lib/
│   │   └── api.test.ts     # API client tests
│   └── components/
│       └── JobList.test.tsx # Component tests
└── tests/                  # E2E and cross-platform tests
    ├── utils/
    │   └── test-helpers.ts  # Shared test utilities
    ├── dashboard.spec.ts    # Dashboard functionality
    ├── jobs.spec.ts         # Job management features
    ├── upload.spec.ts       # File upload workflows
    ├── search.spec.ts       # Search functionality
    ├── compare.spec.ts      # Job comparison features
    └── accessibility-performance.spec.ts # A11y & performance
```

## Running Tests

### Backend Tests

```bash
# Change to backend directory
cd backend

# Run all tests
make test

# Run with coverage
pytest --cov=src/jd_ingestion tests/

# Run specific test file
pytest tests/unit/test_content_processor.py

# Run integration tests only
pytest -m integration
```

### Frontend Unit Tests

```bash
# Run all frontend unit tests
bun run test:unit

# Run with watch mode
bun run test:unit:watch

# Run with coverage
bun run test:unit:coverage

# Run specific test file
bun test src/lib/api.test.ts
```

### End-to-End Tests

```bash
# Run all E2E tests
bun test

# Run in headed mode (visible browser)
bun run test:headed

# Run with UI mode
bun run test:ui

# Run specific test file
npx playwright test tests/dashboard.spec.ts

# Run on specific browser
npx playwright test --project chromium
```

## Test Configuration

### Backend Configuration

**conftest.py**: Defines pytest fixtures for database sessions, test clients, and sample data.

Key fixtures:

- `async_session`: Async SQLAlchemy session for testing
- `async_client`: HTTP client for API testing
- `sample_job_data`: Mock job data for tests

### Frontend Configuration

**bunfig.toml**: Configures Bun test runner with coverage and preload settings.

**test-setup.ts**: Sets up testing environment with:

- DOM testing utilities
- Environment variable mocks
- Global mocks for browser APIs

### E2E Configuration

**playwright.config.ts**: Comprehensive Playwright setup with:

- Multiple browser configurations (Chrome, Firefox, Safari, Mobile)
- Test timeouts and retries
- Screenshot and video capture on failures
- Automated server startup

## Testing Patterns

### Backend Unit Tests

```python
def test_content_processor_extracts_sections():
    processor = ContentProcessor()
    content = "General Accountability: Test content..."

    result = processor.extract_sections(content)

    assert len(result.sections) == 1
    assert result.sections[0].type == "GENERAL_ACCOUNTABILITY"
```

### Frontend Unit Tests

```typescript
test('renders job list with data', async () => {
  render(<JobList />)

  await waitFor(() => {
    expect(screen.getByText('Director, Business Analysis')).toBeInTheDocument()
  })
})
```

### E2E Tests

```typescript
test("should complete job upload workflow", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "Upload" }).click();

  await uploadTestFile(page, "test-job.txt");
  await expect(page.locator("text=Upload successful")).toBeVisible();
});
```

## Test Data and Mocking

### Mock Data Factories

**test-helpers.ts** provides consistent mock data:

- `mockJobData`: Single job with full details
- `mockJobsList`: Collection of jobs for list views
- `mockSearchResults`: Search response data
- `mockStatsData`: Dashboard statistics

### API Mocking

E2E tests use Playwright's route interception:

```typescript
await mockApiResponse(page, "**/api/jobs/**", mockJobsList);
```

Backend tests use pytest fixtures with in-memory SQLite databases.

## Accessibility Testing

Automated accessibility tests check for:

- Proper heading hierarchy (h1 → h2 → h3)
- ARIA labels and roles
- Form field labeling
- Keyboard navigation support
- Color contrast (basic checks)
- Screen reader announcements

### Running Accessibility Tests

```bash
npx playwright test tests/accessibility-performance.spec.ts --grep "Accessibility"
```

## Performance Testing

Performance tests validate:

- Initial page load times (< 5 seconds)
- Large dataset handling (100+ items)
- Memory leak prevention during navigation
- Network error recovery
- Image optimization

### Running Performance Tests

```bash
npx playwright test tests/accessibility-performance.spec.ts --grep "Performance"
```

## Responsive Design Testing

Tests validate layouts across multiple viewports:

- Mobile: 375×667 (iPhone SE)
- Tablet: 768×1024 (iPad)
- Desktop: 1920×1080 (Large desktop)

### Testing Mobile Layouts

```bash
npx playwright test --project "Mobile Chrome"
```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run tests
        run: cd backend && pytest

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Bun
        uses: oven-sh/setup-bun@v1
      - name: Install dependencies
        run: bun install
      - name: Run unit tests
        run: bun run test:unit
      - name: Run E2E tests
        run: bun test
```

## Test Coverage Goals

- **Backend**: > 80% line coverage
- **Frontend**: > 75% component coverage
- **E2E**: Critical user paths covered
- **Accessibility**: WCAG 2.1 AA compliance

### Checking Coverage

```bash
# Backend coverage
cd backend && pytest --cov=src --cov-report=html

# Frontend coverage
bun run test:unit:coverage

# View HTML reports
open backend/htmlcov/index.html  # Backend
open coverage/index.html         # Frontend
```

## Best Practices

### Test Writing

1. **Arrange, Act, Assert**: Structure tests clearly
2. **Descriptive Names**: Test names should explain what they verify
3. **Single Responsibility**: One assertion per test when possible
4. **Mock External Dependencies**: Use fixtures and mocks consistently
5. **Clean Test Data**: Reset state between tests

### Test Organization

1. **Group Related Tests**: Use `describe` blocks effectively
2. **Shared Setup**: Use `beforeEach` for common initialization
3. **Test Isolation**: Tests should not depend on each other
4. **Fast Feedback**: Unit tests should run quickly

### Debugging Tests

1. **Use `--headed` flag**: See browser interactions in E2E tests
2. **Add `page.pause()`**: Stop execution to inspect state
3. **Screenshots**: Automatic on failure, manual with `page.screenshot()`
4. **Console Output**: Check `page.console.log` messages
5. **Network Inspection**: Monitor API calls with `page.route`

## Troubleshooting

### Common Issues

**Tests timing out**: Increase timeout in configuration or use `waitFor` helpers.

**Flaky E2E tests**: Add proper waits for loading states, use `waitForLoadState('networkidle')`.

**Database conflicts**: Ensure test isolation with proper cleanup in `conftest.py`.

**Mock conflicts**: Reset mocks between tests using `beforeEach` hooks.

### Getting Help

1. Check test output for specific error messages
2. Review browser console in E2E tests
3. Verify API responses match expected format
4. Ensure test data is properly mocked
5. Check that servers are running for E2E tests

## Extending Tests

### Adding New Test Files

1. **Backend**: Create in appropriate `backend/tests/` subdirectory
2. **Frontend**: Place alongside source files with `.test.ts` suffix
3. **E2E**: Add to `tests/` directory with `.spec.ts` suffix

### Creating Custom Fixtures

Backend (conftest.py):

```python
@pytest.fixture
async def custom_data():
    return {"key": "value"}
```

Frontend (test file):

```typescript
const mockCustomData = {
  key: "value",
};
```

This testing infrastructure ensures the JDDB application maintains high quality and reliability across all components and user interactions.
