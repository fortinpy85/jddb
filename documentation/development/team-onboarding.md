# Team Onboarding & Development Workflow Documentation

## Table of Contents
1. [Welcome to JDDB Development](#welcome-to-jddb-development)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Repository Structure](#repository-structure)
4. [Development Environment](#development-environment)
5. [Workflow & Branching Strategy](#workflow--branching-strategy)
6. [Code Standards & Guidelines](#code-standards--guidelines)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Process](#deployment-process)
9. [Collaboration Tools](#collaboration-tools)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Resources & Learning](#resources--learning)

## Welcome to JDDB Development

The **Job Description Database (JDDB)** is a sophisticated government application that enables collaborative editing of job descriptions with real-time features, translation memory, and semantic search capabilities.

### Project Overview

- **Frontend**: React/TypeScript with Bun runtime
- **Backend**: Python/FastAPI with Poetry dependency management
- **Database**: PostgreSQL with pgvector for semantic search
- **Real-time**: WebSocket connections for collaborative editing
- **Translation**: pgvector-based translation memory system
- **Infrastructure**: Docker, GitHub Actions, Redis for caching

### Team Structure

- **Tech Lead**: @fortinpy85 (Repository owner)
- **Backend Developers**: Python/FastAPI specialists
- **Frontend Developers**: React/TypeScript experts
- **DevOps Engineer**: CI/CD and infrastructure
- **QA Engineer**: Testing and quality assurance
- **UI/UX Designer**: User experience and interface design

## Prerequisites & Setup

### Required Software

#### Essential Tools
```bash
# Git (version control)
git --version  # Should be 2.30+

# Docker (containerization)
docker --version  # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Node.js and Bun (frontend)
node --version  # Should be 18.0+
bun --version   # Should be 1.1.42+

# Python and Poetry (backend)
python --version  # Should be 3.11+
poetry --version  # Should be 1.8.4+
```

#### Development Tools
- **IDE**: VS Code (recommended) or PyCharm/WebStorm
- **Database**: PostgreSQL client (pgAdmin, DBeaver, or CLI)
- **API Testing**: Postman, Insomnia, or Thunder Client
- **Terminal**: Windows Terminal, iTerm2, or VS Code integrated terminal

### Initial Setup Process

#### 1. Repository Access
```bash
# Clone the repository
git clone https://github.com/fortinpy85/jddb.git
cd jddb

# Verify you're on the main branch
git branch
```

#### 2. Environment Setup
```bash
# Install frontend dependencies
bun install

# Install backend dependencies
cd backend && poetry install

# Return to root directory
cd ..
```

#### 3. Environment Configuration
```bash
# Copy environment templates
cp .env.example .env.local
cp backend/.env.example backend/.env

# Edit environment files with your settings
# .env.local - Frontend configuration
# backend/.env - Backend configuration
```

#### 4. Database Setup
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Initialize database
cd backend && make db-init

# Create sample data
make sample-data
```

#### 5. Verification
```bash
# Start backend server
cd backend && make server
# Should see: "Uvicorn running on http://127.0.0.1:8000"

# In new terminal, start frontend
bun dev
# Should see: "Local: http://localhost:3000"

# Visit http://localhost:3000 to confirm setup
```

## Repository Structure

### High-Level Organization

```
jddb/
├── 📁 .github/           # GitHub workflows and templates
├── 📁 backend/           # Python/FastAPI backend
├── 📁 docs/              # Documentation
├── 📁 src/               # React/TypeScript frontend
├── 📁 tests/             # End-to-end tests
├── 📁 scripts/           # Utility scripts
├── 📄 package.json       # Frontend dependencies (Bun)
├── 📄 bun.lockb          # Bun lock file
├── 📄 docker-compose.yml # Local development services
├── 📄 CLAUDE.md          # Development commands reference
└── 📄 todo.md            # Current development tasks
```

### Backend Structure (`backend/`)

```
backend/
├── 📁 src/jd_ingestion/  # Main application code
│   ├── 📁 api/           # FastAPI endpoints and routers
│   ├── 📁 core/          # Business logic and file processing
│   ├── 📁 database/      # SQLAlchemy models and connections
│   ├── 📁 services/      # Service layer (translation, websocket)
│   └── 📁 utils/         # Utilities and helpers
├── 📁 tests/             # Backend tests
├── 📁 alembic/           # Database migrations
├── 📄 pyproject.toml     # Poetry configuration
└── 📄 Makefile           # Development commands
```

### Frontend Structure (`src/`)

```
src/
├── 📁 app/               # Next.js app router
├── 📁 components/        # React components
│   ├── 📁 editing/       # Collaborative editing components
│   ├── 📁 translation/   # Translation memory components
│   └── 📁 ui/            # Reusable UI components
├── 📁 lib/               # Utilities and configurations
│   ├── 📄 api.ts         # API client
│   └── 📄 store.ts       # State management
└── 📁 hooks/             # Custom React hooks
```

### Documentation Structure (`docs/`)

```
docs/
├── 📁 api/               # API documentation
├── 📁 architecture/      # System architecture docs
├── 📁 development/       # Development guides
├── 📁 security/          # Security guidelines
├── 📁 user-guide/        # End-user documentation
└── 📄 completed.md       # Historical task tracking
```

## Development Environment

### Package Managers

#### Frontend: Bun
- **Installation**: Fast and efficient JavaScript runtime
- **Commands**: `bun install`, `bun dev`, `bun test`
- **Lock File**: `bun.lockb` (binary format)
- **Scripts**: Defined in `package.json`

#### Backend: Poetry
- **Virtual Environment**: Isolated Python environment
- **Commands**: `poetry install`, `poetry run`, `poetry shell`
- **Lock File**: `poetry.lock` (commit to version control)
- **Dependencies**: Defined in `pyproject.toml`

### Development Servers

#### Starting All Services
```bash
# Option 1: Use Docker Compose (recommended)
docker-compose up -d

# Option 2: Start individually
# Terminal 1: Backend
cd backend && make server

# Terminal 2: Frontend
bun dev

# Terminal 3: Database (if not using Docker)
# Start PostgreSQL manually
```

#### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)

### IDE Configuration

#### VS Code Recommended Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "oven.bun-vscode"
  ]
}
```

#### VS Code Settings
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Hot Reload & Development Features

#### Backend Hot Reload
- **Uvicorn**: Automatically reloads on Python file changes
- **FastAPI**: Interactive API docs update automatically
- **Database**: Alembic migrations for schema changes

#### Frontend Hot Reload
- **Bun Dev**: Near-instant hot module replacement
- **TypeScript**: Real-time type checking
- **Tailwind CSS**: Instant style updates

## Workflow & Branching Strategy

### Git Flow Strategy

#### Branch Types

1. **`main`** - Production-ready code
   - Always deployable
   - Protected branch with required reviews
   - Automatic deployment to production

2. **`develop`** - Integration branch
   - Latest development changes
   - Feature branches merge here first
   - Staging environment deployment

3. **`feature/`** - New features
   - Branch from `develop`
   - Naming: `feature/collaborative-editing`
   - Merge back to `develop` via PR

4. **`bugfix/`** - Bug fixes
   - Branch from `develop` or `main`
   - Naming: `bugfix/websocket-connection-issue`
   - Urgent fixes can merge directly to `main`

5. **`hotfix/`** - Production hotfixes
   - Branch from `main`
   - Naming: `hotfix/security-patch-1.2.3`
   - Merge to both `main` and `develop`

#### Workflow Example

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/translation-memory

# Work on feature
git add .
git commit -m "feat: implement translation memory search"

# Push and create PR
git push origin feature/translation-memory
# Create PR to develop via GitHub UI

# After review and approval
git checkout develop
git pull origin develop
git branch -d feature/translation-memory
```

### Commit Message Standards

#### Conventional Commits

```bash
# Format
<type>(<scope>): <subject>

# Types
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation only
style:    # Formatting, missing semicolons, etc.
refactor: # Code change that neither fixes bug nor adds feature
test:     # Adding missing tests
chore:    # Changes to build process or auxiliary tools

# Examples
feat(api): add translation memory endpoints
fix(websocket): resolve connection timeout issues
docs(readme): update setup instructions
test(frontend): add collaborative editing tests
```

#### Good Commit Messages

```bash
# ✅ Good examples
feat(editor): implement real-time cursor synchronization
fix(api): resolve JWT token expiration handling
docs(architecture): add WebSocket design patterns
test(integration): add multi-user collaboration tests

# ❌ Avoid these
fix: stuff
update readme
WIP
temporary fix
```

### Pull Request Process

#### PR Creation Checklist

- [ ] **Branch is up to date** with target branch
- [ ] **Tests pass** locally (`bun test` and `cd backend && make test`)
- [ ] **Linting passes** (`bun run lint` and `cd backend && make lint`)
- [ ] **Documentation updated** if needed
- [ ] **Self-review completed** - review your own changes first

#### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] 🚀 New feature
- [ ] 🐛 Bug fix
- [ ] 📚 Documentation update
- [ ] 🎨 Style/UI change
- [ ] ♻️ Refactoring
- [ ] ✅ Test updates

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Browser compatibility verified

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #[issue number]
```

#### Review Process

1. **Automated Checks**: GitHub Actions run tests and linting
2. **Code Review**: At least one approving review required
3. **Testing**: Reviewer should test changes locally
4. **Documentation**: Verify docs are updated if needed
5. **Merge**: Squash and merge to keep clean history

## Code Standards & Guidelines

### Python/Backend Standards

#### Code Style
```python
# Use Black formatter (automatic)
# Line length: 88 characters
# Follow PEP 8 guidelines

# Example: Good function structure
async def create_translation_entry(
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    quality_score: float = 1.0,
) -> TranslationEntry:
    """Create a new translation memory entry.

    Args:
        source_text: Original text to translate
        target_text: Translated text
        source_lang: Source language code (e.g., 'en')
        target_lang: Target language code (e.g., 'fr')
        context: Optional context metadata
        quality_score: Translation quality (0.0-1.0)

    Returns:
        Created translation entry

    Raises:
        ValidationError: If input validation fails
        DatabaseError: If database operation fails
    """
    # Implementation here
```

#### Type Hints
```python
# Always use type hints
from typing import Dict, List, Optional, Union, Any

# Good examples
def process_document(content: str) -> Dict[str, Any]:
    pass

async def get_translations(
    text: str,
    limit: int = 10
) -> List[TranslationSuggestion]:
    pass

# Use dataclasses for data structures
from dataclasses import dataclass

@dataclass
class TranslationRequest:
    source_text: str
    source_language: str
    target_language: str
    context: Optional[Dict[str, Any]] = None
```

#### Error Handling
```python
# Use specific exceptions
from fastapi import HTTPException

# Good error handling
try:
    result = await translation_service.get_suggestions(text)
except TranslationServiceError as e:
    logger.error(f"Translation service error: {e}")
    raise HTTPException(
        status_code=503,
        detail="Translation service temporarily unavailable"
    )
except ValidationError as e:
    logger.warning(f"Invalid input: {e}")
    raise HTTPException(
        status_code=422,
        detail=str(e)
    )
```

### TypeScript/Frontend Standards

#### Code Style
```typescript
// Use Prettier formatter (automatic)
// 2-space indentation
// Single quotes for strings
// Trailing commas

// Example: Good component structure
interface Props {
  documentId: string;
  onSave?: (content: string) => void;
  readonly?: boolean;
}

export function DocumentEditor({
  documentId,
  onSave,
  readonly = false
}: Props): JSX.Element {
  const [content, setContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Event handlers
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    onSave?.(newContent);
  }, [onSave]);

  // Effects
  useEffect(() => {
    loadDocumentContent();
  }, [documentId]);

  // Render
  return (
    <div className="document-editor">
      {/* Component JSX */}
    </div>
  );
}
```

#### Type Definitions
```typescript
// Create comprehensive type definitions
export interface Document {
  id: string;
  title: string;
  content: Record<string, string>;
  metadata: DocumentMetadata;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentMetadata {
  language: 'en' | 'fr';
  classification: string;
  department: string;
  lastModifiedBy: string;
}

// Use enums for constants
export enum MessageType {
  DOCUMENT_CHANGE = 'document.change',
  CURSOR_POSITION = 'cursor.position',
  USER_PRESENCE = 'user.presence',
}

// Use branded types for IDs
type UserId = string & { readonly brand: unique symbol };
type DocumentId = string & { readonly brand: unique symbol };
```

#### React Best Practices
```typescript
// Custom hooks for logic separation
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    setSocket(ws);

    return () => ws.close();
  }, [url]);

  return { socket, isConnected };
}

// Error boundaries
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }

    return this.props.children;
  }
}
```

### Database Standards

#### Migration Guidelines
```python
# alembic/versions/xxx_add_translation_memory.py
"""Add translation memory tables

Revision ID: abc123
Revises: def456
Create Date: 2025-09-21 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Create table with proper constraints
    op.create_table(
        'translation_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('target_text', sa.Text(), nullable=False),
        sa.Column('source_language', sa.String(5), nullable=False),
        sa.Column('target_language', sa.String(5), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_translation_source_target_lang',
                'source_language', 'target_language'),
    )

def downgrade() -> None:
    op.drop_table('translation_entries')
```

#### Query Optimization
```python
# Use proper indexing and query patterns
class TranslationRepository:
    async def find_similar_translations(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        similarity_threshold: float = 0.8
    ) -> List[TranslationEntry]:
        """Find similar translations using vector search."""

        query = (
            select(TranslationEntry)
            .where(
                and_(
                    TranslationEntry.source_language == source_lang,
                    TranslationEntry.target_language == target_lang,
                    TranslationEntry.embedding.cosine_distance(
                        await self.get_embedding(source_text)
                    ) < (1 - similarity_threshold)
                )
            )
            .order_by(
                TranslationEntry.embedding.cosine_distance(
                    await self.get_embedding(source_text)
                )
            )
            .limit(10)
        )

        result = await self.session.execute(query)
        return result.scalars().all()
```

## Testing Strategy

### Testing Pyramid

```
    /\
   /  \     E2E Tests (Few)
  /____\    Integration Tests (Some)
 /      \   Unit Tests (Many)
/__________\
```

### Unit Testing

#### Backend Unit Tests (pytest)
```python
# backend/tests/unit/test_translation_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from jd_ingestion.services.translation_memory_service import TranslationMemoryService

@pytest.fixture
def translation_service():
    mock_repo = Mock()
    return TranslationMemoryService(mock_repo)

@pytest.mark.asyncio
async def test_get_suggestions_returns_ranked_results(translation_service):
    # Arrange
    mock_entries = [
        TranslationEntry(
            source_text="Hello world",
            target_text="Bonjour le monde",
            confidence=0.95
        )
    ]
    translation_service.repository.find_similar.return_value = mock_entries

    # Act
    suggestions = await translation_service.get_suggestions(
        "Hello world", "en", "fr"
    )

    # Assert
    assert len(suggestions) == 1
    assert suggestions[0].confidence == 0.95
    assert suggestions[0].target_text == "Bonjour le monde"
```

#### Frontend Unit Tests (Bun Test)
```typescript
// src/components/__tests__/DocumentEditor.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentEditor } from '../DocumentEditor';

describe('DocumentEditor', () => {
  test('renders document content', () => {
    const mockDocument = {
      id: 'test-doc',
      content: 'Test content',
    };

    render(<DocumentEditor document={mockDocument} />);

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  test('calls onSave when content changes', () => {
    const mockOnSave = jest.fn();
    const mockDocument = {
      id: 'test-doc',
      content: 'Initial content',
    };

    render(
      <DocumentEditor
        document={mockDocument}
        onSave={mockOnSave}
      />
    );

    const textArea = screen.getByRole('textbox');
    fireEvent.change(textArea, { target: { value: 'New content' } });

    expect(mockOnSave).toHaveBeenCalledWith('New content');
  });
});
```

### Integration Testing

```python
# backend/tests/integration/test_websocket_collaboration.py
@pytest.mark.asyncio
async def test_multiple_users_collaborative_editing():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup document
        document = await create_test_document()

        # Connect two users via WebSocket
        async with websockets.connect(
            f"ws://test/ws/document/{document.id}?token={user1_token}"
        ) as ws1, websockets.connect(
            f"ws://test/ws/document/{document.id}?token={user2_token}"
        ) as ws2:

            # User 1 makes change
            await ws1.send(json.dumps({
                "type": "document.change",
                "payload": {
                    "operation": "insert",
                    "position": 0,
                    "content": "Hello "
                }
            }))

            # User 2 should receive change
            message = await ws2.recv()
            data = json.loads(message)

            assert data["type"] == "document.change"
            assert data["payload"]["content"] == "Hello "
```

### End-to-End Testing (Playwright)

```typescript
// tests/e2e/collaborative-editing.spec.ts
import { test, expect } from '@playwright/test';

test('collaborative editing between multiple users', async ({
  browser
}) => {
  // Create two browser contexts (users)
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();

  const page1 = await context1.newPage();
  const page2 = await context2.newPage();

  // Both users navigate to same document
  await page1.goto('/edit/test-document');
  await page2.goto('/edit/test-document');

  // User 1 types content
  await page1.fill('[data-testid="editor"]', 'Hello from user 1');

  // User 2 should see the content
  await expect(page2.locator('[data-testid="editor"]'))
    .toHaveValue('Hello from user 1');

  // User 2 types additional content
  await page2.fill('[data-testid="editor"]', 'Hello from user 1\nAnd user 2');

  // User 1 should see both changes
  await expect(page1.locator('[data-testid="editor"]'))
    .toHaveValue('Hello from user 1\nAnd user 2');
});
```

### Testing Commands

```bash
# Backend tests
cd backend

# Run all tests
make test

# Run specific test file
poetry run pytest tests/unit/test_translation_service.py -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Frontend tests
# Run unit tests
bun test

# Run unit tests in watch mode
bun run test:unit:watch

# Run E2E tests
bun run test:e2e

# Run all tests
bun run test:all
```

## Deployment Process

### Environment Overview

1. **Development** - Local development environment
2. **Staging** - Testing environment (staging.jddb.gc.ca)
3. **Production** - Live environment (jddb.gc.ca)

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml (simplified)
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      - name: Install dependencies
        run: cd backend && poetry install
      - name: Run tests
        run: cd backend && poetry run pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - name: Install dependencies
        run: bun install
      - name: Run tests
        run: bun test

  deploy-staging:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: # Deployment script

  deploy-production:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: # Production deployment
```

#### Deployment Steps

1. **Automated Testing**: All tests must pass
2. **Security Scanning**: Vulnerability checks
3. **Build Images**: Docker images for frontend/backend
4. **Deploy to Staging**: Automatic for `develop` branch
5. **Manual Approval**: Required for production
6. **Deploy to Production**: Blue-green deployment
7. **Health Checks**: Verify deployment success
8. **Rollback**: Automatic if health checks fail

### Manual Deployment

```bash
# Build and deploy manually
# Backend
cd backend
docker build -t jddb-backend .
docker push ghcr.io/fortinpy85/jddb/backend:latest

# Frontend
docker build -t jddb-frontend .
docker push ghcr.io/fortinpy85/jddb/frontend:latest

# Deploy with docker-compose
docker-compose -f docker-compose.production.yml up -d
```

### Database Migrations

```bash
# Create new migration
cd backend
poetry run alembic revision --autogenerate -m "Add new feature"

# Apply migrations to staging
poetry run alembic upgrade head

# Apply to production (after testing)
# This is typically done through CI/CD
```

## Collaboration Tools

### Communication Channels

#### GitHub
- **Issues**: Bug reports and feature requests
- **Discussions**: Technical discussions and Q&A
- **Pull Requests**: Code review and collaboration
- **Projects**: Sprint planning and task tracking

#### Development Tools
- **Claude Code**: AI-powered development assistant
- **VS Code Live Share**: Real-time collaborative editing
- **GitHub Copilot**: AI code suggestions

### Code Review Process

#### Review Checklist

**Functionality**
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance is acceptable

**Code Quality**
- [ ] Code is readable and well-structured
- [ ] Follows project conventions
- [ ] No code duplication
- [ ] Appropriate abstractions

**Testing**
- [ ] Tests are included and pass
- [ ] Test coverage is adequate
- [ ] Integration points are tested

**Documentation**
- [ ] Code is self-documenting
- [ ] Complex logic has comments
- [ ] API changes are documented
- [ ] User-facing changes have docs

#### Review Comments

```markdown
# Good review comments

## Suggestion with explanation
```suggestion
const isValid = validateInput(input);
```
Consider extracting this validation logic into a separate function for reusability.

## Question for clarification
Why did you choose this approach over using the existing `processDocument` function?

## Positive feedback
Great error handling here! The user feedback will be much clearer.

## Nitpick (non-blocking)
nitpick: Consider using a more descriptive variable name than `data`.
```

### Documentation Standards

#### Code Documentation
```python
# Python docstrings
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts.

    Uses sentence transformers to generate embeddings and computes
    cosine similarity between the vectors.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0.0 and 1.0, where 1.0 is identical

    Raises:
        ValueError: If either text is empty

    Example:
        >>> similarity = calculate_similarity("hello world", "hello earth")
        >>> print(f"Similarity: {similarity:.2f}")
        Similarity: 0.85
    """
```

```typescript
// TypeScript JSDoc
/**
 * Manages WebSocket connections for collaborative editing
 *
 * Handles connection lifecycle, message routing, and automatic
 * reconnection with exponential backoff.
 *
 * @example
 * ```typescript
 * const client = new WebSocketClient('ws://localhost:8000');
 * await client.connect();
 * client.on('message', handleMessage);
 * ```
 */
export class WebSocketClient {
  /**
   * Connect to WebSocket server
   *
   * @param retryAttempts - Number of retry attempts on failure
   * @returns Promise that resolves when connected
   * @throws {ConnectionError} When connection fails after all retries
   */
  async connect(retryAttempts: number = 3): Promise<void> {
    // Implementation
  }
}
```

## Troubleshooting Guide

### Common Issues

#### Frontend Issues

**Build Errors**
```bash
# Clear Bun cache
bun pm cache rm

# Reinstall dependencies
rm -rf node_modules bun.lockb
bun install

# Check TypeScript errors
bun run type-check
```

**Development Server Won't Start**
```bash
# Check port availability
lsof -i :3000  # On Mac/Linux
netstat -ano | findstr :3000  # On Windows

# Try different port
PORT=3001 bun dev

# Check environment variables
cat .env.local
```

**WebSocket Connection Issues**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws/health
```

#### Backend Issues

**Poetry Environment Problems**
```bash
# Recreate virtual environment
cd backend
poetry env remove python
poetry install

# Activate environment
poetry shell

# Check Python path
poetry run which python
```

**Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection
poetry run python -c "
from jd_ingestion.database.connection import get_db_url
print(get_db_url())
"

# Run migrations
poetry run alembic upgrade head
```

**Import Errors**
```bash
# Check PYTHONPATH
poetry run python -c "import sys; print(sys.path)"

# Install in development mode
poetry install --with dev

# Check for circular imports
poetry run python -m py_compile src/jd_ingestion/api/main.py
```

#### Database Issues

**Migration Errors**
```bash
# Check migration status
poetry run alembic current

# Show migration history
poetry run alembic history

# Rollback to previous version
poetry run alembic downgrade -1

# Generate new migration
poetry run alembic revision --autogenerate -m "Description"
```

**Performance Issues**
```bash
# Check database connections
SELECT count(*) FROM pg_stat_activity;

# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM job_descriptions WHERE ...;

# Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats WHERE tablename = 'job_descriptions';
```

### Debugging Techniques

#### Backend Debugging
```python
# Use debugger
import pdb; pdb.set_trace()  # Python debugger

# Or ipdb for better interface
import ipdb; ipdb.set_trace()

# Logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug information")
logger.info("Processing document %s", document_id)
logger.error("Error occurred: %s", str(error))
```

#### Frontend Debugging
```typescript
// Browser debugger
debugger;

// Console logging
console.log('Debug info:', data);
console.table(arrayData);  // For arrays/objects
console.time('operation');  // Performance timing
// ... operation code
console.timeEnd('operation');

// React DevTools
// Install React Developer Tools browser extension
```

#### Network Debugging
```bash
# Check API responses
curl -X GET "http://localhost:8000/api/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -v

# Monitor WebSocket traffic
# Use browser DevTools Network tab, filter by WS

# Check network connectivity
ping api.jddb.gc.ca
nslookup api.jddb.gc.ca
```

### Performance Debugging

#### Backend Performance
```python
# Profile with cProfile
python -m cProfile -o profile.prof script.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.prof

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code
```

#### Frontend Performance
```typescript
// Performance API
const start = performance.now();
// ... operation
const end = performance.now();
console.log(`Operation took ${end - start} milliseconds`);

// React Profiler
import { Profiler } from 'react';

<Profiler id="DocumentEditor" onRender={onRenderCallback}>
  <DocumentEditor />
</Profiler>
```

## Resources & Learning

### Internal Documentation

- **[CLAUDE.md](../CLAUDE.md)**: Development commands and setup
- **[API Documentation](../api/)**: Complete API reference
- **[Architecture Docs](../architecture/)**: System design and patterns
- **[User Guide](../user-guide/)**: End-user documentation

### External Resources

#### Python/FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Poetry Documentation](https://python-poetry.org/docs/)

#### TypeScript/React
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Bun Documentation](https://bun.sh/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

#### DevOps/Infrastructure
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Learning Path for New Developers

#### Week 1: Environment Setup
- [ ] Complete initial setup process
- [ ] Run all tests successfully
- [ ] Make a small documentation change
- [ ] Create first pull request

#### Week 2: Codebase Familiarization
- [ ] Read through main application files
- [ ] Understand API endpoint structure
- [ ] Explore React component hierarchy
- [ ] Review database schema

#### Week 3: First Feature
- [ ] Pick up a "good first issue"
- [ ] Implement feature with tests
- [ ] Get code review feedback
- [ ] Successfully merge PR

#### Week 4: Advanced Features
- [ ] Work on WebSocket-related feature
- [ ] Understand operational transformation
- [ ] Implement translation memory enhancement
- [ ] Review others' pull requests

## Phase 2 Enhancement Features (September 2025)

### ✅ Recently Completed P2 Enhancements

The following Phase 2 features have been successfully implemented and are ready for use:

#### **Enhanced Loading State Messaging**
- **Location**: `src/contexts/LoadingContext.tsx`
- **Description**: Context-aware loading messages that provide specific feedback
- **Usage**:
  ```typescript
  import { useLoadingMessage } from '@/contexts/LoadingContext';

  const { setJobsLoading, setSearchLoading, getMessage } = useLoadingMessage();

  // Set specific loading context
  setJobsLoading(); // Shows "Loading Jobs: Fetching job descriptions from database..."
  setSearchLoading(); // Shows "Searching: Finding matching job descriptions..."
  ```
- **Available Contexts**: dashboard, jobs, search, comparison, upload, job-details, stats, processing, generic

#### **Comprehensive Keyboard Navigation**
- **Location**: `src/hooks/useKeyboardShortcuts.ts`, `src/components/ui/keyboard-shortcuts-modal.tsx`
- **Description**: 11+ keyboard shortcuts for power users with help modal
- **Key Shortcuts**:
  - `Ctrl+1-6`: Navigate between tabs (Dashboard, Jobs, Upload, Search, Compare, Statistics)
  - `/` or `Ctrl+K`: Focus search input
  - `Ctrl+N`: Navigate to upload tab
  - `?` or `Ctrl+H`: Show keyboard shortcuts modal
  - `Ctrl+Shift+T`: Toggle theme (when implemented)
- **Usage**:
  ```typescript
  import { useJDDBKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

  const { shortcuts } = useJDDBKeyboardShortcuts({
    onNavigateToJobs: () => setActiveTab("jobs"),
    onFocusSearch: () => focusSearchInput(),
    onShowShortcuts: () => openHelpModal()
  });
  ```

#### **Translation Memory Service Improvements**
- **Location**: `backend/src/jd_ingestion/services/translation_memory_service.py`
- **Description**: Updated core async patterns for better performance
- **Key Changes**:
  - Converted `create_project()` and `add_translation_memory()` to proper async methods
  - Fixed incorrect async session handling patterns
  - Updated database operations to use `await` consistently
  - Improved error handling with proper rollback patterns

#### **Cross-Platform Development Environment**
- **Location**: `playwright.config.ts`
- **Description**: Enhanced Playwright configuration for Windows development
- **Features**:
  - Platform-aware command execution
  - Proper Windows environment variable syntax
  - 151 comprehensive E2E tests ready for execution
  - WebSocket testing support

#### **Enhanced Error Handling Patterns**
- **Location**: Multiple backend endpoint files
- **Description**: Improved exception specificity and logging
- **Pattern**:
  ```python
  try:
      result = await service_operation()
  except SQLAlchemyError as e:
      logger.error(f"Database error: {e}")
      raise HTTPException(status_code=500, detail="Database operation failed")
  except ValueError as e:
      logger.warning(f"Validation error: {e}")
      raise HTTPException(status_code=422, detail=str(e))
  except Exception as e:
      logger.error(f"Unexpected error: {e}")
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

### Development Environment Enhancements

#### **Test Infrastructure Improvements**
- **Comprehensive Backend Coverage**: 100% of backend modules now have unit tests
- **E2E Test Suite**: 151 tests covering keyboard navigation, accessibility, and usability
- **Performance Testing**: Benchmarking and monitoring capabilities
- **Mock Infrastructure**: Reusable patterns for async service mocking

#### **Build System Stability**
- **Frontend**: Fast Bun-based builds (<1.2s build times)
- **Backend**: Poetry-managed dependencies with isolated environments
- **Cross-Platform**: Windows, macOS, and Linux support
- **Hot Reload**: Both frontend and backend support live reloading

### Using P2 Features in Development

#### **Keyboard Shortcuts Development**
```typescript
// Add new keyboard shortcuts
const shortcuts = createJDDBShortcuts({
  onCustomAction: () => handleCustomAction(),
  // ... other handlers
});

// The shortcuts are automatically enabled and formatted for display
```

#### **Loading States Development**
```typescript
// In your components
const { setCustomMessage, clearCustomMessage } = useLoadingMessage();

// Set custom loading message
setCustomMessage("Processing Document", "Analyzing content and extracting sections...");

// Clear when done
clearCustomMessage();
```

#### **Translation Memory Integration**
```python
# In your backend services
from jd_ingestion.services.translation_memory_service import TranslationMemoryService

service = TranslationMemoryService()

# Create translation project
project = await service.create_project(
    name="Job Descriptions FR-EN",
    source_language="fr",
    target_language="en",
    db=db_session
)

# Add translation entry
entry = await service.add_translation_memory(
    project_id=project.id,
    source_text="Directeur général",
    target_text="Director General",
    source_language="fr",
    target_language="en",
    db=db_session
)
```

### Team Contacts

- **Technical Questions**: Create GitHub Discussion
- **Urgent Issues**: GitHub Issues with `urgent` label
- **General Discussion**: Team Slack/Discord
- **Code Reviews**: Tag appropriate reviewers in PR

### Development Best Practices Summary

1. **Write tests first** when possible (TDD)
2. **Keep PRs small** and focused
3. **Document complex logic** with comments
4. **Follow the established patterns** in the codebase
5. **Ask questions early** rather than struggling alone
6. **Review your own PR** before requesting review
7. **Be constructive** in code review feedback
8. **Keep dependencies up to date** regularly
9. **Monitor performance** of new features
10. **Celebrate team successes** and learn from failures

---

*Welcome to the JDDB development team! This document is a living guide that evolves with our practices. Please suggest improvements through pull requests.*
