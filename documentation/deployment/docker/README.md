# Docker Deployment

Containerization and Docker Compose configuration for the JDDB system.

## Quick Start

```bash
# Development environment
docker-compose up -d

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

## Docker Images

### Backend API
- **Base Image**: python:3.11-slim
- **Port**: 8000
- **Dependencies**: Poetry-managed
- **Health Check**: `/api/health`

### Frontend
- **Base Image**: oven/bun:latest
- **Port**: 3000
- **Build Tool**: Bun native bundler
- **Static Assets**: Served by Bun

### Database
- **Image**: pgvector/pgvector:pg17
- **Port**: 5432
- **Extensions**: pgvector, pg_trgm
- **Volumes**: Persistent data storage

## Configuration Files

- `Dockerfile` (backend) - Located in `backend/`
- `Dockerfile` (frontend) - Located in root
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `.dockerignore` - Excluded files/directories

## Environment Variables

See `.env.example` for required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `SECRET_KEY` - Application secret key
- `REDIS_URL` - Redis cache URL (optional)

## Volume Management

```bash
# Create named volumes
docker volume create jddb_postgres_data
docker volume create jddb_uploads

# Backup database
docker exec jddb_postgres pg_dump -U postgres jddb > backup.sql

# Restore database
docker exec -i jddb_postgres psql -U postgres jddb < backup.sql
```

## Troubleshooting

### Container won't start
- Check logs: `docker logs jddb_backend`
- Verify environment variables
- Ensure PostgreSQL is ready

### Performance issues
- Increase container resources
- Check database connection pool settings
- Monitor with `docker stats`

---

*Last Updated: September 30, 2025*
