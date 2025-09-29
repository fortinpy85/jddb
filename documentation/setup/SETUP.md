# JDDB Setup Guide

This guide provides unified setup instructions for the Job Description Database (JDDB) on Windows, macOS, and Linux.

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

- Download and install PostgreSQL 17 from [the official website](https://www.postgresql.org/download/windows/).
- Alternatively, use Chocolatey: `choco install postgresql --version=17.0.0`

**macOS:**

- Use Homebrew: `brew install postgresql@17`

**Linux (Ubuntu):**

```bash
sudo apt update
sudo apt install postgresql-17 postgresql-client-17
```

### Install pgvector Extension

- **Recommended**: Compile from source. See the [pgvector GitHub](https://github.com/pgvector/pgvector) for instructions.
- **Alternative**: Use a package manager like `apt` or `brew` if available for your system.

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

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and OpenAI key
```

## Step 3: Frontend Setup

```bash
# Navigate to the project root
cd ..

# Install dependencies
bun install

# Configure environment
# Create a .env.local file and add:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Step 4: Running the Application

1.  **Start the backend:**

    ```bash
    cd backend
    # Activate virtual environment if needed
    python scripts/dev_server.py
    ```

2.  **Start the frontend:**

    ```bash
    # In a new terminal, from the project root
    npm run dev
    ```

## Windows-Specific Instructions

For Windows users, it is highly recommended to use the provided batch scripts for a smoother experience.

- `setup.bat`: Installs all dependencies and sets up the environment.
- `server.bat`: Starts the backend server.
- `frontend.bat`: Starts the frontend server.
