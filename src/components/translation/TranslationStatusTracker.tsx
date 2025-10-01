/**
 * Translation Status Tracker Component
 *
 * Provides visual tracking and management of translation progress:
 * - Overall document translation status
 * - Segment-level status breakdown
 * - Progress visualization
 * - Status change history
 * - Batch status operations
 */

"use client";

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CheckCircle,
  Clock,
  Eye,
  AlertCircle,
  TrendingUp,
  Users,
  Calendar,
  Filter,
} from "lucide-react";
import type { BilingualSegment, TranslationStatus } from "./BilingualEditor";

interface StatusChange {
  id: string;
  segmentId: string;
  oldStatus: TranslationStatus;
  newStatus: TranslationStatus;
  timestamp: Date;
  user: string;
}

interface TranslationStatusTrackerProps {
  segments: BilingualSegment[];
  onSegmentClick?: (segmentId: string) => void;
  onBatchStatusChange?: (
    segmentIds: string[],
    status: TranslationStatus,
  ) => void;
  statusHistory?: StatusChange[];
  className?: string;
}

export const TranslationStatusTracker: React.FC<
  TranslationStatusTrackerProps
> = ({
  segments,
  onSegmentClick,
  onBatchStatusChange,
  statusHistory = [],
  className,
}) => {
  const [filterStatus, setFilterStatus] = useState<TranslationStatus | "all">(
    "all",
  );
  const [selectedSegments, setSelectedSegments] = useState<Set<string>>(
    new Set(),
  );
  const [showHistory, setShowHistory] = useState(false);

  // Calculate statistics
  const statistics = useMemo(() => {
    const total = segments.length;
    const draft = segments.filter((s) => s.status === "draft").length;
    const review = segments.filter((s) => s.status === "review").length;
    const approved = segments.filter((s) => s.status === "approved").length;

    const draftPercent = (draft / total) * 100;
    const reviewPercent = (review / total) * 100;
    const approvedPercent = (approved / total) * 100;

    return {
      total,
      draft,
      review,
      approved,
      draftPercent,
      reviewPercent,
      approvedPercent,
    };
  }, [segments]);

  // Filter segments based on selected status
  const filteredSegments = useMemo(() => {
    if (filterStatus === "all") return segments;
    return segments.filter((s) => s.status === filterStatus);
  }, [segments, filterStatus]);

  // Toggle segment selection
  const toggleSegmentSelection = (segmentId: string) => {
    setSelectedSegments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(segmentId)) {
        newSet.delete(segmentId);
      } else {
        newSet.add(segmentId);
      }
      return newSet;
    });
  };

  // Select all filtered segments
  const selectAll = () => {
    setSelectedSegments(new Set(filteredSegments.map((s) => s.id)));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedSegments(new Set());
  };

  // Apply batch status change
  const handleBatchStatusChange = (status: TranslationStatus) => {
    if (selectedSegments.size > 0 && onBatchStatusChange) {
      onBatchStatusChange(Array.from(selectedSegments), status);
      clearSelection();
    }
  };

  // Get status color
  const getStatusColor = (status: TranslationStatus): string => {
    switch (status) {
      case "draft":
        return "bg-yellow-500";
      case "review":
        return "bg-blue-500";
      case "approved":
        return "bg-green-500";
    }
  };

  // Get status badge color
  const getStatusBadgeColor = (status: TranslationStatus): string => {
    switch (status) {
      case "draft":
        return "bg-yellow-100 text-yellow-800";
      case "review":
        return "bg-blue-100 text-blue-800";
      case "approved":
        return "bg-green-100 text-green-800";
    }
  };

  // Get status icon
  const getStatusIcon = (status: TranslationStatus) => {
    switch (status) {
      case "draft":
        return <Clock className="w-3 h-3" />;
      case "review":
        return <Eye className="w-3 h-3" />;
      case "approved":
        return <CheckCircle className="w-3 h-3" />;
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Translation Status Tracker
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">Overall Progress</span>
            <span className="text-xs text-gray-600">
              {statistics.approved}/{statistics.total} approved
            </span>
          </div>

          {/* Stacked Progress Bar */}
          <div className="h-3 w-full bg-gray-200 rounded-full overflow-hidden flex">
            {statistics.approvedPercent > 0 && (
              <div
                className="bg-green-500 h-full transition-all"
                style={{ width: `${statistics.approvedPercent}%` }}
                title={`Approved: ${statistics.approved}`}
              />
            )}
            {statistics.reviewPercent > 0 && (
              <div
                className="bg-blue-500 h-full transition-all"
                style={{ width: `${statistics.reviewPercent}%` }}
                title={`Review: ${statistics.review}`}
              />
            )}
            {statistics.draftPercent > 0 && (
              <div
                className="bg-yellow-500 h-full transition-all"
                style={{ width: `${statistics.draftPercent}%` }}
                title={`Draft: ${statistics.draft}`}
              />
            )}
          </div>

          {/* Status Breakdown */}
          <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col items-center p-2 bg-yellow-50 rounded">
              <div className="flex items-center gap-1 mb-1">
                <Clock className="w-3 h-3 text-yellow-600" />
                <span className="text-xs font-medium text-yellow-900">
                  Draft
                </span>
              </div>
              <span className="text-lg font-bold text-yellow-900">
                {statistics.draft}
              </span>
            </div>

            <div className="flex flex-col items-center p-2 bg-blue-50 rounded">
              <div className="flex items-center gap-1 mb-1">
                <Eye className="w-3 h-3 text-blue-600" />
                <span className="text-xs font-medium text-blue-900">
                  Review
                </span>
              </div>
              <span className="text-lg font-bold text-blue-900">
                {statistics.review}
              </span>
            </div>

            <div className="flex flex-col items-center p-2 bg-green-50 rounded">
              <div className="flex items-center gap-1 mb-1">
                <CheckCircle className="w-3 h-3 text-green-600" />
                <span className="text-xs font-medium text-green-900">
                  Approved
                </span>
              </div>
              <span className="text-lg font-bold text-green-900">
                {statistics.approved}
              </span>
            </div>
          </div>
        </div>

        {/* Filter and Batch Actions */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <Select
              value={filterStatus}
              onValueChange={(value) =>
                setFilterStatus(value as TranslationStatus | "all")
              }
            >
              <SelectTrigger className="h-8 w-[140px] text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Segments</SelectItem>
                <SelectItem value="draft">Draft Only</SelectItem>
                <SelectItem value="review">Review Only</SelectItem>
                <SelectItem value="approved">Approved Only</SelectItem>
              </SelectContent>
            </Select>

            {selectedSegments.size > 0 && (
              <Badge variant="outline" className="text-xs">
                {selectedSegments.size} selected
              </Badge>
            )}
          </div>

          {/* Batch Action Buttons */}
          {selectedSegments.size > 0 && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchStatusChange("draft")}
                className="flex-1"
              >
                <Clock className="w-3 h-3 mr-1" />
                Draft
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchStatusChange("review")}
                className="flex-1"
              >
                <Eye className="w-3 h-3 mr-1" />
                Review
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchStatusChange("approved")}
                className="flex-1"
              >
                <CheckCircle className="w-3 h-3 mr-1" />
                Approve
              </Button>
            </div>
          )}

          {/* Selection Controls */}
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={selectAll}
              className="flex-1 text-xs"
              disabled={filteredSegments.length === 0}
            >
              Select All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelection}
              className="flex-1 text-xs"
              disabled={selectedSegments.size === 0}
            >
              Clear
            </Button>
          </div>
        </div>

        {/* Segment List */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">Segments</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowHistory(!showHistory)}
              className="h-6 text-xs"
            >
              <Calendar className="w-3 h-3 mr-1" />
              {showHistory ? "Hide" : "Show"} History
            </Button>
          </div>

          <ScrollArea className="h-[300px] pr-2">
            {showHistory ? (
              // Status Change History
              <div className="space-y-2">
                {statusHistory.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-500">
                    No status changes recorded
                  </div>
                ) : (
                  statusHistory.map((change) => (
                    <div
                      key={change.id}
                      className="p-2 border rounded text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-xs">
                          Segment {change.segmentId}
                        </Badge>
                        <span className="text-gray-500">
                          {change.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          className={getStatusBadgeColor(change.oldStatus)}
                        >
                          {change.oldStatus}
                        </Badge>
                        <span>→</span>
                        <Badge
                          className={getStatusBadgeColor(change.newStatus)}
                        >
                          {change.newStatus}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1 text-gray-600">
                        <Users className="w-3 h-3" />
                        {change.user}
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              // Segment List
              <div className="space-y-2">
                {filteredSegments.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-500">
                    No segments match the current filter
                  </div>
                ) : (
                  filteredSegments.map((segment) => {
                    const isSelected = selectedSegments.has(segment.id);
                    const enComplete = segment.english.trim().length > 0;
                    const frComplete = segment.french.trim().length > 0;

                    return (
                      <div
                        key={segment.id}
                        className={`p-2 border rounded cursor-pointer transition-colors ${
                          isSelected
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                        onClick={() => {
                          if (onSegmentClick) {
                            onSegmentClick(segment.id);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => {
                                e.stopPropagation();
                                toggleSegmentSelection(segment.id);
                              }}
                              className="w-3 h-3"
                            />
                            <Badge variant="outline" className="text-xs">
                              Segment {segment.id}
                            </Badge>
                          </div>

                          <Badge
                            className={`text-xs ${getStatusBadgeColor(segment.status)}`}
                          >
                            {getStatusIcon(segment.status)}
                            <span className="ml-1">{segment.status}</span>
                          </Badge>
                        </div>

                        {/* Language Completion Indicators */}
                        <div className="flex gap-2 text-xs">
                          <div className="flex items-center gap-1">
                            {enComplete ? (
                              <CheckCircle className="w-3 h-3 text-green-500" />
                            ) : (
                              <AlertCircle className="w-3 h-3 text-yellow-500" />
                            )}
                            <span className="text-gray-600">EN</span>
                          </div>
                          <div className="flex items-center gap-1">
                            {frComplete ? (
                              <CheckCircle className="w-3 h-3 text-green-500" />
                            ) : (
                              <AlertCircle className="w-3 h-3 text-yellow-500" />
                            )}
                            <span className="text-gray-600">FR</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
};
