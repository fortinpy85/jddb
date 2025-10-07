/**
 * ChangeControls Component
 *
 * Provides granular controls for accepting/rejecting individual changes.
 * Includes keyboard shortcuts, bulk actions, and change navigation.
 */

"use client";

import React, { useEffect, useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { TextChange, ChangeCategory } from "@/utils/diffAnalysis";
import {
  Check,
  X,
  CheckCheck,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Info,
  Download,
  FileText,
  FileJson,
  Loader2,
} from "lucide-react";

export interface ChangeControlsProps {
  changes: TextChange[];
  acceptedChangeIds: string[];
  rejectedChangeIds: string[];
  currentChangeIndex: number;
  onAccept: (changeId: string) => void;
  onReject: (changeId: string) => void;
  onAcceptAll: (category?: ChangeCategory) => void;
  onRejectAll: (category?: ChangeCategory) => void;
  onNavigate: (direction: 'next' | 'prev') => void;
  onFilterCategory: (category: ChangeCategory | 'all') => void;
  selectedCategory?: ChangeCategory | 'all';
  finalText?: string;
  className?: string;
}

/**
 * Main ChangeControls Component
 */
export function ChangeControls({
  changes,
  acceptedChangeIds,
  rejectedChangeIds,
  currentChangeIndex,
  onAccept,
  onReject,
  onAcceptAll,
  onRejectAll,
  onNavigate,
  onFilterCategory,
  selectedCategory = 'all',
  finalText = '',
  className = "",
}: ChangeControlsProps) {
  const currentChange = changes[currentChangeIndex];
  const hasNext = currentChangeIndex < changes.length - 1;
  const hasPrev = currentChangeIndex > 0;

  // State for dialogs and operations
  const [showAcceptAllDialog, setShowAcceptAllDialog] = useState(false);
  const [showRejectAllDialog, setShowRejectAllDialog] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [exportFormat, setExportFormat] = useState<'txt' | 'json' | null>(null);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Enter: Accept current change
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && currentChange) {
        e.preventDefault();
        onAccept(currentChange.id);
        if (hasNext) onNavigate('next');
      }

      // Cmd/Ctrl + Delete/Backspace: Reject current change
      if ((e.metaKey || e.ctrlKey) && (e.key === 'Delete' || e.key === 'Backspace') && currentChange) {
        e.preventDefault();
        onReject(currentChange.id);
        if (hasNext) onNavigate('next');
      }

      // Arrow keys: Navigate changes
      if (e.key === 'ArrowRight' && hasNext) {
        e.preventDefault();
        onNavigate('next');
      }
      if (e.key === 'ArrowLeft' && hasPrev) {
        e.preventDefault();
        onNavigate('prev');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentChange, hasNext, hasPrev, onAccept, onReject, onNavigate]);

  // Filter changes by category
  const filteredChanges = selectedCategory === 'all'
    ? changes
    : changes.filter(c => c.category === selectedCategory);

  const pendingChanges = filteredChanges.filter(
    c => !acceptedChangeIds.includes(c.id) && !rejectedChangeIds.includes(c.id)
  );

  // Bulk accept with confirmation
  const handleAcceptAll = async () => {
    setIsProcessing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate processing
      onAcceptAll(selectedCategory === 'all' ? undefined : selectedCategory);
      setShowAcceptAllDialog(false);
    } catch (error) {
      console.error('Failed to accept all changes:', error);
      alert('Failed to accept all changes. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Bulk reject with confirmation
  const handleRejectAll = async () => {
    setIsProcessing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate processing
      onRejectAll(selectedCategory === 'all' ? undefined : selectedCategory);
      setShowRejectAllDialog(false);
    } catch (error) {
      console.error('Failed to reject all changes:', error);
      alert('Failed to reject all changes. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Export final text
  const handleExport = (format: 'txt' | 'json') => {
    try {
      let content: string;
      let mimeType: string;
      let filename: string;

      if (format === 'txt') {
        content = finalText;
        mimeType = 'text/plain';
        filename = `improved_job_description_${new Date().toISOString().split('T')[0]}.txt`;
      } else {
        const exportData = {
          finalText,
          changes: changes.map(c => ({
            id: c.id,
            type: c.type,
            category: c.category,
            severity: c.severity,
            originalText: c.originalText,
            suggestedText: c.suggestedText,
            accepted: acceptedChangeIds.includes(c.id),
            rejected: rejectedChangeIds.includes(c.id),
          })),
          summary: {
            totalChanges: changes.length,
            accepted: acceptedChangeIds.length,
            rejected: rejectedChangeIds.length,
            pending: pendingChanges.length,
          },
          exportDate: new Date().toISOString(),
        };
        content = JSON.stringify(exportData, null, 2);
        mimeType = 'application/json';
        filename = `improved_job_description_${new Date().toISOString().split('T')[0]}.json`;
      }

      const blob = new Blob([content], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExportFormat(null);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <Card className={cn("", className)}>
      <CardContent className="p-4 space-y-4">
        {/* Summary Stats */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-sm">
              {acceptedChangeIds.length} accepted
            </Badge>
            <Badge variant="outline" className="text-sm">
              {rejectedChangeIds.length} rejected
            </Badge>
            <Badge variant="outline" className="text-sm">
              {pendingChanges.length} pending
            </Badge>
          </div>

          {/* Category Filter */}
          <Select
            value={selectedCategory}
            onValueChange={(value) => onFilterCategory(value as ChangeCategory | 'all')}
          >
            <SelectTrigger className="w-[140px] h-8">
              <Filter className="h-3 w-3 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Changes</SelectItem>
              <SelectItem value="grammar">Grammar</SelectItem>
              <SelectItem value="style">Style</SelectItem>
              <SelectItem value="clarity">Clarity</SelectItem>
              <SelectItem value="bias">Bias</SelectItem>
              <SelectItem value="compliance">Compliance</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Current Change Controls */}
        {currentChange && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Change {currentChangeIndex + 1} of {filteredChanges.length}
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onNavigate('prev')}
                  disabled={!hasPrev}
                  className="h-7"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onNavigate('next')}
                  disabled={!hasNext}
                  className="h-7"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Change Details */}
            <CurrentChangeCard
              change={currentChange}
              isAccepted={acceptedChangeIds.includes(currentChange.id)}
              isRejected={rejectedChangeIds.includes(currentChange.id)}
            />

            {/* Accept/Reject Buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="default"
                size="sm"
                onClick={() => {
                  onAccept(currentChange.id);
                  if (hasNext) onNavigate('next');
                }}
                disabled={acceptedChangeIds.includes(currentChange.id)}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                <Check className="h-4 w-4 mr-1" />
                Accept
                <kbd className="ml-2 text-xs opacity-70">⌘↵</kbd>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onReject(currentChange.id);
                  if (hasNext) onNavigate('next');
                }}
                disabled={rejectedChangeIds.includes(currentChange.id)}
                className="flex-1"
              >
                <X className="h-4 w-4 mr-1" />
                Reject
                <kbd className="ml-2 text-xs opacity-70">⌘⌫</kbd>
              </Button>
            </div>
          </div>
        )}

        <Separator />

        {/* Bulk Actions */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
            Bulk Actions
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAcceptAllDialog(true)}
              disabled={pendingChanges.length === 0 || isProcessing}
              className="text-xs"
            >
              {isProcessing && showAcceptAllDialog ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <CheckCheck className="h-3 w-3 mr-1" />
              )}
              Accept All {selectedCategory !== 'all' && selectedCategory}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowRejectAllDialog(true)}
              disabled={pendingChanges.length === 0 || isProcessing}
              className="text-xs"
            >
              {isProcessing && showRejectAllDialog ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <XCircle className="h-3 w-3 mr-1" />
              )}
              Reject All {selectedCategory !== 'all' && selectedCategory}
            </Button>
          </div>
        </div>

        <Separator />

        {/* Export Actions */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
            Export Final Text
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('txt')}
              disabled={!finalText || isProcessing}
              className="text-xs"
            >
              <FileText className="h-3 w-3 mr-1" />
              Export TXT
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('json')}
              disabled={!finalText || isProcessing}
              className="text-xs"
            >
              <FileJson className="h-3 w-3 mr-1" />
              Export JSON
            </Button>
          </div>
        </div>

        {/* Keyboard Shortcuts Help */}
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <details className="text-xs text-gray-600 dark:text-gray-400">
            <summary className="cursor-pointer flex items-center gap-1">
              <Info className="h-3 w-3" />
              Keyboard Shortcuts
            </summary>
            <div className="mt-2 space-y-1 pl-4">
              <div><kbd>⌘ + ↵</kbd> Accept change</div>
              <div><kbd>⌘ + ⌫</kbd> Reject change</div>
              <div><kbd>→</kbd> Next change</div>
              <div><kbd>←</kbd> Previous change</div>
            </div>
          </details>
        </div>
      </CardContent>

      {/* Accept All Confirmation Dialog */}
      <Dialog open={showAcceptAllDialog} onOpenChange={setShowAcceptAllDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Accept All Changes?</DialogTitle>
            <DialogDescription>
              You are about to accept {pendingChanges.length} pending {selectedCategory !== 'all' ? selectedCategory : ''} change{pendingChanges.length !== 1 ? 's' : ''}.
              This action will apply all these changes to your text.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAcceptAllDialog(false)}
              disabled={isProcessing}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handleAcceptAll}
              disabled={isProcessing}
              className="bg-green-600 hover:bg-green-700"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Accepting...
                </>
              ) : (
                <>
                  <CheckCheck className="h-4 w-4 mr-2" />
                  Accept All
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject All Confirmation Dialog */}
      <Dialog open={showRejectAllDialog} onOpenChange={setShowRejectAllDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject All Changes?</DialogTitle>
            <DialogDescription>
              You are about to reject {pendingChanges.length} pending {selectedCategory !== 'all' ? selectedCategory : ''} change{pendingChanges.length !== 1 ? 's' : ''}.
              This action will discard all these changes.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRejectAllDialog(false)}
              disabled={isProcessing}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRejectAll}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject All
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

