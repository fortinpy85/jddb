# Phase 3 Frontend Integration Plan

**Date**: 2025-10-02
**Status**: Planning
**Dependencies**: Backend Phase 3 Complete ✅

---

## Overview

With Phase 3 backend fully implemented and tested, we now need to integrate the AI features into the frontend React application. This plan outlines the components, API integrations, and user experience enhancements needed.

---

## 🎯 Goals

1. **Real-time AI Assistance**: Provide live bias detection and quality feedback as users write
2. **Visual Quality Indicators**: Display quality scores with color-coded metrics
3. **One-Click Improvements**: Allow users to accept AI suggestions with single click
4. **Content Generation**: Enable AI-powered section completion and enhancement
5. **Intuitive UX**: Seamless integration that doesn't interrupt writing flow

---

## 📋 Components to Build

### 1. AI Suggestions Panel (`src/components/ai/AISuggestionsPanel.tsx`)

**Purpose**: Display real-time AI suggestions as user types/edits content

**Features**:
- Live bias detection with inline highlighting
- Grammar and style suggestions
- Quality score display
- Accept/Reject actions for each suggestion
- Keyboard shortcuts for quick actions

**API Integration**:
```typescript
import { api } from '@/lib/api';

// Analyze text for bias
const biasResult = await api.post('/ai/analyze-bias', {
  text: editorContent,
  analysis_types: ['gender', 'age', 'disability', 'cultural'],
});

// Get improvement suggestions
const suggestions = await api.post('/ai/suggest-improvements', {
  text: editorContent,
  suggestion_types: ['grammar', 'style', 'clarity'],
});
```

**UI Design**:
```
┌─────────────────────────────────┐
│ 🤖 AI Suggestions      [×]      │
├─────────────────────────────────┤
│ ⚠️ Bias Detected (3)            │
│  • "young" → "collaborative"    │
│    [Accept] [Ignore]            │
│  • "he" → "they"                │
│    [Accept] [Ignore]            │
│                                 │
│ 📝 Style (2)                    │
│  • Use active voice here        │
│    [Apply] [Ignore]             │
└─────────────────────────────────┘
```

**State Management**:
```typescript
interface AISuggestionsState {
  suggestions: Suggestion[];
  loading: boolean;
  autoAnalyze: boolean;
  lastAnalyzedAt: Date | null;
}
```

---

### 2. Quality Dashboard (`src/components/ai/QualityDashboard.tsx`)

**Purpose**: Visual display of comprehensive quality metrics

**Features**:
- Overall quality score (0-100) with color coding
- Dimension breakdown (Readability, Completeness, Clarity, Inclusivity, Compliance)
- Progress bars for each dimension
- Top recommendations list
- Improvement priority indicators
- Historical trend (optional Phase 4)

**API Integration**:
```typescript
const qualityScore = await api.post('/ai/quality-score', {
  job_data: {
    sections: {
      general_accountability: content.accountability,
      organization_structure: content.structure,
      key_responsibilities: content.responsibilities,
      qualifications: content.qualifications,
    },
  },
});
```

**UI Design**:
```
┌─────────────────────────────────────────┐
│ 📊 Quality Score                         │
│                                          │
│     ┌────────┐                           │
│     │   73   │  Fair                     │
│     └────────┘  🟡                       │
│                                          │
│ Readability        ▓▓▓▓▓▓░░░░ 57% 🟡    │
│ Completeness       ▓▓▓▓▓▓░░░░ 61% 🟡    │
│ Clarity            ▓▓▓▓▓▓▓░░░ 70% 🟢    │
│ Inclusivity        ▓▓▓▓▓▓▓▓▓▓ 100% 🟢   │
│ Compliance         ▓▓▓▓▓▓▓▓░░ 80% 🟢    │
│                                          │
│ 🎯 Priority: Readability, Completeness  │
│                                          │
│ Top Recommendations:                     │
│  1. Simplify sentences (Grade 13→8-10)  │
│  2. Expand Accountability section        │
│  3. Add paragraph breaks                 │
└─────────────────────────────────────────┘
```

**Recharts Integration**:
```typescript
import { RadialBarChart, RadialBar } from 'recharts';

<RadialBarChart
  data={[
    { name: 'Quality', value: qualityScore, fill: getScoreColor(qualityScore) }
  ]}
>
  <RadialBar dataKey="value" />
</RadialBarChart>
```

---

### 3. Bias Detector Widget (`src/components/ai/BiasDetector.tsx`)

