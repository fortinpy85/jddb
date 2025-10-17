import { describe, it, expect, beforeEach } from "vitest";
import { createStore } from "./store";
import type { JobDescription, ProcessingStats } from "./types";

describe("useStore with dependency injection", () => {
  // Create mock API client
  const createMockApi = () => ({
    listJobs: async (params: any) => ({
      jobs: [
        {
          id: 1,
          job_number: "12345",
          title: "Test Job 1",
          classification: "EX-01",
          language: "en",
          created_at: "2024-01-01",
          processed_date: "2024-01-01",
          file_path: "/test/path/job1.txt",
          file_hash: "hash123",
        },
        {
          id: 2,
          job_number: "12346",
          title: "Test Job 2",
          classification: "EX-02",
          language: "fr",
          created_at: "2024-01-02",
          processed_date: "2024-01-02",
          file_path: "/test/path/job2.txt",
          file_hash: "hash456",
        },
      ],
      pagination: {
        skip: params.skip || 0,
        limit: params.limit || 20,
        total: 2,
        has_more: false,
      },
    }),
    getProcessingStatus: async () => ({
      total_jobs: 100,
      by_classification: {
        "EX-01": 50,
        "EX-02": 30,
        "EX-03": 20,
      },
      by_language: {
        en: 60,
        fr: 40,
      },
      processing_status: {
        pending: 5,
        processing: 10,
        completed: 80,
        failed: 3,
        needs_review: 2,
      },
      last_updated: "2024-01-01T00:00:00Z",
    }),
    searchJobs: async (query: any) => ({
      results: [
        {
          job_id: 1,
          job_number: "12345",
          title: "Search Result 1",
          classification: "EX-01",
          language: "en",
          relevance_score: 0.95,
        },
        {
          job_id: 2,
          job_number: "12346",
          title: "Search Result 2",
          classification: "EX-02",
          language: "fr",
          relevance_score: 0.85,
        },
      ],
      total_results: 2,
      page: 1,
      per_page: query.limit || 20,
      total_pages: 1,
    }),
  });

  describe("fetchJobs", () => {
    it("fetches jobs successfully and updates state", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { fetchJobs } = useTestStore.getState();
      await fetchJobs();

      const state = useTestStore.getState();
      expect(state.jobs).toHaveLength(2);
      expect(state.jobs[0].job_number).toBe("12345");
      expect(state.jobs[1].job_number).toBe("12346");
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });

    it("resets jobs when reset=true", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      // Set initial jobs
      useTestStore.setState({
        jobs: [
          {
            id: 99,
            job_number: "OLD",
            title: "Old Job",
            classification: "EX-01",
            language: "en",
            created_at: "2023-01-01",
            processed_date: "2023-01-01",
            file_path: "/test/path/old.txt",
            file_hash: "oldhash123",
          },
        ],
      });

      const { fetchJobs } = useTestStore.getState();
      await fetchJobs(true);

      const state = useTestStore.getState();
      expect(state.jobs).toHaveLength(2);
      expect(state.jobs[0].job_number).toBe("12345");
      expect(state.jobs.find((j) => j.job_number === "OLD")).toBeUndefined();
    });

    it("appends jobs when reset=false", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      // Set initial jobs
      const oldJob: JobDescription = {
        id: 99,
        job_number: "OLD",
        title: "Old Job",
        classification: "EX-01",
        language: "en",
        created_at: "2023-01-01",
        processed_date: "2023-01-01",
        file_path: "/test/path/old.txt",
        file_hash: "oldhash123",
      };
      useTestStore.setState({ jobs: [oldJob] });

      const { fetchJobs } = useTestStore.getState();
      await fetchJobs(false);

      const state = useTestStore.getState();
      expect(state.jobs).toHaveLength(3);
      expect(state.jobs[0].job_number).toBe("OLD");
      expect(state.jobs[1].job_number).toBe("12345");
      expect(state.jobs[2].job_number).toBe("12346");
    });

    it("handles errors correctly", async () => {
      const mockApi = {
        listJobs: async () => {
          throw new Error("Network error");
        },
      } as any;
      const useTestStore = createStore(mockApi);

      const { fetchJobs } = useTestStore.getState();
      await fetchJobs();

      const state = useTestStore.getState();
      expect(state.error).toBe("Network error");
      expect(state.loading).toBe(false);
    });

    it("applies filters when fetching", async () => {
      let capturedParams: any;
      const mockApi = {
        listJobs: async (params: any) => {
          capturedParams = params;
          return {
            jobs: [],
            pagination: { skip: 0, limit: 20, total: 0, has_more: false },
          };
        },
      } as any;
      const useTestStore = createStore(mockApi);

      useTestStore.setState({
        filters: {
          classification: "EX-01",
          language: "en",
        },
      });

      const { fetchJobs } = useTestStore.getState();
      await fetchJobs();

      expect(capturedParams.classification).toBe("EX-01");
      expect(capturedParams.language).toBe("en");
    });

    it("sets loading state during fetch", async () => {
      let resolvePromise: any;
      const slowApi = {
        listJobs: () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          }),
      } as any;
      const useTestStore = createStore(slowApi);

      const { fetchJobs } = useTestStore.getState();
      const fetchPromise = fetchJobs();

      // Check loading is true during fetch
      expect(useTestStore.getState().loading).toBe(true);

      // Resolve and check loading is false after
      resolvePromise({
        jobs: [],
        pagination: { skip: 0, limit: 20, total: 0, has_more: false },
      });
      await fetchPromise;

      expect(useTestStore.getState().loading).toBe(false);
    });
  });

  describe("fetchStats", () => {
    it("fetches stats successfully", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { fetchStats } = useTestStore.getState();
      await fetchStats();

      const state = useTestStore.getState();
      expect(state.stats.total_jobs).toBe(100);
      expect(state.stats.by_classification["EX-01"]).toBe(50);
      expect(state.stats.by_language.en).toBe(60);
      expect(state.stats.processing_status.completed).toBe(80);
    });

    it("handles errors silently", async () => {
      const mockApi = {
        getProcessingStatus: async () => {
          throw new Error("Stats error");
        },
      } as any;
      const useTestStore = createStore(mockApi);

      const { fetchStats } = useTestStore.getState();
      await fetchStats();

      // Should not set error state (errors handled silently in fetchStats)
      const state = useTestStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe("searchJobs", () => {
    it("searches jobs successfully", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { searchJobs } = useTestStore.getState();
      await searchJobs("test query");

      const state = useTestStore.getState();
      expect(state.jobs).toHaveLength(2);
      expect(state.jobs[0].title).toBe("Search Result 1");
      expect(state.jobs[0].relevance_score).toBe(0.95);
      expect(state.pagination.total).toBe(2);
      expect(state.loading).toBe(false);
    });

    it("calls fetchJobs when query is empty", async () => {
      let fetchJobsCalled = false;
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      // Override fetchJobs to track if it was called
      useTestStore.setState({
        fetchJobs: async (reset?: boolean) => {
          fetchJobsCalled = true;
          expect(reset).toBe(true);
        },
      });

      const { searchJobs } = useTestStore.getState();
      await searchJobs("");

      expect(fetchJobsCalled).toBe(true);
    });

    it("calls fetchJobs when query is whitespace", async () => {
      let fetchJobsCalled = false;
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      useTestStore.setState({
        fetchJobs: async (reset?: boolean) => {
          fetchJobsCalled = true;
          expect(reset).toBe(true);
        },
      });

      const { searchJobs } = useTestStore.getState();
      await searchJobs("   ");

      expect(fetchJobsCalled).toBe(true);
    });

    it("handles search errors", async () => {
      const mockApi = {
        searchJobs: async () => {
          throw new Error("Search error");
        },
      } as any;
      const useTestStore = createStore(mockApi);

      const { searchJobs } = useTestStore.getState();
      await searchJobs("test query");

      const state = useTestStore.getState();
      expect(state.error).toBe("Search error");
      expect(state.loading).toBe(false);
    });

    it("applies filters when searching", async () => {
      let capturedQuery: any;
      const mockApi = {
        searchJobs: async (query: any) => {
          capturedQuery = query;
          return {
            results: [],
            total_results: 0,
            page: 1,
            per_page: 20,
            total_pages: 0,
          };
        },
      } as any;
      const useTestStore = createStore(mockApi);

      useTestStore.setState({
        filters: {
          classification: "EX-01",
        },
        pagination: {
          skip: 0,
          limit: 50,
          total: 0,
          has_more: false,
        },
      });

      const { searchJobs } = useTestStore.getState();
      await searchJobs("test");

      expect(capturedQuery.query).toBe("test");
      expect(capturedQuery.classification).toBe("EX-01");
      expect(capturedQuery.limit).toBe(50);
    });

    it("maps search results to JobDescription format", async () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { searchJobs } = useTestStore.getState();
      await searchJobs("test");

      const state = useTestStore.getState();
      const job = state.jobs[0];

      // Check required JobDescription fields
      expect(job).toHaveProperty("id");
      expect(job).toHaveProperty("job_number");
      expect(job).toHaveProperty("title");
      expect(job).toHaveProperty("classification");
      expect(job).toHaveProperty("language");
      expect(job).toHaveProperty("file_path");
      expect(job).toHaveProperty("file_hash");
      expect(job).toHaveProperty("relevance_score");
    });
  });

  describe("selectJob", () => {
    it("selects a job", () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const job: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job.txt",
        file_hash: "jobhash123",
      };

      const { selectJob } = useTestStore.getState();
      selectJob(job);

      const state = useTestStore.getState();
      expect(state.selectedJob).toEqual(job);
    });

    it("deselects a job when passed null", () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const job: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job.txt",
        file_hash: "jobhash123",
      };

      const { selectJob } = useTestStore.getState();
      selectJob(job);
      selectJob(null);

      const state = useTestStore.getState();
      expect(state.selectedJob).toBeNull();
    });
  });

  describe("setFilters", () => {
    it("sets filters", () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { setFilters } = useTestStore.getState();
      setFilters({
        classification: "EX-01",
        language: "en",
        department: "IT",
      });

      const state = useTestStore.getState();
      expect(state.filters.classification).toBe("EX-01");
      expect(state.filters.language).toBe("en");
      expect(state.filters.department).toBe("IT");
    });

    it("overwrites previous filters", () => {
      const mockApi = createMockApi() as any;
      const useTestStore = createStore(mockApi);

      const { setFilters } = useTestStore.getState();
      setFilters({ classification: "EX-01" });
      setFilters({ language: "fr" });

      const state = useTestStore.getState();
      expect(state.filters.classification).toBeUndefined();
      expect(state.filters.language).toBe("fr");
    });
  });
});
