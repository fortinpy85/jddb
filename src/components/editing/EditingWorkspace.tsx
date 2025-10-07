import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DualPaneEditor } from "./DualPaneEditor";
import {
  Plus,
  FileText,
  Languages,
  Users,
  Clock,
  Search,
  Filter,
} from "lucide-react";

interface EditingSession {
  id: string;
  jobId: number;
  jobTitle: string;
  mode: "editing" | "translation" | "comparison";
  status: "active" | "draft" | "completed";
  collaborators: number;
  lastModified: string;
  createdBy: string;
}

const mockSessions: EditingSession[] = [
  {
    id: "session-1",
    jobId: 1,
    jobTitle: "Director of Policy Analysis",
    mode: "editing",
    status: "active",
    collaborators: 2,
    lastModified: "2025-09-20T10:30:00Z",
    createdBy: "Alice Johnson",
  },
  {
    id: "session-2",
    jobId: 2,
    jobTitle: "Senior Business Analyst",
    mode: "translation",
    status: "draft",
    collaborators: 1,
    lastModified: "2025-09-20T09:15:00Z",
    createdBy: "Bob Smith",
  },
];

const mockJobs = [
  { id: 1, title: "Director of Policy Analysis", classification: "EX-01" },
  { id: 2, title: "Senior Business Analyst", classification: "AS-06" },
  { id: 3, title: "Program Manager", classification: "PM-05" },
];

export const EditingWorkspace: React.FC = () => {
  const [sessions, setSessions] = useState<EditingSession[]>(mockSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  if (activeSession) {
    return (
      <DualPaneEditor
        jobId={activeSession.jobId}
        sessionId={activeSession.id}
        mode={activeSession.mode}
        initialLeftContent="# Job Description\n\nThis is the original job description content..."
        initialRightContent="# Enhanced Job Description\n\nThis is the enhanced version..."
      />
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Editing Workspace</h2>
          <p className="text-gray-600">
            Collaborative document editing and translation
          </p>
        </div>
        <Button onClick={() => setActiveSessionId("session-1")}>
          <Plus className="w-4 h-4 mr-2" />
          New Session
        </Button>
      </div>

      <div className="grid gap-4">
        {sessions.map((session) => (
          <Card
            key={session.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setActiveSessionId(session.id)}
          >
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold">{session.jobTitle}</h3>
                    <Badge
                      variant={
                        session.status === "active" ? "default" : "secondary"
                      }
                    >
                      {session.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {session.collaborators} collaborators
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(session.lastModified).toLocaleDateString()}
                    </div>
                    <span>Created by {session.createdBy}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="capitalize">
                    {session.mode}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
