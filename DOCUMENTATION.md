# JDDB Documentation Index

Welcome to the Job Description Database (JDDB) documentation! This index provides a comprehensive guide to all available documentation resources.

## 🚀 Getting Started

### New Users
- **[Quick Start Guide](README.md)** - Get up and running in 10 minutes
- **[Detailed Startup Guide](STARTUP-GUIDE.md)** - Comprehensive setup with Windows batch scripts
- **[Scripts Documentation](scripts/README.md)** - Setup and configuration scripts

### First-Time Setup
1. Read the [Quick Start Guide](README.md#quick-start)
2. Follow [STARTUP-GUIDE.md](STARTUP-GUIDE.md) for detailed instructions
3. Use `start-all.bat` (Windows) or manual startup commands

---

## 💻 Development

### Development Guides
- **[Development Guide](DEVELOPMENT-GUIDE.md)** - Complete development workflow and commands
- **[Backend README](backend/README.md)** - Backend-specific development information
- **[Architecture Overview](docs/README.md)** - System architecture and design patterns

### Development Workflow
- **Backend**: Python 3.11+ with Poetry → FastAPI
- **Frontend**: Node.js 18+ with npm → React + Vite
- **Database**: PostgreSQL 15+ with pgvector extension

### Key Commands
```bash
# Backend
cd backend && make server    # Start development server
cd backend && make test       # Run tests
cd backend && make lint       # Lint code

# Frontend
npm run dev                   # Start Vite dev server
npm test                      # Run unit tests
npm run test:e2e              # Run E2E tests with Playwright

# Both Services
start-all.bat                 # Windows: Start both services
```

---

## 📚 API Documentation

### Core APIs (✅ All Complete)
- **[API Overview](docs/api/README.md)** - Complete API reference with quick start examples
- **[Jobs API](docs/api/jobs-api.md)** - Job description CRUD, filtering, section editing, bulk export ✅ Complete
- **[Ingestion API](docs/api/ingestion-api.md)** - File upload, batch processing, status tracking ✅ Complete
- **[Search API](docs/api/search-api.md)** - Full-text and semantic search with faceted filtering ✅ Complete
- **[Translation Memory API](docs/api/translation_memory_api.md)** - Translation concordance and terminology ✅ Complete

### API Coverage Status
**100% Core API Coverage** - All production APIs fully documented with:
- Complete endpoint specifications
- Request/response examples
- Error handling documentation
- Integration examples (Python, JavaScript, cURL)
- Best practices and performance guidelines

### Future APIs (Planned - Phase 7)
- AI Improvement API - Sentence-level AI enhancement (roadmap complete)
- Translation Mode API - Bilingual translation workflows (roadmap complete)

**Live API Documentation**: http://localhost:8000/api/docs (interactive Swagger UI)

---

## 🏗️ Architecture

### Architecture Documentation
- **[System Overview](docs/README.md#architectural-patterns)** - High-level architecture
- **[Backend Structure](DEVELOPMENT-GUIDE.md#backend-structure-fastapipy thon)** - FastAPI application structure
- **[Frontend Structure](DEVELOPMENT-GUIDE.md#frontend-structure-reacttypescriptvite)** - React + Vite architecture
- **[Database Schema](DEVELOPMENT-GUIDE.md#database-schema-postgresql--pgvector)** - PostgreSQL + pgvector schema

### Key Architectural Decisions
- **Backend**: FastAPI with async/await patterns
- **Frontend**: Vite (migrated from Bun in October 2025)
- **State Management**: Zustand for global state
- **API Client**: Singleton pattern with retry logic
- **Database**: PostgreSQL with pgvector for semantic search

---

## 🧪 Testing

### Testing Documentation
- **[Test Framework Migration](documentation/development/SKILLS_TESTS_FIX_SUMMARY.md)** - Vitest migration details
- **[Testing Commands](DEVELOPMENT-GUIDE.md#testing)** - How to run tests

### Test Structure
- **Backend Tests**: `backend/tests/` - pytest with asyncio
- **Frontend Unit Tests**: `src/**/*.test.{ts,tsx}` - Vitest with JSDOM
- **Frontend E2E Tests**: `tests/*.spec.ts` - Playwright

### Running Tests
```bash
# Backend
cd backend && make test

# Frontend Unit
npm test
npm run test:unit:watch    # Watch mode
npm run test:unit:coverage # Coverage report

# Frontend E2E
npm run test:e2e
npm run test:e2e:headed    # Visible browser

# All Tests
npm run test:all
```

---

## 🚢 Deployment

### Deployment Status
⚠️ **Documentation In Progress**

Current deployment documentation is limited. Production deployment guidelines are needed for:
- Production environment setup
- Docker containerization
- CI/CD pipeline (GitHub Actions)
- Monitoring and logging
- Backup and recovery

**Development Environment**: Fully documented in [STARTUP-GUIDE.md](STARTUP-GUIDE.md)

---

## 🔧 Troubleshooting

### Troubleshooting Resources
- **[Startup Issues](STARTUP-GUIDE.md#troubleshooting-guide)** - Complete troubleshooting guide
- **[Known Issues](DEVELOPMENT-GUIDE.md#known-issues--solutions)** - Resolved issues and solutions
- **[Application Issues](docs/README.md#troubleshooting)** - Common problems and fixes

### Common Issues
1. **Port conflicts**: Use `cleanup.bat` to free ports 8000 and 3006
2. **Package manager**: System uses **npm**, not Bun (migrated October 2025)
3. **Database connection**: Ensure PostgreSQL is running
4. **Environment files**: Check `.env` (backend) and `.env.local` (frontend) exist

---

## 🤝 Contributing

### Contribution Resources
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](docs/CODE_OF_CONDUCT.md)** - Community standards
- **[User Stories](docs/user_stories.md)** - Feature requirements and user stories

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Follow code style guidelines
4. Write tests for new features
5. Update documentation
6. Submit a pull request

---

## 📖 Reference Documentation

### Configuration Files
- **Backend Configuration**:
  - `backend/pyproject.toml` - Poetry dependencies and tool configuration
  - `backend/.env` - Environment variables (database, OpenAI API, etc.)
  - `backend/alembic/` - Database migrations

- **Frontend Configuration**:
  - `package.json` - npm dependencies and scripts
  - `.env.local` - Frontend environment variables
  - `vite.config.ts` - Vite build configuration
  - `tsconfig.json` - TypeScript configuration

### Technology Stack
- **Languages**: Python 3.11+, TypeScript
- **Backend**: FastAPI, SQLAlchemy, Alembic, OpenAI, Celery, Redis
- **Frontend**: React, Vite, Tailwind CSS, Radix UI, Zustand
- **Database**: PostgreSQL 15+ with pgvector extension
- **Testing**: pytest, Vitest, Playwright
- **Package Managers**: Poetry (Python), npm (JavaScript/TypeScript)

---

## 🎯 Documentation Roadmap

### Completed Documentation ✅
✅ Quick start guide
✅ Detailed startup guide
✅ Development workflow
✅ **Complete API documentation** (Jobs, Ingestion, Search, Translation Memory) - **NEW**
✅ API overview with integration examples - **NEW**
✅ **File organization improvements** (CLAUDE.md → DEVELOPMENT-GUIDE.md) - **NEW**
✅ Testing infrastructure
✅ Troubleshooting guide

### In Progress 🚧
🚧 Architecture documentation with Mermaid diagrams
🚧 Database schema documentation with ERD diagrams
🚧 Deployment documentation (Docker, CI/CD, monitoring)

### Planned Documentation 📋
📋 Frontend component library guide
📋 State management patterns
📋 API client usage guide
📋 Database migration guide
📋 Performance optimization guide
📋 Security best practices
📋 Monitoring and logging setup
📋 AI Improvement Mode implementation guide (Phase 7)
📋 Translation Mode implementation guide (Phase 7)

---

## 📞 Getting Help

### Resources
- **Documentation Issues**: Check [Troubleshooting](#troubleshooting)
- **API Reference**: http://localhost:8000/api/docs (live OpenAPI docs)
- **GitHub Issues**: For bugs and feature requests
- **Development Questions**: See [Development Guide](DEVELOPMENT-GUIDE.md)

### Quick Links
- [Project Status](DEVELOPMENT-GUIDE.md#project-status)
- [File Processing Pipeline](DEVELOPMENT-GUIDE.md#file-processing-pipeline)
- [Data Flow](DEVELOPMENT-GUIDE.md#data-flow)
- [API Client Pattern](DEVELOPMENT-GUIDE.md#api-client-pattern)

---

## 📝 Documentation Maintenance

### Keeping Documentation Updated
- Review documentation quarterly
- Update docs with each major release
- Include documentation changes in PRs
- Tag docs with version numbers

### Documentation Owners
- **API Documentation**: Backend team
- **Architecture**: Technical lead
- **Frontend Documentation**: Frontend team
- **Deployment**: DevOps team

---

**Last Updated**: 2025-10-17
**Documentation Version**: 2.0
**Project Status**: Phase 2 Complete - Production Ready

For the most up-to-date information, always check the live API documentation at http://localhost:8000/api/docs when the backend server is running.
