export interface JobDescription {
  id: number;
  job_number: string;
  title: string;
  classification: string;
  language: string;
  file_path: string;
  file_hash: string;
  processed_date?: string;
  created_at?: string;
  updated_at?: string;
  raw_content?: string;
  sections?: JobSection[];
  metadata?: JobMetadata;
  skills?: Skill[];
  quality_score?: number;
  relevance_score?: number; // Present when job is from search results
}

export interface JobSection {
  id: number;
  section_type: string;
  section_content: string;
  section_order: number;
}

export interface JobMetadata {
  reports_to?: string;
  department?: string;
  location?: string;
  fte_count?: number;
  salary_budget?: number;
  effective_date?: string;
}

export interface Skill {
  id: number;
  lightcast_id: string;
  name: string;
  skill_type?: string;
  category?: string;
  subcategory?: string;
  confidence: number;
}

export interface SkillsInventoryResponse {
  total: number;
  limit: number;
  offset: number;
  skills: SkillInventoryItem[];
}

export interface SkillInventoryItem {
  id: number;
  lightcast_id: string;
  name: string;
  skill_type?: string;
  category?: string;
  subcategory?: string;
  job_count: number;
  avg_confidence: number;
}

export interface TopSkillsResponse {
  total_jobs: number;
  top_skills: TopSkill[];
}

export interface TopSkill {
  id: number;
  lightcast_id: string;
  name: string;
  skill_type?: string;
  category?: string;
  job_count: number;
  percentage: number;
  avg_confidence: number;
  confidence_range: {
    min: number;
    max: number;
  };
}

export interface SkillTypesResponse {
  skill_types: SkillType[];
  total_types: number;
}

export interface SkillType {
  type: string;
  skill_count: number;
  job_count: number;
}

export interface SkillsStatsResponse {
  total_unique_skills: number;
  total_skill_associations: number;
  jobs_with_skills: number;
  total_jobs: number;
  skills_coverage_percentage: number;
  avg_skills_per_job: number;
  avg_confidence_score: number;
}

export interface FileMetadata {
  file_path: string;
  job_number?: string;
  classification?: string;
  language?: string;
  title?: string;
  file_size: number;
  is_valid: boolean;
  validation_errors?: string[];
}

export interface SearchQuery {
  query: string;
  classification?: string;
  language?: string;
  department?: string;
  section_types?: string[];
  limit?: number;
}

export interface SearchResult {
  job_id: number;
  job_number: string;
  title: string;
  classification: string;
  language: string;
  relevance_score: number;
  matching_sections: Array<{
    section_type: string;
    section_id: number;
    snippet: string;
  }>;
  snippet: string;
}

export interface ProcessingStats {
  total_jobs: number;
  by_classification: Record<string, number>;
  by_language: Record<string, number>;
  processing_status: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    needs_review: number;
  };
  last_updated: string;
}

export interface BulkUploadStatus {
  status: "started" | "processing" | "completed" | "failed";
  total_files: number;
  processed_files: number;
  successful_files: number;
  failed_files: number;
  files_needing_review: number;
  errors?: string[];
}

// Enhanced stats interfaces for dashboard
export interface IngestionStats {
  total_jobs: number;
  by_classification: Record<string, number>;
  by_language: Record<string, number>;
  processing_status: {
    completed: number;
    partial: number;
    needs_embeddings: number;
    needs_sections: number;
    needs_metadata: number;
  };
  embedding_stats: {
    total_chunks: number;
    embedded_chunks: number;
    embedding_completion_rate: number;
    jobs_with_embeddings: number;
  };
  content_quality: {
    jobs_with_sections: number;
    jobs_with_metadata: number;
    jobs_with_embeddings: number;
    section_coverage_rate: number;
    metadata_coverage_rate: number;
    embedding_coverage_rate: number;
  };
  section_distribution: Record<string, number>;
  recent_activity: {
    jobs_last_7_days: number;
    daily_average: number;
  };
  last_updated: string | null;
}

export interface TaskStats {
  status: string;
  task_stats: {
    active_tasks: number;
    scheduled_tasks: number;
    reserved_tasks: number;
    workers_online: number;
    queue_stats: Record<string, { active: number; reserved: number }>;
    task_types: Record<string, number>;
  };
  timestamp: string;
  error?: string;
}

export interface ResilienceStats {
  status: string;
  overall_health: string;
  degraded_services: string[];
  circuit_breakers: Record<string, CircuitBreakerState>;
  health_indicators: Record<string, HealthIndicator>;
  timestamp: string;
  recommendations: string[];
}

// Search and comparison interfaces
export interface SearchFacets {
  classifications: Array<{ value: string; count: number }>;
  languages: Array<{ value: string; count: number }>;
  section_types: Array<{ value: string; count: number }>;
}

