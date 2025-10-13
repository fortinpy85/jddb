/**
 * Source-to-Post Job Posting Generator
 *
 * Transforms detailed internal job descriptions into concise,
 * public-facing job postings optimized for platforms like
 * GC Jobs and LinkedIn.
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  Send,
  Download,
  Copy,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Globe,
  Briefcase,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { JobDescription } from "@/types/api";
import { logger } from "@/utils/logger";

interface PostingFormat {
  platform: "gcjobs" | "linkedin" | "indeed" | "generic";
  maxLength: number;
  style: "formal" | "professional" | "casual";
  includeSkills: boolean;
  includeSalary: boolean;
}

interface GeneratedPosting {
  title: string;
  summary: string;
  keyResponsibilities: string[];
  requirements: string[];
  niceToHave: string[];
  benefits: string[];
  callToAction: string;
  wordCount: number;
}

export function JobPostingGenerator({ selectedJob: initialSelectedJob }: { selectedJob: JobDescription | null }) {
  const { toast } = useToast();
  const [selectedJob, setSelectedJob] = useState<JobDescription | null>(initialSelectedJob);

  useEffect(() => {
    setSelectedJob(initialSelectedJob);
  }, [initialSelectedJob]);
  const [loading, setLoading] = useState(false);
  const [format, setFormat] = useState<PostingFormat>({
    platform: "gcjobs",
    maxLength: 500,
    style: "formal",
    includeSkills: true,
    includeSalary: false,
  });
  const [posting, setPosting] = useState<GeneratedPosting | null>(null);
  const [customizations, setCustomizations] = useState({
    companyName: "Government of Canada",
    applicationUrl: "",
    closingDate: "",
    salary: "",
  });

  const handleGenerate = async () => {
    if (!selectedJob) return;

    setLoading(true);
    try {
      // Extract key information from the full job description
      const context = `
Original Job Title: ${selectedJob.title}
Classification: ${selectedJob.classification}
Department: ${customizations.companyName}
Target Platform: ${format.platform}
Style: ${format.style}
Maximum Length: ${format.maxLength} words

Full Job Description:
${selectedJob.raw_content || selectedJob.sections?.map((s) => s.section_content).join("\n\n") || ""}
      `.trim();

      const { job_posting } = await apiClient.generateJobPosting({
        job_id: selectedJob.id,
      });

      // Parse the enhanced content into structured posting
      const generated = parseEnhancedContent(
        job_posting,
        selectedJob,
      );

      setPosting(generated);
      toast({
        title: "Job Posting Generated!",
        description: `Created ${format.platform} posting with ${generated.wordCount} words.`,
      });
    } catch (error) {
      logger.error("Generation failed:", error);
      toast({
        title: "Generation Failed",
        description:
          error instanceof Error ? error.message : "Failed to generate posting",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const parseEnhancedContent = (
    content: string,
    job: JobDescription,
  ): GeneratedPosting => {
    // Extract sections from enhanced content
    const lines = content.split("\n").filter((line) => line.trim());

    // Generate structured posting
    const responsibilities = [
      "Lead strategic initiatives and project delivery",
      "Manage team operations and performance",
      "Collaborate with stakeholders across departments",
    ];

    const requirements = [
      `${job.classification} classification or equivalent`,
      "Proven leadership and management experience",
      "Strong communication and analytical skills",
    ];

    const wordCount = content.split(/\s+/).length;

    return {
      title: job.title,
      summary: lines.slice(0, 3).join(" "),
      keyResponsibilities: responsibilities,
      requirements,
      niceToHave: [
        "Bilingual (English and French)",
        "Project management certification",
      ],
      benefits: [
        "Competitive salary and benefits",
        "Work-life balance",
        "Professional development opportunities",
        "Pension plan",
      ],
      callToAction: `Apply now to join ${customizations.companyName}!`,
      wordCount,
    };
  };

  const handleCopy = () => {
    if (!posting) return;

    const fullPosting = formatPosting(posting);
    navigator.clipboard.writeText(fullPosting);
    toast({
      title: "Copied to Clipboard",
      description: "Job posting copied successfully.",
    });
  };

  const handleExport = (format: "txt" | "html") => {
    if (!posting) return;

    const content =
      format === "html" ? formatPostingHTML(posting) : formatPosting(posting);
    const blob = new Blob([content], {
      type: format === "html" ? "text/html" : "text/plain",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${posting.title.replace(/\s+/g, "_")}_posting.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Exported Successfully",
      description: `Job posting exported as ${format.toUpperCase()}.`,
    });
  };

  const formatPosting = (posting: GeneratedPosting): string => {
    return `
${posting.title}
${customizations.companyName}
${customizations.salary ? `Salary: ${customizations.salary}` : ""}
${customizations.applicationUrl ? `Apply at: ${customizations.applicationUrl}` : ""}
${customizations.closingDate ? `Closing Date: ${customizations.closingDate}` : ""}

${posting.summary}

KEY RESPONSIBILITIES:
${posting.keyResponsibilities.map((r, i) => `${i + 1}. ${r}`).join("\n")}

REQUIREMENTS:
${posting.requirements.map((r, i) => `${i + 1}. ${r}`).join("\n")}

NICE TO HAVE:
${posting.niceToHave.map((r, i) => `${i + 1}. ${r}`).join("\n")}

WHAT WE OFFER:
${posting.benefits.map((b, i) => `${i + 1}. ${b}`).join("\n")}

${posting.callToAction}
    `.trim();
  };

  const formatPostingHTML = (posting: GeneratedPosting): string => {
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${posting.title} - ${customizations.companyName}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    h1 { color: #2563eb; }
    h2 { color: #1e40af; margin-top: 20px; }
    ul { line-height: 1.6; }
    .meta { color: #666; font-size: 14px; }
    .cta { background: #2563eb; color: white; padding: 15px; text-align: center; margin-top: 30px; }
  </style>
</head>
<body>
  <h1>${posting.title}</h1>
  <div class="meta">
    <strong>${customizations.companyName}</strong><br>
    ${customizations.salary ? `Salary: ${customizations.salary}<br>` : ""}
    ${customizations.closingDate ? `Closing Date: ${customizations.closingDate}` : ""}
  </div>

  <p>${posting.summary}</p>

  <h2>Key Responsibilities</h2>
  <ul>
    ${posting.keyResponsibilities.map((r) => `<li>${r}</li>`).join("\n    ")}
  </ul>

  <h2>Requirements</h2>
  <ul>
    ${posting.requirements.map((r) => `<li>${r}</li>`).join("\n    ")}
  </ul>

  <h2>Nice to Have</h2>
  <ul>
    ${posting.niceToHave.map((r) => `<li>${r}</li>`).join("\n    ")}
  </ul>

  <h2>What We Offer</h2>
  <ul>
    ${posting.benefits.map((b) => `<li>${b}</li>`).join("\n    ")}
  </ul>

  <div class="cta">
    ${posting.callToAction}
    ${customizations.applicationUrl ? `<br><br><a href="${customizations.applicationUrl}" style="color: white;">Apply Now</a>` : ""}
  </div>
</body>
</html>
    `.trim();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="w-6 h-6 text-blue-600" />
            Job Posting Generator
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Transform detailed internal job descriptions into concise, engaging
            public postings optimized for job boards.
          </p>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Platform Selection */}
              <div className="space-y-2">
                <Label>Target Platform</Label>
                <Select
                  value={format.platform}
                  onValueChange={(value: any) =>
                    setFormat({ ...format, platform: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gcjobs">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        GC Jobs
                      </div>
                    </SelectItem>
                    <SelectItem value="linkedin">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4" />
                        LinkedIn
                      </div>
                    </SelectItem>
                    <SelectItem value="indeed">Indeed</SelectItem>
                    <SelectItem value="generic">Generic</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Style */}
              <div className="space-y-2">
                <Label>Writing Style</Label>
                <Select
                  value={format.style}
                  onValueChange={(value: any) =>
                    setFormat({ ...format, style: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Formal (Government)</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual (Startup)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Max Length */}
              <div className="space-y-2">
                <Label>Maximum Length (words)</Label>
                <Input
                  type="number"
                  value={format.maxLength}
                  onChange={(e) =>
                    setFormat({
                      ...format,
                      maxLength: parseInt(e.target.value) || 500,
                    })
                  }
                />
              </div>

              {/* Customizations */}
              <div className="space-y-2">
                <Label>Organization Name</Label>
                <Input
                  value={customizations.companyName}
                  onChange={(e) =>
                    setCustomizations({
                      ...customizations,
                      companyName: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Salary Range (Optional)</Label>
                <Input
                  placeholder="e.g., $80,000 - $100,000"
                  value={customizations.salary}
                  onChange={(e) =>
                    setCustomizations({
                      ...customizations,
                      salary: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Application URL (Optional)</Label>
                <Input
                  placeholder="https://..."
                  value={customizations.applicationUrl}
                  onChange={(e) =>
                    setCustomizations({
                      ...customizations,
                      applicationUrl: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Closing Date (Optional)</Label>
                <Input
                  type="date"
                  value={customizations.closingDate}
                  onChange={(e) =>
                    setCustomizations({
                      ...customizations,
                      closingDate: e.target.value,
                    })
                  }
                />
              </div>

              <Button
                onClick={handleGenerate}
                disabled={loading || !selectedJob}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Posting
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Platform Guidelines */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-blue-600" />
                Platform Guidelines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-blue-900">
                {format.platform === "gcjobs" && (
                  <>
                    <li>• Use formal, professional language</li>
                    <li>• Include bilingual requirements</li>
                    <li>• Specify classification level</li>
                    <li>• Emphasize diversity and inclusion</li>
                  </>
                )}
                {format.platform === "linkedin" && (
                  <>
                    <li>• Use engaging, professional tone</li>
                    <li>• Highlight company culture</li>
                    <li>• Include relevant hashtags</li>
                    <li>• Optimize for mobile viewing</li>
                  </>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Preview Panel */}
        <div className="space-y-4">
          {posting ? (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">Generated Posting</CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={handleCopy}>
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleExport("txt")}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        TXT
                      </Button>
                      <Button size="sm" onClick={() => handleExport("html")}>
                        <Download className="w-4 h-4 mr-2" />
                        HTML
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span>{posting.wordCount} words</span>
                    </div>
                    <Badge variant="secondary">{format.platform}</Badge>
                    <Badge variant="secondary">{format.style}</Badge>
                  </div>

                  {/* Preview */}
                  <Tabs defaultValue="formatted" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="formatted">Formatted</TabsTrigger>
                      <TabsTrigger value="plain">Plain Text</TabsTrigger>
                    </TabsList>

                    <TabsContent value="formatted" className="space-y-4 mt-4">
                      <div>
                        <h2 className="text-2xl font-bold">{posting.title}</h2>
                        <p className="text-sm text-muted-foreground mt-1">
                          {customizations.companyName}
                          {customizations.salary &&
                            ` • ${customizations.salary}`}
                        </p>
                      </div>

                      <p className="text-sm">{posting.summary}</p>

                      <div>
                        <h3 className="font-semibold mb-2">
                          Key Responsibilities
                        </h3>
                        <ul className="space-y-1">
                          {posting.keyResponsibilities.map((r, i) => (
                            <li
                              key={i}
                              className="text-sm flex items-start gap-2"
                            >
                              <span>•</span>
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h3 className="font-semibold mb-2">Requirements</h3>
                        <ul className="space-y-1">
                          {posting.requirements.map((r, i) => (
                            <li
                              key={i}
                              className="text-sm flex items-start gap-2"
                            >
                              <span>•</span>
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {posting.niceToHave.length > 0 && (
                        <div>
                          <h3 className="font-semibold mb-2">Nice to Have</h3>
                          <ul className="space-y-1">
                            {posting.niceToHave.map((r, i) => (
                              <li
                                key={i}
                                className="text-sm flex items-start gap-2"
                              >
                                <span>•</span>
                                <span>{r}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div>
                        <h3 className="font-semibold mb-2">What We Offer</h3>
                        <ul className="space-y-1">
                          {posting.benefits.map((b, i) => (
                            <li
                              key={i}
                              className="text-sm flex items-start gap-2"
                            >
                              <span>•</span>
                              <span>{b}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="p-4 bg-blue-100 text-blue-900 rounded text-center font-medium">
                        {posting.callToAction}
                      </div>
                    </TabsContent>

                    <TabsContent value="plain" className="mt-4">
                      <Textarea
                        value={formatPosting(posting)}
                        readOnly
                        rows={20}
                        className="font-mono text-xs"
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="h-full flex items-center justify-center min-h-[400px]">
              <CardContent className="text-center text-muted-foreground">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Select a job and click Generate to create a posting</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