**Purpose**: Inline bias highlighting and correction

**Features**:
- Real-time text highlighting
- Hover tooltips with alternatives
- Severity indicators (critical, high, medium, low)
- One-click replacements
- Bias-free badge when clean
- Category filtering (gender, age, disability, cultural)

**API Integration**:
```typescript
const biasAnalysis = await api.post('/ai/analyze-bias', {
  text: sectionContent,
  analysis_types: activeFilters,
  use_gpt4: true, // Enable context-aware detection
});
```

**UI Design**:
```
Text with bias detection:

"We need a [young]🔴 [energetic]🟡 [salesman]🔴..."
           ↓ hover
      ┌─────────────────────────┐
      │ ⚠️ Age Bias (High)      │
      │ "young" suggests age    │
      │ preference              │
      │                         │
      │ Alternatives:           │
      │  • collaborative        │
      │  • innovative           │
      │  • dynamic              │
      │                         │
      │ [Replace] [Ignore All]  │
      └─────────────────────────┘
```

**Mark Component for Highlighting**:
```typescript
import { Mark } from '@/components/ui/mark';

<Mark
  text={content}
  highlights={biasIssues.map(issue => ({
    start: issue.start_index,
    end: issue.end_index,
    color: getSeverityColor(issue.severity),
    tooltip: <BiasTooltip issue={issue} />,
  }))}
/>
```

---

### 4. Content Generator Modal (`src/components/ai/ContentGenerator.tsx`)

**Purpose**: AI-powered section creation and completion

**Features**:
- Section type selection
- Partial content input
- Context fields (classification, department, etc.)
- Language selection (EN/FR)
- Generated content preview
- Edit and refine options
- Insert to document button

**API Integration**:
```typescript
// Auto-complete section
const completion = await api.post('/ai/complete-section', {
  section_type: 'general_accountability',
  partial_content: userInput,
  classification: 'EX-01',
  language: 'en',
  context: {
    department: 'Finance',
    reporting_to: 'CFO',
  },
});

// Enhance existing content
const enhanced = await api.post('/ai/enhance-content', {
  text: originalText,
  enhancement_types: ['clarity', 'active_voice', 'conciseness'],
  language: 'en',
});
```

**UI Design**:
```
┌──────────────────────────────────────────┐
│ ✨ AI Content Generator          [×]     │
├──────────────────────────────────────────┤
│ Section Type: [General Accountability ▼] │
│ Classification: [EX-01         ]         │
│ Language: (•) English  ( ) French        │
│                                          │
│ Partial Content:                         │
│ ┌────────────────────────────────────┐  │
│ │ The Director will oversee...       │  │
│ │ [cursor]                           │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [🤖 Generate Completion]                 │
│                                          │
│ Generated Preview:                       │
│ ┌────────────────────────────────────┐  │
│ │ ...strategic planning and          │  │
│ │ implementation. This role provides │  │
│ │ leadership to the team...          │  │
│ └────────────────────────────────────┘  │
│                                          │
│ Changes Made:                            │
│  • Added strategic context              │
│  • Enhanced leadership description      │
│                                          │
│ [Insert] [Regenerate] [Cancel]          │
└──────────────────────────────────────────┘
```

---

### 5. Inline Suggestions (`src/components/ai/InlineSuggestions.tsx`)

**Purpose**: Real-time writing suggestions at cursor position

**Features**:
- Autocomplete-style suggestions
- Trigger on pause (500ms delay)
- Multiple suggestion options
- Tab to accept, Escape to dismiss
- Reasoning tooltips

**API Integration**:
```typescript
const suggestions = await api.post('/ai/inline-suggestions', {
  text: editorContent,
  cursor_position: cursorIndex,
  context: currentSection,
});
```

**UI Design**:
```
Editor with inline suggestions:

"The incumbent will be responsible for|"
                                        ↓
┌────────────────────────────────────┐
│ 💡 managing the strategic planning │ (Tab)
│ 💡 overseeing all departmental     │
│ 💡 providing leadership and        │
└────────────────────────────────────┘
```

---

### 6. Job Posting Generator (`src/components/ai/PostingGenerator.tsx`)

**Purpose**: Transform internal JD to external job posting

**Features**:
- Source job selection
- Platform selection (GC Jobs, LinkedIn, Indeed)
- Generated posting preview
- Side-by-side comparison (internal vs external)
- Edit and customize
- Export/Copy functionality

