/**
 * Diff Analysis Utilities
 *
 * Provides text comparison and diff analysis using diff-match-patch library.
 * Used for Smart Inline Diff Viewer to show granular changes between original and improved text.
 */

import DiffMatchPatch from 'diff-match-patch';

export type ChangeType = 'addition' | 'deletion' | 'modification' | 'unchanged';
export type ChangeSeverity = 'critical' | 'recommended' | 'optional';
export type ChangeCategory = 'grammar' | 'style' | 'clarity' | 'bias' | 'compliance';

export interface TextChange {
  id: string;
  type: ChangeType;
  category: ChangeCategory;
  severity: ChangeSeverity;
  originalText: string;
  suggestedText: string;
  startIndex: number;
  endIndex: number;
  explanation?: string;
  confidence?: number;
}

export interface DiffResult {
  changes: TextChange[];
  totalChanges: number;
  additionCount: number;
  deletionCount: number;
  modificationCount: number;
}

/**
 * Analyze differences between original and improved text
 */
export function analyzeDiff(
  originalText: string,
  improvedText: string,
  aiSuggestions?: Array<{
    type: string;
    original_text: string;
    suggested_text: string;
    explanation?: string;
    confidence?: number;
  }>
): DiffResult {
  const dmp = new DiffMatchPatch();
  const diffs = dmp.diff_main(originalText, improvedText);
  dmp.diff_cleanupSemantic(diffs);

  const changes: TextChange[] = [];
  let currentIndex = 0;
  let changeCounter = 0;

  diffs.forEach((diff) => {
    const [operation, text] = diff;

    if (operation === 0) {
      // Unchanged text
      currentIndex += text.length;
    } else if (operation === -1) {
      // Deletion
      const change: TextChange = {
        id: `change-${changeCounter++}`,
        type: 'deletion',
        category: determineCategory(text, aiSuggestions),
        severity: determineSeverity(text),
        originalText: text,
        suggestedText: '',
        startIndex: currentIndex,
        endIndex: currentIndex + text.length,
        explanation: findExplanation(text, aiSuggestions),
        confidence: findConfidence(text, aiSuggestions),
      };
      changes.push(change);
      currentIndex += text.length;
    } else if (operation === 1) {
      // Addition
      const change: TextChange = {
        id: `change-${changeCounter++}`,
        type: 'addition',
        category: determineCategory(text, aiSuggestions),
        severity: determineSeverity(text),
        originalText: '',
        suggestedText: text,
        startIndex: currentIndex,
        endIndex: currentIndex,
        explanation: findExplanation(text, aiSuggestions),
        confidence: findConfidence(text, aiSuggestions),
      };
      changes.push(change);
    }
  });

  // Merge adjacent deletions and additions into modifications
  const mergedChanges = mergeIntoModifications(changes);

  return {
    changes: mergedChanges,
    totalChanges: mergedChanges.length,
    additionCount: mergedChanges.filter(c => c.type === 'addition').length,
    deletionCount: mergedChanges.filter(c => c.type === 'deletion').length,
    modificationCount: mergedChanges.filter(c => c.type === 'modification').length,
  };
}

/**
 * Merge adjacent deletions and additions into modifications
 */
function mergeIntoModifications(changes: TextChange[]): TextChange[] {
  const merged: TextChange[] = [];
  let i = 0;

  while (i < changes.length) {
    const current = changes[i];
    const next = changes[i + 1];

    // Check if current deletion is followed by addition (modification)
    if (
      current.type === 'deletion' &&
      next &&
      next.type === 'addition' &&
      current.endIndex === next.startIndex
    ) {
      // Merge into modification
      merged.push({
        ...current,
        type: 'modification',
        suggestedText: next.suggestedText,
        explanation: current.explanation || next.explanation,
        confidence: Math.max(current.confidence || 0, next.confidence || 0),
      });
      i += 2; // Skip both changes
    } else {
      merged.push(current);
      i += 1;
    }
  }

  return merged;
}

/**
 * Determine change category based on AI suggestions
 */
function determineCategory(
  text: string,
  aiSuggestions?: Array<{ type: string; original_text: string; suggested_text: string }>
): ChangeCategory {
  if (!aiSuggestions) return 'style';

  // Find matching suggestion
  const match = aiSuggestions.find(
    s => s.original_text.includes(text) || s.suggested_text.includes(text)
  );

  if (match) {
    return match.type as ChangeCategory;
  }

  // Default categorization based on text characteristics
  if (/[,;:.]/.test(text)) return 'grammar';
  if (text.length < 3) return 'style';
  return 'clarity';
}

/**
 * Determine change severity
 */
function determineSeverity(text: string): ChangeSeverity {
  // Critical: Grammar errors, missing punctuation
  if (/^[A-Z]/.test(text) && text.length < 20) return 'critical';

  // Recommended: Style improvements, clarity
  if (text.length > 3 && text.length < 50) return 'recommended';

  // Optional: Minor style tweaks
  return 'optional';
}

/**
 * Find explanation from AI suggestions
 */
function findExplanation(
  text: string,
  aiSuggestions?: Array<{ original_text: string; suggested_text: string; explanation?: string }>
): string | undefined {
  if (!aiSuggestions) return undefined;

  const match = aiSuggestions.find(
    s => s.original_text.includes(text) || s.suggested_text.includes(text)
  );

  return match?.explanation;
}

/**
 * Find confidence from AI suggestions
 */
function findConfidence(
  text: string,
  aiSuggestions?: Array<{ original_text: string; suggested_text: string; confidence?: number }>
): number | undefined {
  if (!aiSuggestions) return undefined;

  const match = aiSuggestions.find(
    s => s.original_text.includes(text) || s.suggested_text.includes(text)
  );

  return match?.confidence;
}

/**
 * Apply accepted changes to original text
 */
export function applyChanges(
  originalText: string,
  changes: TextChange[],
  acceptedChangeIds: string[]
): string {
  let result = originalText;
  const acceptedChanges = changes
    .filter(c => acceptedChangeIds.includes(c.id))
    .sort((a, b) => b.startIndex - a.startIndex); // Apply in reverse order

  acceptedChanges.forEach(change => {
    if (change.type === 'deletion') {
      result = result.slice(0, change.startIndex) + result.slice(change.endIndex);
    } else if (change.type === 'addition') {
      result = result.slice(0, change.startIndex) + change.suggestedText + result.slice(change.startIndex);
    } else if (change.type === 'modification') {
      result = result.slice(0, change.startIndex) + change.suggestedText + result.slice(change.endIndex);
    }
  });

  return result;
}

/**
 * Get color class for change type
 */
export function getChangeColorClass(type: ChangeType): string {
  switch (type) {
    case 'addition':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'deletion':
      return 'bg-red-100 text-red-800 border-red-300 line-through';
    case 'modification':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'unchanged':
      return '';
  }
}

/**
 * Get color class for change category
 */
export function getCategoryColorClass(category: ChangeCategory): string {
  switch (category) {
    case 'grammar':
      return 'border-l-red-500';
    case 'style':
      return 'border-l-blue-500';
    case 'clarity':
      return 'border-l-purple-500';
    case 'bias':
      return 'border-l-yellow-500';
    case 'compliance':
      return 'border-l-green-500';
  }
}

/**
 * Get severity badge class
 */
export function getSeverityBadgeClass(severity: ChangeSeverity): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-700';
    case 'recommended':
      return 'bg-blue-100 text-blue-700';
    case 'optional':
      return 'bg-gray-100 text-gray-700';
  }
}
