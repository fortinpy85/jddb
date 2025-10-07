/**
 * AI Features Demo Page
 * Phase 3: Advanced AI Content Intelligence
 *
 * Demonstration of all AI features working together
 */

"use client";

import React, { useState } from "react";
import { useAISuggestions } from "@/hooks/useAISuggestions";
import {
  QualityDashboard,
  BiasDetector,
  AISuggestionsPanel,
  ContentGeneratorModal,
} from "@/components/ai";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkles, FileText, AlertTriangle, Target } from "lucide-react";

const SAMPLE_TEXT = `We are seeking a young, energetic salesman with perfect vision to join our team. He must be able to stand for long periods and be a native English speaker. Recent graduates preferred.

The position will be responsible for managing the sales team. Work is done in collaboration with stakeholders. The team is managed by the incumbent.

Requirements include:
- Must be physically fit
- Own transportation required
- Top-tier university degree
- Well-connected in the industry`;

const SAMPLE_SECTIONS = {
  general_accountability:
    "The Director will oversee strategic planning and implementation. This role provides leadership and guidance to the team, ensuring alignment with organizational goals and objectives.",
  organization_structure:
    "Reports to the Assistant Deputy Minister. Manages a team of 12 employees including 3 managers.",
  key_responsibilities:
    "Lead strategic planning initiatives. Manage departmental budget and resource allocation. Provide oversight and guidance to management team.",
  qualifications:
    "Master's degree in public administration or related field. 10+ years of progressive leadership experience in government.",
};

export default function AIDemo() {
  const [testText, setTestText] = useState(SAMPLE_TEXT);
  const [generatorOpen, setGeneratorOpen] = useState(false);
  const [generatorMode, setGeneratorMode] = useState<"complete" | "enhance">(
    "complete",
  );

  const {
    biasAnalysis,
    qualityScore,
    suggestions,
    isLoading,
    analyzeBias,
    calculateQuality,
    fetchSuggestions,
    acceptSuggestion,
    rejectSuggestion,
    clearAll,
  } = useAISuggestions();

  const handleAnalyze = async () => {
    await Promise.all([analyzeBias(testText), fetchSuggestions(testText)]);
  };

  const handleCalculateQuality = async () => {
    await calculateQuality(SAMPLE_SECTIONS);
  };

  const handleReplace = (original: string, replacement: string) => {
    setTestText((text) => text.replace(original, replacement));
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Sparkles className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-3xl font-bold">AI Features Demo</h2>
            <p className="text-gray-600">
              Phase 3: Advanced AI Content Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge className="bg-green-100 text-green-700">
            <FileText className="h-3 w-3 mr-1" />9 Endpoints Active
          </Badge>
          <Badge className="bg-blue-100 text-blue-700">
            <Target className="h-3 w-3 mr-1" />4 Components
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Input & Controls */}
        <div className="lg:col-span-2 space-y-4">
          {/* Test Text Input */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Test Content
              </h2>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setTestText(SAMPLE_TEXT)}
                >
                  Reset
                </Button>
                <Button size="sm" variant="outline" onClick={clearAll}>
                  Clear Results
                </Button>
              </div>
            </div>
            <Textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              className="min-h-[200px] font-mono text-sm"
              placeholder="Enter text to analyze..."
            />
            <div className="flex gap-2">
              <Button
                onClick={handleAnalyze}
                disabled={isLoading || testText.length < 10}
                className="flex-1"
              >
                {isLoading ? "Analyzing..." : "Analyze Bias & Suggestions"}
              </Button>
              <Button
                onClick={handleCalculateQuality}
                disabled={isLoading}
                variant="outline"
              >
                Quality Score
              </Button>
            </div>
          </Card>

          {/* Tabs for Different Views */}
          <Tabs defaultValue="bias" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="bias">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Bias Detection
              </TabsTrigger>
              <TabsTrigger value="suggestions">
                <Sparkles className="h-4 w-4 mr-2" />
                Suggestions
              </TabsTrigger>
              <TabsTrigger value="quality">
                <Target className="h-4 w-4 mr-2" />
                Quality
              </TabsTrigger>
            </TabsList>

            <TabsContent value="bias" className="mt-4">
              <BiasDetector
                text={testText}
                biasAnalysis={biasAnalysis}
                onReplace={handleReplace}
                enabled={true}
              />
            </TabsContent>

            <TabsContent value="suggestions" className="mt-4">
              <AISuggestionsPanel
                suggestions={suggestions}
                loading={isLoading}
                onAccept={(suggestion) => acceptSuggestion(suggestion.id)}
                onReject={(suggestion) => rejectSuggestion(suggestion.id)}
                className="h-[500px]"
              />
            </TabsContent>

            <TabsContent value="quality" className="mt-4">
              <QualityDashboard
                qualityScore={qualityScore}
                loading={isLoading}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Column - Quick Actions */}
        <div className="space-y-4">
          <Card className="p-4 space-y-3">
            <h2 className="font-semibold">Content Generation</h2>
            <div className="space-y-2">
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={() => {
                  setGeneratorMode("complete");
                  setGeneratorOpen(true);
                }}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Complete Section
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={() => {
                  setGeneratorMode("enhance");
                  setGeneratorOpen(true);
                }}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Enhance Content
              </Button>
            </div>
          </Card>

          {/* Stats */}
          {biasAnalysis && (
            <Card className="p-4 space-y-3">
              <h2 className="font-semibold">Analysis Results</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Bias Issues:</span>
                  <Badge
                    variant={biasAnalysis.bias_free ? "outline" : "destructive"}
                  >
                    {biasAnalysis.issues.length}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Inclusivity Score:</span>
                  <Badge>
                    {Math.round(biasAnalysis.inclusivity_score * 100)}%
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Suggestions:</span>
                  <Badge>{suggestions.length}</Badge>
                </div>
              </div>
            </Card>
          )}

          {qualityScore && (
            <Card className="p-4 space-y-3">
              <h2 className="font-semibold">Quality Metrics</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Overall:</span>
                  <Badge
                    className={`bg-${qualityScore.quality_color}-100 text-${qualityScore.quality_color}-700`}
                  >
                    {Math.round(qualityScore.overall_score)}/100
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Level:</span>
                  <Badge variant="outline">{qualityScore.quality_level}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Priority:</span>
                  <Badge>
                    {qualityScore.improvement_priority[0] || "None"}
                  </Badge>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Content Generator Modal */}
      <ContentGeneratorModal
        open={generatorOpen}
        onClose={() => setGeneratorOpen(false)}
        onInsert={(content) => setTestText(testText + "\n\n" + content)}
        mode={generatorMode}
        initialContent={testText}
        classification="EX-01"
        language="en"
      />
    </div>
  );
}
