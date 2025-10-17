/**
 * Collaborative Cursor Component
 *
 * Displays cursors of other collaborators in the editor with:
 * - User-specific colors
 * - Username labels
 * - Smooth position transitions
 */

"use client";

import React from "react";
import "./CollaborativeCursor.css";
import { logger } from "@/utils/logger";

export interface CursorPosition {
  userId: number;
  username?: string;
  position: number;
  color?: string;
}

interface CollaborativeCursorProps {
  cursors: CursorPosition[];
  editorRef: React.RefObject<HTMLTextAreaElement>;
}

const CURSOR_COLORS = [
  "#3B82F6", // blue
  "#10B981", // green
  "#8B5CF6", // purple
  "#EC4899", // pink
  "#F59E0B", // yellow
  "#6366F1", // indigo
  "#EF4444", // red
  "#14B8A6", // teal
];

/**
 * Get consistent color for user ID
 */
function getUserCursorColor(userId: number): string {
  return CURSOR_COLORS[userId % CURSOR_COLORS.length];
}

/**
 * Calculate pixel position from character position in textarea
 */
function getPixelPositionFromCharPosition(
  textarea: HTMLTextAreaElement,
  charPosition: number,
): { top: number; left: number } | null {
  try {
    const text = textarea.value;
    const beforeCursor = text.substring(0, charPosition);

    // Count lines before cursor
    const lines = beforeCursor.split("\n");
    const lineNumber = lines.length - 1;
    const columnNumber = lines[lines.length - 1].length;

    // Approximate calculation (this is simplified)
    const lineHeight = 24; // Should match textarea line-height
    const charWidth = 8; // Approximate character width

    const top = lineNumber * lineHeight + textarea.scrollTop;
    const left = columnNumber * charWidth;

    return { top, left };
  } catch (error) {
    logger.error("Error calculating cursor position:", error);
    return null;
  }
}

export const CollaborativeCursor: React.FC<CollaborativeCursorProps> = ({
  cursors,
  editorRef,
}) => {
  if (!editorRef.current) {
    return null;
  }

  return (
    <div className="absolute inset-0 pointer-events-none">
      {cursors.map((cursor) => {
        if (cursor.position === null || cursor.position === undefined) {
          return null;
        }

        const position = getPixelPositionFromCharPosition(
          editorRef.current!,
          cursor.position,
        );

        if (!position) {
          return null;
        }

        const color = cursor.color || getUserCursorColor(cursor.userId);
        const username = cursor.username || `User ${cursor.userId}`;

        return (
          <div
            key={cursor.userId}
            className="collaborative-cursor absolute transition-all duration-200"
            data-top={position.top}
            data-left={position.left}
          >
            <div
              className={`collaborative-cursor-line w-0.5 h-6 animate-pulse`}
              data-color={color}
            />

            {/* Username label */}
            <div
              className={`collaborative-cursor-label absolute top-0 left-1 text-xs px-2 py-0.5 rounded whitespace-nowrap font-medium text-white shadow-lg`}
              data-color={color}
            >
              {username}
            </div>
          </div>
        );
      })}
    </div>
  );
};
