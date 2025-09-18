# JDDB Documentation

Welcome to the Job Description Database (JDDB) documentation. This folder contains comprehensive documentation for the system, organized by category.

## 📖 **Documentation Structure**

### 📦 **Quick Start**

- **[TODO.md](TODO.md)** - Current development status and feature roadmap

### 🛠️ **Setup & Installation** (`setup/`)

Setup guides and deployment documentation:

- **[SETUP.md](setup/SETUP.md)** - General setup instructions
- **[WINDOWS_QUICKSTART.md](setup/WINDOWS_QUICKSTART.md)** - Windows-specific quick start guide
- **[POSTGRESQL_17_NOTES.md](setup/POSTGRESQL_17_NOTES.md)** - PostgreSQL 17 setup and configuration
- **[DEPLOYMENT.md](setup/DEPLOYMENT.md)** - Production deployment guide
- **[DEPLOYMENT_SUCCESS.md](setup/DEPLOYMENT_SUCCESS.md)** - Historical deployment report (Sept 2025)

### 📋 **Planning & Requirements** (`planning/`)

Project planning and requirements documentation:

- **[project_plan.md](planning/project_plan.md)** - Original project plan and architecture
- **[jd_ingestion_plan.md](planning/jd_ingestion_plan.md)** - Detailed ingestion engine plan
- **[jd_modernization_prd.md](planning/jd_modernization_prd.md)** - Government modernization initiative PRD

### 💻 **Development** (`development/`)

Technical implementation documentation:

- **[SEMANTIC_MATCHING_IMPLEMENTATION.md](development/SEMANTIC_MATCHING_IMPLEMENTATION.md)** - AI-powered semantic matching implementation details

### 🗃️ **Archive** (`archive/`)

Historical and outdated documentation:

- **[problems.md](archive/problems.md)** - Historical linting errors and issues (resolved)
- **[refactor.md](archive/refactor.md)** - Development checklist (completed)

## 🚀 **Getting Started**

### New Users

1. Start with **[SETUP.md](setup/SETUP.md)** or **[WINDOWS_QUICKSTART.md](setup/WINDOWS_QUICKSTART.md)**
2. Check **[TODO.md](TODO.md)** for current system status
3. Review **[project_plan.md](planning/project_plan.md)** for system overview

### Developers

1. Review **[development/SEMANTIC_MATCHING_IMPLEMENTATION.md](development/SEMANTIC_MATCHING_IMPLEMENTATION.md)** for technical details
2. Check **[TODO.md](TODO.md)** for current development priorities
3. Refer to **[planning/](planning/)** documents for requirements context

### System Administrators

1. Follow **[setup/DEPLOYMENT.md](setup/DEPLOYMENT.md)** for production deployment
2. Reference **[setup/POSTGRESQL_17_NOTES.md](setup/POSTGRESQL_17_NOTES.md)** for database setup
3. Review **[setup/DEPLOYMENT_SUCCESS.md](setup/DEPLOYMENT_SUCCESS.md)** for troubleshooting insights

## 📊 **System Overview**

The **Job Description Database (JDDB)** is a production-ready system for processing, analyzing, and managing government job descriptions with AI-powered features:

### **Core Features** ✅

- **File Processing**: Support for .txt, .doc, .docx, .pdf formats
- **AI-Powered Search**: Semantic search using OpenAI embeddings + pgvector
- **Job Analysis**: Intelligent job comparison and similarity matching
- **Web Interface**: React frontend with advanced search capabilities
- **Background Processing**: Celery-based async task processing
- **Quality Assurance**: Comprehensive validation and quality metrics

### **Architecture**

- **Backend**: Python FastAPI with SQLAlchemy
- **Frontend**: React + TypeScript + Bun
- **Database**: PostgreSQL 17 with pgvector extension
- **Search**: Full-text search + vector similarity
- **Processing**: Celery + Redis for background tasks

### **Status**

- ✅ **Production Ready** - All critical features implemented
- ✅ **Comprehensive Testing** - End-to-end Playwright test suite
- ✅ **Performance Optimized** - Sub-200ms search response times
- ✅ **Windows Compatible** - Full Windows deployment support

## 🔗 **Related Documentation**

### Root Level Files

- **[../README.md](../README.md)** - Project overview and quick start
- **[../CLAUDE.md](../CLAUDE.md)** - Development commands and architecture guide
- **[../scripts/README.md](../scripts/README.md)** - Setup scripts documentation

### Technical References

- **API Documentation**: http://localhost:8000/api/docs (when running)
- **Database Schema**: See setup documentation for table structures
- **Configuration**: Backend `.env` and frontend environment setup

## 📅 **Last Updated**

September 13, 2025 - Documentation reorganized and updated

---

_For questions or issues, refer to the specific documentation sections or check the project's main README file._
