/**
 * Content Generator Modal
 * Phase 3: Advanced AI Content Intelligence
 *
 * AI-powered section creation and content enhancement
 */

import React, { useState } from 'react';
import { api } from '@/lib/api';
import type {
  SectionType,
  EnhancementType,
  SECTION_NAMES,
  ENHANCEMENT_LABELS,
} from '@/types/ai';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Sparkles, Loader2, Copy, Check, AlertCircle, RefreshCw } from 'lucide-react';

interface ContentGeneratorModalProps {
  open: boolean;
  onClose: () => void;
  onInsert?: (content: string) => void;
  mode: 'complete' | 'enhance';
  initialContent?: string;
  classification?: string;
  language?: 'en' | 'fr';
}

const SECTION_OPTIONS: Array<{ value: SectionType; label: string }> = [
  { value: 'general_accountability', label: 'General Accountability' },
  { value: 'organization_structure', label: 'Organization Structure' },
  { value: 'key_responsibilities', label: 'Key Responsibilities' },
  { value: 'qualifications', label: 'Qualifications' },
  { value: 'nature_and_scope', label: 'Nature and Scope' },
];

const ENHANCEMENT_OPTIONS: Array<{ value: EnhancementType; label: string; description: string }> = [
  { value: 'clarity', label: 'Clarity', description: 'Simplify complex sentences' },
  { value: 'active_voice', label: 'Active Voice', description: 'Convert passive to active voice' },
  { value: 'conciseness', label: 'Conciseness', description: 'Remove redundancy' },
  { value: 'formality', label: 'Formality', description: 'Adjust tone for government standards' },
  { value: 'bias_free', label: 'Bias-Free', description: 'Remove biased language' },
];

/**
 * Content Generator Modal - Main Component
 */
export function ContentGeneratorModal({
  open,
  onClose,
  onInsert,
  mode,
  initialContent = '',
  classification = 'EX-01',
  language = 'en',
}: ContentGeneratorModalProps) {
  const [content, setContent] = useState(initialContent);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);
  const [changes, setChanges] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Section completion state
  const [sectionType, setSectionType] = useState<SectionType>('general_accountability');
  const [department, setDepartment] = useState('');
  const [reportingTo, setReportingTo] = useState('');

  // Enhancement state
  const [selectedEnhancements, setSelectedEnhancements] = useState<EnhancementType[]>([
    'clarity',
    'active_voice',
  ]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setGeneratedContent(null);
    setChanges([]);
    setConfidence(null);

    try {
      if (mode === 'complete') {
        const result = await api.completeSection({
          section_type: sectionType,
          partial_content: content,
          classification,
          language,
          context: {
            department: department || undefined,
            reporting_to: reportingTo || undefined,
          },
        });

        setGeneratedContent(result.completed_content);
        setConfidence(result.confidence);
      } else {
        const result = await api.enhanceContent({
          text: content,
          enhancement_types: selectedEnhancements,
          language,
        });

        setGeneratedContent(result.enhanced_text);
        setChanges(result.changes);
      }
    } catch (err: any) {
      console.error('Content generation failed:', err);
      setError(err.message || 'Failed to generate content');
    } finally {
      setLoading(false);
    }
  };

  const handleInsert = () => {
    if (generatedContent && onInsert) {
      onInsert(generatedContent);
      onClose();
    }
  };

  const handleCopy = async () => {
    if (generatedContent) {
      await navigator.clipboard.writeText(generatedContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const toggleEnhancement = (type: EnhancementType) => {
    setSelectedEnhancements((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            {mode === 'complete' ? 'AI Section Completion' : 'AI Content Enhancement'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'complete'
              ? 'Let AI complete your section based on context and best practices'
              : 'Enhance your content for clarity, active voice, and professionalism'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Configuration */}
          <div className="grid grid-cols-2 gap-4">
            {mode === 'complete' ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="section-type">Section Type</Label>
                  <Select
                    value={sectionType}
                    onValueChange={(value) => setSectionType(value as SectionType)}
                  >
                    <SelectTrigger id="section-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SECTION_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="classification">Classification</Label>
                  <input
                    id="classification"
                    type="text"
                    value={classification}
                    disabled
                    className="w-full px-3 py-2 border rounded-md bg-gray-50"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">Department (Optional)</Label>
                  <input
                    id="department"
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g., Finance, HR"
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reporting-to">Reports To (Optional)</Label>
                  <input
                    id="reporting-to"
                    type="text"
                    value={reportingTo}
                    onChange={(e) => setReportingTo(e.target.value)}
                    placeholder="e.g., CFO, Director"
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </>
            ) : (
              <div className="col-span-2 space-y-2">
                <Label>Enhancement Types</Label>
                <div className="flex flex-wrap gap-2">
                  {ENHANCEMENT_OPTIONS.map((option) => (
                    <Badge
                      key={option.value}
                      variant={selectedEnhancements.includes(option.value) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => toggleEnhancement(option.value)}
                    >
                      {option.label}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Input Content */}
          <div className="space-y-2">
            <Label htmlFor="content">
              {mode === 'complete' ? 'Partial Content' : 'Original Content'}
            </Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={
                mode === 'complete'
                  ? 'Start typing your content and AI will complete it...'
                  : 'Paste your content here to enhance it...'
              }
              className="min-h-[120px] font-mono text-sm"
            />
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={loading || content.length < 10}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate {mode === 'complete' ? 'Completion' : 'Enhancement'}
              </>
            )}
          </Button>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Generated Content */}
          {generatedContent && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Generated Content</Label>
                <div className="flex items-center gap-2">
                  {confidence !== null && (
                    <Badge variant="outline">
                      {Math.round(confidence * 100)}% confidence
                    </Badge>
                  )}
                  <Button size="sm" variant="outline" onClick={handleCopy}>
                    {copied ? (
                      <>
                        <Check className="mr-1 h-3 w-3" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="mr-1 h-3 w-3" />
                        Copy
                      </>
                    )}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleGenerate}>
                    <RefreshCw className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <Card className="p-4 bg-green-50 border-green-200">
                <div className="whitespace-pre-wrap font-mono text-sm text-gray-900">
                  {generatedContent}
                </div>
              </Card>

              {/* Changes */}
              {changes.length > 0 && (
                <div className="space-y-2">
                  <Label>Changes Made</Label>
                  <ul className="space-y-1 text-sm">
                    {changes.map((change, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-0.5">•</span>
                        <span className="text-gray-700">{change}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Diff View */}
              {mode === 'enhance' && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs text-gray-500">Before</Label>
                    <Card className="p-3 bg-red-50 border-red-200">
                      <div className="whitespace-pre-wrap font-mono text-xs text-gray-700">
                        {content}
                      </div>
                    </Card>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-gray-500">After</Label>
                    <Card className="p-3 bg-green-50 border-green-200">
                      <div className="whitespace-pre-wrap font-mono text-xs text-gray-700">
                        {generatedContent}
                      </div>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          {generatedContent && onInsert && (
            <Button onClick={handleInsert}>
              Insert Content
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