**API Integration** (Backend TODO):
```typescript
const posting = await api.post('/ai/generate-posting', {
  job_description_id: currentJobId,
  platform: 'gc_jobs',
});
```

**UI Design**:
```
┌──────────────────────────────────────────────────────────────┐
│ 🚀 Job Posting Generator                              [×]    │
├──────────────────────────────────────────────────────────────┤
│ Source: Director, Strategic Planning (EX-01)                 │
│ Platform: [GC Jobs ▼]                                        │
│                                                              │
│ ┌────────────────────┐  ┌────────────────────────────────┐ │
│ │ Internal JD        │  │ External Posting               │ │
│ ├────────────────────┤  ├────────────────────────────────┤ │
│ │ General            │  │ Exciting Opportunity!          │ │
│ │ Accountability:    │  │                                │ │
│ │ The incumbent will │  │ Join our dynamic team as a     │ │
│ │ provide strategic  │  │ strategic leader driving...    │ │
│ │ direction...       │  │                                │ │
│ │                    │  │ What You'll Do:                │ │
│ │ [more content]     │  │  • Lead strategic initiatives  │ │
│ │                    │  │  • Manage high-performing team │ │
│ │                    │  │  • Drive organizational change │ │
│ └────────────────────┘  └────────────────────────────────┘ │
│                                                              │
│ [Copy Posting] [Download PDF] [Edit] [Regenerate]           │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Client Extensions

Add AI-related methods to `src/lib/api.ts`:

```typescript
export class APIClient {
  // ... existing methods ...

  // Bias Analysis
  async analyzeBias(params: {
    text: string;
    analysis_types?: string[];
    use_gpt4?: boolean;
  }): Promise<BiasAnalysisResponse> {
    return this.post('/ai/analyze-bias', params, {
      params: { use_gpt4: params.use_gpt4 ?? true },
    });
  }

  // Quality Scoring
  async calculateQualityScore(jobData: {
    sections: Record<string, string>;
  }): Promise<QualityScoreResponse> {
    return this.post('/ai/quality-score', { job_data: jobData });
  }

  // Content Generation
  async completeSection(params: {
    section_type: string;
    partial_content: string;
    classification: string;
    language?: string;
    context?: Record<string, any>;
  }): Promise<SectionCompletionResponse> {
    return this.post('/ai/complete-section', params);
  }

  async enhanceContent(params: {
    text: string;
    enhancement_types: string[];
    language?: string;
  }): Promise<ContentEnhancementResponse> {
    return this.post('/ai/enhance-content', params);
  }

  async getInlineSuggestions(params: {
    text: string;
    cursor_position: number;
    context?: string;
  }): Promise<InlineSuggestionsResponse> {
    return this.post('/ai/inline-suggestions', params);
  }

  // Suggestions
  async getSuggestions(params: {
    text: string;
    context?: string;
    suggestion_types?: string[];
  }): Promise<SuggestionsResponse> {
    return this.post('/ai/suggest-improvements', params);
  }

  // Compliance
  async checkCompliance(params: {
    text: string;
    compliance_frameworks?: string[];
  }): Promise<ComplianceResponse> {
    return this.post('/ai/check-compliance', params);
  }
}

// Type Definitions
export interface BiasAnalysisResponse {
  bias_free: boolean;
  issues: BiasIssue[];
  inclusivity_score: number;
}

export interface BiasIssue {
  type: string;
  description: string;
  problematic_text: string;
  suggested_alternatives: string[];
  severity: 'critical' | 'high' | 'medium' | 'low';
  start_index: number;
  end_index: number;
}

export interface QualityScoreResponse {
  overall_score: number;
  quality_level: 'Excellent' | 'Good' | 'Fair' | 'Needs Improvement';
  quality_color: 'green' | 'blue' | 'yellow' | 'red';
  dimension_scores: {
    readability: QualityDimension;
    completeness: QualityDimension;
    clarity: QualityDimension;
    inclusivity: QualityDimension;
    compliance: QualityDimension;
  };
  top_recommendations: string[];
  improvement_priority: string[];
}

export interface QualityDimension {
  score: number;
  weight: string;
  details: any;
}

export interface SectionCompletionResponse {
  completed_content: string;
  completion_text: string;
  confidence: number;
  message: string;
}

export interface ContentEnhancementResponse {
  enhanced_text: string;
  original_text: string;
  changes: string[];
  enhancement_types: string[];
  message: string;
}