/**
 * Current Change Card Component
 */
interface CurrentChangeCardProps {
  change: TextChange;
  isAccepted: boolean;
  isRejected: boolean;
}

function CurrentChangeCard({ change, isAccepted, isRejected }: CurrentChangeCardProps) {
  return (
    <div className={cn(
      "p-3 rounded-lg border-2 transition-colors",
      isAccepted && "bg-green-50 border-green-300 dark:bg-green-900/20",
      isRejected && "bg-red-50 border-red-300 dark:bg-red-900/20",
      !isAccepted && !isRejected && "bg-blue-50 border-blue-300 dark:bg-blue-900/20"
    )}>
      <div className="space-y-2">
        {/* Category & Severity */}
        <div className="flex items-center gap-2">
          <Badge className={getCategoryBadgeClass(change.category)}>
            {change.category}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {change.severity}
          </Badge>
          {change.confidence !== undefined && (
            <Badge variant="outline" className="text-xs">
              {Math.round(change.confidence * 100)}% confident
            </Badge>
          )}
        </div>

        {/* Change Text */}
        <div className="space-y-1 text-sm">
          {change.type === 'deletion' && (
            <div className="text-red-700 dark:text-red-400">
              <span className="font-medium">Remove:</span> "{change.originalText}"
            </div>
          )}
          {change.type === 'addition' && (
            <div className="text-green-700 dark:text-green-400">
              <span className="font-medium">Add:</span> "{change.suggestedText}"
            </div>
          )}
          {change.type === 'modification' && (
            <>
              <div className="text-red-700 dark:text-red-400">
                <span className="font-medium">From:</span> "{change.originalText}"
              </div>
              <div className="text-green-700 dark:text-green-400">
                <span className="font-medium">To:</span> "{change.suggestedText}"
              </div>
            </>
          )}
        </div>

        {/* Explanation */}
        {change.explanation && (
          <p className="text-xs text-gray-700 dark:text-gray-300 italic">
            {change.explanation}
          </p>
        )}

        {/* Status Indicator */}
        {isAccepted && (
          <div className="flex items-center gap-1 text-xs text-green-700 dark:text-green-400">
            <Check className="h-3 w-3" />
            <span>Accepted</span>
          </div>
        )}
        {isRejected && (
          <div className="flex items-center gap-1 text-xs text-red-700 dark:text-red-400">
            <X className="h-3 w-3" />
            <span>Rejected</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Helper function to get category badge class
 */
function getCategoryBadgeClass(category: ChangeCategory): string {
  switch (category) {
    case 'grammar':
      return 'bg-red-100 text-red-700';
    case 'style':
      return 'bg-blue-100 text-blue-700';
    case 'clarity':
      return 'bg-purple-100 text-purple-700';
    case 'bias':
      return 'bg-yellow-100 text-yellow-700';
    case 'compliance':
      return 'bg-green-100 text-green-700';
  }
}
