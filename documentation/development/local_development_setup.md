# Local Development Setup Guide

## 1. Overview

This guide provides step-by-step instructions for setting up and running the JDDB project on a local machine for development purposes. It covers the setup for the backend, frontend, and the required services (PostgreSQL, Redis).

---

## 2. Prerequisites

Before you begin, ensure you have the following installed:

- **Python:** Version 3.9 or higher.
- **Node.js:** Required for the frontend. We recommend using `nvm` to manage Node versions.
- **Bun:** The JavaScript runtime and toolkit. Install it via `npm install -g bun`.
- **Docker:** The easiest way to run the required services (PostgreSQL and Redis).

---

## 3. Backend Setup

1.  **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    - Create a file named `.env` in the `backend` directory.
    - Copy the contents of `.env.example` into your new `.env` file.
    - **Crucially, you must fill in the following variables:**
        - `DATABASE_URL`: The connection string for your PostgreSQL database.
        - `OPENAI_API_KEY`: Your secret key for the OpenAI API.

5.  **Run Database Migrations:**
    - With your PostgreSQL server running (see Step 5), run the following command from the `backend` directory:
    ```bash
    alembic upgrade head
    ```

6.  **Run the Backend Server:**
    ```bash
    uvicorn src.main:app --reload
    ```
    - The backend API will now be running at [http://localhost:8000](http://localhost:8000).

---

## 4. Frontend Setup

1.  **Navigate to the Project Root:**
    ```bash
    cd C:/JDDB # Or your project's root directory
    ```

2.  **Install Dependencies:**
    ```bash
    bun install
    ```

3.  **Run the Frontend Development Server:**
    ```bash
    bun dev
    ```
    - The frontend application will now be running at [http://localhost:3000](http://localhost:3000).

---

## 5. Running Required Services (Docker)

The easiest way to run PostgreSQL and Redis is by using Docker.

1.  **Create a `docker-compose.yml` file** in the root of the project with the following content:

    ```yaml
    version: '3.8'
    services:
      postgres:
        image: pgvector/pgvector:pg15
        environment:
          - POSTGRES_DB=jddb
          - POSTGRES_USER=user
          - POSTGRES_PASSWORD=password
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data

      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"

    volumes:
      postgres_data:
    ```

2.  **Start the Services:**
    ```bash
    docker-compose up -d
    ```

3.  **Database URL:**
    - The `DATABASE_URL` in your backend `.env` file should now be:
    `postgresql+asyncpg://user:password@localhost:5432/jddb`

---

## 6. Putting It All Together

To run the full application:

1.  Open a terminal and run `docker-compose up -d` to start the database and Redis.
2.  Open a second terminal, navigate to `backend`, activate the virtual environment, and run `uvicorn src.main:app --reload`.
3.  Open a third terminal, navigate to the project root, and run `bun dev`.
4.  You can now access the web application at [http://localhost:3000](http://localhost:3000).
