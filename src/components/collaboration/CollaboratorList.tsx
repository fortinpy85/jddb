/**
 * Collaborator List Component
 *
 * Displays active collaborators in a compact, real-time updated list with:
 * - User avatars with online status
 * - Role indicators
 * - Activity status (typing, idle, active)
 * - Cursor position indicators
 */

"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";
import { Crown, Edit3, Eye, Wifi, Circle } from "lucide-react";
import type { UserRole } from "./SessionManager";

export interface CollaboratorInfo {
  userId: number;
  username: string;
  role: UserRole;
  isOnline: boolean;
  isTyping?: boolean;
  lastActivity?: string;
  cursorPosition?: number;
  color?: string;
}

interface CollaboratorListProps {
  collaborators: CollaboratorInfo[];
  currentUserId?: number;
  maxVisible?: number;
  showRoles?: boolean;
  showActivity?: boolean;
  onCollaboratorClick?: (userId: number) => void;
  className?: string;
}

const AVATAR_COLORS = [
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-orange-500",
  "bg-indigo-500",
  "bg-teal-500",
  "bg-red-500",
];

export const CollaboratorList: React.FC<CollaboratorListProps> = ({
  collaborators,
  currentUserId,
  maxVisible = 5,
  showRoles = true,
  showActivity = true,
  onCollaboratorClick,
  className = "",
}) => {
  const visibleCollaborators = collaborators.slice(0, maxVisible);
  const hiddenCount = Math.max(0, collaborators.length - maxVisible);

  const getAvatarColor = (userId: number, customColor?: string) => {
    if (customColor) return customColor;
    return AVATAR_COLORS[userId % AVATAR_COLORS.length];
  };

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case "owner":
        return <Crown className="w-2 h-2" />;
      case "editor":
        return <Edit3 className="w-2 h-2" />;
      case "viewer":
        return <Eye className="w-2 h-2" />;
    }
  };

  const getActivityStatus = (collaborator: CollaboratorInfo) => {
    if (!collaborator.isOnline) return "Offline";
    if (collaborator.isTyping) return "Typing...";

    if (collaborator.lastActivity) {
      const lastActive = new Date(collaborator.lastActivity);
      const now = new Date();
      const diffMs = now.getTime() - lastActive.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return "Active now";
      if (diffMins < 5) return `Active ${diffMins}m ago`;
      return "Idle";
    }

    return "Active";
  };

  const getActivityColor = (collaborator: CollaboratorInfo) => {
    if (!collaborator.isOnline) return "bg-gray-400";
    if (collaborator.isTyping) return "bg-blue-500 animate-pulse";

    const status = getActivityStatus(collaborator);
    if (status === "Active now" || status === "Active") return "bg-green-500";
    if (status.includes("Active")) return "bg-yellow-500";
    return "bg-gray-400";
  };

  return (
    <div className={`flex items-center ${className}`}>
        <div className="flex items-center -space-x-2">
          {visibleCollaborators.map((collaborator) => {
            const isCurrentUser = collaborator.userId === currentUserId;
            const activityStatus = getActivityStatus(collaborator);

            return (
              <Tooltip
                key={collaborator.userId}
                content={
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">
                        {collaborator.username}
                        {isCurrentUser && " (You)"}
                      </p>
                      {showRoles && (
                        <Badge variant="outline" className="text-xs">
                          {getRoleIcon(collaborator.role)}
                          <span className="ml-1">{collaborator.role}</span>
                        </Badge>
                      )}
                    </div>

                    {showActivity && (
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Circle
                          className={`w-2 h-2 ${getActivityColor(collaborator).replace("animate-pulse", "")}`}
                          fill="currentColor"
                        />
                        {activityStatus}
                      </div>
                    )}

                    {collaborator.cursorPosition !== undefined && (
                      <p className="text-xs text-gray-500">
                        Cursor at position {collaborator.cursorPosition}
                      </p>
                    )}
                  </div>
                }
                side="bottom"
                className="max-w-xs"
              >
                <button
                  onClick={() => onCollaboratorClick?.(collaborator.userId)}
                  className={`relative inline-flex items-center justify-center w-8 h-8 rounded-full border-2 border-white transition-transform hover:scale-110 hover:z-10 ${getAvatarColor(
                    collaborator.userId,
                    collaborator.color,
                  )} ${isCurrentUser ? "ring-2 ring-blue-400 ring-offset-2" : ""}`}
                >
                  <span className="text-xs font-medium text-white">
                    {collaborator.username.slice(0, 2).toUpperCase()}
                  </span>

                  {/* Online/Activity Status Indicator */}
                  <span
                    className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${getActivityColor(
                      collaborator,
                    )}`}
                  />

                  {/* Typing Indicator */}
                  {collaborator.isTyping && (
                    <span className="absolute -top-1 -right-1 flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                    </span>
                  )}
                </button>
              </Tooltip>
            );
          })}

          {/* Hidden Count Badge */}
          {hiddenCount > 0 && (
            <Tooltip
              content={
                <p className="text-xs">
                  {hiddenCount} more{" "}
                  {hiddenCount === 1 ? "collaborator" : "collaborators"}
                </p>
              }
              side="bottom"
            >
              <div className="relative inline-flex items-center justify-center w-8 h-8 rounded-full border-2 border-white bg-gray-200 text-gray-600">
                <span className="text-xs font-medium">+{hiddenCount}</span>
              </div>
            </Tooltip>
          )}
        </div>

        {/* Online Count */}
        {collaborators.length > 0 && (
          <div className="ml-3 flex items-center gap-1 text-xs text-gray-600">
            <Wifi className="w-3 h-3" />
            <span>{collaborators.filter((c) => c.isOnline).length} online</span>
          </div>
        )}
    </div>
  );
};

/**
 * Compact Collaborator List Variant
 * Minimal version for toolbars and headers
 */
export const CompactCollaboratorList: React.FC<{
  collaborators: CollaboratorInfo[];
  currentUserId?: number;
}> = ({ collaborators, currentUserId }) => {
  if (collaborators.length === 0) return null;

  return (
    <div className="flex items-center gap-2 px-2 py-1 bg-gray-100 rounded-md">
      <CollaboratorList
        collaborators={collaborators}
        currentUserId={currentUserId}
        maxVisible={3}
        showRoles={false}
        showActivity={false}
      />
    </div>
  );
};
