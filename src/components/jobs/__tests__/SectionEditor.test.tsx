/**
 * Unit tests for SectionEditor component
 * Tests section editing UI, behavior, and API integration
 */

import { describe, test, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SectionEditor } from "../SectionEditor";

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, any>) => {
      const translations: Record<string, string> = {
        "jobs:actions.edit": "Edit",
        "jobs:actions.editSectionAria": `Edit ${params?.section || "section"}`,
        "common:actions.save": "Save",
        "common:actions.saving": "Saving...",
        "common:actions.cancel": "Cancel",
        "jobs:placeholders.sectionContent": "Enter section content",
        "jobs:messages.noContent": "No content available",
      };
      return translations[key] || key;
    },
  }),
}));

describe("SectionEditor", () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnEditToggle = vi.fn();

  const defaultProps = {
    sectionId: 1,
    sectionType: "GENERAL_ACCOUNTABILITY",
    initialContent: "Test accountability content",
    onSave: mockOnSave,
  };

  beforeEach(() => {
    mockOnSave.mockClear();
    mockOnCancel.mockClear();
    mockOnEditToggle.mockClear();
  });

  describe("Rendering", () => {
    test("renders in view mode by default", () => {
      render(<SectionEditor {...defaultProps} />);

      expect(screen.getByText("General Accountability")).toBeInTheDocument();
      expect(
        screen.getByText("Test accountability content"),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    });

    test("renders section title with proper formatting", () => {
      render(
        <SectionEditor
          {...defaultProps}
          sectionType="SPECIFIC_ACCOUNTABILITIES"
        />,
      );

      expect(screen.getByText("Specific Accountabilities")).toBeInTheDocument();
    });

    test("displays 'No content available' when content is empty", () => {
      render(<SectionEditor {...defaultProps} initialContent="" />);

      expect(screen.getByText("No content available")).toBeInTheDocument();
    });

    test("applies custom className", () => {
      const { container } = render(
        <SectionEditor {...defaultProps} className="custom-class" />,
      );

      expect(container.querySelector(".custom-class")).toBeInTheDocument();
    });
  });

  describe("Edit Mode Toggle", () => {
    test("enters edit mode when Edit button is clicked", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      expect(screen.getByRole("textbox")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });

    test("displays ring highlight when in edit mode", async () => {
      const { container } = render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const card = container.querySelector(".ring-2");
      expect(card).toBeInTheDocument();
    });

    test("auto-focuses textarea when entering edit mode", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      expect(textarea).toHaveFocus();
    });

    test("positions cursor at end of content", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
      expect(textarea.selectionStart).toBe(defaultProps.initialContent.length);
      expect(textarea.selectionEnd).toBe(defaultProps.initialContent.length);
    });

    test("calls onEditToggle when provided", async () => {
      render(
        <SectionEditor {...defaultProps} onEditToggle={mockOnEditToggle} />,
      );

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      expect(mockOnEditToggle).toHaveBeenCalledWith(true);
    });
  });

  describe("Content Editing", () => {
    test("updates content when typing in textarea", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "New content");

      expect(textarea).toHaveValue("New content");
    });

    test("preserves content changes when not saved", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "Modified content");

      expect(textarea).toHaveValue("Modified content");
    });

    test("allows multiline content editing", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "Line 1{Enter}Line 2{Enter}Line 3");

      expect(textarea.value).toContain("\n");
    });
  });

  describe("Save Functionality", () => {
    test("enables Save button when content is changed", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toBeEnabled();
    });

    test("disables Save button when content is unchanged", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toBeDisabled();
    });

    test("calls onSave with correct parameters", async () => {
      mockOnSave.mockResolvedValue(undefined);
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "Updated content");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(1, "Updated content");
    });

    test("displays saving indicator during save", async () => {
      let resolveSave: () => void;
      const savePromise = new Promise<void>((resolve) => {
        resolveSave = resolve;
      });
      mockOnSave.mockReturnValue(savePromise);

      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      expect(screen.getByText("Saving...")).toBeInTheDocument();
      expect(saveButton).toBeDisabled();

      resolveSave!();
      await waitFor(() => {
        expect(screen.queryByText("Saving...")).not.toBeInTheDocument();
      });
    });

    test("exits edit mode after successful save", async () => {
      mockOnSave.mockResolvedValue(undefined);
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      });
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    });

    test("calls onEditToggle(false) after successful save", async () => {
      mockOnSave.mockResolvedValue(undefined);

      // Component uses internal state when onEditToggle is provided but isEditing is not
      render(
        <SectionEditor {...defaultProps} onEditToggle={mockOnEditToggle} />,
      );

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      // Component uses internal state, so edit mode activates immediately
      await waitFor(() => {
        expect(screen.queryByRole("textbox")).toBeInTheDocument();
      });

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      });

      // Check that onEditToggle was called twice: once with true, once with false
      expect(mockOnEditToggle).toHaveBeenCalledTimes(2);
      expect(mockOnEditToggle).toHaveBeenNthCalledWith(1, true);
      expect(mockOnEditToggle).toHaveBeenNthCalledWith(2, false);
    });

    test("handles save errors gracefully", async () => {
      const consoleError = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});
      mockOnSave.mockRejectedValue(new Error("Save failed"));

      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          "Failed to save section:",
          expect.any(Error),
        );
      });

      // Should remain in edit mode on error
      expect(screen.getByRole("textbox")).toBeInTheDocument();

      consoleError.mockRestore();
    });
  });

  describe("Cancel Functionality", () => {
    test("reverts content to original when Cancel is clicked", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "Modified content");

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      await waitFor(
        () => {
          expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
          expect(
            screen.getByRole("button", { name: /edit/i }),
          ).toBeInTheDocument();
        },
        { timeout: 3000 },
      );

      // Re-enter edit mode to verify content was reverted
      await userEvent.click(screen.getByRole("button", { name: /edit/i }));

      await waitFor(
        () => {
          const newTextarea = screen.getByRole("textbox");
          expect(newTextarea).toHaveValue(defaultProps.initialContent);
        },
        { timeout: 3000 },
      );
    });

    test("exits edit mode when Cancel is clicked", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      await waitFor(
        () => {
          expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
          expect(
            screen.getByRole("button", { name: /edit/i }),
          ).toBeInTheDocument();
        },
        { timeout: 3000 },
      );
    });

    test("calls onCancel callback when provided", async () => {
      render(<SectionEditor {...defaultProps} onCancel={mockOnCancel} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    test("calls onEditToggle(false) when Cancel is clicked", async () => {
      // Component uses internal state when onEditToggle is provided but isEditing is not
      render(
        <SectionEditor {...defaultProps} onEditToggle={mockOnEditToggle} />,
      );

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      // Component uses internal state, so edit mode activates immediately
      await waitFor(() => {
        expect(screen.queryByRole("textbox")).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      });

      // Check that onEditToggle was called twice: once with true, once with false
      expect(mockOnEditToggle).toHaveBeenCalledTimes(2);
      expect(mockOnEditToggle).toHaveBeenNthCalledWith(1, true);
      expect(mockOnEditToggle).toHaveBeenNthCalledWith(2, false);
    });
  });

  describe("External Edit State Control", () => {
    test("respects external isEditing prop", () => {
      render(<SectionEditor {...defaultProps} isEditing={true} />);

      expect(screen.getByRole("textbox")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
    });

    test("syncs with external isEditing changes", async () => {
      const { rerender } = render(
        <SectionEditor {...defaultProps} isEditing={false} />,
      );

      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

      rerender(<SectionEditor {...defaultProps} isEditing={true} />);

      expect(screen.getByRole("textbox")).toBeInTheDocument();
    });

    test("doesn't sync internal content when not editing", async () => {
      const { rerender } = render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      // Change content
      const textarea = screen.getByRole("textbox");
      await userEvent.clear(textarea);
      await userEvent.type(textarea, "Modified");

      // Update prop while still editing
      rerender(
        <SectionEditor {...defaultProps} initialContent="Updated original" />,
      );

      // Content should NOT change while editing
      expect(textarea).toHaveValue("Modified");
    });

    test("syncs content when exiting edit mode", async () => {
      const { rerender } = render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await userEvent.click(cancelButton);

      // Now update content while not editing
      rerender(
        <SectionEditor {...defaultProps} initialContent="Updated content" />,
      );

      expect(screen.getByText("Updated content")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("Edit button has proper aria-label", () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      expect(editButton).toHaveAttribute(
        "aria-label",
        "Edit General Accountability",
      );
    });

    test("Save button has proper aria-label", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toHaveAttribute("aria-label", "Save");
    });

    test("Cancel button has proper aria-label", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      expect(cancelButton).toHaveAttribute("aria-label", "Cancel");
    });

    test("textarea has placeholder text", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      expect(textarea).toHaveAttribute("placeholder", "Enter section content");
    });

    test("buttons are disabled appropriately during save", async () => {
      let resolveSave: () => void;
      const savePromise = new Promise<void>((resolve) => {
        resolveSave = resolve;
      });
      mockOnSave.mockReturnValue(savePromise);

      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      await userEvent.type(textarea, " modified");

      const saveButton = screen.getByRole("button", { name: /save/i });
      const cancelButton = screen.getByRole("button", { name: /cancel/i });

      await userEvent.click(saveButton);

      expect(saveButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();

      resolveSave!();
      await waitFor(() => {
        expect(screen.queryByText("Saving...")).not.toBeInTheDocument();
      });
    });
  });

  describe("Edge Cases", () => {
    test("handles empty initial content", () => {
      render(<SectionEditor {...defaultProps} initialContent="" />);

      expect(screen.getByText("No content available")).toBeInTheDocument();
    });

    test("handles very long content", async () => {
      const longContent = "A".repeat(10000);
      render(<SectionEditor {...defaultProps} initialContent={longContent} />);

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      expect(textarea).toHaveValue(longContent);
    });

    test("handles special characters in content", async () => {
      const specialContent = `Special chars: <>&"'\n\t${String.fromCharCode(0)}`;
      render(
        <SectionEditor {...defaultProps} initialContent={specialContent} />,
      );

      const editButton = screen.getByRole("button", { name: /edit/i });
      await userEvent.click(editButton);

      const textarea = screen.getByRole("textbox");
      expect(textarea).toHaveValue(specialContent);
    });

    test("handles rapid edit/cancel cycles", async () => {
      render(<SectionEditor {...defaultProps} />);

      const editButton = screen.getByRole("button", { name: /edit/i });

      // Toggle edit mode with proper state settling
      for (let i = 0; i < 5; i++) {
        await userEvent.click(editButton);

        // Wait for edit mode to be active
        await waitFor(() => {
          expect(screen.queryByRole("textbox")).toBeInTheDocument();
        });

        const cancelButton = screen.getByRole("button", { name: /cancel/i });
        await userEvent.click(cancelButton);

        // Wait for edit mode to exit before next cycle
        await waitFor(() => {
          expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
        });
      }

      // Should be in view mode
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    });
  });
});
