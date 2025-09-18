"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useStore } from "@/lib/store";
import { apiClient } from "@/lib/api";
import type { JobDescription } from "@/lib/types";
import { ErrorBoundaryWrapper } from "@/components/ui/error-boundary";
import {
  Search,
  GitCompare,
  TrendingUp,
  BarChart3,
  Users,
  Target,
  Lightbulb,
  ArrowRight,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

interface ComparisonResult {
  comparison_id: string;
  jobs: {
    job1: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
    job2: {
      id: number;
      job_number: string;
      title: string;
      classification: string;
      language: string;
    };
  };
  similarity_analysis: {
    overall_similarity: number;
    similarity_level: string;
    metadata_comparison: {
      classification: {
        job1: string;
        job2: string;
        match: boolean;
      };
      language: {
        job1: string;
        job2: string;
        match: boolean;
      };
      title_similarity: number;
    };
    section_comparison: Array<{
      section_type: string;
      job1_content: string;
      job2_content: string;
      similarity_score: number;
      both_present: boolean;
      job1_only: boolean;
      job2_only: boolean;
    }>;
  };
  recommendations: string[];
}

interface JobComparisonProps {
  onJobSelect?: (job: JobDescription) => void;
}

function JobComparison({ onJobSelect }: JobComparisonProps) {
  const { jobs } = useStore();
  const [selectedJobA, setSelectedJobA] = useState<JobDescription | null>(null);
  const [selectedJobB, setSelectedJobB] = useState<JobDescription | null>(null);
  const [comparisonResult, setComparisonResult] =
    useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTermA, setSearchTermA] = useState("");
  const [searchTermB, setSearchTermB] = useState("");
  const [suggestedJobsB, setSuggestedJobsB] = useState<JobDescription[]>([]);

  // Filter jobs based on search terms
  const filteredJobsA = jobs.filter(
    (job) =>
      job.title.toLowerCase().includes(searchTermA.toLowerCase()) ||
      job.job_number.toLowerCase().includes(searchTermA.toLowerCase()) ||
      job.classification.toLowerCase().includes(searchTermA.toLowerCase()),
  );

  const filteredJobsB = jobs.filter(
    (job) =>
      job.title.toLowerCase().includes(searchTermB.toLowerCase()) ||
      job.job_number.toLowerCase().includes(searchTermB.toLowerCase()) ||
      job.classification.toLowerCase().includes(searchTermB.toLowerCase()),
  );

  // Load similar jobs when Job A is selected
  const loadSimilarJobs = async (jobId: number) => {
    try {
      const similarJobs = await apiClient.findSimilarJobs(jobId, 5);
      const similarJobDetails = similarJobs.similar_jobs
        .map((similarJob) => jobs.find((job) => job.id === similarJob.id))
        .filter(Boolean) as JobDescription[];
      setSuggestedJobsB(similarJobDetails);
    } catch (error) {
      console.error("Failed to load similar jobs:", error);
      setSuggestedJobsB([]);
    }
  };

  const handleJobASelect = (job: JobDescription | null) => {
    setSelectedJobA(job);
    setComparisonResult(null); // Clear previous results
    if (job) {
      loadSimilarJobs(job.id);
    } else {
      setSuggestedJobsB([]);
    }
  };

  const handleCompareJobs = async () => {
    if (!selectedJobA || !selectedJobB) {
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.compareJobs({
        job_a_id: selectedJobA.id,
        job_b_id: selectedJobB.id,
      });

      setComparisonResult(response);
    } catch (error) {
      console.error("Failed to compare jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return "text-green-600 bg-green-100";
    if (score >= 0.6) return "text-blue-600 bg-blue-100";
    if (score >= 0.4) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getMatchColor = (score: number) => {
    if (score >= 0.85) return "text-green-600 bg-green-100";
    if (score >= 0.7) return "text-blue-600 bg-blue-100";
    if (score >= 0.5) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <GitCompare className="w-6 h-6 mr-2" />
            Job Comparison Tool
          </h2>
          <p className="text-gray-600 mt-1">
            Compare two job positions using AI-powered semantic analysis
          </p>
        </div>
      </div>

      {/* Job Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job A Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Job A (Base Position)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search jobs by title, number, or classification..."
                value={searchTermA}
                onChange={(e) => setSearchTermA(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select
              value={selectedJobA?.id.toString() || ""}
              onValueChange={(value) => {
                const job = jobs.find((j) => j.id.toString() === value);
                handleJobASelect(job || null);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a job to compare from" />
              </SelectTrigger>
              <SelectContent>
                {filteredJobsA.slice(0, 20).map((job) => (
                  <SelectItem key={job.id} value={job.id.toString()}>
                    <div className="flex flex-col">
                      <span className="font-medium">{job.title}</span>
                      <span className="text-sm text-gray-500">
                        {job.job_number} • {job.classification}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedJobA && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-900">
                  {selectedJobA.title}
                </h4>
                <p className="text-sm text-blue-700">
                  {selectedJobA.job_number} • {selectedJobA.classification} •{" "}
                  {selectedJobA.language}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Job B Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Job B (Comparison Position)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search jobs by title, number, or classification..."
                value={searchTermB}
                onChange={(e) => setSearchTermB(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select
              value={selectedJobB?.id.toString() || ""}
              onValueChange={(value) => {
                const job = jobs.find((j) => j.id.toString() === value);
                setSelectedJobB(job || null);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a job to compare to" />
              </SelectTrigger>
              <SelectContent>
                {filteredJobsB.slice(0, 20).map((job) => (
                  <SelectItem key={job.id} value={job.id.toString()}>
                    <div className="flex flex-col">
                      <span className="font-medium">{job.title}</span>
                      <span className="text-sm text-gray-500">
                        {job.job_number} • {job.classification}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedJobB && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-semibold text-green-900">
                  {selectedJobB.title}
                </h4>
                <p className="text-sm text-green-700">
                  {selectedJobB.job_number} • {selectedJobB.classification} •{" "}
                  {selectedJobB.language}
                </p>
              </div>
            )}

            {/* Suggested Similar Jobs */}
            {selectedJobA && suggestedJobsB.length > 0 && !selectedJobB && (
              <div className="mt-4">
                <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <Target className="w-4 h-4 mr-2" />
                  Suggested Similar Jobs
                </h5>
                <div className="space-y-2">
                  {suggestedJobsB.slice(0, 3).map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelectedJobB(job)}
                    >
                      <div>
                        <p className="text-sm font-medium">{job.title}</p>
                        <p className="text-xs text-gray-500">
                          {job.job_number} • {job.classification}
                        </p>
                      </div>
                      <Button variant="outline" size="sm">
                        Select
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Compare Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleCompareJobs}
          disabled={!selectedJobA || !selectedJobB || loading}
          size="lg"
          className="px-8"
        >
          {loading ? (
            <>
              <div className="animate-spin w-4 h-4 mr-2 border-2 border-current border-t-transparent rounded-full" />
              Analyzing...
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4 mr-2" />
              Compare Jobs
            </>
          )}
        </Button>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="space-y-6">
          {/* Job Info Header */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <GitCompare className="w-5 h-5 mr-2" />
                Comparison Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">Job A</h4>
                  <p className="text-sm text-blue-700">
                    <strong>{comparisonResult.jobs.job1.title}</strong>
                  </p>
                  <p className="text-xs text-blue-600">
                    {comparisonResult.jobs.job1.job_number} •{" "}
                    {comparisonResult.jobs.job1.classification} •{" "}
                    {comparisonResult.jobs.job1.language}
                  </p>
                </div>
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="font-semibold text-green-900 mb-2">Job B</h4>
                  <p className="text-sm text-green-700">
                    <strong>{comparisonResult.jobs.job2.title}</strong>
                  </p>
                  <p className="text-xs text-green-600">
                    {comparisonResult.jobs.job2.job_number} •{" "}
                    {comparisonResult.jobs.job2.classification} •{" "}
                    {comparisonResult.jobs.job2.language}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="similarity" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="similarity">Similarity Analysis</TabsTrigger>
              <TabsTrigger value="metadata">Metadata Comparison</TabsTrigger>
            </TabsList>

            {/* Similarity Analysis */}
            <TabsContent value="similarity" className="space-y-4">
              {/* Overall Similarity */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Overall Similarity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <Badge
                        className={getSimilarityColor(
                          comparisonResult.similarity_analysis
                            .overall_similarity,
                        )}
                      >
                        {(
                          comparisonResult.similarity_analysis
                            .overall_similarity * 100
                        ).toFixed(1)}
                        %
                      </Badge>
                      <p className="text-sm text-gray-600 mt-2">
                        {comparisonResult.similarity_analysis.similarity_level}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">
                        {(
                          comparisonResult.similarity_analysis
                            .overall_similarity * 100
                        ).toFixed(0)}
                        %
                      </p>
                      <p className="text-sm text-gray-500">Match</p>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {comparisonResult.recommendations.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2 flex items-center">
                        <Lightbulb className="w-4 h-4 mr-2" />
                        Analysis Insights
                      </h4>
                      <ul className="text-blue-800 text-sm space-y-1">
                        {comparisonResult.recommendations.map(
                          (recommendation, index) => (
                            <li key={index}>• {recommendation}</li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Section Comparison */}
              {comparisonResult.similarity_analysis.section_comparison.length >
                0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <BarChart3 className="w-5 h-5 mr-2" />
                      Section-by-Section Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {comparisonResult.similarity_analysis.section_comparison.map(
                        (section, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium">
                                {section.section_type}
                              </h5>
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{
                                      width: `${section.similarity_score * 100}%`,
                                    }}
                                  />
                                </div>
                                <span className="text-sm font-semibold">
                                  {(section.similarity_score * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                              <div>
                                <p className="font-medium text-blue-700 mb-1">
                                  Job A Content:
                                </p>
                                <p className="text-gray-600 bg-blue-50 p-2 rounded">
                                  {section.job1_content ||
                                    "No content available"}
                                </p>
                              </div>
                              <div>
                                <p className="font-medium text-green-700 mb-1">
                                  Job B Content:
                                </p>
                                <p className="text-gray-600 bg-green-50 p-2 rounded">
                                  {section.job2_content ||
                                    "No content available"}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center space-x-4 mt-2 text-xs">
                              {section.both_present && (
                                <Badge
                                  variant="outline"
                                  className="text-green-600"
                                >
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Both Jobs
                                </Badge>
                              )}
                              {section.job1_only && (
                                <Badge
                                  variant="outline"
                                  className="text-blue-600"
                                >
                                  Job A Only
                                </Badge>
                              )}
                              {section.job2_only && (
                                <Badge
                                  variant="outline"
                                  className="text-green-600"
                                >
                                  Job B Only
                                </Badge>
                              )}
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Metadata Comparison */}
            <TabsContent value="metadata" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Users className="w-5 h-5 mr-2" />
                    Job Attributes Comparison
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Classification Comparison */}
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline">Classification</Badge>
                        <span className="text-sm">
                          {
                            comparisonResult.similarity_analysis
                              .metadata_comparison.classification.job1
                          }
                          {" vs "}
                          {
                            comparisonResult.similarity_analysis
                              .metadata_comparison.classification.job2
                          }
                        </span>
                      </div>
                      <div className="flex items-center">
                        {comparisonResult.similarity_analysis
                          .metadata_comparison.classification.match ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Match
                          </Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Different
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Language Comparison */}
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline">Language</Badge>
                        <span className="text-sm">
                          {
                            comparisonResult.similarity_analysis
                              .metadata_comparison.language.job1
                          }
                          {" vs "}
                          {
                            comparisonResult.similarity_analysis
                              .metadata_comparison.language.job2
                          }
                        </span>
                      </div>
                      <div className="flex items-center">
                        {comparisonResult.similarity_analysis
                          .metadata_comparison.language.match ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Match
                          </Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Different
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Title Similarity */}
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline">Title Similarity</Badge>
                        <span className="text-sm">
                          Based on common words and phrases
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${comparisonResult.similarity_analysis.metadata_comparison.title_similarity * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-semibold">
                          {(
                            comparisonResult.similarity_analysis
                              .metadata_comparison.title_similarity * 100
                          ).toFixed(0)}
                          %
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}

// Memoized component with error boundary
const MemoizedJobComparison = React.memo(JobComparison);

export default function JobComparisonWithErrorBoundary(
  props: JobComparisonProps,
) {
  return (
    <ErrorBoundaryWrapper>
      <MemoizedJobComparison {...props} />
    </ErrorBoundaryWrapper>
  );
}
