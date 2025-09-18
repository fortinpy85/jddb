# Setup & Installation Documentation

This folder contains all documentation related to setting up and deploying the JDDB system.

## 📋 **Setup Guides**

### **[SETUP.md](SETUP.md)**

General setup instructions for all platforms.

### **[WINDOWS_QUICKSTART.md](WINDOWS_QUICKSTART.md)**

Windows-specific quick start guide with step-by-step instructions for Windows users.

### **[POSTGRESQL_17_NOTES.md](POSTGRESQL_17_NOTES.md)**

Detailed PostgreSQL 17 setup and configuration, including pgvector extension installation.

## 🚀 **Deployment Documentation**

### **[DEPLOYMENT.md](DEPLOYMENT.md)**

Production deployment guide with Docker, environment configuration, and scaling considerations.

### **[DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)**

Historical deployment report from September 2025 - documents successful resolution of deployment issues and system readiness.

## 🛠️ **Quick Start Process**

1. **Choose Your Platform**:
   - Windows: Start with `WINDOWS_QUICKSTART.md`
   - Linux/Mac: Start with `SETUP.md`

2. **Database Setup**: Follow `POSTGRESQL_17_NOTES.md` for database configuration

3. **Production Deployment**: Use `DEPLOYMENT.md` for production environments

4. **Troubleshooting**: Reference `DEPLOYMENT_SUCCESS.md` for common issues and solutions

## ✅ **System Requirements**

- **Database**: PostgreSQL 17+ with pgvector extension
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy
- **Frontend**: Node.js, Bun runtime, React
- **Processing**: Redis for background tasks
- **Platform**: Windows, Linux, or macOS support
