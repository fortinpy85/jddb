# CI/CD Pipeline Documentation

Continuous Integration and Continuous Deployment automation for the JDDB system.

## GitHub Actions Workflows

### Build & Test Workflow
**File**: `.github/workflows/test.yml`

```yaml
Triggers:
  - Pull requests to main/develop
  - Push to main/develop

Jobs:
  1. Backend Tests (pytest, mypy, ruff)
  2. Frontend Tests (bun test, type-check)
  3. E2E Tests (Playwright)
  4. Security Scan (Snyk)
```

### Deploy to Staging
**File**: `.github/workflows/deploy-staging.yml`

```yaml
Trigger: Push to develop branch

Steps:
  1. Build Docker images
  2. Run database migrations
  3. Deploy to staging environment
  4. Run smoke tests
  5. Notify team
```

### Deploy to Production
**File**: `.github/workflows/deploy-production.yml`

```yaml
Trigger: Manual approval (Release)

Steps:
  1. Create backup
  2. Build production images
  3. Run database migrations
  4. Blue-green deployment
  5. Health checks
  6. Switch traffic
  7. Rollback on failure
```

## Pipeline Stages

### 1. Code Quality
- Linting (ruff, eslint)
- Type checking (mypy, TypeScript)
- Code formatting (black, prettier)
- Security scanning (detect-secrets, Snyk)

### 2. Testing
- Unit tests (pytest, bun test)
- Integration tests
- E2E tests (Playwright)
- Performance tests

### 3. Build
- Docker image building
- Multi-stage builds for optimization
- Image scanning (Trivy)
- Push to registry

### 4. Deploy
- Database migrations (Alembic)
- Application deployment
- Configuration updates
- Health checks

### 5. Verify
- Smoke tests
- Integration tests on deployed environment
- Performance baselines
- Alert configuration

## Secrets Management

### Required Secrets
- `DATABASE_URL` - Production database connection
- `OPENAI_API_KEY` - OpenAI API credentials
- `SECRET_KEY` - Application secret
- `DOCKER_REGISTRY_TOKEN` - Container registry access
- `SSH_PRIVATE_KEY` - Deployment server access

### Secret Rotation
- Automated rotation every 90 days
- Manual rotation on security incidents
- Audit trail in GitHub Actions logs

## Rollback Procedures

### Automatic Rollback
```bash
# Failed health checks trigger automatic rollback
- Health check failures > 3
- Error rate > 5%
- Response time > 2s
```

### Manual Rollback
```bash
# Rollback to previous version
gh workflow run rollback.yml --ref main \
  -f version=previous
```

## Monitoring & Notifications

### Slack Notifications
- Build failures
- Deployment start/complete
- Test failures
- Security vulnerabilities

### Metrics Collection
- Build duration
- Test coverage
- Deployment frequency
- Mean time to recovery (MTTR)

## Best Practices

1. **Always review PR checks before merging**
2. **Run full test suite on staging before production**
3. **Create database backup before deployment**
4. **Monitor alerts for 1 hour after deployment**
5. **Document rollback steps in release notes**

---

*Last Updated: September 30, 2025*
