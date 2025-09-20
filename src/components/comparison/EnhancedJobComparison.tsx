"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  FileText,
  Calendar,
  Users,
  Building,
  ChevronDown,
  X,
  Eye,
  GitCompare,
  CheckCircle2,
  AlertCircle,
  Lightbulb
} from "lucide-react";

interface JobSummary {
  id: number;
  title: string;
  status: "Published" | "Draft" | "Under Review";
  group: string;
  jobLevel: string;
  lastPublished: string;
  summary: string;
}

interface CompetencyItem {
  name: string;
  level: string;
  color?: string;
}

interface EnhancedJobComparisonProps {
  onClose?: () => void;
}

export const EnhancedJobComparison: React.FC<EnhancedJobComparisonProps> = ({ onClose }) => {
  const [selectedFilter, setSelectedFilter] = useState("differences");
  const [expandedSections, setExpandedSections] = useState<string[]>(["competencies"]);

  // Mock data inspired by the screenshot
  const jobs: JobSummary[] = [
    {
      id: 1,
      title: "Business Development Representative",
      status: "Published",
      group: "Account Management & Business Development",
      jobLevel: "Individual Contributor",
      lastPublished: "Feb 8, 2024",
      summary: "The Business Development Representative supports sales activities through qualifying leads generated from other teams, and committing to developing those leads into new business."
    },
    {
      id: 2,
      title: "Sales Representative",
      status: "Draft",
      group: "General Sales",
      jobLevel: "Individual Contributor",
      lastPublished: "Feb 8, 2024",
      summary: "The Sales Representative delivers new business opportunities through liaising with potential customers to identify solutions to their needs."
    }
  ];

  const competencies: { [key: number]: CompetencyItem[] } = {
    1: [
      { name: "Account Management", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Business Development", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Fostering Communication", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Managing the Sales Process", level: "Level 3", color: "bg-amber-100 text-amber-800" }
    ],
    2: [
      { name: "Product and Technical Knowledge", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Managing the Sales Process", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Client Focus", level: "Level 3", color: "bg-amber-100 text-amber-800" },
      { name: "Achievement Orientation", level: "Level 2", color: "bg-blue-100 text-blue-800" }
    ]
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev =>
      prev.includes(sectionId)
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Published":
        return "bg-green-100 text-green-800 border-green-200";
      case "Draft":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "Under Review":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold">Compare jobs</h2>
            </div>

            {/* Filter Dropdown */}
            <Select value={selectedFilter} onValueChange={setSelectedFilter}>
              <SelectTrigger className="w-40 bg-yellow-50 border-yellow-200">
                <div className="flex items-center space-x-2">
                  <Lightbulb className="w-4 h-4 text-yellow-600" />
                  <SelectValue />
                </div>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="differences">Differences</SelectItem>
                <SelectItem value="similarities">Similarities</SelectItem>
                <SelectItem value="all">All content</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>

        {/* Filter Options */}
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-sm font-medium">Differences</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Matches</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Nothing</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="grid grid-cols-2 h-full">
            {/* Left Job */}
            <div className="border-r border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <h3 className="text-lg font-semibold">{jobs[0].title}</h3>
                  <Button variant="ghost" size="sm">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                  <Badge className={getStatusColor(jobs[0].status)}>{jobs[0].status}</Badge>
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>Created on: {jobs[0].lastPublished}</span>
                  </span>
                </div>
              </div>

              <ScrollArea className="h-full p-6">
                {/* Summary */}
                <div className="mb-6">
                  <h4 className="font-semibold mb-3">Summary</h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {jobs[0].summary}
                  </p>
                </div>

                <Separator className="my-6" />

                {/* Information */}
                <div className="mb-6">
                  <h4 className="font-semibold mb-3">Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Group</span>
                      <span className="font-medium text-amber-600">{jobs[0].group}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Job levels</span>
                      <span className="font-medium">{jobs[0].jobLevel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last published</span>
                      <span className="font-medium">{jobs[0].lastPublished}</span>
                    </div>
                  </div>
                </div>

                <Separator className="my-6" />

                {/* Competencies */}
                <div>
                  <button
                    onClick={() => toggleSection("competencies")}
                    className="flex items-center justify-between w-full mb-3"
                  >
                    <h4 className="font-semibold">Competencies</h4>
                    <ChevronDown
                      className={`w-4 h-4 transition-transform ${
                        expandedSections.includes("competencies") ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {expandedSections.includes("competencies") && (
                    <div className="space-y-3">
                      {competencies[1].map((competency, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm font-medium">{competency.name}</span>
                          <Badge className={competency.color}>{competency.level}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>

            {/* Right Job */}
            <div>
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <h3 className="text-lg font-semibold">{jobs[1].title}</h3>
                  <Button variant="ghost" size="sm">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                  <Badge className={getStatusColor(jobs[1].status)}>{jobs[1].status}</Badge>
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>Created on: {jobs[1].lastPublished}</span>
                  </span>
                </div>
              </div>

              <ScrollArea className="h-full p-6">
                {/* Summary */}
                <div className="mb-6">
                  <h4 className="font-semibold mb-3">Summary</h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {jobs[1].summary}
                  </p>
                </div>

                <Separator className="my-6" />

                {/* Information */}
                <div className="mb-6">
                  <h4 className="font-semibold mb-3">Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Group</span>
                      <span className="font-medium text-amber-600">{jobs[1].group}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Job levels</span>
                      <span className="font-medium">{jobs[1].jobLevel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last published</span>
                      <span className="font-medium">{jobs[1].lastPublished}</span>
                    </div>
                  </div>
                </div>

                <Separator className="my-6" />

                {/* Competencies */}
                <div>
                  <button
                    onClick={() => toggleSection("competencies")}
                    className="flex items-center justify-between w-full mb-3"
                  >
                    <h4 className="font-semibold">Competencies</h4>
                    <ChevronDown
                      className={`w-4 h-4 transition-transform ${
                        expandedSections.includes("competencies") ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {expandedSections.includes("competencies") && (
                    <div className="space-y-3">
                      {competencies[2].map((competency, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm font-medium">{competency.name}</span>
                          <Badge className={competency.color}>{competency.level}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};