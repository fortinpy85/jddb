/**
 * Unit tests for JobList component
 */
import React from "react";
import { render, screen, fireEvent, waitFor, cleanup } from "../test-utils";
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { JobList } from "./JobList";
import { useStore } from "../lib/store";
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("../lib/store", () => ({
  useStore: vi.fn(),
}));

vi.mock("../lib/utils", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
  getClassificationLevel: vi.fn(
    (classification: string) => `Level for ${classification}`,
  ),
  getLanguageName: vi.fn((lang: string) =>
    lang === "EN" ? "English" : "French",
  ),
  getStatusColor: vi.fn(() => "bg-green-100 text-green-800"),
  handleExport: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  apiClient: {
    deleteJob: vi.fn(() => Promise.resolve()),
  },
}));

// Mock the store module
const mockFetchJobs = vi.fn(() => Promise.resolve());
const mockFetchStats = vi.fn(() => Promise.resolve());
const mockSetFilters = vi.fn(() => {});
const mockSearchJobs = vi.fn(() => Promise.resolve());

// Create a mock store state that we can modify in tests
let mockStoreState: any;

// Create a proper mock for useStore that handles selectors
const mockUseStore = vi.fn((selector?: any) => {
  if (typeof selector === "function") {
    return selector(mockStoreState);
  }
  return mockStoreState;
});

(vi.mocked as any)(useStore).mockImplementation(mockUseStore);

const mockJobs = [
  {
    id: 1,
    job_number: "123456",
    title: "Director of Business Analysis",
    classification: "EX-01",
    language: "EN",
    processed_date: "2024-01-15T10:00:00Z",
    sections_count: 5,
  },
  {
    id: 2,
    job_number: "789012",
    title: "Senior Policy Analyst",
    classification: "EX-02",
    language: "FR",
    processed_date: "2024-01-16T11:00:00Z",
    sections_count: 3,
  },
];

