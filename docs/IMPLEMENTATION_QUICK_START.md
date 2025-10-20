# JDDB Phase 7 Implementation Quick Start Guide

**Target Audience**: Developers implementing AI Improvement and Translation Mode
**Prerequisites**: Familiarity with FastAPI, React, PostgreSQL, and OpenAI API

---

## 🚀 Quick Start Checklist

### 1. Environment Setup (15 minutes)

```bash
# Backend setup
cd backend
poetry install
poetry run alembic upgrade head  # Apply all migrations

# Set environment variables
export OPENAI_API_KEY="sk-..."  # Required for AI features
export DATABASE_URL="postgresql://user:pass@localhost:5432/jddb"

# Frontend setup
cd ../
npm install

# Set frontend environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
```

### 2. Apply New Database Migrations (5 minutes)

```bash
cd backend

# For AI Improvement Mode
poetry run alembic upgrade +1  # Apply ai_improvement_tables migration

# For Translation Mode
poetry run alembic upgrade +1  # Apply translation_tables migration

# Verify migrations
poetry run alembic current
poetry run alembic history
```

### 3. Verify Database Schema (5 minutes)

```sql
-- Connect to PostgreSQL
psql -U user -d jddb

-- Verify AI tables exist
\dt ai_*

-- Verify translation tables exist
\dt translation_*
\dt bilingual_*
\dt terminology_*

-- Check indexes
\di ai_*
\di translation_*
```

---

## 📦 AI Improvement Mode Implementation

### Step-by-Step Implementation Guide

#### Phase 1: Backend Service (Week 1)

**File**: `backend/src/jd_ingestion/services/ai_improvement_service.py`

```python
# Already complete in roadmap - copy from AI_IMPROVEMENT_IMPLEMENTATION_ROADMAP.md
# Key methods to test:
# - analyze_section(): Generates AI suggestions
# - calculate_quality_score(): Scores content quality
# - _split_into_sentences(): Sentence tokenization
```

**Test the service**:
```bash
cd backend
poetry run pytest tests/unit/test_ai_improvement_service.py -v
```

#### Phase 2: API Endpoints (Week 1)

**File**: `backend/src/jd_ingestion/api/endpoints/ai_improvement.py`

```python
# Already complete in roadmap - copy from AI_IMPROVEMENT_IMPLEMENTATION_ROADMAP.md
# Key endpoints:
# - POST /ai-improvement/sessions/start
# - POST /ai-improvement/sections/analyze
# - POST /ai-improvement/suggestions/action
# - POST /ai-improvement/sessions/complete
```

**Register router in main.py**:
```python
from jd_ingestion.api.endpoints import ai_improvement

app.include_router(ai_improvement.router, prefix="/api")
```

**Test endpoints**:
```bash
# Start backend server
poetry run uvicorn jd_ingestion.api.main:app --reload

# Test with curl
curl -X POST http://localhost:8000/api/ai-improvement/sessions/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "job_id": 1,
    "configuration": {
      "granularity": "sentence",
      "aggressiveness": "moderate",
      "focus_areas": ["clarity", "professionalism"]
    }
  }'
```

#### Phase 3: Frontend Context (Week 2)

**File**: `src/contexts/AIImprovementContext.tsx`

```typescript
// Already complete in roadmap - copy from AI_IMPROVEMENT_IMPLEMENTATION_ROADMAP.md
// Provides state management for AI improvement sessions
```

**Add to App Provider**:
```typescript
// src/app/page.tsx or root layout
import { AIImprovementProvider } from '@/contexts/AIImprovementContext';

<AIImprovementProvider>
  {/* Your app components */}
</AIImprovementProvider>
```

#### Phase 4: Frontend UI (Week 2-3)

**File**: `src/components/ai/AIImprovementView.tsx`

```typescript
// Already complete in roadmap - copy from AI_IMPROVEMENT_IMPLEMENTATION_ROADMAP.md
// Split-pane comparison view with accept/reject/modify controls
```

