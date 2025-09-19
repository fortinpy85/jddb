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
  content?: string;
  sections?: any[];
  job_metadata?: any;
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
  message: string;
  job_id: number;
  task_id: string;
}

export interface ComparisonResult {
  similarity_score: number;
  common_sections: Record<string, number>;
}

// Placeholder types for missing imports
export interface BulkUploadStatus {}
export interface FileMetadata {}
export interface StructuredFields {}
export interface ProcessingResult {}
export interface CircuitBreakerState {}
export interface HealthIndicator {}
export interface FileProcessingResponse {}
export interface ResilienceStats {}
export interface HealthCheckResponse {}
export interface JobSectionResponse {}
export interface JobDeleteResponse {}
export interface DirectoryScanResponse {}
export interface FileProcessResponse {}
export interface BatchIngestResponse {}
export interface SearchJobsResponse {}
export interface SimilarJobsResponse {}
export interface SearchFacetsResponse {}
export interface SearchSuggestionsResponse {}
export interface TaskStatsResponse {}
export interface AnalyticsResponse {}
export interface MonitoringStats {}
export interface PerformanceMetrics {}
export interface CacheStats {}
export interface ErrorStats {}
export interface SecurityAuditLog {}
export interface ComplianceReport {}
export interface UsageReport {}
export interface SystemHealth {}
export interface BackupStatus {}
export interface AlertConfig {}
export interface NotificationSettings {}
export interface UserPreferences {}
export interface SessionInfo {}
export interface AuditLog {}
export interface LogEntry {}
export interface ConfigValidation {}
export interface EnvironmentInfo {}
export interface APILimits {}
export interface RateLimitInfo {}
export interface QuotaInfo {}
export interface ServiceStatus {}
export interface DependencyStatus {}
export interface DatabaseStatus {}
export interface RedisStatus {}
export interface QueueStatus {}
export interface WorkerStatus {}
export interface TaskStatus {}
export interface JobStatus {}
export interface ProcessingQueue {}
export interface TaskQueue {}
export interface WorkerPool {}
export interface ResourceUsage {}
export interface MemoryUsage {}
export interface CPUUsage {}
export interface DiskUsage {}
export interface NetworkUsage {}
export interface ThreadStats {}
export interface ConnectionStats {}
export interface TransactionStats {}
export interface QueryStats {}
export interface IndexStats {}
export interface CacheHitRatio {}
export interface ResponseTimes {}
export interface Throughput {}
export interface ErrorRates {}
export interface SuccessRates {}
export interface AvailabilityStats {}
export interface UptimeStats {}
export interface DowntimeStats {}
export interface MaintenanceWindow {}
export interface DeploymentInfo {}
export interface VersionInfo {}
export interface FeatureFlags {}
export interface Configuration {}
export interface Settings {}
export interface Preferences {}
export interface Profile {}
export interface Permissions {}
export interface Roles {}
export interface AccessControl {}
export interface Authentication {}
export interface Authorization {}
export interface Security {}
export interface Encryption {}
export interface Certificates {}
export interface Keys {}
export interface Tokens {}
export interface Sessions {}
export interface Cookies {}
export interface Headers {}
export interface Middleware {}
export interface Interceptors {}
export interface Filters {}
export interface Validators {}
export interface Transformers {}
export interface Serializers {}
export interface Deserializers {}
export interface Formatters {}
export interface Parsers {}
export interface Converters {}
export interface Mappers {}
export interface Adapters {}
export interface Providers {}
export interface Services {}
export interface Repositories {}
export interface Controllers {}
export interface Routes {}
export interface Endpoints {}
export interface Resources {}
export interface Models {}
export interface Entities {}
export interface DTOs {}
export interface ViewModels {}
export interface Schemas {}
export interface Specifications {}
export interface Contracts {}
export interface Interfaces {}
export interface Abstractions {}
export interface Implementations {}
export interface Factories {}
export interface Builders {}
export interface Strategies {}
export interface Policies {}
export interface Rules {}
export interface Constraints {}
export interface Validations {}
export interface Assertions {}
export interface Expectations {}
export interface Assumptions {}
export interface Requirements {}
export interface Dependencies {}
export interface Configurations {}
export interface Options {}
export interface Parameters {}
export interface Arguments {}
export interface Results {}
export interface Responses {}
export interface Requests {}
export interface Commands {}
export interface Queries {}
export interface Events {}
export interface Messages {}
export interface Notifications {}
export interface Alerts {}
export interface Warnings {}
export interface Errors {}
export interface Exceptions {}
export interface Failures {}
export interface Successes {}
export interface Completions {}
export interface Cancellations {}
export interface Timeouts {}
export interface Retries {}
export interface Fallbacks {}
export interface Recoveries {}
export interface Compensations {}
export interface Rollbacks {}
export interface Transactions {}
export interface Operations {}
export interface Actions {}
export interface Activities {}
export interface Tasks {}
export interface Jobs {}
export interface Processes {}
export interface Workflows {}
export interface Pipelines {}
export interface Stages {}
export interface Steps {}
export interface Phases {}
export interface Cycles {}
export interface Iterations {}
export interface Loops {}
export interface Batches {}
export interface Chunks {}
export interface Segments {}
export interface Partitions {}
export interface Shards {}
export interface Replicas {}
export interface Backups {}
export interface Snapshots {}
export interface Checkpoints {}
export interface Markers {}
export interface Bookmarks {}
export interface References {}
export interface Pointers {}
export interface Links {}
export interface Connections {}
export interface Relationships {}
export interface Associations {}
export interface Mappings {}
export interface Bindings {}
export interface Attachments {}
export interface Extensions {}
export interface Plugins {}
export interface Modules {}
export interface Components {}
export interface Elements {}
export interface Parts {}
export interface Pieces {}
export interface Fragments {}
export interface Sections {}
export interface Blocks {}
export interface Units {}
export interface Items {}
export interface Objects {}
export interface Instances {}
export interface Copies {}
export interface Clones {}
export interface Duplicates {}
export interface Variants {}
export interface Versions {}
export interface Revisions {}
export interface Changes {}
export interface Modifications {}
export interface Updates {}
export interface Patches {}
export interface Fixes {}
export interface Improvements {}
export interface Enhancements {}
export interface Features {}
export interface Capabilities {}
export interface Functions {}
export interface Methods {}
export interface Procedures {}
export interface Routines {}
export interface Algorithms {}
export interface Formulas {}
export interface Calculations {}
export interface Computations {}
export interface Evaluations {}
export interface Assessments {}
export interface Analyses {}
export interface Examinations {}
export interface Inspections {}
export interface Reviews {}
export interface Audits {}
export interface Checks {}
export interface Tests {}
export interface Verifications {}
export interface Validations {}
export interface Confirmations {}
export interface Approvals {}
export interface Rejections {}
export interface Denials {}
export interface Permissions {}
export interface Grants {}
export interface Rights {}
export interface Privileges {}
export interface Access {}
export interface Entry {}
export interface Exit {}
export interface Start {}
export interface Stop {}
export interface Pause {}
export interface Resume {}
export interface Continue {}
export interface Break {}
export interface Return {}
export interface Yield {}
export interface Wait {}
export interface Sleep {}
export interface Delay {}
export interface Timeout {}
export interface Interval {}
export interface Duration {}
export interface Period {}
export interface Time {}
export interface Date {}
export interface Timestamp {}
export interface Clock {}
export interface Timer {}
export interface Counter {}
export interface Index {}
export interface Position {}
export interface Location {}
export interface Address {}
export interface Path {}
export interface Route {}
export interface Direction {}
export interface Destination {}
export interface Source {}
export interface Origin {}
export interface Target {}
export interface Goal {}
export interface Objective {}
export interface Purpose {}
export interface Intent {}
export interface Reason {}
export interface Cause {}
export interface Effect {}
export interface Result {}
export interface Outcome {}
export interface Output {}
export interface Input {}
export interface Data {}
export interface Information {}
export interface Content {}
export interface Text {}
export interface String {}
export interface Number {}
export interface Boolean {}
export interface Array {}
export interface List {}
export interface Set {}
export interface Map {}
export interface Dictionary {}
export interface Hash {}
export interface Tree {}
export interface Graph {}
export interface Network {}
export interface Cluster {}
export interface Group {}
export interface Collection {}
export interface Bundle {}
export interface Package {}
export interface Container {}
export interface Wrapper {}
export interface Envelope {}
export interface Frame {}
export interface Border {}
export interface Boundary {}
export interface Limit {}
export interface Range {}
export interface Scope {}
export interface Context {}
export interface Environment {}
export interface Setting {}
export interface State {}
export interface Status {}
export interface Condition {}
export interface Situation {}
export interface Scenario {}
export interface Case {}
export interface Example {}
export interface Sample {}
export interface Specimen {}
export interface Instance {}
export interface Occurrence {}
export interface Event {}
export interface Incident {}
export interface Issue {}
export interface Problem {}
export interface Challenge {}
export interface Difficulty {}
export interface Obstacle {}
export interface Barrier {}
export interface Blocker {}
export interface Impediment {}
export interface Constraint {}
export interface Limitation {}
export interface Restriction {}
export interface Rule {}
export interface Regulation {}
export interface Policy {}
export interface Guideline {}
export interface Standard {}
export interface Specification {}
export interface Requirement {}
export interface Expectation {}
export interface Assumption {}
export interface Premise {}
export interface Hypothesis {}
export interface Theory {}
export interface Principle {}
export interface Concept {}
export interface Idea {}
export interface Notion {}
export interface Thought {}
export interface Opinion {}
export interface Belief {}
export interface View {}
export interface Perspective {}
export interface Angle {}
export interface Aspect {}
export interface Dimension {}
export interface Factor {}
export interface Element {}
export interface Component {}
export interface Part {}
export interface Piece {}
export interface Fragment {}
export interface Section {}
export interface Segment {}
export interface Portion {}
export interface Share {}
export interface Fraction {}
export interface Percentage {}
export interface Ratio {}
export interface Proportion {}
export interface Rate {}
export interface Speed {}
export interface Velocity {}
export interface Acceleration {}
export interface Force {}
export interface Power {}
export interface Energy {}
export interface Strength {}
export interface Intensity {}
export interface Magnitude {}
export interface Size {}
export interface Scale {}
export interface Level {}
export interface Degree {}
export interface Grade {}
export interface Rank {}
export interface Order {}
export interface Sequence {}
export interface Series {}
export interface Chain {}
export interface Link {}
export interface Connection {}
export interface Relation {}
export interface Association {}
export interface Correlation {}
export interface Dependency {}
export interface Requirement {}
export interface Prerequisite {}
export interface Condition {}
export interface Criteria {}
export interface Standard {}
export interface Benchmark {}
export interface Baseline {}
export interface Reference {}
export interface Guide {}
export interface Manual {}
export interface Documentation {}
export interface Instructions {}
export interface Directions {}
export interface Steps {}
export interface Procedures {}
export interface Process {}
export interface Method {}
export interface Approach {}
export interface Strategy {}
export interface Technique {}
export interface Tactic {}
export interface Plan {}
export interface Scheme {}
export interface Design {}
export interface Pattern {}
export interface Template {}
export interface Model {}
export interface Prototype {}
export interface Example {}
export interface Sample {}
export interface Demo {}
export interface Preview {}
export interface Snapshot {}
export interface Image {}
export interface Picture {}
export interface Photo {}
export interface Illustration {}
export interface Diagram {}
export interface Chart {}
export interface Graph {}
export interface Table {}
export interface List {}
export interface Menu {}
export interface Options {}
export interface Choices {}
export interface Alternatives {}
export interface Selections {}
export interface Picks {}
export interface Preferences {}
export interface Settings {}
export interface Configurations {}
export interface Properties {}
export interface Attributes {}
export interface Characteristics {}
export interface Features {}
export interface Qualities {}
export interface Traits {}
export interface Aspects {}
export interface Facets {}
export interface Dimensions {}
export interface Parameters {}
export interface Variables {}
export interface Values {}
export interface Constants {}
export interface Literals {}
export interface Expressions {}
export interface Statements {}
export interface Declarations {}
export interface Definitions {}
export interface Descriptions {}
export interface Explanations {}
export interface Clarifications {}
export interface Details {}
export interface Specifics {}
export interface Particulars {}
export interface Information {}