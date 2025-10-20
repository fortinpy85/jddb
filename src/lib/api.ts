/**
 * JDDB API Client
 * TypeScript client for the Job Description Database API
 */
import { logger } from "@/utils/logger";
import type {
  JobDescription,
  ProcessingStats,
  SearchQuery,
  BulkUploadStatus,
  FileMetadata,
  StructuredFields,
  CircuitBreakerState,
  HealthIndicator,
  FileProcessingResponse,
  UploadResponse,
  TaskUploadResponse,
  ResilienceStats,
  HealthCheckResponse,
  JobListResponse,
  JobSectionResponse,
  JobDeleteResponse,
  DirectoryScanResponse,
  FileProcessResponse,
  BatchIngestResponse,
  SearchJobsResponse,
  SimilarJobsResponse,
  SearchFacetsResponse,
  SearchSuggestionsResponse,
  TaskStatsResponse,
  CircuitBreakerResetResponse,
  JobComparisonResponse,
} from "./types";

// Environment configuration with validation and fallbacks
function getApiBaseUrl(): string {
  // Try to get from environment variables
  let apiUrl: string | undefined;

  // Check for Node.js environment
  if (
    typeof process !== "undefined" &&
    (process as any).env?.NEXT_PUBLIC_API_URL
  ) {
    apiUrl = (process as any).env.NEXT_PUBLIC_API_URL;
  } else if (
    typeof window !== "undefined" &&
    (window as any).__API_BASE_URL__
  ) {
    // Fallback to window global if set by build process
    apiUrl = (window as any).__API_BASE_URL__;
  }

  // RUNTIME DETECTION: Check if we're on a unified server (same origin)
  // If current origin has working API proxy, use relative URLs
  if (typeof window !== "undefined") {
    const currentOrigin = window.location.origin;
    // If we're on port 3003 (unified server), use relative URLs
    if (currentOrigin.includes(":3003")) {
      logger.debug("Detected unified server, using relative API URLs");
      return "/api";
    }
  }

  // Use default fallback
  const defaultUrl = "http://localhost:8000/api";
  const finalUrl = apiUrl || defaultUrl;

  // Handle relative URLs (starting with /)
  if (finalUrl.startsWith("/")) {
    return finalUrl.replace(/\/$/, "");
  }

  // Basic URL validation for absolute URLs
  try {
    new URL(finalUrl.startsWith("http") ? finalUrl : `http://${finalUrl}`);
  } catch (error) {
    logger.warn(
      `Invalid API URL: ${finalUrl}, falling back to default: ${defaultUrl}`,
    );
    return defaultUrl;
  }

  // Ensure no trailing slash
  return finalUrl.replace(/\/$/, "");
}

export const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data: any,
    public isRetryable: boolean = false,
  ) {
    super(message);
    this.name = "ApiError";
  }

  static isNetworkError(error: Error): boolean {
    return error.name === "TypeError" && error.message.includes("fetch");
  }

  static isTimeoutError(error: Error): boolean {
    return error.name === "AbortError" || error.message.includes("timeout");
  }

  static isServerError(status: number): boolean {
    return status >= 500 && status < 600;
  }

  static isRetryableError(error: Error | ApiError): boolean {
    if (error instanceof ApiError) {
      return (
        error.isRetryable ||
        this.isServerError(error.status) ||
        error.status === 429
      ); // Rate limiting
    }
    return this.isNetworkError(error) || this.isTimeoutError(error);
  }
}

// API Client Class
export class JDDBApiClient {
  private static instance: JDDBApiClient;
  private baseUrl: string;
  private apiKey: string = "";
  private defaultTimeout: number = 120000; // 2 minutes
  private defaultRetries: number = 3;
  private retryDelay: number = 500; // 500ms base delay

  public setApiKey(apiKey: string): void {
    this.apiKey = apiKey;
  }

  public setDefaultTimeout(timeout: number): void {
    this.defaultTimeout = timeout;
  }

  public setDefaultRetries(retries: number): void {
    this.defaultRetries = retries;
  }

  public setRetryDelay(delay: number): void {
    this.retryDelay = delay;
  }

  // Private constructor for singleton
  private constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Singleton accessor
  public static getInstance(): JDDBApiClient {
    if (!JDDBApiClient.instance) {
      JDDBApiClient.instance = new JDDBApiClient();
    }
    return JDDBApiClient.instance;
  }