export interface InlineSuggestionsResponse {
  suggestions: Array<{
    text: string;
    reason: string;
  }>;
  cursor_position: number;
  message: string;
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
  overall_score: number;
  processing_time_ms: number;
}

export interface Suggestion {
  id: string;
  type: string;
  original_text: string;
  suggested_text: string;
  explanation: string;
  confidence: number;
  start_index: number;
  end_index: number;
}

export interface ComplianceResponse {
  compliant: boolean;
  issues: ComplianceIssue[];
  compliance_score: number;
}

export interface ComplianceIssue {
  framework: string;
  issue_type: string;
  description: string;
  severity: string;
  location?: string;
  recommendation: string;
}
```

---

## 🎨 UI/UX Integration Points

### 1. Job Detail View Enhancement

**Location**: `src/components/jobs/JobDetailView.tsx`

**Changes**:
- Add Quality Score widget in header
- Add Bias Detector toggle
- Add "Enhance Content" button per section
- Add floating AI Assistant button

```typescript
<div className="job-detail-header">
  <h1>{job.title}</h1>
  <QualityScoreBadge score={qualityScore} />
  <Button onClick={openAIPanel}>
    🤖 AI Assistant
  </Button>
</div>

<div className="job-section">
  <h2>General Accountability</h2>
  <BiasDetector text={job.accountability} enabled={biasDetectionOn} />
  <Button onClick={() => enhanceSection('accountability')}>
    ✨ Enhance
  </Button>
</div>
```

### 2. Bilingual Editor Integration

**Location**: `src/components/translation/BilingualEditor.tsx`

**Changes**:
- Add AI Suggestions panel alongside editor
- Add inline suggestions in editor
- Add quality indicators for both languages
- Add translation quality comparison

### 3. Template Customizer Integration

**Location**: `src/components/templates/TemplateCustomizer.tsx`

**Changes**:
- Add "Generate with AI" button
- Pre-fill sections using AI completion
- Suggest improvements as user customizes

### 4. Dashboard Quick Actions

**Location**: `src/components/dashboard/QuickActionsGrid.tsx`

**Changes**:
- Add "Create Job with AI" quick action
- Add "Check Quality" quick action
- Add "Analyze Bias" quick action

---

## 📱 State Management

### Zustand Store Extension

**Location**: `src/lib/store.ts`

```typescript
interface AIState {
  // Suggestions
  activeSuggestions: Suggestion[];
  suggestionsLoading: boolean;
  lastAnalyzedText: string | null;

  // Quality Score
  currentQualityScore: QualityScoreResponse | null;
  qualityLoading: boolean;

  // Bias Detection
  biasIssues: BiasIssue[];
  biasDetectionEnabled: boolean;
  biasAnalysisLoading: boolean;

  // Content Generation
  generatingContent: boolean;
  lastGeneratedContent: string | null;

  // Settings
  autoAnalyzeEnabled: boolean;
  gpt4Enabled: boolean;
  analysisDelay: number; // milliseconds

  // Actions
  analyzeBias: (text: string) => Promise<void>;
  calculateQuality: (jobData: any) => Promise<void>;
  generateContent: (params: any) => Promise<void>;
  clearSuggestions: () => void;
  toggleBiasDetection: () => void;
  setAutoAnalyze: (enabled: boolean) => void;
}

