import { describe, it, expect, beforeEach } from "vitest";
import { useStore } from "./store";
import type { JobDescription } from "./types";

describe("useStore - simple state management tests", () => {
  beforeEach(() => {
    // Reset store state before each test
    useStore.setState({
      jobs: [],
      selectedJob: null,
      stats: {
        total_jobs: 0,
        by_classification: {},
        by_language: {},
        processing_status: {
          completed: 0,
          partial: 0,
          needs_embeddings: 0,
          needs_sections: 0,
          needs_metadata: 0,
        },
        embedding_stats: {
          total_chunks: 0,
          embedded_chunks: 0,
          embedding_completion_rate: 0,
          jobs_with_embeddings: 0,
        },
        content_quality: {
          jobs_with_sections: 0,
          jobs_with_metadata: 0,
          jobs_with_embeddings: 0,
          section_coverage_rate: 0,
          metadata_coverage_rate: 0,
          embedding_coverage_rate: 0,
        },
        section_distribution: {},
        recent_activity: {
          jobs_last_7_days: 0,
          daily_average: 0,
        },
        last_updated: null,
      },
      loading: false,
      error: null,
      pagination: {
        skip: 0,
        limit: 20,
        total: 0,
        has_more: false,
      },
      filters: {},
    });
  });

  describe("initial state", () => {
    it("has correct initial values", () => {
      const state = useStore.getState();
      expect(state.jobs).toEqual([]);
      expect(state.selectedJob).toBeNull();
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.pagination.skip).toBe(0);
      expect(state.pagination.limit).toBe(20);
      expect(state.filters).toEqual({});
    });

    it("has default stats structure", () => {
      const state = useStore.getState();
      expect(state.stats.total_jobs).toBe(0);
      expect(state.stats.by_classification).toEqual({});
      expect(state.stats.by_language).toEqual({});
      expect(state.stats.processing_status.completed).toBe(0);
      expect(state.stats.processing_status.partial).toBe(0);
      expect(state.stats.processing_status.needs_embeddings).toBe(0);
      expect(state.stats.processing_status.needs_sections).toBe(0);
      expect(state.stats.processing_status.needs_metadata).toBe(0);
    });
  });

  describe("selectJob action", () => {
    it("selects a job", () => {
      const job: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job.txt",
        file_hash: "abc123hash",
      };

      const { selectJob } = useStore.getState();
      selectJob(job);

      const state = useStore.getState();
      expect(state.selectedJob).toEqual(job);
      expect(state.selectedJob?.job_number).toBe("12345");
      expect(state.selectedJob?.title).toBe("Test Job");
    });

    it("deselects a job when passed null", () => {
      const job: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job.txt",
        file_hash: "abc123hash",
      };

      const { selectJob } = useStore.getState();
      selectJob(job);

      expect(useStore.getState().selectedJob).not.toBeNull();

      selectJob(null);

      const state = useStore.getState();
      expect(state.selectedJob).toBeNull();
    });

    it("can switch between different jobs", () => {
      const job1: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Job 1",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job1.txt",
        file_hash: "hash1",
      };

      const job2: JobDescription = {
        id: 2,
        job_number: "67890",
        title: "Job 2",
        classification: "EX-02",
        language: "fr",
        created_at: "2024-01-02",
        processed_date: "2024-01-02",
        file_path: "/test/path/job2.txt",
        file_hash: "hash2",
      };

      const { selectJob } = useStore.getState();

      selectJob(job1);
      expect(useStore.getState().selectedJob?.id).toBe(1);

      selectJob(job2);
      expect(useStore.getState().selectedJob?.id).toBe(2);
    });
  });

  describe("setFilters action", () => {
    it("sets filters correctly", () => {
      const { setFilters } = useStore.getState();

      setFilters({
        classification: "EX-01",
        language: "en",
        department: "IT",
      });

      const state = useStore.getState();
      expect(state.filters.classification).toBe("EX-01");
      expect(state.filters.language).toBe("en");
      expect(state.filters.department).toBe("IT");
    });

    it("overwrites previous filters", () => {
      const { setFilters } = useStore.getState();

      setFilters({ classification: "EX-01" });
      expect(useStore.getState().filters.classification).toBe("EX-01");

      setFilters({ language: "fr" });

      const state = useStore.getState();
      expect(state.filters.classification).toBeUndefined();
      expect(state.filters.language).toBe("fr");
    });

    it("can clear filters by setting empty object", () => {
      const { setFilters } = useStore.getState();

      setFilters({ classification: "EX-01", language: "en" });
      expect(Object.keys(useStore.getState().filters).length).toBeGreaterThan(
        0,
      );

      setFilters({});

      const state = useStore.getState();
      expect(state.filters).toEqual({});
    });

    it("can set individual filter properties", () => {
      const { setFilters } = useStore.getState();

      setFilters({ classification: "EX-01" });
      expect(useStore.getState().filters.classification).toBe("EX-01");

      setFilters({ classification: "EX-02" });
      expect(useStore.getState().filters.classification).toBe("EX-02");
    });
  });

  describe("state mutations", () => {
    it("allows direct state updates", () => {
      useStore.setState({ loading: true });
      expect(useStore.getState().loading).toBe(true);

      useStore.setState({ loading: false });
      expect(useStore.getState().loading).toBe(false);
    });

    it("allows updating jobs array directly", () => {
      const jobs: JobDescription[] = [
        {
          id: 1,
          job_number: "12345",
          title: "Job 1",
          classification: "EX-01",
          language: "en",
          created_at: "2024-01-01",
          processed_date: "2024-01-01",
          file_path: "/test/path/job1.txt",
          file_hash: "hash1",
        },
        {
          id: 2,
          job_number: "67890",
          title: "Job 2",
          classification: "EX-02",
          language: "fr",
          created_at: "2024-01-02",
          processed_date: "2024-01-02",
          file_path: "/test/path/job2.txt",
          file_hash: "hash2",
        },
      ];

      useStore.setState({ jobs });

      const state = useStore.getState();
      expect(state.jobs).toHaveLength(2);
      expect(state.jobs[0].job_number).toBe("12345");
      expect(state.jobs[1].job_number).toBe("67890");
    });

    it("allows updating pagination", () => {
      useStore.setState({
        pagination: {
          skip: 20,
          limit: 50,
          total: 100,
          has_more: true,
        },
      });

      const state = useStore.getState();
      expect(state.pagination.skip).toBe(20);
      expect(state.pagination.limit).toBe(50);
      expect(state.pagination.total).toBe(100);
      expect(state.pagination.has_more).toBe(true);
    });

    it("allows updating stats", () => {
      useStore.setState({
        stats: {
          total_jobs: 150,
          by_classification: {
            "EX-01": 50,
            "EX-02": 100,
          },
          by_language: {
            en: 100,
            fr: 50,
          },
          processing_status: {
            completed: 130,
            partial: 10,
            needs_embeddings: 5,
            needs_sections: 3,
            needs_metadata: 2,
          },
          embedding_stats: {
            total_chunks: 0,
            embedded_chunks: 0,
            embedding_completion_rate: 0,
            jobs_with_embeddings: 0,
          },
          content_quality: {
            jobs_with_sections: 0,
            jobs_with_metadata: 0,
            jobs_with_embeddings: 0,
            section_coverage_rate: 0,
            metadata_coverage_rate: 0,
            embedding_coverage_rate: 0,
          },
          section_distribution: {},
          recent_activity: {
            jobs_last_7_days: 0,
            daily_average: 0,
          },
          last_updated: "2024-01-01T00:00:00Z",
        },
      });

      const state = useStore.getState();
      expect(state.stats.total_jobs).toBe(150);
      expect(state.stats.by_classification["EX-01"]).toBe(50);
      expect(state.stats.by_language.en).toBe(100);
      expect(state.stats.processing_status.completed).toBe(130);
    });

    it("allows setting error messages", () => {
      useStore.setState({ error: "Test error message" });
      expect(useStore.getState().error).toBe("Test error message");

      useStore.setState({ error: null });
      expect(useStore.getState().error).toBeNull();
    });
  });

  describe("complex state scenarios", () => {
    it("handles loading state transitions", () => {
      useStore.setState({ loading: false, error: null });

      // Start loading
      useStore.setState({ loading: true, error: null });
      expect(useStore.getState().loading).toBe(true);
      expect(useStore.getState().error).toBeNull();

      // Complete with success
      useStore.setState({ loading: false });
      expect(useStore.getState().loading).toBe(false);

      // Start loading again
      useStore.setState({ loading: true, error: null });

      // Complete with error
      useStore.setState({ loading: false, error: "Failed to load" });
      expect(useStore.getState().loading).toBe(false);
      expect(useStore.getState().error).toBe("Failed to load");
    });

    it("maintains independent state properties", () => {
      const job: JobDescription = {
        id: 1,
        job_number: "12345",
        title: "Test Job",
        classification: "EX-01",
        language: "en",
        created_at: "2024-01-01",
        processed_date: "2024-01-01",
        file_path: "/test/path/job.txt",
        file_hash: "abc123hash",
      };

      useStore.setState({
        selectedJob: job,
        loading: true,
        filters: { classification: "EX-01" },
      });

      const state = useStore.getState();
      expect(state.selectedJob).toEqual(job);
      expect(state.loading).toBe(true);
      expect(state.filters.classification).toBe("EX-01");

      // Update one property
      useStore.setState({ loading: false });

      // Others remain unchanged
      const newState = useStore.getState();
      expect(newState.selectedJob).toEqual(job);
      expect(newState.loading).toBe(false);
      expect(newState.filters.classification).toBe("EX-01");
    });
  });
});
