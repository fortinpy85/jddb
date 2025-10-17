import { describe, it, expect } from "vitest";
import {
  cn,
  formatFileSize,
  getClassificationLevel,
  getLanguageName,
  getStatusColor,
} from "./utils";

describe("cn", () => {
  it("merges class names correctly", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    // eslint-disable-next-line no-constant-binary-expression
    expect(cn("foo", false && "bar", "baz")).toBe("foo baz");
  });

  it("merges tailwind classes correctly", () => {
    expect(cn("px-2 py-1", "px-4")).toBe("py-1 px-4");
  });

  it("handles arrays and objects", () => {
    expect(cn(["foo", "bar"], { baz: true, qux: false })).toBe("foo bar baz");
  });
});

describe("formatFileSize", () => {
  it("formats bytes correctly", () => {
    expect(formatFileSize(0)).toBe("0 B");
    expect(formatFileSize(100)).toBe("100 B");
    expect(formatFileSize(999)).toBe("999 B");
  });

  it("formats kilobytes correctly", () => {
    expect(formatFileSize(1024)).toBe("1 KB");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(2048)).toBe("2 KB");
  });

  it("formats megabytes correctly", () => {
    expect(formatFileSize(1048576)).toBe("1 MB");
    expect(formatFileSize(1572864)).toBe("1.5 MB");
    expect(formatFileSize(5242880)).toBe("5 MB");
  });

  it("formats gigabytes correctly", () => {
    expect(formatFileSize(1073741824)).toBe("1 GB");
    expect(formatFileSize(2147483648)).toBe("2 GB");
  });
});

describe("getClassificationLevel", () => {
  it("returns correct level for EX-01", () => {
    expect(getClassificationLevel("EX-01")).toBe("Director");
  });

  it("returns correct level for EX-02", () => {
    expect(getClassificationLevel("EX-02")).toBe("Executive Director");
  });

  it("returns correct level for EX-03", () => {
    expect(getClassificationLevel("EX-03")).toBe("Director General");
  });

  it("returns correct level for EX-04", () => {
    expect(getClassificationLevel("EX-04")).toBe("Assistant Deputy Minister");
  });

  it("returns correct level for EX-05", () => {
    expect(getClassificationLevel("EX-05")).toBe("Senior ADM/Deputy Minister");
  });

  it("returns original classification for unknown codes", () => {
    expect(getClassificationLevel("AS-01")).toBe("AS-01");
    expect(getClassificationLevel("PM-03")).toBe("PM-03");
    expect(getClassificationLevel("UNKNOWN")).toBe("UNKNOWN");
  });
});

describe("getLanguageName", () => {
  it("returns English for en code", () => {
    expect(getLanguageName("en")).toBe("English");
  });

  it("returns French for fr code", () => {
    expect(getLanguageName("fr")).toBe("French");
  });

  it("returns original code for unknown languages", () => {
    expect(getLanguageName("de")).toBe("de");
    expect(getLanguageName("es")).toBe("es");
    expect(getLanguageName("unknown")).toBe("unknown");
  });
});

describe("getStatusColor", () => {
  it("returns yellow classes for pending status", () => {
    expect(getStatusColor("pending")).toBe("bg-yellow-100 text-yellow-800");
  });

  it("returns blue classes for processing status", () => {
    expect(getStatusColor("processing")).toBe("bg-blue-100 text-blue-800");
  });

  it("returns green classes for completed status", () => {
    expect(getStatusColor("completed")).toBe("bg-green-100 text-green-800");
  });

  it("returns red classes for failed status", () => {
    expect(getStatusColor("failed")).toBe("bg-red-100 text-red-800");
  });

  it("returns orange classes for needs_review status", () => {
    expect(getStatusColor("needs_review")).toBe(
      "bg-orange-100 text-orange-800",
    );
  });

  it("returns gray classes for unknown status", () => {
    expect(getStatusColor("unknown")).toBe("bg-gray-100 text-gray-800");
    expect(getStatusColor("custom")).toBe("bg-gray-100 text-gray-800");
  });
});

// Note: handleExport tests are skipped because they require complex mocking
// of apiClient and DOM methods that are difficult to reliably test in isolation.
// This function is tested through E2E tests instead.
