# JDDB Deployment Guide

Complete deployment guide for the Job Description Database (JDDB) system.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **PostgreSQL**: 17 (latest version with optimal performance)
- **Node.js**: 18 or higher (for React frontend)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space minimum

### Required Software

1. **PostgreSQL with pgvector**
2. **Python 3.9+**
3. **Node.js 18+**
4. **Git**
5. **OpenAI API Key** (for embedding generation)

## Step 1: PostgreSQL Setup

### Install PostgreSQL 17

**Windows:**

```powershell
# Download and install PostgreSQL 17 from https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql --version=17.0.0

# Start PostgreSQL service
net start postgresql-x64-17
```

**macOS:**

```bash
# Using Homebrew
brew install postgresql@17
brew services start postgresql@17
```

**Ubuntu/Linux:**

```bash
# Add PostgreSQL APT repository
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# Update and install
sudo apt update
sudo apt install postgresql-17 postgresql-client-17

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Install pgvector Extension

**Method 1: From Source (Recommended for PostgreSQL 17)**

```bash
# Install build dependencies
## Ubuntu/Debian:
sudo apt install build-essential postgresql-server-dev-17 git

## macOS:
# Make sure you have Xcode command line tools installed
xcode-select --install

## Windows:
# Install Visual Studio Build Tools and ensure PostgreSQL 17 development headers are available

# Clone and build pgvector (latest version for PostgreSQL 17)
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install # May require sudo on Linux/macOS
```

**Method 2: Using Package Manager**

```bash
# Ubuntu/Debian (if available for PostgreSQL 17)
sudo apt install postgresql-17-pgvector

# macOS
brew install pgvector
```

**Method 3: Docker (Alternative)**

```bash
# Use the pre-built pgvector image with PostgreSQL 17
docker pull pgvector/pgvector:pg17
docker run --name jddb-postgres -e POSTGRES_PASSWORD=your_password -d -p 5432:5432 pgvector/pgvector:pg17
```

### Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE USER jddb_user WITH PASSWORD 'secure_password_123';
CREATE DATABASE JDDB OWNER jddb_user;
GRANT ALL PRIVILEGES ON DATABASE JDDB TO jddb_user;

-- Connect to JDDB database
\c JDDB

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Exit
\q
```

## Step 2: Backend Setup

### Clone and Install Dependencies

```bash
# Navigate to project directory
cd C:\JDDB  # or your project path

# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
## Windows:
venv\Scripts\activate
## macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
```

**Complete .env Configuration:**

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://jddb_user:secure_password_123@localhost:5432/JDDB
DATABASE_SYNC_URL=postgresql://jddb_user:secure_password_123@localhost:5432/JDDB

# Redis Configuration (for future Celery tasks)
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-in-production-please

# File Processing
MAX_FILE_SIZE_MB=50
SUPPORTED_EXTENSIONS=[".txt",".doc",".docx",".pdf"]
DATA_DIR=C:/JDDB/data

# Embedding Settings
EMBEDDING_MODEL=text-embedding-ada-002
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
```

### Initialize Database

```bash
# Run database initialization script
python scripts/init_db.py

# Create sample data (optional)
python scripts/sample_data.py

# Verify database setup
python -c "import asyncio; from src.jd_ingestion.database.connection import async_engine; asyncio.run(async_engine.connect().aclose())"
```

## Step 3: Frontend Setup

### Install Node.js Dependencies

```bash
# Navigate to project root
cd C:\JDDB

# Install dependencies
bun install
```

### Configure Frontend Environment

Create `.env.local` in project root:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Step 4: Start the Application

### Start Backend Server

```bash
# Navigate to backend directory
cd C:\JDDB\backend

# Activate virtual environment (if not already active)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Start development server
python scripts/dev_server.py

# Or using make (if available)
make server

# Or manually
python -m uvicorn jd_ingestion.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend Server

```bash
# In new terminal, navigate to project root
cd C:\JDDB

# Start React development server
bun dev
```

## Step 5: Verify Installation

### Backend Health Check

```bash
# Test API endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

### Frontend Access

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **API Root**: http://localhost:8000/api

### Test File Processing

```bash
# Test file discovery
curl -X POST "http://localhost:8000/api/ingestion/scan-directory" \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "C:/JDDB/data/raw", "recursive": true}'

