/**
 * TypeScript Type Definitions for AI API Responses
 * Phase 3: Advanced AI Content Intelligence
 */

// ============================================================================
// Bias Analysis Types
// ============================================================================

export type BiasSeverity = "critical" | "high" | "medium" | "low";
export type BiasType =
  | "gender"
  | "age"
  | "disability"
  | "cultural"
  | "gender_coded_masculine"
  | "gender_coded_feminine";

export interface BiasIssue {
  type: BiasType;
  description: string;
  problematic_text: string;
  suggested_alternatives: string[];
  severity: BiasSeverity;
  start_index: number;
  end_index: number;
}

export interface BiasAnalysisRequest {
  text: string;
  analysis_types?: BiasType[];
  use_gpt4?: boolean;
}

export interface BiasAnalysisResponse {
  bias_free: boolean;
  issues: BiasIssue[];
  inclusivity_score: number;
}

// ============================================================================
// Quality Scoring Types
// ============================================================================

export type QualityLevel = "Excellent" | "Good" | "Fair" | "Needs Improvement";
export type QualityColor = "green" | "blue" | "yellow" | "red";

export interface ReadabilityDetails {
  flesch_reading_ease: number | null;
  flesch_kincaid_grade: number | null;
  smog_index: number | null;
  automated_readability_index: number | null;
  coleman_liau_index: number | null;
  reading_level: string;
  target_grade_level: number;
  meets_target: boolean;
  recommendations: string[];
}

export interface SectionScore {
  name: string;
  present: boolean;
  word_count: number;
  adequate: boolean;
  score: number;
}

export interface ThinSection {
  section: string;
  word_count: number;
  min_required: number;
}

export interface CompletenessDetails {
  completeness_score: number;
  sections_present: number;
  sections_required: number;
  sections_adequate: number;
  missing_sections: string[];
  thin_sections: ThinSection[];
  section_scores: Record<string, SectionScore>;
  recommendations: string[];
}

export interface ClarityDetails {
  clarity_score: number;
  avg_sentence_length: number;
  optimal_range: string;
  sentence_count: number;
  long_sentences: number;
  paragraph_count: number;
  recommendations: string[];
}

export interface QualityDimension {
  score: number;
  weight: string;
  details:
    | ReadabilityDetails
    | CompletenessDetails
    | ClarityDetails
    | BiasAnalysisResponse
    | any;
}

export interface QualityScoreRequest {
  job_data: {
    sections: Record<string, string>;
    raw_content?: string;
  };
}

