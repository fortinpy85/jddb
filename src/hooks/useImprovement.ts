/**
 * useImprovement Hook
 *
 * Manages state for the improvement workflow with inline diff viewing.
 * Handles change acceptance/rejection, navigation, and RLHF data capture.
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { analyzeDiff, applyChanges } from '@/utils/diffAnalysis';
import type { TextChange, ChangeCategory, DiffResult } from '@/utils/diffAnalysis';
import type { AISuggestion } from './useAISuggestions';
import { useVersionHistory, type UseVersionHistoryReturn } from './useVersionHistory';

export interface UseImprovementOptions {
  originalText: string;
  improvedText: string;
  aiSuggestions?: AISuggestion[];
  onAcceptChange?: (change: TextChange) => void;
  onRejectChange?: (change: TextChange) => void;
  onApplyChanges?: (finalText: string, acceptedChanges: TextChange[]) => void;
  captureRLHF?: boolean;
}

export interface UseImprovementReturn {
  // Diff analysis
  diffResult: DiffResult;
  changes: TextChange[];
  filteredChanges: TextChange[];

  // Current change state
  currentChangeIndex: number;
  currentChange: TextChange | null;
  selectedChangeId: string | null;

  // Accepted/Rejected tracking
  acceptedChangeIds: string[];
  rejectedChangeIds: string[];
  pendingChanges: TextChange[];

  // Actions
  acceptChange: (changeId: string) => void;
  rejectChange: (changeId: string) => void;
  acceptAll: (category?: ChangeCategory) => void;
  rejectAll: (category?: ChangeCategory) => void;
  navigateChange: (direction: 'next' | 'prev') => void;
  selectChange: (changeId: string | null) => void;

  // Filtering
  selectedCategory: ChangeCategory | 'all';
  setSelectedCategory: (category: ChangeCategory | 'all') => void;

  // Final text
  finalText: string;
  applyAcceptedChanges: () => string;
  hasChanges: boolean;
  hasPendingChanges: boolean;

  // Version history
  versionHistory: UseVersionHistoryReturn;
}

/**
 * Main useImprovement hook
 */
