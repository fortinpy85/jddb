/**
 * Smart Template Selector Component
 *
 * Allows users to browse and select job description templates with:
 * - Classification-based filtering
 * - Bilingual template support
 * - Template preview
 * - Quick template application
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  FileText,
  Check,
  Eye,
  Languages,
  Sparkles,
  ChevronRight,
  Search,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

export interface Template {
  classification: string;
  category: string;
  language: string;
  sections: {
    [key: string]: {
      title: string;
      content: string;
      placeholders?: string[];
    };
  };
  metadata: {
    created_at: string;
    version: string;
    source: string;
    customizations_applied?: number;
  };
}

export interface Classification {
  code: string;
  name: string;
}

interface SmartTemplateSelectorProps {
  onSelectTemplate?: (template: Template) => void;
  selectedLanguage?: string;
  className?: string;
}

export const SmartTemplateSelector: React.FC<SmartTemplateSelectorProps> = ({
  onSelectTemplate,
  selectedLanguage = "en",
  className,
}) => {
  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [selectedClassification, setSelectedClassification] =
    useState<string>("");
  const [selectedLevel, setSelectedLevel] = useState<string>("");
  const [language, setLanguage] = useState<string>(selectedLanguage);
  const [template, setTemplate] = useState<Template | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Load available classifications on mount
  useEffect(() => {
    loadClassifications();
  }, []);

  const loadClassifications = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/templates/classifications`);
      const data = await response.json();
      setClassifications(data);
    } catch (error) {
      console.error("Failed to load classifications:", error);
    }
  };

  const loadTemplate = async () => {
    if (!selectedClassification) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        language,
        ...(selectedLevel && { level: selectedLevel }),
      });

      const response = await fetch(
        `${API_BASE_URL}/templates/generate/${selectedClassification}?${params}`,
      );
      const data = await response.json();

      if (data.success) {
        setTemplate(data.template);
      }
    } catch (error) {
      console.error("Failed to load template:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = () => {
    if (template && onSelectTemplate) {
      onSelectTemplate(template);
    }
  };

  const filteredClassifications = classifications.filter(
    (c) =>
      c.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Smart Template Selector
          <Badge variant="outline" className="ml-auto">
            <Sparkles className="w-3 h-3 mr-1" />
            AI-Powered
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search Classifications */}
        <div className="space-y-2">
          <Label className="text-xs">Search Classifications</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by code or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-9"
            />
          </div>
        </div>

        {/* Classification Selection */}
        <div className="space-y-2">
          <Label className="text-xs">Classification</Label>
          <Select
            value={selectedClassification}
            onValueChange={setSelectedClassification}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Select classification" />
            </SelectTrigger>
            <SelectContent>
              {filteredClassifications.map((classification) => (
                <SelectItem
                  key={classification.code}
                  value={classification.code}
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono text-xs">
                      {classification.code}
                    </Badge>
                    <span className="text-sm">{classification.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Level Selection */}
        <div className="space-y-2">
          <Label className="text-xs">Level (Optional)</Label>
          <Select value={selectedLevel} onValueChange={setSelectedLevel}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Select level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None</SelectItem>
              <SelectItem value="01">01</SelectItem>
              <SelectItem value="02">02</SelectItem>
              <SelectItem value="03">03</SelectItem>
              <SelectItem value="04">04</SelectItem>
              <SelectItem value="05">05</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Language Selection */}
        <div className="space-y-2">
          <Label className="text-xs">Language</Label>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">
                <div className="flex items-center gap-2">
                  <Languages className="w-3 h-3" />
                  English
                </div>
              </SelectItem>
              <SelectItem value="fr">
                <div className="flex items-center gap-2">
                  <Languages className="w-3 h-3" />
                  Français
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={loadTemplate}
            disabled={!selectedClassification || loading}
            className="flex-1"
            size="sm"
          >
            {loading ? (
              <>Loading...</>
            ) : (
              <>
                <FileText className="w-3 h-3 mr-1" />
                Generate Template
              </>
            )}
          </Button>

          {template && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPreviewOpen(true)}
            >
              <Eye className="w-3 h-3 mr-1" />
              Preview
            </Button>
          )}
        </div>

        {/* Template Summary */}
        {template && (
          <div className="border rounded-lg p-3 bg-green-50 border-green-200">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-sm font-medium text-green-900">
                  Template Ready
                </p>
                <p className="text-xs text-green-700">
                  {template.classification} - {template.category}
                </p>
              </div>
              <Badge className="bg-green-100 text-green-800">
                {Object.keys(template.sections).length} sections
              </Badge>
            </div>

            <Button
              onClick={handleSelectTemplate}
              className="w-full"
              size="sm"
              variant="default"
            >
              <Check className="w-3 h-3 mr-1" />
              Use This Template
            </Button>
          </div>
        )}

        {/* Quick Classifications */}
        <div className="space-y-2">
          <Label className="text-xs">Quick Select</Label>
          <div className="flex flex-wrap gap-2">
            {classifications.slice(0, 5).map((classification) => (
              <Button
                key={classification.code}
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => {
                  setSelectedClassification(classification.code);
                  setSearchQuery("");
                }}
              >
                {classification.code}
              </Button>
            ))}
          </div>
        </div>
      </CardContent>

      {/* Template Preview Dialog */}
      {template && (
        <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
          <DialogContent className="max-w-3xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>Template Preview</DialogTitle>
              <DialogDescription>
                {template.classification} - {template.category}
              </DialogDescription>
            </DialogHeader>

            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                {Object.entries(template.sections).map(
                  ([sectionId, section]) => (
                    <div
                      key={sectionId}
                      className="border-b pb-4 last:border-0"
                    >
                      <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                        <ChevronRight className="w-4 h-4" />
                        {section.title}
                      </h4>
                      <p className="text-sm text-gray-700 whitespace-pre-line pl-6">
                        {section.content}
                      </p>
                      {section.placeholders &&
                        section.placeholders.length > 0 && (
                          <div className="mt-2 pl-6">
                            <p className="text-xs text-gray-500 mb-1">
                              Placeholders to customize:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {section.placeholders.map((placeholder, idx) => (
                                <Badge
                                  key={idx}
                                  variant="outline"
                                  className="text-xs font-mono"
                                >
                                  {placeholder}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  ),
                )}
              </div>
            </ScrollArea>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setPreviewOpen(false)}>
                Close
              </Button>
              <Button onClick={handleSelectTemplate}>
                <Check className="w-3 h-3 mr-1" />
                Use Template
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Card>
  );
};
