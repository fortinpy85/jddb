/**
 * API Response Types for JDDB Frontend
 */

export interface JobDescription {
  id: number;
  job_number: string;
  title: string;
  classification: string;
  language: string;
  created_at?: string;
  updated_at?: string;
  processed_date?: string;
  file_path: string; // Required for backend compatibility
  file_hash: string; // Required for backend compatibility
  content?: string;
  raw_content?: string; // Raw unprocessed content for JobPostingGenerator
  sections?: any[];
  job_metadata?: any;
  relevance_score?: number; // For search results
  quality_score?: number; // For job listings
}

export interface JobListResponse {
  jobs: JobDescription[];
  total: number;
  page: number;
  pages: number;
  pagination: {
    page: number;
    pages: number;
    total: number;
    limit: number;
    skip: number;
  };
}

export interface SearchQuery {
  query?: string;
  semantic?: boolean;
  classification?: string;
  language?: string;
  limit?: number;
  skip?: number;
}

export interface SearchResult {
  jobs: JobDescription[];
  total: number;
  query: string;
}

export interface ProcessingStats {
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
    avg_chunks_per_job: number;
    embedding_coverage: number;
  };
  quality_metrics: {
    avg_content_length: number;
    structured_fields_coverage: number;
    bilingual_coverage: number;
  };
  last_updated: string | null;
}

export interface UploadResponse {
  status: string;
  filename: string;
  processing_result: ProcessingResult;
}

export interface ProcessingResult {
  status: string;
  file_path: string;
  job_id?: number;
  file_metadata?: FileMetadata;
  processed_content?: ProcessedContent;
  errors?: string[];
}

export interface ProcessedContent {
  sections?: Record<string, string>;
  structured_fields?: StructuredFields;
  chunks_generated?: number;
  processing_errors?: string[];
}

export interface FileMetadata {
  file_name?: string;
  file_size?: number;
  encoding?: string;
  language?: string;
  job_number?: string;
  classification?: string;
  title?: string;
  is_valid?: boolean;
  validation_errors?: string[];
}

export interface StructuredFields {
  position_title?: string;
  job_number?: string;
  classification?: string;
  department?: string;
  reports_to?: string;
  location?: string;
  fte_count?: number;
  salary_budget?: number;
}

export interface ComparisonResult {
  similarity_score: number;
  common_sections: Record<string, number>;
}

/**
 * NOTE: Most types have been consolidated into src/lib/types.ts
 * This file is kept for backward compatibility with existing imports.
 * New code should import from @/lib/types instead.
 */