**Integrate with Job Detail View**:
```typescript
// src/components/jobs/JobDetailView.tsx
import { AIImprovementView } from '@/components/ai/AIImprovementView';

// Add state
const [showAIImprovement, setShowAIImprovement] = useState(false);

// Add button
<Button onClick={() => setShowAIImprovement(true)}>
  AI Improvement Mode
</Button>

// Render when active
{showAIImprovement && (
  <AIImprovementView
    jobId={job.id}
    sections={job.sections}
    onExit={() => setShowAIImprovement(false)}
  />
)}
```

#### Phase 5: API Client Methods (Week 2)

**File**: `src/lib/api.ts`

```typescript
// Add to ApiClient class

async startImprovementSession(
  jobId: number,
  configuration: ImprovementConfiguration
): Promise<SessionStartResponse> {
  return this.request('/ai-improvement/sessions/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, configuration }),
  });
}

async analyzeSectionForImprovement(
  sessionId: number,
  sectionId: number
): Promise<SectionAnalysisResponse> {
  return this.request('/ai-improvement/sections/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, section_id: sectionId }),
  });
}

async handleSuggestionAction(
  suggestionId: number,
  action: 'accept' | 'reject' | 'modify',
  modifiedText?: string,
  feedback?: string
): Promise<void> {
  return this.request('/ai-improvement/suggestions/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      suggestion_id: suggestionId,
      action,
      modified_text: modifiedText,
      advisor_feedback: feedback,
    }),
  });
}

async completeImprovementSession(
  sessionId: number
): Promise<SessionCompleteResponse> {
  return this.request('/ai-improvement/sessions/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
}
```

#### Phase 6: Testing (Week 4)

```bash
# Backend tests
cd backend
poetry run pytest tests/unit/test_ai_improvement_service.py -v
poetry run pytest tests/integration/test_ai_improvement_api.py -v

# Frontend tests
npm run test:unit -- src/components/ai/__tests__/AIImprovementView.test.tsx

# E2E tests
npm run test:e2e -- tests/ai-improvement.spec.ts
```

---

## 🌐 Translation Mode Implementation

### Step-by-Step Implementation Guide

#### Phase 1: Database and Models (Week 1-2)

**Already Complete**:
- ✅ Database migration script (`TRANSLATION_MODE_IMPLEMENTATION_ROADMAP.md`)
- ✅ SQLAlchemy models (all 6 tables)

**Apply migration**:
```bash
cd backend
poetry run alembic upgrade +1  # Apply translation_tables migration
```

**Verify tables**:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%translation%' OR table_name LIKE '%bilingual%';
```

#### Phase 2: Translation Service (Week 3-4)

**File**: `backend/src/jd_ingestion/services/translation_service.py`

```python
"""
Translation Service
Handles machine translation and translation memory lookups
"""

import openai
from typing import List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jd_ingestion.database.models import TranslationMemory, TerminologyDatabase
from jd_ingestion.config.settings import settings

openai.api_key = settings.OPENAI_API_KEY


@dataclass
class TranslationSuggestion:
    """Translation suggestion with TM and MT sources"""
    source_text: str
    mt_translation: Optional[str]
    tm_translation: Optional[str]
    tm_match_score: float
    combined_suggestion: str


