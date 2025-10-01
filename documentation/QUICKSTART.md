# JDDB Quick Start Guide

Get up and running with JDDB in under 10 minutes! 🚀

---

## Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 18+** with Bun
- **PostgreSQL 15+** with pgvector extension
- **Git**

---

## 🎯 5-Minute Setup

### 1. Clone & Install
```bash
# Clone repository
git clone https://github.com/your-org/jddb.git
cd jddb

# Backend setup
cd backend
poetry install
cd ..

# Frontend setup
bun install
```

### 2. Database Setup
```bash
# Start PostgreSQL (if not running)
# On Windows: Start PostgreSQL service
# On Mac/Linux: brew services start postgresql

# Initialize database
cd backend
make db-init
make sample-data
cd ..
```

### 3. Environment Configuration
```bash
# Backend .env
cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/jddb
OPENAI_API_KEY=your-key-here
DATA_DIRECTORY=../data
EOF

# Frontend .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api
EOF
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend
cd backend && make server

# Terminal 2: Frontend
bun dev
```

### 5. Open Application
```
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/api/docs
```

---

## 🎓 First Steps

### Upload Your First Job Description
1. Navigate to **Upload** tab
2. Drag & drop a `.txt` file or click to browse
3. Click **Upload** and watch AI process it!

### Search Job Descriptions
1. Go to **Search** tab
2. Enter keywords (e.g., "Director" or "planning")
3. Apply filters by classification, department, language
4. Click on results to view full details

### Try Collaborative Editing
1. Open a job description
2. Click **Edit** button
3. Make changes in real-time
4. See AI suggestions in the sidebar

---

## 🔧 Development Commands

### Backend
```bash
cd backend

# Run tests
make test

# Type checking
make type-check

# Linting
make lint

# Format code
make format

# Full check (all of the above)
make check
```

### Frontend
```bash
# Run unit tests
bun test

# Run E2E tests
bun run test:e2e

# Type checking
bun run type-check

# Linting
bun run lint
```

---

## 📚 Next Steps

### Learn the System
- **[Architecture Overview](architecture/README.md)** - Understand the system design
- **[API Documentation](api/README.md)** - Explore available endpoints
- **[User Guide](user-guide/collaborative-editing.md)** - Master advanced features

### Start Contributing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[Development Guide](development/team-onboarding.md)** - Team onboarding
- **[Todo List](development/todo.md)** - Current priorities

### Explore Features
- **Real-Time Collaboration** - Multi-user editing with WebSockets
- **AI Assistance** - Smart suggestions and template generation
- **Translation Memory** - Bilingual editing with quality scoring
- **Semantic Search** - Find similar job descriptions with pgvector

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify database exists
psql -U postgres -l | grep jddb

# Recreate if needed
cd backend && make db-init
```

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
poetry install --sync

# Check for port conflicts
netstat -an | grep 8000
```

### Frontend Won't Start
```bash
# Check Bun version
bun --version  # Should be 1.0+

# Clear cache and reinstall
rm -rf node_modules bun.lockb
bun install

# Check for port conflicts
netstat -an | grep 3000
```

### Tests Failing
```bash
# Backend tests
cd backend
poetry run pytest tests/ -v

# Frontend tests
bun test

# E2E tests (ensure dev servers are running)
bun run test:e2e
```

---

## 💡 Pro Tips

1. **Use Docker Compose** for faster setup: `docker-compose up -d`
2. **Enable pre-commit hooks** for automatic code quality: `pre-commit install`
3. **Check API docs** at `/api/docs` for interactive endpoint testing
4. **Use API client methods** in `src/lib/api.ts` for type-safe frontend calls
5. **Monitor logs** for debugging: Backend console + Browser DevTools

---

## 🆘 Need Help?

- **Documentation**: Check [README.md](README.md) for full documentation structure
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Team Chat**: Join the development Slack/Discord channel
- **Email**: Contact the team at dev@jddb.example.com

---

## 🎉 You're Ready!

Congratulations! You're now set up to develop on JDDB. Happy coding! 🚀

For more detailed information, see:
- **[Full Setup Guide](setup/WINDOWS_QUICKSTART.md)**
- **[Team Onboarding](development/team-onboarding.md)**
- **[Architecture Documentation](architecture/README.md)**

---

*Last Updated: September 30, 2025*
