import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Search,
  BookOpen,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Star,
  TrendingUp,
  Languages,
  Zap,
  Clock
} from 'lucide-react';

interface TranslationMatch {
  id: number;
  source_text: string;
  target_text: string;
  similarity_score: number;
  quality_score?: number;
  confidence_score?: number;
  usage_count: number;
  domain?: string;
  subdomain?: string;
  match_type: 'exact' | 'fuzzy';
  confidence: number;
  last_used?: string;
  created_at: string;
}

interface TranslationMemoryPanelProps {
  sourceLanguage: string;
  targetLanguage: string;
  onMatchSelect?: (match: TranslationMatch) => void;
  className?: string;
}

// Mock translation memory data
const mockMatches: TranslationMatch[] = [
  {
    id: 1,
    source_text: "Responsible for strategic planning and policy development",
    target_text: "Responsable de la planification stratégique et de l'élaboration des politiques",
    similarity_score: 0.95,
    quality_score: 0.92,
    confidence_score: 0.89,
    usage_count: 15,
    domain: 'government',
    subdomain: 'job_descriptions',
    match_type: 'exact',
    confidence: 1.0,
    last_used: '2025-09-19T14:30:00Z',
    created_at: '2025-01-15T10:00:00Z'
  },
  {
    id: 2,
    source_text: "Strategic planning and policy formulation",
    target_text: "Planification stratégique et formulation de politiques",
    similarity_score: 0.87,
    quality_score: 0.85,
    confidence_score: 0.82,
    usage_count: 8,
    domain: 'government',
    subdomain: 'job_descriptions',
    match_type: 'fuzzy',
    confidence: 0.87,
    last_used: '2025-09-18T16:45:00Z',
    created_at: '2025-02-03T09:30:00Z'
  },
  {
    id: 3,
    source_text: "Develop and implement strategic initiatives",
    target_text: "Développer et mettre en œuvre des initiatives stratégiques",
    similarity_score: 0.82,
    quality_score: 0.88,
    confidence_score: 0.85,
    usage_count: 12,
    domain: 'government',
    subdomain: 'job_descriptions',
    match_type: 'fuzzy',
    confidence: 0.82,
    last_used: '2025-09-17T11:20:00Z',
    created_at: '2025-01-28T14:15:00Z'
  }
];

export const TranslationMemoryPanel: React.FC<TranslationMemoryPanelProps> = ({
  sourceLanguage,
  targetLanguage,
  onMatchSelect,
  className
}) => {
  const [matches, setMatches] = useState<TranslationMatch[]>(mockMatches);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<number | null>(null);

  const filteredMatches = matches.filter(match =>
    match.source_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    match.target_text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMatchSelect = (match: TranslationMatch) => {
    setSelectedMatch(match.id);
    onMatchSelect?.(match);
  };

  const handleApproval = (matchId: number, approved: boolean) => {
    // Update match with user feedback
    console.log(`Match ${matchId} ${approved ? 'approved' : 'rejected'}`);
  };

  const handleCopyTranslation = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatLastUsed = (dateString?: string) => {
    if (!dateString) return 'Never used';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getMatchTypeColor = (matchType: string, confidence: number) => {
    if (matchType === 'exact') return 'bg-green-500';
    if (confidence > 0.9) return 'bg-blue-500';
    if (confidence > 0.8) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  const getQualityStars = (score?: number) => {
    if (!score) return null;
    const stars = Math.round(score * 5);
    return (
      <div className="flex items-center gap-1">
        {Array.from({ length: 5 }, (_, i) => (
          <Star
            key={i}
            className={`w-3 h-3 ${
              i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <Card className={`flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Translation Memory
          <Badge variant="outline" className="ml-auto">
            {sourceLanguage.toUpperCase()} → {targetLanguage.toUpperCase()}
          </Badge>
        </CardTitle>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search translations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-8"
          />
        </div>

        {/* Statistics */}
        <div className="flex items-center gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {matches.length} entries
          </div>
          <div className="flex items-center gap-1">
            <Languages className="w-3 h-3" />
            {matches.filter(m => m.match_type === 'exact').length} exact
          </div>
          <div className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            {Math.round(matches.reduce((sum, m) => sum + (m.quality_score || 0), 0) / matches.length * 100)}% avg
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 flex-1 flex flex-col">
        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Searching translation memory...</p>
            </div>
          ) : filteredMatches.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No translation matches found</p>
              {searchQuery && (
                <p className="text-xs">Try different search terms</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredMatches.map((match) => (
                <TranslationMatchCard
                  key={match.id}
                  match={match}
                  isSelected={selectedMatch === match.id}
                  onSelect={() => handleMatchSelect(match)}
                  onApproval={(approved) => handleApproval(match.id, approved)}
                  onCopy={() => handleCopyTranslation(match.target_text)}
                  formatLastUsed={formatLastUsed}
                  getMatchTypeColor={getMatchTypeColor}
                  getQualityStars={getQualityStars}
                />
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Quick actions */}
        <Separator className="my-3" />
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Last updated: {formatLastUsed(matches[0]?.last_used)}
          </div>
          <Button variant="ghost" size="sm" className="h-6 text-xs">
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const TranslationMatchCard: React.FC<{
  match: TranslationMatch;
  isSelected: boolean;
  onSelect: () => void;
  onApproval: (approved: boolean) => void;
  onCopy: () => void;
  formatLastUsed: (date?: string) => string;
  getMatchTypeColor: (type: string, confidence: number) => string;
  getQualityStars: (score?: number) => React.ReactNode;
}> = ({
  match,
  isSelected,
  onSelect,
  onApproval,
  onCopy,
  formatLastUsed,
  getMatchTypeColor,
  getQualityStars
}) => (
  <div
    className={`border rounded-lg p-3 space-y-2 cursor-pointer transition-all hover:shadow-md ${
      isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
    }`}
    onClick={onSelect}
  >
    {/* Header */}
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${getMatchTypeColor(match.match_type, match.confidence)}`}
        />
        <Badge variant={match.match_type === 'exact' ? 'default' : 'secondary'} className="text-xs">
          {match.match_type === 'exact' ? 'Exact' : `${Math.round(match.confidence * 100)}%`}
        </Badge>
        {match.domain && (
          <Badge variant="outline" className="text-xs">
            {match.domain}
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-1">
        {getQualityStars(match.quality_score)}
      </div>
    </div>

    {/* Source Text */}
    <div className="space-y-1">
      <div className="text-xs text-gray-500">Source:</div>
      <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
        {match.source_text}
      </div>
    </div>

    {/* Target Text */}
    <div className="space-y-1">
      <div className="text-xs text-gray-500">Translation:</div>
      <div className="text-sm text-gray-900 bg-blue-50 p-2 rounded">
        {match.target_text}
      </div>
    </div>

    {/* Metadata */}
    <div className="flex items-center justify-between text-xs text-gray-500">
      <div className="flex items-center gap-3">
        <span>Used {match.usage_count} times</span>
        <span>Last: {formatLastUsed(match.last_used)}</span>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={(e) => {
            e.stopPropagation();
            onCopy();
          }}
        >
          <Copy className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-green-600 hover:text-green-700"
          onClick={(e) => {
            e.stopPropagation();
            onApproval(true);
          }}
        >
          <ThumbsUp className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
          onClick={(e) => {
            e.stopPropagation();
            onApproval(false);
          }}
        >
          <ThumbsDown className="w-3 h-3" />
        </Button>
      </div>
    </div>
  </div>
);