class TranslationService:
    """Service for machine translation and TM lookups"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.mt_model = "gpt-4-turbo-preview"
        self.tm_fuzzy_threshold = 0.75

    async def translate_sentence(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        section_type: Optional[str] = None
    ) -> TranslationSuggestion:
        """
        Translate a sentence using TM first, then MT if needed
        """
        # Search TM for exact or fuzzy matches
        tm_match, tm_score = await self._search_translation_memory(
            source_text, source_lang, target_lang, section_type
        )

        # Get machine translation
        mt_translation = await self._machine_translate(
            source_text, source_lang, target_lang, section_type
        )

        # Determine combined suggestion
        if tm_score >= 0.95:  # Exact or near-exact TM match
            combined = tm_match
        elif tm_score >= self.tm_fuzzy_threshold:  # Fuzzy TM match
            combined = tm_match  # Prefer TM over MT for fuzzy matches
        else:  # Low TM match, use MT
            combined = mt_translation

        return TranslationSuggestion(
            source_text=source_text,
            mt_translation=mt_translation,
            tm_translation=tm_match,
            tm_match_score=tm_score,
            combined_suggestion=combined
        )

    async def _search_translation_memory(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        section_type: Optional[str] = None
    ) -> Tuple[Optional[str], float]:
        """
        Search TM for best match using fuzzy matching
        Returns (best_translation, confidence_score)
        """
        # Query TM for potential matches
        query = select(TranslationMemory).where(
            TranslationMemory.source_language == source_lang,
            TranslationMemory.target_language == target_lang
        )

        if section_type:
            query = query.where(TranslationMemory.section_type == section_type)

        result = await self.db.execute(query)
        tm_entries = result.scalars().all()

        if not tm_entries:
            return None, 0.0

        # Find best fuzzy match
        best_match = None
        best_score = 0.0

        for entry in tm_entries:
            score = SequenceMatcher(None, source_text, entry.source_text).ratio()
            if score > best_score:
                best_score = score
                best_match = entry.target_text

                # Update usage stats
                entry.usage_count += 1
                entry.last_used = func.now()

        await self.db.commit()

        return best_match, best_score

    async def _machine_translate(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        section_type: Optional[str] = None
    ) -> str:
        """
        Machine translate using OpenAI GPT-4
        """
        lang_names = {'en': 'English', 'fr': 'French'}

        system_prompt = f"""You are a professional translator specializing in Canadian government job descriptions.
Translate the following text from {lang_names[source_lang]} to {lang_names[target_lang]}.

Guidelines:
- Maintain professional tone appropriate for executive-level government positions
- Preserve meaning and intent exactly
- Use appropriate governmental terminology
- Ensure natural fluency in target language
"""

        if section_type:
            system_prompt += f"\nThis text is from the '{section_type}' section of a job description."

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.mt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": source_text}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Machine translation failed: {str(e)}")

    async def lookup_terminology(
        self,
        term: str,
        source_lang: str
    ) -> List[dict]:
        """
        Lookup term in terminology database
        """
        if source_lang == 'en':
            query = select(TerminologyDatabase).where(
                func.lower(TerminologyDatabase.term_english).contains(term.lower())
            )
        else:
            query = select(TerminologyDatabase).where(
                func.lower(TerminologyDatabase.term_french).contains(term.lower())
            )

        query = query.where(TerminologyDatabase.validation_status == 'validated')
        result = await self.db.execute(query)
        terms = result.scalars().all()

        return [
            {
                'term_en': t.term_english,
                'term_fr': t.term_french,
                'category': t.category,
                'definition': t.definition_english if source_lang == 'en' else t.definition_french,
                'usage_count': t.usage_count
            }
            for t in terms
        ]

    async def validate_concurrence(
        self,
        english_sections: List[dict],
        french_sections: List[dict]
    ) -> dict:
        """
        Validate concurrence between English and French versions
        Returns validation report with discrepancies
        """
        discrepancies = []

        # Check section count
        if len(english_sections) != len(french_sections):
            discrepancies.append({
                'type': 'section_count_mismatch',
                'english_count': len(english_sections),
                'french_count': len(french_sections)
            })

        # Check each section pair
        for idx, (en_section, fr_section) in enumerate(zip(english_sections, french_sections)):
            if en_section['section_type'] != fr_section['section_type']:
                discrepancies.append({
                    'type': 'section_type_mismatch',
                    'index': idx,
                    'english_type': en_section['section_type'],
                    'french_type': fr_section['section_type']
                })

            # Check sentence count
            en_sentences = en_section['content'].split('. ')
            fr_sentences = fr_section['content'].split('. ')

            if len(en_sentences) != len(fr_sentences):
                discrepancies.append({
                    'type': 'sentence_count_mismatch',
                    'section': en_section['section_type'],
                    'english_count': len(en_sentences),
                    'french_count': len(fr_sentences)
                })

        validation_result = 'pass' if len(discrepancies) == 0 else 'fail'

        return {
            'result': validation_result,
            'discrepancies': discrepancies,
            'discrepancy_count': len(discrepancies)
        }
```

**Test the service**:
```python
# tests/unit/test_translation_service.py
import pytest
from jd_ingestion.services.translation_service import TranslationService

@pytest.mark.asyncio
async def test_translate_sentence_with_tm_match(db_session):
    service = TranslationService(db_session)

    suggestion = await service.translate_sentence(
        source_text="The incumbent is accountable for strategic planning.",
        source_lang="en",
        target_lang="fr",
        section_type="general_accountability"
    )

    assert suggestion.combined_suggestion is not None
    assert suggestion.tm_match_score >= 0.0
```

#### Phase 3: API Endpoints (Week 3-4)

**File**: `backend/src/jd_ingestion/api/endpoints/translation.py`

```python
"""
Translation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from jd_ingestion.database.connection import get_async_session
from jd_ingestion.services.translation_service import TranslationService
from jd_ingestion.api.dependencies import get_api_key