  // Test connection to API
  public async testConnection(): Promise<boolean> {
    try {
      // For connection testing, we want to know if the API is healthy right now,
      // not if it eventually succeeds after retries. So we disable retries.
      await this.request("/health", { method: "GET", retries: 0 });
      return true;
    } catch (error) {
      return false;
    }
  }

  // Get environment info for configuration validation
  public getEnvironmentInfo(): {
    hasValidConfig: boolean;
    isProduction: boolean;
    apiUrl: string;
    apiKeyPresent: boolean;
    environment: string;
  } {
    const apiUrl = this.baseUrl || "";
    const apiKeyPresent = !!this.apiKey;
    const isProduction =
      (typeof process !== "undefined" &&
        (process as any).env?.NODE_ENV === "production") ||
      (typeof window !== "undefined" &&
        window.location.hostname !== "localhost");
    const hasValidConfig =
      apiUrl !== "http://localhost:8000/api" &&
      apiUrl !== "" &&
      apiUrl !== "/api";
    const environment =
      typeof process !== "undefined"
        ? (process as any).env?.NODE_ENV || "development"
        : "browser";
    return {
      hasValidConfig,
      isProduction,
      apiUrl,
      apiKeyPresent,
      environment,
    };
  }

  // Configuration validation
  public async validateConfiguration(): Promise<{
    isValid: boolean;
    connectionTest: boolean;
    environmentInfo: ReturnType<JDDBApiClient["getEnvironmentInfo"]>;
    issues: string[];
  }> {
    const issues: string[] = [];
    const environmentInfo = this.getEnvironmentInfo();

    // Check environment configuration
    if (!environmentInfo.hasValidConfig) {
      issues.push(
        "Using default localhost configuration - may not work in production",
      );
    }

    if (environmentInfo.isProduction && this.baseUrl.startsWith("http://")) {
      issues.push("Using HTTP in production environment - consider HTTPS");
    }

    // Test connection
    const connectionTest = await this.testConnection();
    if (!connectionTest) {
      issues.push("Cannot establish connection to API server");
    }

    return {
      isValid: issues.length === 0,
      connectionTest,
      environmentInfo,
      issues,
    };
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit & {
      timeout?: number;
      retries?: number;
      retryDelay?: number;
    } = {},
  ): Promise<T> {
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      retryDelay = this.retryDelay,
      ...fetchOptions
    } = options;

    const url = `${this.baseUrl}${endpoint}`;
    let lastError: Error | ApiError;

    logger.debug(
      `🌐 API Request starting: ${fetchOptions.method || "GET"} ${url}`,
    );
    logger.debug(`📋 Request options:`, { timeout, retries, retryDelay });
    logger.debug(`🔑 API Key present:`, { hasApiKey: !!this.apiKey });

