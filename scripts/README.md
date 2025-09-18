# Setup and Configuration Scripts

This folder contains Windows batch scripts for setting up and configuring the JDDB (Job Description Database) system.

## Scripts Overview

### `setup-windows.bat`

**Primary setup script** - Installs all dependencies and sets up the development environment.

- Installs Python dependencies in backend virtual environment
- Installs Node.js dependencies with Bun
- Creates necessary directories
- Configures development environment
- **Run this first** for initial setup

### `init-db.bat`

**Database initialization script** - Sets up the PostgreSQL database schema.

- Activates Python virtual environment
- Runs Alembic migrations to create database tables
- Populates database with sample data
- **Run after** `setup-windows.bat` and PostgreSQL installation

### `configure-env.bat`

**Environment configuration utility** - Interactive script for configuring environment files.

- Helps set up `.env` files for backend configuration
- Prompts for database connection settings
- Validates configuration
- Can run database initialization

### `setup.bat`

**Basic setup script** - Minimal setup without full configuration.

- Used by `quick-start-windows.bat`
- Installs basic dependencies

### `quick-start-windows.bat`

**Interactive quick-start menu** - Provides a menu-driven setup experience.

- Menu-driven interface for setup options
- Calls other setup scripts as needed
- Good for guided setup process

## Usage Order

For initial setup, run scripts in this order:

1. **`setup-windows.bat`** - Install all dependencies
2. Ensure PostgreSQL 17 is installed and running
3. **`init-db.bat`** - Initialize database schema
4. Use `server.bat` and `frontend.bat` (in root directory) to start services

## Notes

- All scripts are designed to run from the `scripts/` folder
- Scripts automatically navigate to correct directories as needed
- Virtual environment paths are relative to the backend folder
- Database scripts require PostgreSQL to be running