router = APIRouter(prefix="/translation", tags=["Translation"])


class TranslationSessionRequest(BaseModel):
    source_job_id: int
    source_language: str = Field(pattern="^(en|fr)$")
    target_language: str = Field(pattern="^(en|fr)$")


class TranslateSectionRequest(BaseModel):
    session_id: int
    section_id: int


@router.post("/sessions/start")
async def start_translation_session(
    request: TranslationSessionRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """Start a new translation session"""
    # Implementation here
    pass


@router.post("/sections/translate")
async def translate_section(
    request: TranslateSectionRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """Get translation suggestions for a section"""
    # Implementation here
    pass


# Additional endpoints...
```

---

## 🧪 Testing Strategy

### Backend Testing

```bash
# Unit tests (fast, no external dependencies)
poetry run pytest tests/unit/ -v

# Integration tests (database required)
poetry run pytest tests/integration/ -v

# All tests
poetry run pytest tests/ -v --cov=jd_ingestion

# Specific test file
poetry run pytest tests/unit/test_ai_improvement_service.py::test_analyze_section -v
```

### Frontend Testing

```bash
# Unit tests
npm run test:unit

# E2E tests (requires backend running)
npm run test:e2e

# Watch mode for development
npm run test:unit:watch

# Coverage report
npm run test:unit:coverage
```

---

## 🐛 Common Issues and Solutions

### Issue: OpenAI API Rate Limit

**Error**: `openai.error.RateLimitError: Rate limit exceeded`

**Solution**:
```python
# Add retry logic with exponential backoff
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_openai_api(...):
    # Your OpenAI API call
    pass
```

### Issue: Database Migration Conflicts

**Error**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**:
```bash
# Check current revision
poetry run alembic current

# View migration history
poetry run alembic history

# Downgrade and re-apply
poetry run alembic downgrade -1
poetry run alembic upgrade head
```

### Issue: Frontend API Connection

**Error**: `TypeError: Cannot read property 'data' of undefined`

**Solution**:
```typescript
// Check .env.local file exists
// Verify API URL is correct
console.log(process.env.NEXT_PUBLIC_API_URL);

// Add error handling
try {
  const response = await apiClient.someMethod();
  // Handle response
} catch (error) {
  console.error('API Error:', error);
  // Show user-friendly error message
}
```

---

## 📚 Additional Resources

### Documentation

- [AI Improvement Roadmap](./AI_IMPROVEMENT_IMPLEMENTATION_ROADMAP.md)
- [Translation Mode Roadmap](./TRANSLATION_MODE_IMPLEMENTATION_ROADMAP.md)
- [Comprehensive Status Report](./COMPREHENSIVE_IMPLEMENTATION_STATUS.md)
- [User Stories & Testing](./SENIOR_ADVISOR_USER_STORIES.md)

### API Documentation

- Backend: http://localhost:8000/api/docs (Swagger UI)
- Backend: http://localhost:8000/api/redoc (ReDoc)

### External APIs

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

## ✅ Final Checklist

Before starting implementation, ensure:

- [ ] PostgreSQL database is running and accessible
- [ ] OpenAI API key is configured
- [ ] Backend dependencies installed (`poetry install`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] All existing tests pass
- [ ] Development environment variables configured
- [ ] You've read the comprehensive implementation status report
- [ ] You understand the database schema changes
- [ ] You're familiar with the API endpoint specifications

**Ready to implement? Start with AI Improvement Mode Week 1 tasks!**
