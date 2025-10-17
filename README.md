# Job Description Database (JDDB)

**Job Description Database (JDDB)** is an AI-powered, full-stack web application for managing and analyzing government job descriptions. It features a modern system with a FastAPI backend and a React frontend, designed for government organizations to provide intelligent document processing, semantic search, and collaborative editing capabilities.

## 🚀 Quick Start

Get up and running with JDDB in under 10 minutes!

### Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 18+** with Bun
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
    bun install
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
    DATABASE_URL=postgresql://postgres:password@localhost:5432/jddb
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
    bun dev
    ```

5.  **Open Application**
    ```
    Frontend: http://localhost:3000
    Backend API: http://localhost:8000
    API Docs: http://localhost:8000/api/docs
    ```

## 📂 Documentation

For more detailed documentation, please see the [docs](docs/README.md) directory.