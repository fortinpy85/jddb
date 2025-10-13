"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  AlertCircle,
  Info,
  CheckCircle2,
  Target,
  BarChart3,
  Sparkles,
  Brain,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { JobDescription } from "@/lib/types";
import { logger } from "@/utils/logger";

interface PredictionResult {
  applicationVolume: {
    predicted: number;
    confidence: number;
    range: { low: number; high: number };
    factors: string[];
    trend: "high" | "medium" | "low";
  };
  timeToFill: {
    predictedDays: number;
    confidence: number;
    range: { low: number; high: number };
    factors: string[];
    category: "fast" | "average" | "slow";
  };
  contentQuality: {
    score: number;
    strengths: string[];
    improvements: string[];
  };
  competitiveness: {
    score: number;
    marketComparison: string;
    recommendations: string[];
  };
  skillDemand: {
    highDemand: string[];
    lowDemand: string[];
    marketTrends: Array<{
      skill: string;
      trend: "rising" | "stable" | "declining";
    }>;
  };
}

interface AnalyticsInput {
  jobId?: number;
  jobTitle?: string;
  classification?: string;
  skills?: string[];
  location?: string;
  salaryRange?: { min?: number; max?: number };
  content?: string;
}

export function PredictiveAnalytics() {
  const [input, setInput] = useState<AnalyticsInput>({});
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [customSkills, setCustomSkills] = useState<string>("");
  const { toast } = useToast();

  // Fetch available jobs for selection
  useEffect(() => {
    const loadJobs = async () => {
      try {
        const response = await apiClient.getJobs({ limit: 100 });
        setJobs(response.jobs || []);
      } catch (error) {
        logger.error("Failed to load jobs", error);
      }
    };
    loadJobs();
  }, []);

  // Load selected job details
  const handleJobSelect = async (jobId: string) => {
    setSelectedJobId(jobId);
    if (!jobId) {
      setInput({});
      return;
    }

    try {
      const job = await apiClient.getJob(parseInt(jobId));
      const skills = job.skills?.map((s) => s.name) || [];

      setInput({
        jobId: job.id,
        jobTitle: job.title || "",
        classification: job.classification || "",
        skills: skills,
        location: job.metadata?.location || "",
        content: job.sections?.map((s) => s.section_content).join("\n\n") || "",
      });
    } catch {
      toast({
        title: "Error loading job",
        description: "Failed to load job details",
        variant: "destructive",
      });
    }
  };

  // Run predictive analysis
  const runPrediction = async () => {
    if (!input.jobTitle && !input.jobId) {
      toast({
        title: "Missing information",
        description: "Please select a job or enter job details",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const result = await apiClient.runPredictiveAnalysis({
        job_id: input.jobId!,  // Non-null assertion since we check !input.jobId above
      });

      setPrediction(result.analysis);
      toast({
        title: "Analysis complete",
        description: "Predictions generated successfully",
      });
    } catch (error) {
      toast({
        title: "Analysis failed",
        description:
          error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Add custom skills
  const handleAddSkills = () => {
    if (customSkills.trim()) {
      const skills = customSkills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      setInput({
        ...input,
        skills: [...(input.skills || []), ...skills],
      });
      setCustomSkills("");
    }
  };

  // Remove skill
  const removeSkill = (skill: string) => {
    setInput({
      ...input,
      skills: input.skills?.filter((s) => s !== skill) || [],
    });
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Predictive Content Analytics
          </CardTitle>
          <CardDescription>
            Analyze job descriptions to predict application volume,
            time-to-fill, and content effectiveness
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs defaultValue="existing">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="existing">Existing Job</TabsTrigger>
              <TabsTrigger value="manual">Manual Input</TabsTrigger>
            </TabsList>

            <TabsContent value="existing" className="space-y-4">
              <div className="space-y-2">
                <Label>Select Job Description</Label>
                <Select value={selectedJobId} onValueChange={handleJobSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a job to analyze" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobs.map((job) => (
                      <SelectItem key={job.id} value={job.id.toString()}>
                        {job.title || `Job ${job.id}`} -{" "}
                        {job.classification || "N/A"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>

            <TabsContent value="manual" className="space-y-4">
              <div className="grid gap-4">
                <div className="space-y-2">
                  <Label>Job Title</Label>
                  <Input
                    placeholder="e.g., Senior Software Developer"
                    value={input.jobTitle || ""}
                    onChange={(e) =>
                      setInput({ ...input, jobTitle: e.target.value })
                    }
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Classification</Label>
                    <Input
                      placeholder="e.g., IT-04"
                      value={input.classification || ""}
                      onChange={(e) =>
                        setInput({ ...input, classification: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Location</Label>
                    <Input
                      placeholder="e.g., Ottawa, ON"
                      value={input.location || ""}
                      onChange={(e) =>
                        setInput({ ...input, location: e.target.value })
                      }
                    />
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {/* Skills Section */}
          <div className="space-y-3">
            <Label>Required Skills</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Enter skills (comma-separated)"
                value={customSkills}
                onChange={(e) => setCustomSkills(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddSkills()}
              />
              <Button onClick={handleAddSkills} variant="outline">
                Add
              </Button>
            </div>
            {input.skills && input.skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {input.skills.map((skill) => (
                  <Badge key={skill} variant="secondary" className="gap-1">
                    {skill}
                    <button
                      onClick={() => removeSkill(skill)}
                      className="ml-1 hover:text-destructive"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <Button
            onClick={runPrediction}
            disabled={isLoading || (!input.jobTitle && !input.jobId)}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Target className="w-4 h-4 mr-2" />
                Run Predictive Analysis
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results Section */}
      {prediction && (
        <div className="space-y-6">
          {/* Application Volume Prediction */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Application Volume Prediction
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Predicted Applications
                  </p>
                  <p className="text-4xl font-bold">
                    {prediction.applicationVolume.predicted}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Range: {prediction.applicationVolume.range.low} -{" "}
                    {prediction.applicationVolume.range.high}
                  </p>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      prediction.applicationVolume.trend === "high"
                        ? "default"
                        : prediction.applicationVolume.trend === "medium"
                          ? "secondary"
                          : "outline"
                    }
                    className="gap-1"
                  >
                    {prediction.applicationVolume.trend === "high" ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {prediction.applicationVolume.trend.toUpperCase()}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    {prediction.applicationVolume.confidence.toFixed(0)}%
                    confidence
                  </p>
                  <Progress
                    value={prediction.applicationVolume.confidence}
                    className="mt-1 w-24"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium">Key Factors:</p>
                <ul className="space-y-1">
                  {prediction.applicationVolume.factors.map((factor, i) => (
                    <li
                      key={i}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Time to Fill Prediction */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Time-to-Fill Prediction
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Estimated Days to Fill
                  </p>
                  <p className="text-4xl font-bold">
                    {prediction.timeToFill.predictedDays}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Range: {prediction.timeToFill.range.low} -{" "}
                    {prediction.timeToFill.range.high} days
                  </p>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      prediction.timeToFill.category === "fast"
                        ? "default"
                        : prediction.timeToFill.category === "average"
                          ? "secondary"
                          : "outline"
                    }
                  >
                    {prediction.timeToFill.category.toUpperCase()}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    {prediction.timeToFill.confidence.toFixed(0)}% confidence
                  </p>
                  <Progress
                    value={prediction.timeToFill.confidence}
                    className="mt-1 w-24"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium">Influencing Factors:</p>
                <ul className="space-y-1">
                  {prediction.timeToFill.factors.map((factor, i) => (
                    <li
                      key={i}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <Info className="w-4 h-4 mt-0.5 text-blue-500 flex-shrink-0" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Content Quality & Competitiveness */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Content Quality
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Quality Score</span>
                    <span className="text-2xl font-bold">
                      {prediction.contentQuality.score}/100
                    </span>
                  </div>
                  <Progress value={prediction.contentQuality.score} />
                </div>
                {prediction.contentQuality.strengths.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2 flex items-center gap-2">
                      <ThumbsUp className="w-4 h-4 text-green-500" />
                      Strengths
                    </p>
                    <ul className="space-y-1">
                      {prediction.contentQuality.strengths.map(
                        (strength, i) => (
                          <li key={i} className="text-sm text-muted-foreground">
                            • {strength}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
                {prediction.contentQuality.improvements.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2 flex items-center gap-2">
                      <ThumbsDown className="w-4 h-4 text-orange-500" />
                      Improvements
                    </p>
                    <ul className="space-y-1">
                      {prediction.contentQuality.improvements.map(
                        (improvement, i) => (
                          <li key={i} className="text-sm text-muted-foreground">
                            • {improvement}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Market Competitiveness
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">
                      Competitiveness Score
                    </span>
                    <span className="text-2xl font-bold">
                      {prediction.competitiveness.score}/100
                    </span>
                  </div>
                  <Progress value={prediction.competitiveness.score} />
                </div>
                <Alert>
                  <AlertCircle className="w-4 h-4" />
                  <AlertTitle>Market Comparison</AlertTitle>
                  <AlertDescription>
                    {prediction.competitiveness.marketComparison}
                  </AlertDescription>
                </Alert>
                <div>
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  <ul className="space-y-1">
                    {prediction.competitiveness.recommendations.map(
                      (rec, i) => (
                        <li key={i} className="text-sm text-muted-foreground">
                          • {rec}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Skill Demand Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Skill Demand Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-6">
                {prediction.skillDemand.highDemand.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-3 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      High-Demand Skills
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {prediction.skillDemand.highDemand.map((skill) => (
                        <Badge
                          key={skill}
                          variant="default"
                          className="bg-green-500"
                        >
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {prediction.skillDemand.lowDemand.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-3 flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-gray-500" />
                      Standard Skills
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {prediction.skillDemand.lowDemand.map((skill) => (
                        <Badge key={skill} variant="secondary">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {prediction.skillDemand.marketTrends.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-3">Market Trends</p>
                  <div className="space-y-2">
                    {prediction.skillDemand.marketTrends.map((trend) => (
                      <div
                        key={trend.skill}
                        className="flex items-center justify-between p-2 rounded bg-muted"
                      >
                        <span className="text-sm font-medium">
                          {trend.skill}
                        </span>
                        <Badge
                          variant={
                            trend.trend === "rising"
                              ? "default"
                              : trend.trend === "stable"
                                ? "secondary"
                                : "outline"
                          }
                          className="gap-1"
                        >
                          {trend.trend === "rising" && (
                            <TrendingUp className="w-3 h-3" />
                          )}
                          {trend.trend === "declining" && (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {trend.trend}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default PredictiveAnalytics;
