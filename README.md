# Job Description Database (JDDB)

**Job Description Database (JDDB)** is an AI-powered, full-stack web application for managing and analyzing government job descriptions. It features a modern system with a FastAPI backend and a React frontend, designed for government organizations to provide intelligent document processing, semantic search, and collaborative editing capabilities.

## 🚀 Quick Start

Get up and running with JDDB in under 10 minutes!

### Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 18+** with npm
- **PostgreSQL 15+** with pgvector extension
- **Git**

### 5-Minute Setup

1.  **Clone & Install**
    ```bash
    # Clone repository
    git clone https://github.com/your-org/jddb.git
    cd jddb

    # Backend setup
    cd backend
    poetry install
    cd ..

    # Frontend setup
    npm install
    ```

2.  **Database Setup**
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

3.  **Environment Configuration**
    ```bash
    # Backend .env
    cat > backend/.env << EOF
    DATABASE_URL=postgresql://postgres:password@localhost:5432/jddb # pragma: allowlist secret
    OPENAI_API_KEY=your-key-here
    DATA_DIRECTORY=../data
    EOF

    # Frontend .env.local
    cat > .env.local << EOF
    NEXT_PUBLIC_API_URL=http://localhost:8000/api
    EOF
    ```

4.  **Start Development Servers**
    ```bash
    # Terminal 1: Backend
    cd backend && make server

    # Terminal 2: Frontend
    npm run dev
    ```

5.  **Open Application**
    ```
    Frontend: http://localhost:3006
    Backend API: http://localhost:8000
    API Docs: http://localhost:8000/api/docs
    ```

    **Note:** Vite will automatically use the next available port (3007, 3008, etc.) if 3006 is busy.

## 🪟 Windows Quick Start

For Windows users, we provide convenient batch scripts:

```bash
# Start both backend and frontend
start-all.bat

# Or start individually
server.bat      # Backend only
frontend.bat    # Frontend only

# Clean up processes if needed
cleanup.bat
```

See [STARTUP-GUIDE.md](STARTUP-GUIDE.md) for detailed information about startup scripts.

## 📂 Documentation

**📑 [Complete Documentation Index](DOCUMENTATION.md)** - Master index of all documentation resources

### Quick Links
- [Startup Guide](STARTUP-GUIDE.md) - Detailed setup and troubleshooting
- [Development Guide](DEVELOPMENT-GUIDE.md) - Development workflow and commands
- [API Documentation](docs/api/) - REST API reference
- [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute
- [Architecture Overview](docs/README.md) - System design and patterns

For comprehensive documentation navigation, see **[DOCUMENTATION.md](DOCUMENTATION.md)**.
