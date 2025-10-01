# Deployment Documentation

Deployment guides, infrastructure as code, and CI/CD configuration for the JDDB system.

## Contents

### Deployment Guides
- **[Docker Deployment](docker/)** - Docker containerization and Docker Compose setup
- **[Kubernetes Deployment](kubernetes/)** - Kubernetes manifests and Helm charts
- **[CI/CD Pipeline](ci-cd/)** - GitHub Actions workflows and automation

### Quick Start
- **[Windows Deployment](../setup/WINDOWS_QUICKSTART.md)** - Windows-specific deployment guide
- **[Production Deployment](../setup/DEPLOYMENT.md)** - Full production deployment guide
- **[Deployment Success Checklist](../setup/DEPLOYMENT_SUCCESS.md)** - Post-deployment verification

## Deployment Options

### Local Development
- Docker Compose for local development
- Bun + Poetry for direct execution
- See: [../CLAUDE.md](../../CLAUDE.md) for development setup

### Production Environments
- **Docker**: Containerized deployment with Docker Compose
- **Kubernetes**: Orchestrated deployment with Helm
- **Cloud**: AWS, Azure, or GCP managed services

## Infrastructure Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB SSD
- **Database**: PostgreSQL 15+ with pgvector

### Recommended Production
- **CPU**: 4-8 cores
- **Memory**: 16GB RAM
- **Storage**: 100GB SSD
- **Database**: PostgreSQL 17 with pgvector, read replicas
- **Load Balancer**: NGINX or cloud load balancer
- **Monitoring**: Prometheus + Grafana

## CI/CD Pipeline

### GitHub Actions Workflows
- **Build & Test**: Run on every PR
- **Deploy to Staging**: Auto-deploy from `develop` branch
- **Deploy to Production**: Manual approval from `main` branch
- **Database Migrations**: Automated with Alembic
- **Security Scanning**: Snyk, Dependabot

### Deployment Checklist
1. ✅ Code review and approval
2. ✅ All tests passing
3. ✅ Security scan clean
4. ✅ Database backup created
5. ✅ Rollback plan documented
6. ✅ Monitoring alerts configured
7. ✅ Post-deployment verification

## Related Documentation
- [Operations Runbook](../operations/README.md)
- [Security Checklist](../security/phase2_security_checklist.md)
- [Monitoring Guide](../metrics/README.md)

---

*Last Updated: September 30, 2025*
