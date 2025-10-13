/**
 * Session Manager Component
 *
 * Manages collaborative editing sessions with:
 * - Session creation and invitation
 * - User role management (owner, editor, viewer)
 * - Session settings and controls
 * - Participant management
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  Users,
  UserPlus,
  Share2,
  CheckCircle,
  Settings,
  Crown,
  Edit3,
  Eye,
  X,
  Link as LinkIcon,
} from "lucide-react";
import { logger } from "@/utils/logger";

export type UserRole = "owner" | "editor" | "viewer";

export interface SessionParticipant {
  userId: number;
  username: string;
  email?: string;
  role: UserRole;
  isOnline: boolean;
  joinedAt: string;
}

export interface SessionInfo {
  sessionId: string;
  jobId: number;
  ownerId: number;
  createdAt: string;
  participants: SessionParticipant[];
  inviteLink?: string;
  isPublic: boolean;
}

interface SessionManagerProps {
  sessionInfo: SessionInfo | null;
  currentUserId: number;
  onInviteUser?: (email: string, role: UserRole) => Promise<void>;
  onChangeRole?: (userId: number, newRole: UserRole) => Promise<void>;
  onRemoveParticipant?: (userId: number) => Promise<void>;
  onLeaveSession?: () => void;
  onUpdateSettings?: (settings: { isPublic: boolean }) => Promise<void>;
  className?: string;
}

export const SessionManager: React.FC<SessionManagerProps> = ({
  sessionInfo,
  currentUserId,
  onInviteUser,
  onChangeRole,
  onRemoveParticipant,
  onLeaveSession,
  className,
}) => {
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<UserRole>("editor");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  const currentUser = sessionInfo?.participants.find(
    (p) => p.userId === currentUserId,
  );
  const isOwner = currentUserId === sessionInfo?.ownerId;
  const canManageUsers = isOwner || currentUser?.role === "editor";

  const handleInviteUser = async () => {
    if (!inviteEmail || !onInviteUser) return;

    setIsInviting(true);
    try {
      await onInviteUser(inviteEmail, inviteRole);
      setInviteEmail("");
      setInviteDialogOpen(false);
    } catch (error) {
      logger.error("Failed to invite user:", error);
    } finally {
      setIsInviting(false);
    }
  };

  const handleCopyInviteLink = () => {
    if (!sessionInfo?.inviteLink) return;

    navigator.clipboard.writeText(sessionInfo.inviteLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case "owner":
        return <Crown className="w-3 h-3" />;
      case "editor":
        return <Edit3 className="w-3 h-3" />;
      case "viewer":
        return <Eye className="w-3 h-3" />;
    }
  };

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case "owner":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "editor":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "viewer":
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  if (!sessionInfo) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No active session</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Session Management
            <Badge variant="outline" className="ml-1">
              {sessionInfo.participants.filter((p) => p.isOnline).length} online
            </Badge>
          </div>
          {isOwner && (
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <Settings className="w-3 h-3" />
            </Button>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Invite Section */}
        {canManageUsers && (
          <div className="space-y-2">
            <Label className="text-xs">Invite Collaborators</Label>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setInviteDialogOpen(true)}
              >
                <UserPlus className="w-3 h-3 mr-1" />
                Invite User
              </Button>
              <Dialog
                open={inviteDialogOpen}
                onOpenChange={setInviteDialogOpen}
              >
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Invite User to Session</DialogTitle>
                    <DialogDescription>
                      Send an invitation to collaborate on this job description
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="invite-email">Email Address</Label>
                      <Input
                        id="invite-email"
                        type="email"
                        placeholder="colleague@example.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="invite-role">Role</Label>
                      <Select
                        value={inviteRole}
                        onValueChange={(value) =>
                          setInviteRole(value as UserRole)
                        }
                      >
                        <SelectTrigger id="invite-role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="editor">
                            <div className="flex items-center gap-2">
                              <Edit3 className="w-3 h-3" />
                              Editor - Can edit and comment
                            </div>
                          </SelectItem>
                          <SelectItem value="viewer">
                            <div className="flex items-center gap-2">
                              <Eye className="w-3 h-3" />
                              Viewer - Read-only access
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="outline"
                      onClick={() => setInviteDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleInviteUser}
                      disabled={!inviteEmail || isInviting}
                    >
                      {isInviting ? "Sending..." : "Send Invitation"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              {sessionInfo.inviteLink && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyInviteLink}
                  className="flex-1"
                >
                  {linkCopied ? (
                    <>
                      <CheckCircle className="w-3 h-3 mr-1 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <LinkIcon className="w-3 h-3 mr-1" />
                      Copy Link
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Participants List */}
        <div className="space-y-2">
          <Label className="text-xs">
            Participants ({sessionInfo.participants.length})
          </Label>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {sessionInfo.participants.map((participant) => (
              <div
                key={participant.userId}
                className="flex items-center justify-between p-2 rounded-lg border bg-white hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <div className="relative">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                        participant.isOnline
                          ? "bg-blue-100 text-blue-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {participant.username.slice(0, 2).toUpperCase()}
                    </div>
                    {participant.isOnline && (
                      <div className="absolute bottom-0 right-0 w-2 h-2 bg-green-500 rounded-full border border-white" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <p className="text-sm font-medium truncate">
                        {participant.username}
                        {participant.userId === currentUserId && " (You)"}
                      </p>
                    </div>
                    {participant.email && (
                      <p className="text-xs text-gray-500 truncate">
                        {participant.email}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {isOwner && participant.userId !== currentUserId ? (
                    <Select
                      value={participant.role}
                      onValueChange={(value) =>
                        onChangeRole?.(participant.userId, value as UserRole)
                      }
                    >
                      <SelectTrigger className="h-6 text-xs w-24">
                        <div className="flex items-center gap-1">
                          {getRoleIcon(participant.role)}
                          <SelectValue />
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="editor">Editor</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <Badge
                      variant="outline"
                      className={`text-xs ${getRoleBadgeColor(participant.role)}`}
                    >
                      <div className="flex items-center gap-1">
                        {getRoleIcon(participant.role)}
                        {participant.role}
                      </div>
                    </Badge>
                  )}

                  {isOwner &&
                    participant.userId !== currentUserId &&
                    participant.role !== "owner" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() =>
                          onRemoveParticipant?.(participant.userId)
                        }
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Session Actions */}
        {!isOwner && (
          <Button
            variant="outline"
            size="sm"
            className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={onLeaveSession}
          >
            Leave Session
          </Button>
        )}

        {/* Session Info */}
        <div className="pt-2 border-t text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>Session ID:</span>
            <span className="font-mono">
              {sessionInfo.sessionId.slice(0, 8)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Created:</span>
            <span>{new Date(sessionInfo.createdAt).toLocaleString()}</span>
          </div>
          {sessionInfo.isPublic && (
            <Badge variant="outline" className="text-xs">
              <Share2 className="w-2 h-2 mr-1" />
              Public Session
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
