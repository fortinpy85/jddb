import { create } from "zustand";
import type { JobDescription, ProcessingStats, IngestionStats } from "./types";
import { apiClient } from "@/lib/api";
import type { JDDBApiClient } from "@/lib/api";
import { logger } from "@/utils/logger";

interface AppState {
  jobs: JobDescription[];
  selectedJob: JobDescription | null;
  mergedJob: JobDescription | null;
  stats: IngestionStats;
  loading: boolean;
  error: string | null;
  pagination: {
    skip: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
  filters: {
    classification?: string;
    language?: string;
    department?: string;
  };

  // Actions
  fetchJobs: (reset?: boolean) => Promise<void>;
  fetchStats: () => Promise<void>;
  selectJob: (job: JobDescription | null) => void;
  setMergedJob: (job: JobDescription | null) => void;
  setFilters: (filters: AppState["filters"]) => void;
  searchJobs: (query: string) => Promise<void>;
}

// Factory function to create store with injectable api client (for testing)
export const createStore = (api: JDDBApiClient = apiClient) =>
  create<AppState>((set, get) => ({
    jobs: [],
    selectedJob: null,
    mergedJob: null,
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

    fetchJobs: async (reset = false) => {
      logger.debug("fetchJobs started", { reset });
      set({ loading: true, error: null });
      try {
        const { filters, pagination } = get();
        const skip = reset ? 0 : pagination.skip;
        logger.debug("Calling api.listJobs", {
          skip,
          limit: pagination.limit,
          ...filters,
        });
        const response = await api.listJobs({
          skip,
          limit: pagination.limit,
          ...filters,
        });
        logger.debug("fetchJobs response received", {
          jobsCount: response.jobs.length,
          pagination: response.pagination,
        });

        set((state) => ({
          jobs: reset ? response.jobs : [...state.jobs, ...response.jobs],
          pagination: response.pagination,
          loading: false,
        }));
        logger.debug("fetchJobs state updated");
      } catch (error) {
        logger.error("fetchJobs error:", error);
        set({ error: (error as Error).message, loading: false });
      }
    },

    fetchStats: async () => {
      logger.debug("fetchStats started");
      try {
        logger.debug("Calling api.getProcessingStatus");
        const response = await api.getProcessingStatus();
        logger.debug("fetchStats response received", { stats: response });
        set({ stats: response });
        logger.debug("fetchStats state updated");
      } catch (error) {
        logger.error("fetchStats error:", error);
      }
    },

    selectJob: (job) => {
      set({ selectedJob: job });
    },

    setMergedJob: (job) => {
      set({ mergedJob: job });
    },

    setFilters: (filters) => {
      set({ filters });
    },

    searchJobs: async (query) => {
      if (!query.trim()) {
        get().fetchJobs(true);
        return;
      }
      set({ loading: true, error: null });
      try {
        const { filters, pagination } = get();
        const response = await api.searchJobs({
          query,
          ...filters,
          limit: pagination.limit,
        });
        const jobsFromSearch = response.results.map((result) => ({
          id: result.job_id,
          job_number: result.job_number,
          title: result.title,
          classification: result.classification,
          language: result.language,
          file_path: "",
          file_hash: "",
          relevance_score: result.relevance_score,
        })) as JobDescription[];
        set({
          jobs: jobsFromSearch,
          pagination: {
            ...pagination,
            total: response.total_results,
            has_more: false,
          },
          loading: false,
        });
      } catch (error) {
        set({ error: (error as Error).message, loading: false });
      }
    },
  }));

// Default store instance using real apiClient
export const useStore = createStore();
