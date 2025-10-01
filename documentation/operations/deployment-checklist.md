# Deployment Checklist

Pre-deployment and post-deployment verification checklist for JDDB.

## Pre-Deployment

### Code & Tests
- [ ] All PR reviews completed and approved
- [ ] All tests passing (backend, frontend, E2E)
- [ ] No linting or type errors
- [ ] Security scans clean (Snyk, detect-secrets)
- [ ] Code coverage maintained or improved

### Database
- [ ] Database backup created and verified
- [ ] Migrations tested on staging environment
- [ ] Migration rollback plan documented
- [ ] No breaking schema changes (or properly versioned)

### Configuration
- [ ] Environment variables updated
- [ ] Secrets rotated if needed
- [ ] Feature flags configured
- [ ] Rate limits reviewed

### Documentation
- [ ] CHANGELOG updated
- [ ] API documentation current
- [ ] Deployment notes prepared
- [ ] Rollback procedure documented

## Deployment Steps

### 1. Pre-Deployment Communication
- [ ] Notify team of deployment window
- [ ] Post deployment notice in channels
- [ ] Confirm on-call engineer availability

### 2. Database Migration
```bash
# Run migrations
cd backend && poetry run alembic upgrade head

# Verify migrations
poetry run alembic current
```

### 3. Application Deployment
```bash
# Deploy backend
docker-compose up -d backend

# Deploy frontend
docker-compose up -d frontend

# Or use Kubernetes
kubectl apply -f k8s/
```

### 4. Health Checks
- [ ] API health endpoint responding
- [ ] Database connections healthy
- [ ] WebSocket connections working
- [ ] Cache layer operational

## Post-Deployment Verification

### Smoke Tests
- [ ] Homepage loads successfully
- [ ] User can log in
- [ ] Job search returns results
- [ ] File upload works
- [ ] WebSocket connections establish

### Integration Tests
- [ ] Run E2E test suite
- [ ] Verify API endpoints
- [ ] Test collaborative editing
- [ ] Check translation memory

### Monitoring
- [ ] Check error rates (< 1%)
- [ ] Verify response times (< 200ms p95)
- [ ] Monitor database performance
- [ ] Review application logs

### Performance Baselines
- [ ] API response time within SLA
- [ ] Database query performance acceptable
- [ ] Frontend load time < 2s
- [ ] No memory leaks detected

## Rollback Criteria

Trigger rollback if:
- Error rate > 5%
- Response time > 2s (p95)
- Critical features broken
- Database corruption detected
- Security vulnerability exposed

## Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/jddb-backend

# Or with Docker
docker-compose up -d --force-recreate

# Revert database if needed
psql < backup_$(date +%Y%m%d).sql
```

## Post-Deployment

### Communication
- [ ] Announce deployment success
- [ ] Update status page
- [ ] Document any issues encountered

### Monitoring Period
- [ ] Monitor for 1 hour after deployment
- [ ] Check error logs every 15 minutes
- [ ] Respond to any alerts promptly

### Documentation
- [ ] Update deployment log
- [ ] Document any manual steps taken
- [ ] Create postmortem if issues occurred

---

*Last Updated: September 30, 2025*
