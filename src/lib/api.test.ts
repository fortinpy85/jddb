/**
 * Unit tests for API client
 */
import { describe, test, expect, beforeEach, vi } from "vitest";
import { JDDBApiClient } from "./api";

// Helper to create a proper mock Response with headers
const createMockResponse = (overrides: Partial<Response> = {}): Response =>
  ({
    ok: true,
    status: 200,
    statusText: "OK",
    redirected: false,
    json: async () => ({}),
    text: async () => "",
    headers: {
      entries: () => [],
      get: () => null,
      has: () => false,
      forEach: () => {},
    } as any,
    ...overrides,
  }) as Response;

// Mock fetch globally
const mockFetch = vi.fn(() => Promise.resolve(createMockResponse()));
global.fetch = mockFetch as unknown as typeof fetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(() => {}),
  removeItem: vi.fn(() => {}),
  clear: vi.fn(() => {}),
};
(global as any).localStorage = mockLocalStorage;

describe("JDDBApiClient", () => {
  let apiClient: JDDBApiClient;

  beforeEach(() => {
    // Mock the environment for consistent testing
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api";

    mockFetch.mockReset();
    mockLocalStorage.getItem.mockReset();
    mockLocalStorage.setItem.mockReset();

    // Clear singleton instance to get fresh instance with mocked env
    (JDDBApiClient as any).instance = undefined;
    apiClient = JDDBApiClient.getInstance();
  });

  describe("constructor", () => {
    test("should use environment API URL when available", () => {
      expect(apiClient).toBeDefined();
    });

    test("should use fallback URL when environment not available", () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_API_URL;

      // Clear singleton to force recreation
      (JDDBApiClient as any).instance = undefined;

      const client = JDDBApiClient.getInstance();
      expect(client).toBeDefined();

      // Verify it uses default URL
      const envInfo = client.getEnvironmentInfo();
      expect(envInfo.apiUrl).toBe("http://localhost:8000/api");

      process.env.NEXT_PUBLIC_API_URL = originalEnv;
    });
  });

  describe("testConnection", () => {
    test("should return true when API is reachable", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          status: 200,
          json: async () => ({ status: "healthy" }),
        }),
      );

      const result = await apiClient.testConnection();
      expect(result).toBe(true);
    });

    test("should return false when API is unreachable", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const result = await apiClient.testConnection();
      expect(result).toBe(false);
    });

    test("should return false when API returns error status", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: false,
          status: 500,
          json: async () => ({ error: "Server error" }),
        }),
      );

      const result = await apiClient.testConnection();
      expect(result).toBe(false);
    });
  });

  describe("getJobs", () => {
    const mockJobsResponse = {
      jobs: [
        {
          id: 1,
          job_number: "123456",
          title: "Test Job",
          classification: "EX-01",
          language: "EN",
          file_path: "/path/to/file",
          file_hash: "hash123",
        },
      ],
      pagination: {
        skip: 0,
        limit: 100,
        total: 1,
        has_more: false,
      },
    };

    test("should fetch jobs successfully", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockJobsResponse,
        }),
      );

      const result = await apiClient.listJobs({});

      expect(result).toEqual(mockJobsResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/jobs?skip=0&limit=100",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });

    test("should handle pagination parameters", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockJobsResponse,
        }),
      );

      await apiClient.listJobs({ skip: 20, limit: 20 });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/jobs?skip=20&limit=20",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });

    test("should handle search parameters", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockJobsResponse,
        }),
      );

      await apiClient.listJobs({
        classification: "EX-01",
        language: "EN",
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("classification=EX-01&language=EN"),
        expect.objectContaining({
          method: "GET",
        }),
      );
    });

    test("should throw error when API request fails", async () => {
      // Mock fetch to reject with a network error to test error handling
      mockFetch.mockRejectedValueOnce(new Error("Server error"));

      await expect(apiClient.listJobs({})).rejects.toThrow("Server error");
    });
  });

  describe("getJobById", () => {
    const mockJob = {
      id: 1,
      job_number: "123456",
      title: "Test Job",
      classification: "EX-01",
      language: "EN",
      file_path: "/path/to/file",
      file_hash: "hash123",
      sections: [],
      job_metadata: null,
    };

    test("should fetch job by ID successfully", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockJob,
        }),
      );

      const result = await apiClient.getJob(1);

      expect(result).toEqual(mockJob);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/1"),
        expect.any(Object),
      );
    });

    test("should handle not found error", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: false,
          status: 404,
          statusText: "Not Found",
          json: async () => ({ detail: "HTTP 404: Not Found" }),
        }),
      );

      await expect(apiClient.getJob(999)).rejects.toThrow("HTTP 404");
    });
  });

  describe("uploadFile", () => {
    test("should upload file successfully", async () => {
      const mockResponse = {
        status: "success",
        filename: "test.txt",
        processing_result: {
          status: "success" as const,
          file_info: {
            filename: "test.txt",
            file_size: 12,
            file_hash: "hash123",
          },
          processed_content: {
            sections_found: 2,
            sections: ["GENERAL_ACCOUNTABILITY", "SPECIFIC_ACCOUNTABILITIES"],
            structured_fields: {
              title: "Test Job",
              classification: "EX-01",
            },
            chunks_generated: 5,
            processing_errors: [],
          },
          job_id: 1,
          message: "File processed successfully",
          errors: [],
        },
      };

      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockResponse,
          text: async () => "",
        }),
      );

      const file = new File(["test content"], "test.txt", {
        type: "text/plain",
      });
      const result = await apiClient.uploadFile(file);

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ingestion/upload"),
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        }),
      );
    });

    test("should handle upload failure", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: false,
          status: 400,
          statusText: "Bad Request",
          text: async () => "Invalid file format",
        }),
      );

      const file = new File(["test"], "test.txt", { type: "text/plain" });

      await expect(apiClient.uploadFile(file)).rejects.toThrow(
        "HTTP 400: Bad Request",
      );
    });
  });

  describe("searchJobs", () => {
    const mockSearchResults = {
      query: "director",
      total_results: 1,
      results: [
        {
          job_id: 1,
          job_number: "123456",
          title: "Director, Business Analysis",
          classification: "EX-01",
          language: "EN",
          relevance_score: 0.95,
          matching_sections: [
            {
              section_type: "GENERAL_ACCOUNTABILITY",
              section_id: 1,
              snippet: "Test snippet...",
            },
          ],
          snippet: "Test snippet...",
        },
      ],
    };

    test("should search jobs successfully", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockSearchResults,
          text: async () => "",
        }),
      );

      const result = await apiClient.searchJobs({ query: "director" });

      expect(result).toEqual(mockSearchResults);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/search/"),
        expect.any(Object),
      );
    });

    test("should handle advanced search parameters", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockSearchResults,
          text: async () => "",
        }),
      );

      await apiClient.searchJobs({
        query: "director",
        classification: "EX-01",
        limit: 20,
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/search/",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("classification"),
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("compareJobs", () => {
    const mockComparison = {
      comparison_id: "comp-123",
      jobs: {
        job1: {
          id: 1,
          job_number: "123456",
          title: "Job A",
          classification: "EX-01",
          language: "EN",
        },
        job2: {
          id: 2,
          job_number: "654321",
          title: "Job B",
          classification: "EX-02",
          language: "EN",
        },
      },
      similarity_analysis: {
        overall_similarity: 0.85,
        similarity_level: "high",
        metadata_comparison: {
          classification: {
            job1: "EX-01",
            job2: "EX-02",
            match: false,
          },
          language: {
            job1: "EN",
            job2: "EN",
            match: true,
          },
          title_similarity: 0.7,
        },
        section_comparison: [
          {
            section_type: "GENERAL_ACCOUNTABILITY",
            job1_content: "Content A",
            job2_content: "Content B",
            similarity_score: 0.9,
            both_present: true,
            job1_only: false,
            job2_only: false,
          },
        ],
      },
      recommendations: ["Consider similar responsibilities"],
    };

    test("should compare jobs successfully", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockComparison,
          text: async () => "",
        }),
      );

      const result = await apiClient.compareJobs({ job_a_id: 1, job_b_id: 2 });

      expect(result).toEqual(mockComparison);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/search/compare/1/2",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("getJobStatistics", () => {
    const mockStats = {
      total_jobs: 100,
      by_classification: {
        "EX-01": 60,
        "EX-02": 30,
        "EX-03": 10,
      },
      by_language: {
        EN: 80,
        FR: 20,
      },
      processing_status: {
        completed: 90,
        partial: 8,
        needs_embeddings: 2,
        needs_sections: 0,
        needs_metadata: 0,
      },
      embedding_stats: {
        total_chunks: 500,
        embedded_chunks: 490,
        embedding_completion_rate: 98.0,
        jobs_with_embeddings: 98,
      },
      content_quality: {
        jobs_with_sections: 95,
        jobs_with_metadata: 85,
        jobs_with_embeddings: 98,
        section_coverage_rate: 95.0,
        metadata_coverage_rate: 85.0,
        embedding_coverage_rate: 98.0,
      },
      section_distribution: {
        GENERAL_ACCOUNTABILITY: 100,
        SPECIFIC_ACCOUNTABILITIES: 98,
        KNOWLEDGE_SKILLS: 95,
      },
      recent_activity: {
        jobs_last_7_days: 5,
        daily_average: 0.7,
      },
      last_updated: "2024-01-01T00:00:00Z",
    };

    test("should fetch statistics successfully", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => mockStats,
          text: async () => "",
        }),
      );

      const result = await apiClient.getIngestionStats();

      expect(result).toEqual(mockStats);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/ingestion/stats",
        expect.objectContaining({
          method: "GET",
        }),
      );
    });
  });

  describe("error handling", () => {
    test("should handle network errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(apiClient.listJobs({})).rejects.toThrow("Network error");
    });

    test("should handle timeout errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("The operation timed out"));

      await expect(apiClient.listJobs({})).rejects.toThrow(
        "The operation timed out",
      );
    });

    test("should handle JSON parsing errors", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => {
            throw new Error("Invalid JSON");
          },
          text: async () => "",
        }),
      );

      await expect(apiClient.listJobs({})).rejects.toThrow("Invalid JSON");
    });
  });

  describe("retry logic", () => {
    test("should retry on 5xx errors", async () => {
      // First call fails with 500, second succeeds
      mockFetch
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 500,
            statusText: "Internal Server Error",
            json: async () => ({ detail: "Server error" }),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: true,
            json: async () => ({ jobs: [], total: 0, page: 1, pages: 0 }),
          }),
        );

      const result = await apiClient.listJobs({});

      expect(result).toBeDefined();
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    test("should not retry on 4xx errors", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: false,
          status: 400,
          statusText: "Bad Request",
          text: async () => "Bad request",
        }),
      );

      await expect(apiClient.listJobs({})).rejects.toThrow("HTTP 400");
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe("request headers", () => {
    test("should include correct headers in requests", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ jobs: [], total: 0, page: 1, pages: 0 }),
          text: async () => "",
        }),
      );

      await apiClient.listJobs({});

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("http://localhost:8000/api/jobs"),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });

    test("should not include Content-Type for FormData requests", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ message: "Success" }),
          text: async () => "",
        }),
      );

      const file = new File(["test"], "test.txt");
      await apiClient.uploadFile(file);

      const calls = mockFetch.mock.calls as any[];
      const lastCall = calls[calls.length - 1];
      if (lastCall && lastCall.length > 1) {
        const requestInit = lastCall[1] as RequestInit;
        const headers = requestInit?.headers as
          | Record<string, string>
          | undefined;
        expect(headers?.["Content-Type"]).toBeUndefined();
      } else {
        // If no call was made or call doesn't have the expected structure, fail the test
        expect(lastCall).toBeDefined();
        expect(lastCall?.length).toBeGreaterThan(1);
      }
    });
  });

  describe("configuration methods", () => {
    test("setApiKey updates the API key", () => {
      apiClient.setApiKey("new-api-key");
      expect(apiClient["apiKey"]).toBe("new-api-key");
    });

    test("setDefaultTimeout updates timeout value", () => {
      apiClient.setDefaultTimeout(5000);
      expect(apiClient["defaultTimeout"]).toBe(5000);
    });

    test("setDefaultRetries updates retries value", () => {
      apiClient.setDefaultRetries(5);
      expect(apiClient["defaultRetries"]).toBe(5);
    });

    test("setRetryDelay updates retry delay", () => {
      apiClient.setRetryDelay(2000);
      expect(apiClient["retryDelay"]).toBe(2000);
    });

    test("getInstance returns singleton instance", () => {
      const instance1 = JDDBApiClient.getInstance();
      const instance2 = JDDBApiClient.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe("environment info", () => {
    test("getEnvironmentInfo returns correct structure", () => {
      const info = apiClient.getEnvironmentInfo();

      expect(info).toHaveProperty("apiUrl");
      expect(info).toHaveProperty("isProduction");
      expect(info).toHaveProperty("hasValidConfig");
      expect(info).toHaveProperty("environment");
      expect(info.apiUrl).toBe("http://localhost:8000/api");
      expect(info.isProduction).toBe(false);
    });

    test("detects production environment", () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";
      const info = apiClient.getEnvironmentInfo();
      expect(info.isProduction).toBe(true);
      process.env.NODE_ENV = originalEnv;
    });
  });

  describe("health endpoints", () => {
    test("healthCheck returns health status", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            status: "healthy",
            timestamp: new Date().toISOString(),
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.healthCheck();
      expect(response.status).toBe("healthy");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health"),
        expect.any(Object),
      );
    });

    test("getDetailedHealth returns detailed health data", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ database: "connected", redis: "connected" }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getDetailedHealth();
      expect(response).toHaveProperty("database");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health/detailed"),
        expect.any(Object),
      );
    });
  });

  describe("job management methods", () => {
    test("getJobSection retrieves specific job section", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            section_type: "accountability",
            section_content: "Test content",
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getJobSection(1, "10");
      expect(response.section_type).toBe("accountability");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/1/sections/10"),
        expect.any(Object),
      );
    });

    test("deleteJob removes a job", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ message: "Job deleted successfully" }),
          text: async () => "",
        }),
      );

      const response = await apiClient.deleteJob(1);
      expect(response.message).toContain("deleted");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/1"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    test("reprocessJob triggers job reprocessing", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            message: "Job reprocessing started",
            job_id: 1,
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.reprocessJob(1);
      expect(response.job_id).toBe(1);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/1/reprocess"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("skills endpoints", () => {
    test("getSkillsInventory retrieves skills data", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ skills: [], total: 0 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSkillsInventory({ limit: 10 });
      expect(response).toHaveProperty("skills");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/analytics/skills/inventory"),
        expect.any(Object),
      );
    });

    test("getTopSkills retrieves top skills", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ skills: [], limit: 10 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getTopSkills({ limit: 10 });
      expect(response).toHaveProperty("skills");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/analytics/skills/top"),
        expect.any(Object),
      );
    });

    test("getSkillTypes retrieves skill types", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ types: [] }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSkillTypes();
      expect(response).toHaveProperty("types");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/analytics/skills/types"),
        expect.any(Object),
      );
    });

    test("getSkillsStats retrieves skills statistics", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ total_skills: 0, total_jobs_with_skills: 0 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSkillsStats();
      expect(response).toHaveProperty("total_skills");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/analytics/skills/stats"),
        expect.any(Object),
      );
    });
  });

  describe("preferences endpoints", () => {
    test("getAllPreferences retrieves all preferences", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            preferences: { theme: "dark" },
            session_id: "123",
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getAllPreferences();
      expect(response).toHaveProperty("preferences");
      expect(response).toHaveProperty("session_id");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences"),
        expect.any(Object),
      );
    });

    test("updatePreference updates a single preference", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            message: "Updated",
            key: "theme",
            value: "dark",
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.updatePreference("theme", "dark");
      expect(response.key).toBe("theme");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences/theme"),
        expect.objectContaining({ method: "PUT" }),
      );
    });

    test("getPreference retrieves a single preference", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ key: "theme", value: "dark" }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getPreference("theme");
      expect(response.key).toBe("theme");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences/theme"),
        expect.any(Object),
      );
    });

    test("deletePreference removes a preference", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ message: "Deleted" }),
          text: async () => "",
        }),
      );

      const response = await apiClient.deletePreference("theme");
      expect(response.message).toBe("Deleted");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences/theme"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  describe("AI and bias detection endpoints", () => {
    test("analyzeBias analyzes job for bias", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ bias_score: 0.2, issues: [] }),
          text: async () => "",
        }),
      );

      const response = await apiClient.analyzeBias({ job_id: 1 });
      expect(response).toHaveProperty("bias_score");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ai/bias"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("calculateQualityScore calculates quality metrics", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ quality_score: 85, metrics: {} }),
          text: async () => "",
        }),
      );

      const response = await apiClient.calculateQualityScore({
        sections: { accountability: "Test content" },
        raw_content: "Test content",
      });
      expect(response).toHaveProperty("quality_score");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ai/quality-score"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("getSuggestions retrieves AI suggestions", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ suggestions: [] }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSuggestions({
        job_id: 1,
        section_type: "accountability",
      });
      expect(response).toHaveProperty("suggestions");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ai/suggestions"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("template endpoints", () => {
    test("getTemplate retrieves a template", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            template: "Test template",
            classification: "EX-01",
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getTemplate("EX-01", "en");
      expect(response).toHaveProperty("template");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/templates/EX-01"),
        expect.any(Object),
      );
    });

    test("generateTemplate generates a new template", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            template: "Generated template",
            classification: "EX-01",
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.generateTemplate({
        classification: "EX-01",
        language: "en",
      });
      expect(response).toHaveProperty("template");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/templates/generate"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("search utility endpoints", () => {
    test("getSearchFacets retrieves search facets", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            facets: { classifications: [], languages: [] },
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSearchFacets();
      expect(response).toHaveProperty("facets");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/search/facets"),
        expect.any(Object),
      );
    });

    test("getSearchSuggestions retrieves search suggestions", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ suggestions: ["test", "testing"] }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSearchSuggestions("test");
      expect(response).toHaveProperty("suggestions");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/search/suggestions"),
        expect.any(Object),
      );
    });

    test("findSimilarJobs finds similar jobs", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ similar_jobs: [], count: 0 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.findSimilarJobs(1, 5);
      expect(response).toHaveProperty("similar_jobs");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/search/similar"),
        expect.any(Object),
      );
    });
  });

  describe("job creation and ingestion", () => {
    test("createJob creates a new job", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            status: "success",
            message: "Job created",
            job_id: 1,
            job: { id: 1, job_number: "12345", title: "Test Job" },
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.createJob({
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
      });
      expect(response.job_id).toBe(1);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("scanDirectory scans a directory for files", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ files: [], count: 0 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.scanDirectory("/path/to/dir", true);
      expect(response).toHaveProperty("files");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ingestion/scan-directory"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("processFile processes a single file", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ status: "processed", job_id: 1 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.processFile("/path/to/file.pdf");
      expect(response).toHaveProperty("status");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ingestion/process-file"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("batchIngest processes multiple files", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ processed: 5, failed: 0, total: 5 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.batchIngest("/path/to/dir", {
        recursive: true,
      });
      expect(response).toHaveProperty("processed");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/ingestion/batch-ingest"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("additional health endpoints", () => {
    test("getSystemAlerts retrieves system alerts", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => [{ level: "warning", message: "High CPU" }],
          text: async () => "",
        }),
      );

      const response = await apiClient.getSystemAlerts();
      expect(Array.isArray(response)).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health/alerts"),
        expect.any(Object),
      );
    });

    test("getComponentHealth retrieves component health", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ status: "healthy", component: "database" }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getComponentHealth("database");
      expect(response).toHaveProperty("status");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health/components/database"),
        expect.any(Object),
      );
    });

    test("getSystemMetrics retrieves system metrics", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ cpu: 45, memory: 2048, disk: 50000 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getSystemMetrics();
      expect(response).toHaveProperty("cpu");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health/metrics/system"),
        expect.any(Object),
      );
    });

    test("getApplicationMetrics retrieves application metrics", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ requests: 1000, errors: 5, response_time: 250 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.getApplicationMetrics();
      expect(response).toHaveProperty("requests");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health/metrics/application"),
        expect.any(Object),
      );
    });
  });

  describe("additional preferences endpoints", () => {
    test("updatePreferencesBulk updates multiple preferences", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({
            message: "Updated",
            updated: 3,
            created: 1,
            total: 4,
          }),
          text: async () => "",
        }),
      );

      const response = await apiClient.updatePreferencesBulk({
        theme: "dark",
        language: "en",
      });
      expect(response).toHaveProperty("updated");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences/bulk"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    test("resetAllPreferences resets all preferences", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          ok: true,
          json: async () => ({ message: "Reset", deleted: 5 }),
          text: async () => "",
        }),
      );

      const response = await apiClient.resetAllPreferences();
      expect(response).toHaveProperty("deleted");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/preferences"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });
});