export function useImprovement({
  originalText,
  improvedText,
  aiSuggestions,
  onAcceptChange,
  onRejectChange,
  onApplyChanges,
  captureRLHF = false,
}: UseImprovementOptions): UseImprovementReturn {
  // Run diff analysis
  const diffResult = useMemo(() => {
    return analyzeDiff(originalText, improvedText, aiSuggestions);
  }, [originalText, improvedText, aiSuggestions]);

  const changes = diffResult.changes;

  // State
  const [acceptedChangeIds, setAcceptedChangeIds] = useState<string[]>([]);
  const [rejectedChangeIds, setRejectedChangeIds] = useState<string[]>([]);
  const [currentChangeIndex, setCurrentChangeIndex] = useState(0);
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<ChangeCategory | 'all'>('all');

  // Version history for undo/redo
  const versionHistory = useVersionHistory(
    {
      acceptedChangeIds: [],
      rejectedChangeIds: [],
      description: 'Initial state'
    },
    {
      maxHistorySize: 50,
      onStateChange: (state) => {
        setAcceptedChangeIds(state.acceptedChangeIds);
        setRejectedChangeIds(state.rejectedChangeIds);
      }
    }
  );

  // Keyboard shortcuts for undo/redo
  useEffect(() => {
    window.addEventListener('keydown', versionHistory.handleKeyDown);
    return () => window.removeEventListener('keydown', versionHistory.handleKeyDown);
  }, [versionHistory.handleKeyDown]);

  // Filter changes by category
  const filteredChanges = useMemo(() => {
    return selectedCategory === 'all'
      ? changes
      : changes.filter(c => c.category === selectedCategory);
  }, [changes, selectedCategory]);

  // Get current change
  const currentChange = filteredChanges[currentChangeIndex] || null;

  // Get pending changes
  const pendingChanges = useMemo(() => {
    return filteredChanges.filter(
      c => !acceptedChangeIds.includes(c.id) && !rejectedChangeIds.includes(c.id)
    );
  }, [filteredChanges, acceptedChangeIds, rejectedChangeIds]);

  // Accept change
  const acceptChange = useCallback((changeId: string) => {
    const change = changes.find(c => c.id === changeId);
    if (!change) return;

    const newAccepted = [...acceptedChangeIds, changeId];
    const newRejected = rejectedChangeIds.filter(id => id !== changeId);

    setAcceptedChangeIds(newAccepted);
    setRejectedChangeIds(newRejected);

    // Push to version history
    versionHistory.pushVersion({
      acceptedChangeIds: newAccepted,
      rejectedChangeIds: newRejected,
      description: `Accepted change: ${change.category}`
    });

    // Call callback
    onAcceptChange?.(change);

    // Capture RLHF data
    if (captureRLHF) {
      captureRLHFData(change, 'accept');
    }
  }, [changes, acceptedChangeIds, rejectedChangeIds, onAcceptChange, captureRLHF, versionHistory]);

  // Reject change
  const rejectChange = useCallback((changeId: string) => {
    const change = changes.find(c => c.id === changeId);
    if (!change) return;

    const newRejected = [...rejectedChangeIds, changeId];
    const newAccepted = acceptedChangeIds.filter(id => id !== changeId);

    setRejectedChangeIds(newRejected);
    setAcceptedChangeIds(newAccepted);

    // Push to version history
    versionHistory.pushVersion({
      acceptedChangeIds: newAccepted,
      rejectedChangeIds: newRejected,
      description: `Rejected change: ${change.category}`
    });

    // Call callback
    onRejectChange?.(change);

    // Capture RLHF data
    if (captureRLHF) {
      captureRLHFData(change, 'reject');
    }
  }, [changes, acceptedChangeIds, rejectedChangeIds, onRejectChange, captureRLHF, versionHistory]);

  // Accept all changes (optionally filtered by category)
  const acceptAll = useCallback((category?: ChangeCategory) => {
    const changesToAccept = category
      ? changes.filter(c => c.category === category)
      : changes;

    const ids = changesToAccept.map(c => c.id);
    setAcceptedChangeIds(prev => [...new Set([...prev, ...ids])]);
    setRejectedChangeIds(prev => prev.filter(id => !ids.includes(id)));

    // Call callbacks and RLHF
    changesToAccept.forEach(change => {
      onAcceptChange?.(change);
      if (captureRLHF) {
        captureRLHFData(change, 'accept');
      }
    });
  }, [changes, onAcceptChange, captureRLHF]);

  // Reject all changes (optionally filtered by category)
  const rejectAll = useCallback((category?: ChangeCategory) => {
    const changesToReject = category
      ? changes.filter(c => c.category === category)
      : changes;

    const ids = changesToReject.map(c => c.id);
    setRejectedChangeIds(prev => [...new Set([...prev, ...ids])]);
    setAcceptedChangeIds(prev => prev.filter(id => !ids.includes(id)));

    // Call callbacks and RLHF
    changesToReject.forEach(change => {
      onRejectChange?.(change);
      if (captureRLHF) {
        captureRLHFData(change, 'reject');
      }
    });
  }, [changes, onRejectChange, captureRLHF]);

  // Navigate changes
  const navigateChange = useCallback((direction: 'next' | 'prev') => {
    setCurrentChangeIndex(prev => {
      if (direction === 'next') {
        return Math.min(prev + 1, filteredChanges.length - 1);
      } else {
        return Math.max(prev - 1, 0);
      }
    });
  }, [filteredChanges.length]);

  // Select specific change
  const selectChange = useCallback((changeId: string | null) => {
    setSelectedChangeId(changeId);
    if (changeId) {
      const index = filteredChanges.findIndex(c => c.id === changeId);
      if (index !== -1) {
        setCurrentChangeIndex(index);
      }
    }
  }, [filteredChanges]);

  // Apply accepted changes to get final text
  const applyAcceptedChanges = useCallback(() => {
    const finalText = applyChanges(originalText, changes, acceptedChangeIds);
    onApplyChanges?.(finalText, changes.filter(c => acceptedChangeIds.includes(c.id)));
    return finalText;
  }, [originalText, changes, acceptedChangeIds, onApplyChanges]);

  // Get final text (memoized)
  const finalText = useMemo(() => {
    return applyChanges(originalText, changes, acceptedChangeIds);
  }, [originalText, changes, acceptedChangeIds]);

  // Auto-select first change when category changes
  useEffect(() => {
    if (filteredChanges.length > 0) {
      setCurrentChangeIndex(0);
      setSelectedChangeId(filteredChanges[0].id);
    }
  }, [selectedCategory, filteredChanges]);

  return {
    // Diff analysis
    diffResult,
    changes,
    filteredChanges,

    // Current change state
    currentChangeIndex,
    currentChange,
    selectedChangeId,

    // Accepted/Rejected tracking
    acceptedChangeIds,
    rejectedChangeIds,
    pendingChanges,

    // Actions
    acceptChange,
    rejectChange,
    acceptAll,
    rejectAll,
    navigateChange,
    selectChange,

    // Filtering
    selectedCategory,
    setSelectedCategory,

    // Final text
    finalText,
    applyAcceptedChanges,
    hasChanges: changes.length > 0,
    hasPendingChanges: pendingChanges.length > 0,

    // Version history
    versionHistory,
  };
}

/**
 * Capture RLHF data for a change action
 */
function captureRLHFData(change: TextChange, action: 'accept' | 'reject' | 'modify') {
  // Store RLHF data for later analysis
  const rlhfData = {
    changeId: change.id,
    category: change.category,
    severity: change.severity,
    originalText: change.originalText,
    suggestedText: change.suggestedText,
    userAction: action,
    confidence: change.confidence,
    timestamp: new Date().toISOString(),
  };

  // Save to localStorage for now (will be moved to backend API)
  try {
    const existingData = JSON.parse(localStorage.getItem('rlhf_data') || '[]');
    existingData.push(rlhfData);
    localStorage.setItem('rlhf_data', JSON.stringify(existingData));
  } catch (error) {
    console.error('Failed to capture RLHF data:', error);
  }
}

/**
 * Export RLHF data (for analytics/training)
 */
export function exportRLHFData(): Array<any> {
  try {
    return JSON.parse(localStorage.getItem('rlhf_data') || '[]');
  } catch (error) {
    console.error('Failed to export RLHF data:', error);
    return [];
  }
}

/**
 * Clear RLHF data
 */
export function clearRLHFData(): void {
  try {
    localStorage.removeItem('rlhf_data');
  } catch (error) {
    console.error('Failed to clear RLHF data:', error);
  }
}