export interface QualityScoreResponse {
  overall_score: number;
  quality_level: QualityLevel;
  quality_color: QualityColor;
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

// ============================================================================
// Content Generation Types
// ============================================================================

export type SectionType =
  | "general_accountability"
  | "organization_structure"
  | "key_responsibilities"
  | "qualifications"
  | "nature_and_scope";

export type EnhancementType =
  | "clarity"
  | "active_voice"
  | "conciseness"
  | "formality"
  | "bias_free";

export interface SectionCompletionRequest {
  section_type: SectionType;
  partial_content: string;
  classification: string;
  language?: "en" | "fr";
  context?: {
    department?: string;
    reporting_to?: string;
    [key: string]: any;
  };
}

export interface SectionCompletionResponse {
  completed_content: string;
  completion_text: string;
  confidence: number;
  message: string;
}

export interface ContentEnhancementRequest {
  text: string;
  enhancement_types: EnhancementType[];
  language?: "en" | "fr";
}

export interface ContentEnhancementResponse {
  enhanced_text: string;
  original_text: string;
  changes: string[];
  enhancement_types: EnhancementType[];
  message: string;
}

export interface InlineSuggestionsRequest {
  text: string;
  cursor_position: number;
  context?: string;
}

export interface InlineSuggestion {
  text: string;
  reason: string;
}

export interface InlineSuggestionsResponse {
  suggestions: InlineSuggestion[];
  cursor_position: number;
  message: string;
}

// ============================================================================
// Text Suggestions Types
// ============================================================================

export type SuggestionType =
  | "grammar"
  | "style"
  | "clarity"
  | "bias"
  | "compliance";

export interface Suggestion {
  id: string;
  type: SuggestionType;
  original_text: string;
  suggested_text: string;
  explanation: string;
  confidence: number;
  start_index: number;
  end_index: number;
}

export interface TextSuggestionRequest {
  text: string;
  context?: string;
  suggestion_types?: SuggestionType[];
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
  overall_score: number;
  processing_time_ms: number;
}

// ============================================================================
// Compliance Types
// ============================================================================

export type ComplianceFramework =
  | "treasury_board"
  | "accessibility"
  | "bilingual";

export interface ComplianceIssue {
  framework: string;
  issue_type: string;
  description: string;
  severity: string;
  location?: string;
  recommendation: string;
}

export interface ComplianceCheckRequest {
  text: string;
  compliance_frameworks?: ComplianceFramework[];
}

export interface ComplianceResponse {
  compliant: boolean;
  issues: ComplianceIssue[];
  compliance_score: number;
}

// ============================================================================
// Template Types
// ============================================================================

export interface TemplateRequest {
  classification: string;
  language?: "en" | "fr";
  custom_requirements?: Record<string, any>;
}

export interface TemplateResponse {
  template_id: string;
  classification: string;
  language: string;
  sections: Record<string, string>;
  metadata: Record<string, any>;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface AIAnalysisState {
  // Bias Detection
  biasIssues: BiasIssue[];
  biasLoading: boolean;
  biasDetectionEnabled: boolean;

  // Quality Scoring
  qualityScore: QualityScoreResponse | null;
  qualityLoading: boolean;

  // Suggestions
  suggestions: Suggestion[];
  suggestionsLoading: boolean;

  // Content Generation
  generatingContent: boolean;
  lastGenerated: string | null;

  // Settings
  autoAnalyzeEnabled: boolean;
  gpt4Enabled: boolean;
  analysisDelay: number;
}

export interface BiasHighlight {
  start: number;
  end: number;
  issue: BiasIssue;
  color: string;
}

export interface QualityScoreBadgeProps {
  score: number;
  level: QualityLevel;
  color: QualityColor;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

// ============================================================================
// Utility Types
// ============================================================================

export interface AIFeatureConfig {
  enableBiasDetection: boolean;
  enableQualityScoring: boolean;
  enableContentGeneration: boolean;
  enableInlineSuggestions: boolean;
  gpt4Enabled: boolean;
  autoAnalyze: boolean;
  debounceMs: number;
}

export const DEFAULT_AI_CONFIG: AIFeatureConfig = {
  enableBiasDetection: true,
  enableQualityScoring: true,
  enableContentGeneration: true,
  enableInlineSuggestions: true,
  gpt4Enabled: true,
  autoAnalyze: true,
  debounceMs: 1000,
};

// Helper type guards
export const isBiasIssue = (obj: any): obj is BiasIssue => {
  return (
    obj && typeof obj.type === "string" && typeof obj.severity === "string"
  );
};

export const isQualityScoreResponse = (
  obj: any,
): obj is QualityScoreResponse => {
  return (
    obj &&
    typeof obj.overall_score === "number" &&
    typeof obj.quality_level === "string"
  );
};

// Severity color mapping
export const SEVERITY_COLORS: Record<BiasSeverity, string> = {
  critical: "rgb(220, 38, 38)", // red-600
  high: "rgb(239, 68, 68)", // red-500
  medium: "rgb(251, 146, 60)", // orange-400
  low: "rgb(250, 204, 21)", // yellow-400
};

// Quality score color mapping
export const QUALITY_COLORS: Record<QualityColor, string> = {
  green: "rgb(34, 197, 94)", // green-500
  blue: "rgb(59, 130, 246)", // blue-500
  yellow: "rgb(234, 179, 8)", // yellow-500
  red: "rgb(239, 68, 68)", // red-500
};

// Section display names
export const SECTION_NAMES: Record<SectionType, string> = {
  general_accountability: "General Accountability",
  organization_structure: "Organization Structure",
  key_responsibilities: "Key Responsibilities",
  qualifications: "Qualifications",
  nature_and_scope: "Nature and Scope",
};

// Enhancement type labels
export const ENHANCEMENT_LABELS: Record<EnhancementType, string> = {
  clarity: "Clarity",
  active_voice: "Active Voice",
  conciseness: "Conciseness",
  formality: "Formality",
  bias_free: "Bias-Free Language",
};