export const useAIStore = create<AIState>((set, get) => ({
  // Initial state
  activeSuggestions: [],
  suggestionsLoading: false,
  lastAnalyzedText: null,
  currentQualityScore: null,
  qualityLoading: false,
  biasIssues: [],
  biasDetectionEnabled: true,
  biasAnalysisLoading: false,
  generatingContent: false,
  lastGeneratedContent: null,
  autoAnalyzeEnabled: true,
  gpt4Enabled: true,
  analysisDelay: 1000,

  // Actions
  analyzeBias: async (text: string) => {
    set({ biasAnalysisLoading: true });
    try {
      const result = await api.analyzeBias({
        text,
        use_gpt4: get().gpt4Enabled,
      });
      set({
        biasIssues: result.issues,
        biasAnalysisLoading: false,
        lastAnalyzedText: text,
      });
    } catch (error) {
      console.error('Bias analysis failed:', error);
      set({ biasAnalysisLoading: false });
    }
  },

  calculateQuality: async (jobData: any) => {
    set({ qualityLoading: true });
    try {
      const score = await api.calculateQualityScore(jobData);
      set({
        currentQualityScore: score,
        qualityLoading: false,
      });
    } catch (error) {
      console.error('Quality calculation failed:', error);
      set({ qualityLoading: false });
    }
  },

  generateContent: async (params: any) => {
    set({ generatingContent: true });
    try {
      const result = await api.completeSection(params);
      set({
        lastGeneratedContent: result.completed_content,
        generatingContent: false,
      });
    } catch (error) {
      console.error('Content generation failed:', error);
      set({ generatingContent: false });
    }
  },

  clearSuggestions: () => {
    set({ activeSuggestions: [], lastAnalyzedText: null });
  },

  toggleBiasDetection: () => {
    set({ biasDetectionEnabled: !get().biasDetectionEnabled });
  },

  setAutoAnalyze: (enabled: boolean) => {
    set({ autoAnalyzeEnabled: enabled });
  },
}));
```

---

## 🧪 Testing Strategy

### Unit Tests
- Component rendering tests
- API client method tests
- State management tests
- Utility function tests

### Integration Tests
- End-to-end bias detection flow
- Quality scoring workflow
- Content generation workflow
- User interaction scenarios

### Performance Tests
- Debounced analysis (avoid excessive API calls)
- Large text handling (10,000+ characters)
- Multiple simultaneous analyses
- Response time monitoring

---

## 📦 Dependencies to Add

```json
{
  "dependencies": {
    "recharts": "^2.10.0",        // Quality score visualizations
    "react-markdown": "^9.0.0",   // Render AI suggestions with formatting
    "diff": "^5.1.0",             // Show text differences before/after
    "@radix-ui/react-tooltip": "^1.0.0",  // Bias detection tooltips
    "react-syntax-highlighter": "^15.5.0"  // Code/text highlighting
  }
}
```

---

## 🚀 Implementation Timeline

### Week 3: Core Components (5 days)
- **Day 1**: API client extensions + TypeScript types
- **Day 2**: Quality Dashboard + Bias Detector Widget
- **Day 3**: AI Suggestions Panel + Inline highlighting
- **Day 4**: Content Generator Modal + Section completion
- **Day 5**: Integration into existing views + Testing

### Week 4: Enhancement & Polish (5 days)
- **Day 1**: Real-time analysis with debouncing
- **Day 2**: One-click fixes and suggestions
- **Day 3**: Inline suggestions at cursor
- **Day 4**: Job Posting Generator (Phase 3 Feature 4)
- **Day 5**: User feedback, refinement, documentation

### Week 5: Testing & Deployment (5 days)
- **Day 1-2**: Comprehensive testing (unit, integration, E2E)
- **Day 3**: Performance optimization
- **Day 4**: User documentation and guides
- **Day 5**: Deployment and monitoring

---

## 🎯 Success Criteria

### User Experience
- ✅ Analysis completes in < 3 seconds
- ✅ No UI blocking during AI operations
- ✅ Clear visual feedback for all actions
- ✅ Intuitive controls (minimal learning curve)
- ✅ Graceful error handling

### Technical
- ✅ All API integrations working
- ✅ State management properly handles async operations
- ✅ Components are reusable and maintainable
- ✅ TypeScript types are complete and accurate
- ✅ Tests cover critical paths (80%+ coverage)

### Business
- ✅ Users can detect and fix bias quickly
- ✅ Quality scores help improve content
- ✅ Content generation saves time
- ✅ Reduced manual review workload
- ✅ Improved job description quality

---

## 🔐 Security Considerations

1. **Input Validation**: Sanitize all text before sending to API
2. **Rate Limiting**: Implement client-side rate limiting to avoid abuse
3. **Error Handling**: Never expose API keys or sensitive data in errors
4. **Content Security**: Validate AI-generated content before insertion
5. **User Permissions**: Check permissions before enabling AI features

---

## 📊 Monitoring & Analytics

Track usage metrics:
- Number of bias detections per day
- Quality score improvements over time
- Content generation usage
- Suggestion acceptance rate
- Feature adoption by users
- API response times
- Error rates

---

## 📝 Documentation Needed

1. **User Guide**: How to use AI features
2. **Developer Guide**: Component API documentation
3. **Integration Guide**: Adding AI to new views
4. **Best Practices**: When to use each AI feature
5. **Troubleshooting**: Common issues and solutions

---

**Next Steps**: Begin Week 3 implementation with API client extensions and core component development.

---

**Document Owner**: Development Team
**Last Updated**: 2025-10-02
**Status**: Planning - Ready to Begin Week 3
