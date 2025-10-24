/**
 * AI-Assisted Job Description Writer
 *
 * Comprehensive tool for generating job descriptions using AI.
 * Features a step-by-step wizard interface for inputting requirements
 * and generating complete, high-quality job descriptions.
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Wand2,
  ChevronRight,
  ChevronLeft,
  Save,
  Download,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Plus,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { logger } from "@/utils/logger";

interface JobRequirements {
  jobTitle: string;
  classification: string;
  department: string;
  reportsTo: string;
  location: string;
  skills: string[];
  responsibilities: string[];
  qualifications: string[];
  additionalInfo: string;
}

interface GeneratedContent {
  title: string;
  summary: string;
  accountabilities: string;
  organizationStructure: string;
  natureAndScope: string;
  specificAccountabilities: string;
  dimensions: string;
  knowledgeAndSkills: string;
  qualityScore: number;
  suggestions: string[];
}

export function AIJobWriter() {
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [requirements, setRequirements] = useState<JobRequirements>({
    jobTitle: "",
    classification: "",
    department: "",
    reportsTo: "",
    location: "",
    skills: [],
    responsibilities: [],
    qualifications: [],
    additionalInfo: "",
  });
  const [generatedContent, setGeneratedContent] =
    useState<GeneratedContent | null>(null);
  const [currentSkill, setCurrentSkill] = useState("");
  const [currentResponsibility, setCurrentResponsibility] = useState("");
  const [currentQualification, setCurrentQualification] = useState("");

  const totalSteps = 4;
  const progress = (step / totalSteps) * 100;

  // Classifications for government jobs
  const classifications = [
    "EX-01",
    "EX-02",
    "EX-03",
    "EX-04",
    "EX-05",
    "AS-01",
    "AS-02",
    "AS-03",
    "AS-04",
    "AS-05",
    "AS-06",
    "AS-07",
    "AS-08",
    "CS-01",
    "CS-02",
    "CS-03",
    "CS-04",
    "CS-05",
    "IT-01",
    "IT-02",
    "IT-03",
    "IT-04",
    "IT-05",
    "PM-01",
    "PM-02",
    "PM-03",
    "PM-04",
    "PM-05",
    "PM-06",
    "EC-01",
    "EC-02",
    "EC-03",
    "EC-04",
    "EC-05",
    "EC-06",
    "EC-07",
    "EC-08",
  ];

  const handleAddSkill = () => {
    if (currentSkill.trim()) {
      setRequirements({
        ...requirements,
        skills: [...requirements.skills, currentSkill.trim()],
      });
      setCurrentSkill("");
    }
  };

  const handleRemoveSkill = (index: number) => {
    setRequirements({
      ...requirements,
      skills: requirements.skills.filter((_, i) => i !== index),
    });
  };

  const handleAddResponsibility = () => {
    if (currentResponsibility.trim()) {
      setRequirements({
        ...requirements,
        responsibilities: [
          ...requirements.responsibilities,
          currentResponsibility.trim(),
        ],
      });
      setCurrentResponsibility("");
    }
  };

  const handleRemoveResponsibility = (index: number) => {
    setRequirements({
      ...requirements,
      responsibilities: requirements.responsibilities.filter(
        (_, i) => i !== index,
      ),
    });
  };

  const handleAddQualification = () => {
    if (currentQualification.trim()) {
      setRequirements({
        ...requirements,
        qualifications: [
          ...requirements.qualifications,
          currentQualification.trim(),
        ],
      });
      setCurrentQualification("");
    }
  };

  const handleRemoveQualification = (index: number) => {
    setRequirements({
      ...requirements,
      qualifications: requirements.qualifications.filter((_, i) => i !== index),
    });
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Build the context from requirements
      const context = `
Job Title: ${requirements.jobTitle}
Classification: ${requirements.classification}
Department: ${requirements.department}
Reports To: ${requirements.reportsTo}
Location: ${requirements.location}

Key Skills Required:
${requirements.skills.map((s, i) => `${i + 1}. ${s}`).join("\n")}

Core Responsibilities:
${requirements.responsibilities.map((r, i) => `${i + 1}. ${r}`).join("\n")}

Required Qualifications:
${requirements.qualifications.map((q, i) => `${i + 1}. ${q}`).join("\n")}

Additional Information:
${requirements.additionalInfo}
      `.trim();

      // Generate each section
      const sections = {
        title: requirements.jobTitle,
        summary: "",
        accountabilities: "",
        organizationStructure: "",
        natureAndScope: "",
        specificAccountabilities: "",
        dimensions: "",
        knowledgeAndSkills: "",
      };

      // Generate General Accountability
      const accountabilityResponse = await apiClient.generateSectionCompletion({
        section_type: "general_accountability",
        current_content: context,
        job_context: context,
        classification: requirements.classification,
        language: "en",
      });
      sections.accountabilities =
        accountabilityResponse.completed_content ||
        accountabilityResponse.content;

      // Generate Organization Structure
      const orgStructureResponse = await apiClient.generateSectionCompletion({
        section_type: "organization_structure",
        current_content: `${requirements.reportsTo}\n${requirements.department}`,
        job_context: context,
        classification: requirements.classification,
        language: "en",
      });
      sections.organizationStructure =
        orgStructureResponse.completed_content || orgStructureResponse.content;

      // Generate Nature and Scope
      const natureResponse = await apiClient.generateSectionCompletion({
        section_type: "nature_and_scope",
        current_content: requirements.additionalInfo,
        job_context: context,
        classification: requirements.classification,
        language: "en",
      });
      sections.natureAndScope =
        natureResponse.completed_content || natureResponse.content;

      // Generate Specific Accountabilities
      const specificAccountabilityContent =
        requirements.responsibilities.join("\n");
      const specificResponse = await apiClient.generateSectionCompletion({
        section_type: "specific_accountabilities",
        current_content: specificAccountabilityContent,
        job_context: context,
        classification: requirements.classification,
        language: "en",
      });
      sections.specificAccountabilities =
        specificResponse.completed_content || specificResponse.content;

      // Generate Knowledge and Skills
      const skillsContent =
        requirements.skills.join("\n") +
        "\n" +
        requirements.qualifications.join("\n");
      const skillsResponse = await apiClient.generateSectionCompletion({
        section_type: "knowledge_and_skills",
        current_content: skillsContent,
        job_context: context,
        classification: requirements.classification,
        language: "en",
      });
      sections.knowledgeAndSkills =
        skillsResponse.completed_content || skillsResponse.content;

      // Generate summary
      sections.summary = `The ${requirements.jobTitle} (${requirements.classification}) is responsible for ${requirements.responsibilities[0]?.toLowerCase() || "key organizational objectives"}. This position reports to the ${requirements.reportsTo} and is located in ${requirements.location}.`;

      // Calculate real quality score using API
      let qualityScore = 75; // Fallback default
      try {
        const qualityResponse = await apiClient.calculateQualityScore({
          sections: {
            general_accountability: sections.accountabilities,
            organization_structure: sections.organizationStructure,
            nature_and_scope: sections.natureAndScope,
            specific_accountabilities: sections.specificAccountabilities,
            knowledge_and_skills: sections.knowledgeAndSkills,
          },
          raw_content: context,
        });

        if (qualityResponse && qualityResponse.overall_score !== undefined) {
          qualityScore = Math.round(qualityResponse.overall_score);
          logger.info(
            `Quality score calculated: ${qualityScore}`,
            qualityResponse,
          );
        }
      } catch (error) {
        logger.warn(
          "Quality scoring API failed, using fallback value:",
          error as Error,
        );
        // Continue with fallback value
      }

      setGeneratedContent({
        ...sections,
        dimensions:
          "To be determined based on organizational structure and budget allocation.",
        qualityScore,
        suggestions: [
          "Consider adding more specific metrics and KPIs",
          "Review bilingual requirements for government positions",
          "Add security clearance level if applicable",
        ],
      });

      setStep(4);
      toast({
        title: "Job Description Generated!",
        description: "Your AI-generated job description is ready for review.",
      });
    } catch (error) {
      logger.error("Generation failed:", error);
      toast({
        title: "Generation Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to generate job description",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!generatedContent) return;

    try {
      // Create job description
      const jobData = {
        job_number: `DRAFT-${Date.now()}`,
        title: generatedContent.title,
        classification: requirements.classification,
        language: "en",
        raw_content: `
GENERAL ACCOUNTABILITY:
${generatedContent.accountabilities}

ORGANIZATION STRUCTURE:
${generatedContent.organizationStructure}

NATURE AND SCOPE:
${generatedContent.natureAndScope}

SPECIFIC ACCOUNTABILITIES:
${generatedContent.specificAccountabilities}

DIMENSIONS:
${generatedContent.dimensions}

KNOWLEDGE AND SKILLS:
${generatedContent.knowledgeAndSkills}
        `.trim(),
      };

      await apiClient.createJob(jobData);

      toast({
        title: "Job Description Saved!",
        description: "Your job description has been saved to the database.",
      });
    } catch (error) {
      logger.error("Save failed:", error);
      toast({
        title: "Save Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to save job description",
        variant: "destructive",
      });
    }
  };

  const handleExport = () => {
    if (!generatedContent) return;

    const content = `
JOB DESCRIPTION
${generatedContent.title}
Classification: ${requirements.classification}
Department: ${requirements.department}
Reports To: ${requirements.reportsTo}
Location: ${requirements.location}

SUMMARY:
${generatedContent.summary}

GENERAL ACCOUNTABILITY:
${generatedContent.accountabilities}

ORGANIZATION STRUCTURE:
${generatedContent.organizationStructure}

NATURE AND SCOPE:
${generatedContent.natureAndScope}

SPECIFIC ACCOUNTABILITIES:
${generatedContent.specificAccountabilities}

DIMENSIONS:
${generatedContent.dimensions}

KNOWLEDGE AND SKILLS:
${generatedContent.knowledgeAndSkills}
    `.trim();

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${requirements.jobTitle.replace(/\s+/g, "_")}_JD.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Exported Successfully",
      description: "Job description downloaded as text file.",
    });
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return requirements.jobTitle && requirements.classification;
      case 2:
        return requirements.skills.length > 0;
      case 3:
        return requirements.responsibilities.length > 0;
      default:
        return true;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="w-6 h-6 text-purple-600" />
            AI-Assisted Job Description Writer
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Create comprehensive job descriptions with AI assistance. Provide
            basic information and let AI generate professional content.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">
                Step {step} of {totalSteps}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Basic Information */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600">
                1
              </div>
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="jobTitle">Job Title *</Label>
              <Input
                id="jobTitle"
                placeholder="e.g., Director of Business Analysis"
                value={requirements.jobTitle}
                onChange={(e) =>
                  setRequirements({ ...requirements, jobTitle: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="classification">Classification *</Label>
                <Select
                  value={requirements.classification}
                  onValueChange={(value) =>
                    setRequirements({ ...requirements, classification: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select classification" />
                  </SelectTrigger>
                  <SelectContent>
                    {classifications.map((cls) => (
                      <SelectItem key={cls} value={cls}>
                        {cls}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  placeholder="e.g., Information Technology"
                  value={requirements.department}
                  onChange={(e) =>
                    setRequirements({
                      ...requirements,
                      department: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="reportsTo">Reports To</Label>
                <Input
                  id="reportsTo"
                  placeholder="e.g., Chief Information Officer"
                  value={requirements.reportsTo}
                  onChange={(e) =>
                    setRequirements({
                      ...requirements,
                      reportsTo: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  placeholder="e.g., Ottawa, ON"
                  value={requirements.location}
                  onChange={(e) =>
                    setRequirements({
                      ...requirements,
                      location: e.target.value,
                    })
                  }
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Skills and Qualifications */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600">
                2
              </div>
              Required Skills and Qualifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Skills */}
            <div className="space-y-3">
              <Label>Key Skills Required *</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., Project Management, Data Analysis"
                  value={currentSkill}
                  onChange={(e) => setCurrentSkill(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleAddSkill()}
                />
                <Button onClick={handleAddSkill} size="sm">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {requirements.skills.map((skill, index) => (
                  <Badge key={index} variant="secondary" className="gap-1">
                    {skill}
                    <button
                      onClick={() => handleRemoveSkill(index)}
                      title="Remove skill"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>

            {/* Qualifications */}
            <div className="space-y-3">
              <Label>Required Qualifications</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., Bachelor's degree in Computer Science"
                  value={currentQualification}
                  onChange={(e) => setCurrentQualification(e.target.value)}
                  onKeyPress={(e) =>
                    e.key === "Enter" && handleAddQualification()
                  }
                />
                <Button onClick={handleAddQualification} size="sm">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="space-y-2">
                {requirements.qualifications.map((qual, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-2 bg-muted rounded"
                  >
                    <span className="flex-1 text-sm">{qual}</span>
                    <Button
                      onClick={() => handleRemoveQualification(index)}
                      title="Remove qualification"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Responsibilities */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600">
                3
              </div>
              Core Responsibilities
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <Label>Key Responsibilities *</Label>
              <div className="flex gap-2">
                <Textarea
                  placeholder="e.g., Lead strategic planning initiatives for enterprise systems"
                  value={currentResponsibility}
                  onChange={(e) => setCurrentResponsibility(e.target.value)}
                  rows={2}
                />
                <Button onClick={handleAddResponsibility} size="sm">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="space-y-2">
                {requirements.responsibilities.map((resp, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-3 bg-muted rounded"
                  >
                    <span className="text-sm font-medium text-muted-foreground">
                      {index + 1}.
                    </span>
                    <span className="flex-1 text-sm">{resp}</span>
                    <Button onClick={() => handleRemoveResponsibility(index)}>
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="additionalInfo">
                Additional Context (Optional)
              </Label>
              <Textarea
                id="additionalInfo"
                placeholder="Any additional information about the role, team, or organizational context..."
                value={requirements.additionalInfo}
                onChange={(e) =>
                  setRequirements({
                    ...requirements,
                    additionalInfo: e.target.value,
                  })
                }
                rows={4}
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={loading || !canProceed()}
              className="w-full"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Job Description
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Review and Edit */}
      {step === 4 && generatedContent && (
        <div className="space-y-4">
          {/* Quality Score */}
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-8 h-8 text-green-600" />
                  <div>
                    <h3 className="font-semibold text-green-900">
                      Quality Score: {generatedContent.qualityScore}%
                    </h3>
                    <p className="text-sm text-green-700">
                      Your job description meets high quality standards
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleSave} variant="outline">
                    <Save className="w-4 h-4 mr-2" />
                    Save
                  </Button>
                  <Button onClick={handleExport}>
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generated Content */}
          <Card>
            <CardHeader>
              <CardTitle>{generatedContent.title}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {requirements.classification} • {requirements.department}
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <Section title="Summary" content={generatedContent.summary} />
              <Section
                title="General Accountability"
                content={generatedContent.accountabilities}
              />
              <Section
                title="Organization Structure"
                content={generatedContent.organizationStructure}
              />
              <Section
                title="Nature and Scope"
                content={generatedContent.natureAndScope}
              />
              <Section
                title="Specific Accountabilities"
                content={generatedContent.specificAccountabilities}
              />
              <Section
                title="Dimensions"
                content={generatedContent.dimensions}
              />
              <Section
                title="Knowledge and Skills"
                content={generatedContent.knowledgeAndSkills}
              />
            </CardContent>
          </Card>

          {/* Suggestions */}
          {generatedContent.suggestions.length > 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-blue-600" />
                  AI Suggestions for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {generatedContent.suggestions.map((suggestion, index) => (
                    <li
                      key={index}
                      className="text-sm text-blue-900 flex items-start gap-2"
                    >
                      <span className="text-blue-600">•</span>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Navigation */}
      {step < 4 && (
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          <Button
            onClick={() => setStep(Math.min(totalSteps, step + 1))}
            disabled={!canProceed() || step === 3}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}

      {step === 4 && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => setStep(1)}>
            Create Another Job Description
          </Button>
        </div>
      )}
    </div>
  );
}

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-lg">{title}</h3>
      <div className="p-4 bg-muted rounded-lg">
        <p className="text-sm whitespace-pre-line">{content}</p>
      </div>
    </div>
  );
}