    for (let attempt = 0; attempt <= retries; attempt++) {
      logger.debug(`🔄 Attempt ${attempt + 1}/${retries + 1} for ${url}`);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        logger.debug(
          `⏰ Request timeout triggered after ${timeout}ms for ${url}`,
        );
        controller.abort();
      }, timeout);

      try {
        // Prepare headers, but don't override Content-Type for FormData
        const headers: HeadersInit = {};
        if (this.apiKey) {
          headers["X-API-Key"] = this.apiKey;
        }

        // Always set Accept header for JSON responses
        headers["Accept"] = "application/json";

        if (!fetchOptions.body || !(fetchOptions.body instanceof FormData)) {
          headers["Content-Type"] = "application/json";
        }

        logger.debug(`📤 About to call fetch() with:`, {
          url,
          method: fetchOptions.method || "GET",
          headers,
          hasBody: !!fetchOptions.body,
          bodyType: fetchOptions.body
            ? fetchOptions.body.constructor.name
            : "none",
        });

        const response = await fetch(url, {
          ...fetchOptions,
          headers: {
            ...headers,
            ...fetchOptions.headers,
          },
          signal: controller.signal,
        });

        logger.debug(`📥 Fetch response received:`, {
          url,
          status: response.status,
          statusText: response.statusText,
          ok: response.ok,
          headers: Object.fromEntries(response.headers.entries()),
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          let errorData: any = {};
          try {
            errorData = await response.json();
            logger.debug(`❌ Error response data:`, errorData);
          } catch (jsonError) {
            logger.debug(`❌ Failed to parse error response JSON:`, {
              error:
                jsonError instanceof Error
                  ? jsonError.message
                  : String(jsonError),
            });
            // JSON parsing failed, use empty object
          }

          const isRetryable =
            ApiError.isServerError(response.status) || response.status === 429;

          const error = new ApiError(
            errorData.detail ||
              `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            errorData,
            isRetryable,
          );

          logger.debug(`❌ API Error created:`, {
            message: error.message,
            status: error.status,
            isRetryable,
            attempt,
            maxRetries: retries,
          });

          // Don't retry for client errors (4xx) except 429
          if (!isRetryable || attempt === retries) {
            logger.debug(
              `❌ Throwing error - no more retries or not retryable`,
            );
            throw error;
          }

          lastError = error;
          logger.debug(
            `🔄 Will retry after ${retryDelay * Math.pow(2, attempt)}ms`,
          );
          await this.sleep(retryDelay * Math.pow(2, attempt)); // Exponential backoff
          continue;
        }

        logger.debug(`✅ Successful response, parsing JSON...`);
        const result = await response.json();
        logger.debug(
          `✅ API Request completed successfully for ${url}`,
          result,
        );
        return result;
      } catch (error: any) {
        logger.debug(`❌ Fetch error caught:`, {
          name: error.name,
          message: error.message,
          stack: error.stack?.split("\n").slice(0, 3).join("\n"),
        });

        clearTimeout(timeoutId);

        // Handle fetch errors (network, timeout, etc.)
        let processedError = error;
        if (error.name === "AbortError") {
          processedError = new Error(`Request timeout after ${timeout}ms`);
          logger.debug(`⏰ Request was aborted due to timeout`);
        }

        const isRetryable = ApiError.isRetryableError(processedError);
        logger.debug(`🔄 Error is retryable:`, {
          isRetryable,
          attempt,
          maxRetries: retries,
        });

        if (!isRetryable || attempt === retries) {
          logger.debug(
            `❌ Throwing final error - no more retries or not retryable`,
          );
          throw processedError instanceof ApiError
            ? processedError
            : new ApiError(processedError.message, 0, {}, isRetryable);
        }

        lastError = processedError;
        logger.debug(
          `🔄 Will retry after ${retryDelay * Math.pow(2, attempt)}ms due to error`,
        );
        await this.sleep(retryDelay * Math.pow(2, attempt)); // Exponential backoff
      }
    }

    logger.debug(`❌ All attempts exhausted, throwing last error`);
    throw lastError!;
  }

  // Health and Status
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request("/health", { method: "GET" });
  }

  async getDetailedHealth(): Promise<any> {
    return this.request("/health/detailed", { method: "GET" });
  }

  async getSystemAlerts(): Promise<any[]> {
    return this.request("/health/alerts", { method: "GET" });
  }

  async getComponentHealth(component: string): Promise<any> {
    return this.request(`/health/components/${component}`, { method: "GET" });
  }

  async getSystemMetrics(): Promise<any> {
    return this.request("/health/metrics/system", { method: "GET" });
  }

  async getApplicationMetrics(): Promise<any> {
    return this.request("/health/metrics/application", { method: "GET" });
  }

  // User Preferences
  async getAllPreferences(): Promise<{
    preferences: Record<string, any>;
    session_id: string;
  }> {
    return this.request("/preferences", {
      method: "GET",
      headers: {
        "X-Session-ID": this.getSessionId(),
      },
    });
  }

  async updatePreference(
    key: string,
    value: any,
  ): Promise<{ message: string; key: string; value: any }> {
    return this.request(`/preferences/${key}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": this.getSessionId(),
      },
      body: JSON.stringify({ value }),
    });
  }

  async updatePreferencesBulk(preferences: Record<string, any>): Promise<{
    message: string;
    updated: number;
    created: number;
    total: number;
  }> {
    return this.request("/preferences/bulk", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": this.getSessionId(),
      },
      body: JSON.stringify(preferences),
    });
  }

  async getPreference(
    key: string,
  ): Promise<{ key: string; value: any; updated_at?: string }> {
    return this.request(`/preferences/${key}`, {
      method: "GET",
      headers: {
        "X-Session-ID": this.getSessionId(),
      },
    });
  }

  async deletePreference(key: string): Promise<{ message: string }> {
    return this.request(`/preferences/${key}`, {
      method: "DELETE",
      headers: {
        "X-Session-ID": this.getSessionId(),
      },
    });
  }

  async resetAllPreferences(): Promise<{ message: string; deleted: number }> {
    return this.request("/preferences", {
      method: "DELETE",
      headers: {
        "X-Session-ID": this.getSessionId(),
      },
    });
  }

  // Helper method to get or create session ID
  private getSessionId(): string {
    let sessionId = localStorage.getItem("jddb_session_id");
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      localStorage.setItem("jddb_session_id", sessionId);
    }
    return sessionId;
  }

  // Job Management
  async listJobs({
    skip = 0,
    limit = 100,
    classification,
    language,
    department,
    skill_ids,
  }: {
    skip?: number;
    limit?: number;
    classification?: string;
    language?: string;
    department?: string;
    skill_ids?: number[];
  } = {}): Promise<JobListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (classification) params.append("classification", classification);
    if (language) params.append("language", language);
    if (department) params.append("department", department);
    if (skill_ids && skill_ids.length > 0)
      params.append("skill_ids", skill_ids.join(","));

    return this.request(`/jobs?${params}`, { method: "GET" });
  }

  async getJob(
    jobId: number,
    options: {
      include_content?: boolean;
      include_sections?: boolean;
      include_metadata?: boolean;
      include_skills?: boolean;
    } = {},
  ): Promise<JobDescription> {
    const params = new URLSearchParams();
    if (options.include_content) params.append("include_content", "true");
    if (options.include_sections) params.append("include_sections", "true");
    if (options.include_metadata) params.append("include_metadata", "true");
    if (options.include_skills !== false)
      params.append("include_skills", "true"); // Default to true

    const query = params.toString() ? `?${params}` : "";
    return this.request(`/jobs/${jobId}${query}`, { method: "GET" });
  }

  async getJobSection(
    jobId: number,
    sectionType: string,
  ): Promise<JobSectionResponse> {
    return this.request(`/jobs/${jobId}/sections/${sectionType}`, {
      method: "GET",
    });
  }

  async createJob(jobData: {
    job_number: string;
    title: string;
    classification: string;
    language?: string;
    department?: string;
    reports_to?: string;
    content?: string;
    sections?: Record<string, string>;
  }): Promise<{
    status: string;
    message: string;
    job_id: number;
    job: JobDescription;
  }> {
    return this.request(`/jobs/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jobData),
    });
  }

  async reprocessJob(jobId: number): Promise<{
    status: string;
    message: string;
    job_id: number;
  }> {
    return this.request(`/jobs/${jobId}/reprocess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
  }

  async deleteJob(jobId: number): Promise<JobDeleteResponse> {
    return this.request(`/jobs/${jobId}`, { method: "DELETE" });
  }

  async updateJob(
    jobId: number,
    updates: {
      title?: string;
      classification?: string;
      language?: string;
      raw_content?: string;
      department?: string;
      reports_to?: string;
    },
  ): Promise<{
    status: string;
    message: string;
    job_id: number;
    job: JobDescription;
  }> {
    return this.request(`/jobs/${jobId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
  }

  async updateJobSection(
    jobId: number,
    sectionId: number,
    sectionContent: string,
  ): Promise<{
    status: string;
    message: string;
    section: {
      id: number;
      section_type: string;
      section_content: string;
      section_order: number;
    };
  }> {
    return this.request(`/jobs/${jobId}/sections/${sectionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section_content: sectionContent }),
    });
  }

  // File Processing and Ingestion
  async scanDirectory(
    directoryPath: string,
    recursive = true,
  ): Promise<DirectoryScanResponse> {
    return this.request("/ingestion/scan-directory", {
      method: "POST",
      body: JSON.stringify({
        directory_path: directoryPath,
        recursive,
      }),
    });
  }

  async processFile(filePath: string): Promise<FileProcessResponse> {
    return this.request("/ingestion/process-file", {
      method: "POST",
      body: JSON.stringify({ file_path: filePath }),
    });
  }

  async batchIngest(
    directoryPath: string,
    options: {
      recursive?: boolean;
      max_files?: number;
    } = {},
  ): Promise<BatchIngestResponse> {
    return this.request("/ingestion/batch-ingest", {
      method: "POST",
      body: JSON.stringify({
        directory_path: directoryPath,
        recursive: options.recursive ?? true,
        max_files: options.max_files,
      }),
    });
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return this.request("/ingestion/upload", {
      method: "POST",
      body: formData,
      // Don't set Content-Type for FormData - let browser set it with boundary
    });
  }

  // Search Functionality
  async searchJobs(searchQuery: SearchQuery): Promise<SearchJobsResponse> {
    return this.request("/search/", {
      method: "POST",
      body: JSON.stringify(searchQuery),
    });
  }

  async findSimilarJobs(
    jobId: number,
    limit = 10,
  ): Promise<SimilarJobsResponse> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.request(`/search/similar/${jobId}?${params}`, {
      method: "GET",
    });
  }

  async getSearchFacets(): Promise<SearchFacetsResponse> {
    return this.request("/search/facets", { method: "GET" });
  }

  async getSearchSuggestions(
    query: string,
    limit = 10,
  ): Promise<SearchSuggestionsResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });
    return this.request(`/search/suggestions?${params}`, { method: "GET" });
  }

  // Status and Monitoring
  async getProcessingStatus(): Promise<ProcessingStats> {
    return this.request("/jobs/status", { method: "GET" });
  }

  async getIngestionStats(): Promise<{
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
  }> {
    return this.request("/ingestion/stats", { method: "GET" });
  }

  async getTaskStats(): Promise<TaskStatsResponse> {
    return this.request("/ingestion/task-stats", { method: "GET" });
  }

  async getResilienceStatus(): Promise<ResilienceStats> {
    return this.request("/ingestion/resilience-status", { method: "GET" });
  }

  async resetCircuitBreakers(
    serviceName?: string,
  ): Promise<CircuitBreakerResetResponse> {
    const params = serviceName ? `?service_name=${serviceName}` : "";
    return this.request(`/ingestion/reset-circuit-breakers${params}`, {
      method: "POST",
    });
  }

  // Bulk Upload Management
  async bulkUploadFiles(files: FileList): Promise<BulkUploadStatus> {
    const formData = new FormData();
    Array.from(files).forEach((file, index) => {
      formData.append(`files`, file);
    });

    return this.request("/ingestion/bulk-upload", {
      method: "POST",
      body: formData,
      // Don't set Content-Type for FormData - let browser set it with boundary
    });
  }

  // Job Comparison and Analysis
  async compareJobs({
    job_a_id,
    job_b_id,
    comparison_types = ["similarity", "skill_gap", "requirements"],
    include_details = true,
  }: {
    job_a_id: number;
    job_b_id: number;
    comparison_types?: string[];
    include_details?: boolean;
  }): Promise<JobComparisonResponse> {
    return this.request(`/search/compare/${job_a_id}/${job_b_id}`, {
      method: "GET",
    });
  }

  async mergeJobs(
    jobId1: number,
    jobId2: number,
    strategy: string,
  ): Promise<JobDescription> {
    // Simulate API call
    logger.debug(
      `Merging jobs ${jobId1} and ${jobId2} with strategy: ${strategy}`,
    );
    const job1 = await this.getJob(jobId1, {
      include_content: true,
      include_sections: true,
    });
    const job2 = await this.getJob(jobId2, {
      include_content: true,
      include_sections: true,
    });

    const mergedContent = `Merged content from job ${job1.job_number} and ${job2.job_number}.\n\n${job1.sections ? Object.values(job1.sections).join("\n") : ""}\n\n${job2.sections ? Object.values(job2.sections).join("\n") : ""}`;

    const newJob: JobDescription = {
      id: Math.floor(Math.random() * 10000),
      job_number: `MERGED-${job1.job_number}-${job2.job_number}`,
      title: `Merged: ${job1.title} / ${job2.title}`,
      classification: job1.classification,
      language: job1.language,
      sections: job1.sections?.concat(job2.sections || []),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      file_path: "",
      file_hash: "",
    };

    return Promise.resolve(newJob);
  }

  // ============================================================================
  // AI Enhancement Methods (Phase 3)
  // ============================================================================

  /**
   * Analyze text for bias and inclusivity issues
   * @param params - Text to analyze, analysis types, and GPT-4 flag
   * @returns Bias analysis with issues and inclusivity score
   */
  async analyzeBias(params: {
    job_id?: number;
    text?: string;
    analysis_types?: string[];
    use_gpt4?: boolean;
  }): Promise<any> {
    return this.request(`/ai/bias`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Calculate comprehensive quality score for job description
   * @param jobData - Job description data with sections
   * @returns Quality score with dimension breakdown
   */
  async calculateQualityScore(jobData: {
    sections: Record<string, string>;
    raw_content?: string;
  }): Promise<any> {
    return this.request("/ai/quality-score", {
      method: "POST",
      body: JSON.stringify({ job_data: jobData }),
    });
  }

  /**
   * Auto-complete a job description section using GPT-4
   * @param params - Section details and context
   * @returns Completed content with completion text
   */
  async completeSection(params: {
    section_type: string;
    partial_content: string;
    classification: string;
    language?: string;
    context?: Record<string, any>;
  }): Promise<any> {
    return this.request("/ai/complete-section", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Enhance content for clarity, active voice, and professionalism
   * @param params - Text and enhancement types
   * @returns Enhanced text with changes
   */
  async enhanceContent(params: {
    text: string;
    enhancement_types: string[];
    language?: string;
  }): Promise<any> {
    return this.request("/ai/enhance-content", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Get inline writing suggestions at cursor position
   * @param params - Text, cursor position, and context
   * @returns Suggestions array
   */
  async getInlineSuggestions(params: {
    text: string;
    cursor_position: number;
    context?: string;
  }): Promise<any> {
    return this.request("/ai/inline-suggestions", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async saveImprovedContent(params: {
    job_id: number;
    improved_content: string;
  }): Promise<any> {
    return this.request("/ai/content/save-improved-content", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async translateContent(params: {
    text: string;
    target_language: string;
  }): Promise<{ translated_text: string }> {
    return this.request("/ai/content/translate-content", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async generateJobPosting(params: {
    job_id: number;
  }): Promise<{ job_posting: string }> {
    return this.request("/ai/content/generate-job-posting", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async runPredictiveAnalysis(params: { job_id: number }): Promise<any> {
    return this.request("/ai/content/run-predictive-analysis", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Get text improvement suggestions
   * @param params - Text, context, and suggestion types
   * @returns Suggestions with overall score
   */
  async getSuggestions(params: {
    job_id?: number;
    section_type?: string;
    text?: string;
    context?: string;
    suggestion_types?: string[];
  }): Promise<any> {
    return this.request("/ai/suggestions", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Check compliance against government standards
   * @param params - Text and compliance frameworks
   * @returns Compliance status and issues
   */
  async checkCompliance(params: {
    text: string;
    compliance_frameworks?: string[];
  }): Promise<any> {
    return this.request("/ai/check-compliance", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Get job description template for classification
   * @param classification - Job classification code
   * @param language - Template language (en or fr)
   * @returns Template with sections
   */
  async getTemplate(
    classification: string,
    language: string = "en",
  ): Promise<any> {
    return this.request(
      `/ai/templates/${classification}?language=${language}`,
      {
        method: "GET",
      },
    );
  }

  /**
   * Generate custom job description template
   * @param params - Classification, language, and custom requirements
   * @returns Generated template
   */
  async generateTemplate(params: {
    classification: string;
    language?: string;
    custom_requirements?: Record<string, any>;
  }): Promise<any> {
    return this.request("/ai/templates/generate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Generate section completion for job description
   * @param params - Section type, context, and requirements
   * @returns Generated section content
   */
  async generateSectionCompletion(params: {
    section_type: string;
    current_content?: string;
    job_context?: string;
    classification?: string;
    language?: string;
    context?: Record<string, any>;
  }): Promise<{
    completed_content: string;
    content: string;
    confidence: number;
    message: string;
  }> {
    // Map frontend parameters to backend expected format
    const backendRequest = {
      section_type: params.section_type,
      partial_content: params.current_content || "",
      classification: params.classification || "EX-01",
      language: params.language || "en",
      context:
        params.context ||
        (params.job_context ? { job_context: params.job_context } : {}),
    };

    return this.request("/ai/content/complete-section", {
      method: "POST",
      body: JSON.stringify(backendRequest),
    });
  }

  /**
   * Alias for listJobs - get list of jobs with filters
   * @param options - Query parameters (skip, limit, filters)
   * @returns Job list response
   */
  async getJobs(
    options: {
      skip?: number;
      limit?: number;
      classification?: string;
      language?: string;
      department?: string;
      skill_ids?: number[];
    } = {},
  ): Promise<JobListResponse> {
    return this.listJobs(options);
  }

  /**
   * Sync RLHF events from localStorage to backend
   * @param events - Array of RLHF events to sync
   * @returns Synced feedback records
   */
  async syncRLHFEvents(
    events: Array<{
      timestamp: string;
      eventType: "accept" | "reject" | "modify" | "generate";
      suggestionId?: string;
      suggestionType?: string;
      originalText: string;
      suggestedText?: string;
      finalText?: string;
      userAction: string;
      confidence?: number;
      metadata?: Record<string, any>;
    }>,
  ): Promise<any> {
    if (events.length === 0) {
      return { synced: 0, message: "No events to sync" };
    }

    // Transform frontend events to backend format
    const feedbackItems = events.map((event) => ({
      event_type: event.eventType,
      original_text: event.originalText,
      suggested_text: event.suggestedText,
      final_text: event.finalText,
      suggestion_type: event.suggestionType,
      user_action: event.userAction,
      confidence: event.confidence,
      metadata: {
        ...event.metadata,
        timestamp: event.timestamp,
        suggestion_id: event.suggestionId,
      },
    }));

    return this.request("/rlhf/feedback/bulk", {
      method: "POST",
      body: JSON.stringify({ feedback_items: feedbackItems }),
    });
  }

  // === Skills Analytics Methods ===

  /**
   * Get skills inventory with filtering and pagination
   */
  async getSkillsInventory(
    options: {
      search?: string;
      skill_type?: string;
      min_job_count?: number;
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<import("./types").SkillsInventoryResponse> {
    const params = new URLSearchParams();
    if (options.search) params.append("search", options.search);
    if (options.skill_type) params.append("skill_type", options.skill_type);
    if (options.min_job_count)
      params.append("min_job_count", String(options.min_job_count));
    if (options.limit) params.append("limit", String(options.limit));
    if (options.offset) params.append("offset", String(options.offset));

    const query = params.toString() ? `?${params}` : "";
    return this.request(`/analytics/skills/inventory${query}`, {
      method: "GET",
    });
  }

  /**
   * Get top N most frequently requested skills
   */
  async getTopSkills(
    options: {
      limit?: number;
      skill_type?: string;
    } = {},
  ): Promise<import("./types").TopSkillsResponse> {
    const params = new URLSearchParams();
    if (options.limit) params.append("limit", String(options.limit));
    if (options.skill_type) params.append("skill_type", options.skill_type);

    const query = params.toString() ? `?${params}` : "";
    return this.request(`/analytics/skills/top${query}`, { method: "GET" });
  }

  /**
   * Get distribution of skills by type
   */
  async getSkillTypes(): Promise<import("./types").SkillTypesResponse> {
    return this.request("/analytics/skills/types", { method: "GET" });
  }

  /**
   * Get overall skills statistics
   */
  async getSkillsStats(): Promise<import("./types").SkillsStatsResponse> {
    return this.request("/analytics/skills/stats", { method: "GET" });
  }
}

// Helper to set API key from environment
export function setApiKeyFromEnv(client: JDDBApiClient) {
  let apiKey = "";
  if (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_KEY) {
    apiKey = import.meta.env.VITE_API_KEY;
  } else if (
    typeof process !== "undefined" &&
    (process as any).env?.NEXT_PUBLIC_API_KEY
  ) {
    apiKey = (process as any).env.NEXT_PUBLIC_API_KEY;
  }
  if (apiKey) {
    client.setApiKey(apiKey);
  }
}

// Singleton accessor
export function getJDDBApiClient(): JDDBApiClient {
  const client = JDDBApiClient.getInstance();
  setApiKeyFromEnv(client);
  return client;
}

// Export singleton instance
export const apiClient = JDDBApiClient.getInstance();

// Export default api instance for backward compatibility
export const api = apiClient;

// React Hook for API operations
export function useApi() {
  return apiClient;
}

// Export types for use by other modules
export type {
  JobDescription,
  Skill,
  SkillsInventoryResponse,
  SkillInventoryItem,
  TopSkillsResponse,
  TopSkill,
  SkillTypesResponse,
  SkillType,
  SkillsStatsResponse,
  ProcessingStats,
  SearchQuery,
  SearchResult,
  BulkUploadStatus,
  FileMetadata,
} from "./types";