export interface SearchSuggestions {
  query: string;
  suggestions: string[];
}

export interface ComparisonResult {
  comparison_id: string;
  jobs: {
    job1: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
    job2: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
  };
  similarity_analysis: {
    overall_similarity: number;
    similarity_level: string;
    metadata_comparison: {
      classification: {
        job1: string;
        job2: string;
        match: boolean;
      };
      language: {
        job1: string;
        job2: string;
        match: boolean;
      };
      title_similarity: number;
    };
    section_comparison: Array<{
      section_type: string;
      job1_content: string;
      job2_content: string;
      similarity_score: number;
      both_present: boolean;
      job1_only: boolean;
      job2_only: boolean;
    }>;
  };
  recommendations: string[];
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Error handling interfaces
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

// Additional interfaces for improved type safety
export interface StructuredFields {
  title?: string;
  classification?: string;
  language?: string;
  reports_to?: string;
  department?: string;
  location?: string;
  fte_count?: number;
  salary_budget?: number;
  effective_date?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface LegacyProcessingResult {
  status: "success" | "error" | "partial";
  file_info: {
    filename: string;
    file_size: number;
    file_hash: string;
  };
  processed_content: {
    sections_found: number;
    sections: string[];
    structured_fields: StructuredFields;
    chunks_generated: number;
    processing_errors: string[];
  };
  job_id?: number;
  message?: string;
  errors?: string[];
}

export interface CircuitBreakerState {
  state: "CLOSED" | "OPEN" | "HALF_OPEN";
  failure_count: number;
  last_failure_time?: string;
  next_attempt?: string;
  success_threshold: number;
  failure_threshold: number;
  timeout: number;
}

export interface HealthIndicator {
  status: "healthy" | "unhealthy" | "degraded";
  message?: string;
  details?: Record<string, string | number | boolean>;
  last_check?: string;
  response_time_ms?: number;
}

// File processing interfaces
export interface FileProcessingResponse {
  status: string;
  file_info: {
    filename: string;
    file_size: number;
    file_hash: string;
  };
  processed_content: {
    sections_found: number;
    sections: string[];
    structured_fields: StructuredFields;
    chunks_generated: number;
    processing_errors: string[];
  };
}

export interface LegacyUploadResponse {
  status: string;
  filename: string;
  processing_result: LegacyProcessingResult;
}

// Comprehensive API Response Interfaces
export interface HealthCheckResponse {
  status: string;
  database: string;
  version: string;
}

export interface JobListResponse {
  jobs: JobDescription[];
  pagination: {
    skip: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

export interface JobSectionResponse {
  job_id: number;
  section_id: number;
  section_type: string;
  section_content: string;
  section_order: number;
}

export interface JobDeleteResponse {
  status: string;
  message: string;
}

export interface DirectoryScanResponse {
  status: string;
  directory: string;
  stats: {
    total_files: number;
    valid_files: number;
    invalid_files: number;
    by_classification: Record<string, number>;
    by_language: Record<string, number>;
    total_size_mb: number;
    avg_size_kb: number;
  };
  files: FileMetadata[];
  total_files_found: number;
}

export interface FileProcessResponse {
  status: string;
  file_path: string;
  metadata: {
    job_number?: string;
    classification?: string;
    language?: string;
    title?: string;
    file_size: number;
    file_hash: string;
  };
  processed_content: {
    sections_found: number;
    sections: string[];
    structured_fields: StructuredFields;
    chunks_generated: number;
    processing_errors: string[];
  };
}

export interface BatchIngestResponse {
  status: string;
  directory: string;
  files_to_process: number;
  message: string;
}

export interface SearchJobsResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
}

export interface SimilarJobsResponse {
  source_job: {
    id: number;
    job_number: string;
    title: string;
    classification: string;
  };
  similar_jobs: Array<{
    id: number;
    job_number: string;
    title: string;
    classification: string;
    language: string;
    similarity_score: number;
  }>;
  total_found: number;
}

export interface SearchFacetsResponse {
  classifications: Array<{ value: string; count: number }>;
  languages: Array<{ value: string; count: number }>;
  section_types: Array<{ value: string; count: number }>;
}

export interface SearchSuggestionsResponse {
  query: string;
  suggestions: string[];
}

export interface TaskStatsResponse {
  status: string;
  task_stats: {
    active_tasks: number;
    scheduled_tasks: number;
    reserved_tasks: number;
    workers_online: number;
    queue_stats: Record<string, { active: number; reserved: number }>;
    task_types: Record<string, number>;
  };
  timestamp: string;
  error?: string;
}

export interface CircuitBreakerResetResponse {
  status: string;
  message: string;
  timestamp: string;
}

export interface JobComparisonResponse {
  comparison_id: string;
  jobs: {
    job1: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
    job2: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
  };
  similarity_analysis: {
    overall_similarity: number;
    similarity_level: string;
    metadata_comparison: {
      classification: {
        job1: string;
        job2: string;
        match: boolean;
      };
      language: {
        job1: string;
        job2: string;
        match: boolean;
      };
      title_similarity: number;
    };
    section_comparison: Array<{
      section_type: string;
      job1_content: string;
      job2_content: string;
      similarity_score: number;
      both_present: boolean;
      job1_only: boolean;
      job2_only: boolean;
    }>;
  };
  recommendations: string[];
}

// Analysis API Response Interfaces
export interface BatchComparisonResponse {
  base_job_id: number;
  comparison_type: string;
  total_comparisons: number;
  results: Array<{
    job_id: number;
    job_title: string;
    classification: string;
    score: number;
    analysis: any;
  }>;
}

export interface CareerPathsResponse {
  job_id: number;
  career_paths: Array<{
    path_type: string;
    next_roles: Array<{
      job_id: number;
      title: string;
      classification: string;
      progression_score: number;
    }>;
  }>;
}

export interface SkillGapResponse {
  base_job_id: number;
  target_job_id: number;
  skill_gaps: Array<{
    skill: string;
    gap_level: string;
    importance: number;
  }>;
  recommendations: string[];
}

export interface ClassificationBenchmarkResponse {
  classification: string;
  benchmark_data: {
    average_salary: number;
    job_count: number;
    common_skills: string[];
    career_progression: any;
  };
}

export interface JobSkillsResponse {
  job_id: number;
  extracted_skills: Array<{
    skill: string;
    category: string;
    confidence: number;
  }>;
}

export interface SimilarSalaryRangeResponse {
  job_id: number;
  salary_range: {
    min: number;
    max: number;
    average: number;
  };
  similar_jobs: Array<{
    job_id: number;
    title: string;
    salary: number;
  }>;
}

export interface JobClustersResponse {
  clusters: Array<{
    cluster_id: string;
    cluster_name: string;
    job_count: number;
    representative_jobs: Array<{
      job_id: number;
      title: string;
      classification: string;
    }>;
  }>;
}

export interface CompensationAnalysisResponse {
  analysis_type: string;
  compensation_data: {
    salary_ranges: Record<string, { min: number; max: number; avg: number }>;
    benefits_comparison: any;
    market_positioning: any;
  };
}

// Quality API Response Interfaces
export interface QualityMetricsResponse {
  job_id: number;
  metrics: {
    completeness_score: number;
    accuracy_score: number;
    consistency_score: number;
    overall_quality: number;
  };
  status: string;
}

export interface QualityReportResponse {
  report_id: string;
  generated_at: string;
  summary: {
    total_jobs: number;
    quality_distribution: Record<string, number>;
    common_issues: string[];
  };
  detailed_metrics: any;
}

export interface QualityOverviewResponse {
  overview: {
    average_quality: number;
    quality_trends: any;
    improvement_suggestions: string[];
  };
}

export interface ValidationResponse {
  job_id: number;
  validation_results: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    score: number;
  };
}

export interface QualityDistributionResponse {
  distribution: Record<string, number>;
  statistics: {
    mean: number;
    median: number;
    std_dev: number;
  };
}

export interface BatchValidationResponse {
  batch_id: string;
  validation_results: Array<{
    job_id: number;
    is_valid: boolean;
    score: number;
    issues: string[];
  }>;
}

export interface QualityRecommendationsResponse {
  job_id: number;
  recommendations: Array<{
    type: string;
    priority: string;
    description: string;
    suggested_action: string;
  }>;
}

// Analytics API Response Interfaces
export interface ActivityTrackingResponse {
  status: string;
  activity_logged: boolean;
  session_id?: string;
}

export interface AIUsageTrackingResponse {
  status: string;
  usage_recorded: boolean;
  cost_tracking: {
    tokens_used: number;
    estimated_cost: number;
  };
}

export interface UsageStatisticsResponse {
  statistics: {
    total_searches: number;
    active_users: number;
    popular_queries: string[];
    usage_trends: any;
  };
}

export interface AnalyticsDashboardResponse {
  status: string;
  dashboard: {
    usage: any;
    search_patterns: any;
    performance: any;
    ai_usage: any;
  };
}

export interface SystemMetricsResponse {
  metrics: {
    database_performance: any;
    api_response_times: any;
    resource_usage: any;
    error_rates: any;
  };
  generated_at: string;
}

export interface SearchPatternsResponse {
  patterns: {
    common_queries: Array<{
      query: string;
      frequency: number;
    }>;
    search_trends: any;
    user_behavior: any;
  };
}

export interface PerformanceMetricsResponse {
  performance: {
    response_times: Record<string, number>;
    throughput: any;
    error_rates: any;
    system_health: any;
  };
}

export interface AIUsageAnalysisResponse {
  ai_usage: {
    total_requests: number;
    cost_breakdown: any;
    efficiency_metrics: any;
    usage_patterns: any;
  };
}

export interface UsageTrendsResponse {
  trends: {
    daily_usage: any;
    feature_adoption: any;
    user_engagement: any;
  };
}

export interface AnalyticsExportResponse {
  export_id: string;
  download_url: string;
  expires_at: string;
}

export interface SessionGenerateResponse {
  session_id: string;
  expires_at: string;
}

// Performance API Response Interfaces
export interface PerformanceStatsResponse {
  stats: {
    api_performance: any;
    database_performance: any;
    system_resources: any;
  };
}

export interface VectorSearchBenchmarkResponse {
  status: string;
  benchmark_results: {
    query_text: string;
    configuration: {
      limit: number;
      similarity_threshold: number;
      filters_applied: boolean;
      classification_filter?: string;
      language_filter?: string;
    };
    performance_metrics: {
      embedding_generation_ms: number;
      similarity_search_ms: number;
      semantic_search_ms: number;
      total_time_ms: number;
    };
    result_counts: {
      similarity_results: number;
      semantic_results: number;
    };
    sample_results: {
      similarity_search: any[];
      semantic_search: any[];
    };
  };
  generated_at: string;
}

export interface DatabaseOptimizationResponse {
  status: string;
  optimization_results: {
    indexes_created: string[];
    indexes_dropped: string[];
    performance_improvement: any;
  };
}

export interface PerformanceHealthCheckResponse {
  health_status: string;
  performance_indicators: {
    response_time: number;
    throughput: number;
    error_rate: number;
  };
  recommendations: string[];
}

// Saved Searches API Response Interfaces
export interface SavedSearchResponse {
  status: string;
  saved_search: {
    id: number;
    name: string;
    description?: string;
    search_query?: string;
    search_type: string;
    search_filters?: any;
    is_public: boolean;
    is_favorite: boolean;
    created_at: string;
    search_metadata?: any;
  };
}

export interface SavedSearchListResponse {
  saved_searches: Array<{
    id: number;
    name: string;
    description?: string;
    search_type: string;
    is_public: boolean;
    is_favorite: boolean;
    created_at: string;
    last_used?: string;
  }>;
  total: number;
}

export interface SavedSearchDetailResponse {
  saved_search: {
    id: number;
    name: string;
    description?: string;
    search_query?: string;
    search_type: string;
    search_filters?: any;
    is_public: boolean;
    is_favorite: boolean;
    created_at: string;
    updated_at?: string;
    usage_count: number;
    search_metadata?: any;
  };
}

export interface SavedSearchExecuteResponse {
  search_id: number;
  results: SearchResult[];
  execution_time_ms: number;
  total_results: number;
}

export interface PopularSearchesResponse {
  popular_searches: Array<{
    id: number;
    name: string;
    description?: string;
    usage_count: number;
    created_by: string;
  }>;
}

export interface UserPreferenceResponse {
  status: string;
  preference: {
    type: string;
    value: any;
    updated_at: string;
  };
}

export interface UserPreferencesResponse {
  preferences: Record<string, any>;
  last_updated: string;
}

// Tasks API Response Interfaces
export interface UploadResponse {
  status: string;
  filename: string;
  processing_result: {
    status: string;
    file_path: string;
    job_id?: number;
    file_metadata?: FileMetadata;
    processed_content?: {
      sections?: Record<string, string>;
      structured_fields?: StructuredFields;
      chunks_generated?: number;
      processing_errors?: string[];
    };
    errors?: string[];
  };
}

export interface TaskUploadResponse {
  status: string;
  task_id: string;
  filename: string;
  message: string;
}

export interface TaskBatchProcessResponse {
  status: string;
  task_id: string;
  files_to_process: number;
  message: string;
}

export interface TaskEmbeddingResponse {
  status: string;
  task_id: string;
  jobs_to_process: number;
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskResultResponse {
  task_id: string;
  result: any;
  status: string;
  completed_at: string;
}

export interface TaskCancelResponse {
  status: string;
  task_id: string;
  message: string;
}

export interface ActiveTasksResponse {
  active_tasks: Array<{
    task_id: string;
    task_type: string;
    status: string;
    created_at: string;
    progress?: {
      current: number;
      total: number;
      percentage: number;
    };
  }>;
  total_active: number;
}

export interface TaskStatsDetailedResponse {
  status: string;
  detailed_stats: {
    queue_stats: Record<string, any>;
    worker_stats: any;
    task_history: any;
    performance_metrics: any;
  };
  timestamp: string;
}
