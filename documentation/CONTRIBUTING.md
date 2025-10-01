# Contributing to JDDB

Thank you for your interest in contributing to JDDB! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** with Poetry for dependency management
- **Node.js 18+** with Bun runtime
- **PostgreSQL 15+** with pgvector extension
- **Git** for version control
- **Code Editor** with TypeScript and Python support (VS Code recommended)

### Development Setup

1. **Fork and Clone**
   ```bash
   git fork https://github.com/your-org/jddb
   git clone https://github.com/your-username/jddb
   cd jddb
   ```

2. **Backend Setup**
   ```bash
   cd backend
   poetry install                # Install dependencies
   make db-init                  # Initialize database
   make sample-data              # Create test data
   make test                     # Verify setup
   ```

3. **Frontend Setup**
   ```bash
   bun install                   # Install dependencies
   bun dev                       # Start development server
   ```

4. **Environment Configuration**
   ```bash
   # Copy example environment files
   cp backend/.env.example backend/.env
   cp .env.example .env.local

   # Edit with your configuration
   # backend/.env - Add database URL and OpenAI API key
   # .env.local - Set API URL
   ```

## 📋 Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: New features and enhancements
- **fix/***: Bug fixes
- **docs/***: Documentation improvements

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(api): add semantic search endpoint
fix(ui): resolve pagination bug in job list
docs(readme): update installation instructions
test(backend): add integration tests for file upload
chore(deps): update FastAPI to v0.104
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `perf`: Performance improvements

### Development Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Backend testing
   cd backend
   make test                     # Full test suite
   make lint                     # Code quality
   make type-check               # Type checking

   # Frontend testing (when available)
   bun test
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(api): add new search filters"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request via GitHub interface
   ```

## 🧪 Testing Guidelines

### Backend Testing

**Unit Tests**
- Test individual functions and classes
- Mock external dependencies (OpenAI, database)
- Aim for >95% code coverage

**Integration Tests**
- Test API endpoints end-to-end
- Use test database with real PostgreSQL
- Verify database operations and business logic

**Test Structure**
```python
# tests/unit/test_service.py
import pytest
from unittest.mock import Mock, patch

class TestEmbeddingService:
    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    async def test_generate_embedding_success(self, mock_openai, embedding_service):
        # Test implementation
        pass
```

**Running Tests**
```bash
cd backend
make test                        # All tests
poetry run pytest tests/unit/   # Unit tests only
poetry run pytest tests/integration/ # Integration tests only
poetry run pytest -v --tb=short # Verbose output
```

### Frontend Testing

**Component Tests** (when implemented)
- Test React components in isolation
- Mock API calls and external dependencies
- Use React Testing Library for user-centric tests

**Integration Tests** (planned)
- Test user workflows end-to-end
- Use Playwright for browser automation
- Verify API integration

## 📝 Code Style Guidelines

### Python (Backend)

**Formatting**
- Use `black` for code formatting
- Use `isort` for import sorting
- Maximum line length: 88 characters

**Style**
- Follow PEP 8 conventions
- Use type hints for all functions
- Use descriptive variable and function names
- Add docstrings for public APIs

**Example**
```python
from typing import List, Optional
from pydantic import BaseModel

class JobMetadata(BaseModel):
    """Job metadata with structured fields."""

    department: Optional[str] = None
    classification: Optional[str] = None
    reports_to: Optional[str] = None

async def process_job_file(
    file_path: str,
    extract_sections: bool = True
) -> ProcessingResult:
    """Process a job description file.

    Args:
        file_path: Path to the job description file
        extract_sections: Whether to extract content sections

    Returns:
        ProcessingResult with extracted data

    Raises:
        FileNotFoundError: If file doesn't exist
        ProcessingError: If file processing fails
    """
    # Implementation
```

**Quality Checks**
```bash
make format                      # Format code
make lint                        # Check style
make type-check                  # Type checking
```

### TypeScript (Frontend)

**Formatting**
- Use Prettier for code formatting
- Use ESLint for style enforcement
- 2-space indentation
- Single quotes for strings

**Style**
- Use TypeScript strict mode
- Define interfaces for all data structures
- Use descriptive component and function names
- Prefer functional components with hooks

**Example**
```typescript
interface JobDescription {
  id: string;
  title: string;
  classification: string;
  department?: string;
  language: 'en' | 'fr';
  sections: JobSection[];
}

interface SearchFilters {
  classification?: string;
  department?: string;
  language?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export const JobList: React.FC<{ filters: SearchFilters }> = ({ filters }) => {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(false);

  // Component implementation
};
```

## 🛠️ Code Architecture

### Backend Architecture

**Layer Structure**
```
src/jd_ingestion/
├── api/                         # FastAPI routes and endpoints
│   ├── endpoints/               # Route handlers
│   └── dependencies.py         # Dependency injection
├── core/                        # Business logic
│   ├── processors/              # File processing logic
│   └── services/                # External service integrations
├── database/                    # Data access layer
│   ├── models/                  # SQLAlchemy models
│   └── repositories/            # Data access objects
└── config/                      # Configuration and settings
```

**Principles**
- **Dependency Injection**: Use FastAPI's dependency system
- **Async/Await**: Use async patterns for I/O operations
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Validation**: Use Pydantic models for request/response validation

**Adding New Endpoints**
```python
# api/endpoints/new_feature.py
from fastapi import APIRouter, Depends
from ..core.services import NewFeatureService
from ..database.dependencies import get_database

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/process")
async def process_item(
    item: ItemRequest,
    service: NewFeatureService = Depends(),
    db: Database = Depends(get_database)
) -> ItemResponse:
    """Process an item through the new feature."""
    return await service.process(item, db)
```

### Frontend Architecture

**Component Structure**
```
src/
├── app/                         # Next.js app router
│   ├── page.tsx                 # Main dashboard
│   └── jobs/                    # Job-related pages
├── components/                  # Reusable UI components
│   ├── ui/                      # Basic UI primitives
│   └── features/                # Feature-specific components
└── lib/                         # Utilities and services
    ├── api.ts                   # API client
    ├── store.ts                 # State management
    └── utils.ts                 # Helper functions
```

**Patterns**
- **Component Composition**: Build complex UIs from simple components
- **Custom Hooks**: Extract stateful logic into reusable hooks
- **State Management**: Use Zustand for global state
- **API Integration**: Centralized API client with error handling

**Adding New Components**
```typescript
// components/features/NewFeature.tsx
import { useState } from 'react';
import { Button } from '../ui/button';
import { useNewFeature } from '../../lib/hooks/useNewFeature';

interface NewFeatureProps {
  onComplete?: (result: FeatureResult) => void;
}

export const NewFeature: React.FC<NewFeatureProps> = ({ onComplete }) => {
  const { process, loading, error } = useNewFeature();

  // Component implementation
};
```

## 🔍 Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally (`make test`)
- [ ] Code follows style guidelines (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated for notable changes

### PR Description Template

```markdown
## Description
Brief description of the changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated Checks**: CI pipeline runs tests and quality checks
2. **Code Review**: Team members review for:
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Security considerations
3. **Approval**: At least one approving review required
4. **Merge**: Squash and merge to maintain clean history

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues for duplicates
2. Test with latest version
3. Reproduce in clean environment

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
- OS: [e.g. Windows 10, macOS 12]
- Python version: [e.g. 3.9.7]
- Node.js version: [e.g. 18.17.0]
- Browser [e.g. chrome, safari]

**Additional context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Before Requesting

1. Check roadmap and existing issues
2. Consider if it fits project scope
3. Think about implementation approach

### Feature Request Template

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.

**Implementation ideas**
If you have ideas about how this could be implemented, please share them.
```

## 🏷️ Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Build and test production artifacts
- [ ] Create release notes
- [ ] Tag release in Git
- [ ] Deploy to production
- [ ] Announce release

## 🔐 Security

### Reporting Security Issues

Please report security vulnerabilities privately to the maintainers rather than opening public issues.

### Security Guidelines

- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive configuration
- Validate all user inputs
- Follow OWASP security best practices
- Keep dependencies updated

## 📞 Getting Help

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community discussion
- **Documentation**: Check docs/ directory first

### Maintainer Contact

For questions about contributing or project direction, reach out to:
- Architecture questions: Open GitHub Discussion
- Security issues: Private contact via GitHub
- General questions: GitHub Issues with "question" label

## 🎯 Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- GitHub contributors page
- Special recognition for significant contributions

Thank you for contributing to JDDB! 🙏

---

*Last Updated: December 2025*