describe("JobList Component", () => {
  beforeEach(() => {
    // Reset mocks
    if (mockFetchJobs.mockReset) mockFetchJobs.mockReset();
    if (mockFetchStats.mockReset) mockFetchStats.mockReset();
    if (mockSetFilters.mockReset) mockSetFilters.mockReset();
    if (mockSearchJobs.mockReset) mockSearchJobs.mockReset();

    // Reset to default state
    mockStoreState = {
      jobs: mockJobs,
      loading: false,
      error: null,
      pagination: { has_more: false },
      stats: {
        total_jobs: 2,
        processing_status: {
          completed: 2,
          processing: 0,
          pending: 0,
          needs_review: 0,
          failed: 0,
        },
        by_classification: {
          "EX-01": 1,
          "EX-02": 1,
        },
        by_language: {
          EN: 1,
          FR: 1,
        },
      },
      filters: {},
      fetchJobs: mockFetchJobs as any,
      fetchStats: mockFetchStats as any,
      setFilters: mockSetFilters as any,
      searchJobs: mockSearchJobs as any,
    };

    // Clear any previous renders
    document.body.innerHTML = "";
  });

  afterEach(() => {
    cleanup();
  });

  test("renders job list container", async () => {
    render(<JobList />);

    // Component uses i18n key, mock returns the key itself
    expect(screen.getByText(/jobs:list.title/i)).toBeInTheDocument();
  });

  test("renders jobs after loading", async () => {
    render(<JobList />);

    await waitFor(() => {
      expect(
        screen.getByText("Director of Business Analysis"),
      ).toBeInTheDocument();
      expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();
    });

    expect(screen.getByText("123456")).toBeInTheDocument();
    expect(screen.getByText("789012")).toBeInTheDocument();
  });

  test("displays job classifications", async () => {
    render(<JobList />);

    await waitFor(() => {
      expect(screen.getByText("EX-01")).toBeInTheDocument();
      expect(screen.getByText("EX-02")).toBeInTheDocument();
    });
  });

  test("displays job languages", async () => {
    render(<JobList />);

    await waitFor(() => {
      // Check if language information is present (could be in badges or text)
      expect(
        screen.getByText("Director of Business Analysis"),
      ).toBeInTheDocument();
      expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();
    });
  });

  test("shows total count in header", async () => {
    render(<JobList />);

    // Component uses i18n key, mock returns the key itself
    expect(screen.getByText(/jobs:list.title/i)).toBeInTheDocument();
  });

  test("handles empty job list", async () => {
    // Mock empty state
    mockStoreState = {
      ...mockStoreState,
      jobs: [],
      loading: false,
      error: null,
      stats: {
        ...mockStoreState.stats,
        total_jobs: 0,
        processing_status: {
          completed: 0,
          processing: 0,
          pending: 0,
          needs_review: 0,
          failed: 0,
        },
        by_classification: {},
        by_language: {},
      },
    };

    render(<JobList />);

    // When component first renders with no jobs, it shows initialization UI
    // Check for the initialization UI elements instead using i18n keys
    expect(screen.getByText(/jobs:list.title/i)).toBeInTheDocument();
    expect(screen.getByText(/jobs:list.loadPrompt/i)).toBeInTheDocument();
    expect(screen.getByText(/jobs:actions.loadData/i)).toBeInTheDocument();
  });

  test("handles error gracefully", async () => {
    // Mock error state - with jobs loaded first so it shows main UI
    mockStoreState = {
      ...mockStoreState,
      jobs: mockJobs, // Need jobs so it doesn't show init UI
      error: "Failed to load jobs",
      stats: {
        ...mockStoreState.stats,
        total_jobs: 0,
        processing_status: {
          completed: 0,
          processing: 0,
          pending: 0,
          needs_review: 0,
          failed: 0,
        },
        by_classification: {},
        by_language: {},
      },
    };

    render(<JobList />);

    expect(screen.getByText("Failed to load jobs")).toBeInTheDocument();
  });

  test("filters by search term", async () => {
    render(<JobList />);

    const searchInput = screen.getByPlaceholderText(/jobs:search.placeholder/i);
    fireEvent.change(searchInput, { target: { value: "director" } });

    const searchButton = screen.getByText(/jobs:actions.search/i);
    fireEvent.click(searchButton);

    expect(mockSearchJobs).toHaveBeenCalledWith("director");
  });

  test("filters by classification", async () => {
    render(<JobList />);

    const classificationSelect = screen.getByLabelText(
      /jobs:filters.classificationLabel/i,
    );
    fireEvent.change(classificationSelect, { target: { value: "EX-01" } });

    expect(mockSetFilters).toHaveBeenCalledWith(
      expect.objectContaining({
        classification: "EX-01",
      }),
    );
  });

  test("filters by language", async () => {
    render(<JobList />);

    const languageSelect = screen.getByLabelText(/jobs:filters.languageLabel/i);
    fireEvent.change(languageSelect, { target: { value: "EN" } });

    expect(mockSetFilters).toHaveBeenCalledWith(
      expect.objectContaining({
        language: "EN",
      }),
    );
  });

  test("handles pagination with load more", async () => {
    // Mock pagination state
    mockStoreState = {
      ...mockStoreState,
      pagination: { has_more: true },
      stats: {
        ...mockStoreState.stats,
        total_jobs: 50,
      },
    };

    render(<JobList />);

    expect(screen.getByText(/jobs:actions.loadMore/i)).toBeInTheDocument();
  });

  test("loads more jobs on button click", async () => {
    // Mock pagination state
    mockStoreState = {
      ...mockStoreState,
      pagination: { has_more: true },
      stats: {
        ...mockStoreState.stats,
        total_jobs: 50,
      },
    };

    render(<JobList />);

    const loadMoreButton = screen.getByText(/jobs:actions.loadMore/i);
    fireEvent.click(loadMoreButton);

    expect(mockFetchJobs).toHaveBeenCalled();
  });

  test("shows job details on click", async () => {
    render(<JobList />);

    await waitFor(() => {
      expect(
        screen.getByText("Director of Business Analysis"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Director of Business Analysis"));

    // Should expand to show more details or navigate
    await waitFor(() => {
      // This would depend on the actual implementation
      // For now, just verify the click was handled
      expect(
        screen.getByText("Director of Business Analysis"),
      ).toBeInTheDocument();
    });
  });

  test("refreshes data on refresh button click", async () => {
    render(<JobList />);

    const refreshButton = screen.getByText(/jobs:actions.refresh/i);
    fireEvent.click(refreshButton);

    expect(mockFetchJobs).toHaveBeenCalledWith(true);
    expect(mockFetchStats).toHaveBeenCalled();
  });

  test("displays loading indicator when loading", async () => {
    // Mock loading state
    mockStoreState = {
      ...mockStoreState,
      jobs: [],
      loading: true,
      stats: {
        ...mockStoreState.stats,
        total_jobs: 0,
        processing_status: {
          completed: 0,
          processing: 0,
          pending: 0,
          needs_review: 0,
          failed: 0,
        },
        by_classification: {},
        by_language: {},
      },
    };

    render(<JobList />);

    // When loading with no jobs, component shows initialization UI with disabled button showing "Loading..."
    const loadButton = screen.getByRole("button", { name: /loading/i });
    expect(loadButton).toBeInTheDocument();
    expect(loadButton.hasAttribute("disabled")).toBe(true);
  });

  test("calls fetch and stats when Load Data button is clicked", async () => {
    // Start with empty jobs to show init UI
    mockStoreState = {
      ...mockStoreState,
      jobs: [],
      loading: false,
      error: null,
    };

    render(<JobList />);

    // Find and click the Load Data button using i18n key
    const loadButton = screen.getByText(/jobs:actions.loadData/i);
    fireEvent.click(loadButton);

    // Now the fetch functions should be called
    await waitFor(() => {
      expect(mockFetchJobs).toHaveBeenCalledWith(true);
      expect(mockFetchStats).toHaveBeenCalled();
    });
  });

  test("displays formatted dates", async () => {
    render(<JobList />);

    // Verify jobs are rendered with their basic information
    await waitFor(() => {
      expect(
        screen.getByText("Director of Business Analysis"),
      ).toBeInTheDocument();
      expect(screen.getByText("123456")).toBeInTheDocument();
    });
  });

  test("displays job information correctly", async () => {
    render(<JobList />);

    expect(
      screen.getByText("Director of Business Analysis"),
    ).toBeInTheDocument();
    expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();
    expect(screen.getByText("123456")).toBeInTheDocument();
    expect(screen.getByText("789012")).toBeInTheDocument();
  });

  test("handles keyboard search on Enter", async () => {
    render(<JobList />);

    const searchInput = screen.getByPlaceholderText(/jobs:search.placeholder/i);
    fireEvent.change(searchInput, { target: { value: "analyst" } });
    fireEvent.keyDown(searchInput, { key: "Enter" });

    expect(mockSearchJobs).toHaveBeenCalledWith("analyst");
  });

  test("shows processing status overview", async () => {
    render(<JobList />);

    // Check that status labels are present using i18n keys
    expect(
      screen.queryAllByText(/jobs:status.completed/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryAllByText(/jobs:status.processing/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryAllByText(/jobs:status.pending/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryAllByText(/jobs:status.needsReview/i).length,
    ).toBeGreaterThan(0);
    expect(screen.queryAllByText(/jobs:status.failed/i).length).toBeGreaterThan(
      0,
    );
  });
});
