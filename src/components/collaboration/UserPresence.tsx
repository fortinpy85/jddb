/**
 * User Presence Component
 *
 * Displays active collaborators in a session with:
 * - User avatars and names
 * - Active/idle status indicators
 * - Cursor position indicators
 */

"use client";

import React from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Users, Circle } from "lucide-react";

export interface CollaboratorInfo {
  userId: number;
  username?: string;
  isActive?: boolean;
  cursorPosition?: number | null;
  color?: string;
}

interface UserPresenceProps {
  collaborators: CollaboratorInfo[];
  currentUserId?: number;
  maxDisplay?: number;
}

const AVATAR_COLORS = [
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-yellow-500",
  "bg-indigo-500",
  "bg-red-500",
  "bg-teal-500",
];

/**
 * Get initials from username
 */
function getInitials(username: string): string {
  const parts = username.split(" ");
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return username.slice(0, 2).toUpperCase();
}

/**
 * Get consistent color for user ID
 */
function getUserColor(userId: number): string {
  return AVATAR_COLORS[userId % AVATAR_COLORS.length];
}

export const UserPresence: React.FC<UserPresenceProps> = ({
  collaborators,
  currentUserId,
  maxDisplay = 5,
}) => {
  const displayedCollaborators = collaborators.slice(0, maxDisplay);
  const remainingCount = Math.max(0, collaborators.length - maxDisplay);

  if (collaborators.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center space-x-2">
      <Users className="w-4 h-4 text-gray-500" />

      <div className="flex -space-x-2">
        {displayedCollaborators.map((collaborator) => {
          const isCurrentUser = collaborator.userId === currentUserId;
          const color = collaborator.color || getUserColor(collaborator.userId);
          const username =
            collaborator.username || `User ${collaborator.userId}`;

          return (
            <div
              key={collaborator.userId}
              className="relative group"
              title={username}
            >
              <Avatar
                className={`w-8 h-8 border-2 border-white dark:border-gray-800 ${color} ${
                  isCurrentUser ? "ring-2 ring-blue-500" : ""
                }`}
              >
                <AvatarFallback className="text-white text-xs font-semibold">
                  {getInitials(username)}
                </AvatarFallback>
              </Avatar>

              {/* Active status indicator */}
              {collaborator.isActive && (
                <Circle className="absolute -bottom-0.5 -right-0.5 w-3 h-3 text-green-500 fill-current" />
              )}

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                  {username}
                  {isCurrentUser && " (You)"}
                </div>
              </div>
            </div>
          );
        })}

        {remainingCount > 0 && (
          <div
            className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 border-2 border-white dark:border-gray-800 flex items-center justify-center"
            title={`${remainingCount} more ${remainingCount === 1 ? "user" : "users"}`}
          >
            <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
              +{remainingCount}
            </span>
          </div>
        )}
      </div>

      <span className="text-sm text-gray-600 dark:text-gray-400">
        {collaborators.length}{" "}
        {collaborators.length === 1 ? "collaborator" : "collaborators"}
      </span>
    </div>
  );
};