# Test single file processing (update path as needed)
curl -X POST "http://localhost:8000/api/ingestion/process-file" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "C:/JDDB/data/raw/EX-01 Dir, Business Analysis 103249 - JD.txt"}'
```

## Production Deployment

### Environment Preparation

1. **Security Updates**

```env
DEBUG=False
SECRET_KEY=generate-strong-production-secret-key
LOG_LEVEL=WARNING
```

2. **Database Performance (PostgreSQL 17 Optimized)**

```sql
-- Optimize PostgreSQL 17 for production
-- Add to postgresql.conf:
shared_preload_libraries = 'pg_stat_statements'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# PostgreSQL 17 specific optimizations
enable_partitionwise_join = on
enable_partitionwise_aggregate = on
jit = on
```

3. **Application Server**

```bash
# Use Gunicorn for production
pip install gunicorn[gevent]

# Start with Gunicorn
gunicorn jd_ingestion.api.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile for backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "scripts/dev_server.py"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: JDDB
      POSTGRES_USER: jddb_user
      POSTGRES_PASSWORD: secure_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://jddb_user:secure_password_123@postgres:5432/JDDB
      DATABASE_SYNC_URL: postgresql://jddb_user:secure_password_123@postgres:5432/JDDB
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./data:/app/data

  frontend:
    build: .
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

1. **pgvector Extension Not Found**

```sql
-- Verify extension is installed
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- If not available, reinstall pgvector
-- Follow pgvector installation steps above
```

2. **Database Connection Failed**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
net start postgresql-x64-15  # Windows

# Test connection manually
psql -h localhost -U jddb_user -d JDDB
```

3. **Python Dependencies Issues**

```bash
# Upgrade pip and try again
python -m pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

4. **Port Already in Use**

```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux

# Kill process or change port in .env
```

5. **File Permission Issues**

```bash
# Ensure data directory is writable
mkdir -p C:/JDDB/data/raw
mkdir -p C:/JDDB/data/processed
chmod -R 755 C:/JDDB/data  # Linux/macOS
```

### Performance Optimization

1. **Database Indexing**

```sql
-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_descriptions_classification ON job_descriptions(classification);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_language ON job_descriptions(language);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_processed_date ON job_descriptions(processed_date);
CREATE INDEX IF NOT EXISTS idx_content_chunks_job_id ON content_chunks(job_id);
```

2. **File Processing Optimization**

```env
# Adjust chunk sizes based on your data
CHUNK_SIZE=256  # Smaller chunks for more granular search
CHUNK_OVERLAP=25  # Less overlap for faster processing
```

### Monitoring and Logs

1. **Application Logs**

```bash
# Backend logs location
tail -f C:/JDDB/backend/logs/app.log

# Check application health
curl http://localhost:8000/health
```

2. **Database Monitoring**

```sql
-- Monitor database performance
SELECT * FROM pg_stat_activity WHERE datname = 'JDDB';

-- Check table sizes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    most_common_vals
FROM pg_stats
WHERE schemaname = 'public';
```

## Security Considerations

### Production Security Checklist

- [ ] Change default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Restrict API access if needed

### Backup Strategy

```bash
# Database backup
pg_dump -h localhost -U jddb_user JDDB > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql -h localhost -U jddb_user JDDB < backup_file.sql

# File backup
rsync -av C:/JDDB/data/ /backup/location/data/
```

## Support

For technical support or issues:

1. Check logs in `backend/logs/` directory
2. Verify database connectivity
3. Ensure all environment variables are set correctly
4. Check API documentation at http://localhost:8000/api/docs
5. Review this deployment guide

## Next Steps

After successful deployment:

1. **Data Import**: Upload your job description files to `C:/JDDB/data/raw/`
2. **Batch Processing**: Use the bulk ingestion API to process files
3. **Frontend Configuration**: Customize the React interface for your needs
4. **API Integration**: Connect external systems via the REST API
5. **Performance Tuning**: Optimize based on your data volume and usage patterns

The system is now ready for job description ingestion and analysis!
