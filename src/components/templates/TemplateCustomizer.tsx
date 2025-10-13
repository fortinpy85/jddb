/**
 * Template Customizer Component
 *
 * Allows users to customize job description templates by:
 * - Extracting and displaying all placeholders
 * - Providing input fields for each placeholder
 * - Real-time preview of customized content
 * - Applying customizations to generate final template
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Edit3,
  Eye,
  CheckCircle,
  AlertCircle,
  Sparkles,
  ChevronRight,
  Copy,
  RotateCcw,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { Template } from "./SmartTemplateSelector";
import { logger } from "@/utils/logger";

interface TemplateCustomizerProps {
  template: Template;
  onComplete?: (customizedTemplate: Template) => void;
  onCancel?: () => void;
  className?: string;
}

interface PlaceholderValue {
  placeholder: string;
  value: string;
  section: string;
}

export const TemplateCustomizer: React.FC<TemplateCustomizerProps> = ({
  template,
  onComplete,
  onCancel,
  className,
}) => {
  const [placeholders, setPlaceholders] = useState<PlaceholderValue[]>([]);
  const [customizedTemplate, setCustomizedTemplate] = useState<Template | null>(
    null,
  );
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [validationStatus, setValidationStatus] = useState<{
    complete: boolean;
    missing: number;
  }>({ complete: false, missing: 0 });

  // Extract all placeholders from template on mount
  useEffect(() => {
    extractPlaceholders();
  }, [template]);

  // Update validation status when placeholder values change
  useEffect(() => {
    updateValidationStatus();
  }, [placeholders]);

  const extractPlaceholders = () => {
    const extracted: PlaceholderValue[] = [];

    Object.entries(template.sections).forEach(([sectionId, section]) => {
      if (section.placeholders && section.placeholders.length > 0) {
        section.placeholders.forEach((placeholder) => {
          extracted.push({
            placeholder,
            value: "",
            section: section.title,
          });
        });
      }
    });

    setPlaceholders(extracted);
  };

  const updateValidationStatus = () => {
    const missing = placeholders.filter((p) => !p.value.trim()).length;
    setValidationStatus({
      complete: missing === 0,
      missing,
    });
  };

  const handlePlaceholderChange = (placeholder: string, value: string) => {
    setPlaceholders((prev) =>
      prev.map((p) => (p.placeholder === placeholder ? { ...p, value } : p)),
    );
  };

  const handleGeneratePreview = async () => {
    setLoading(true);
    try {
      const customizations: { [key: string]: string } = {};
      placeholders.forEach((p) => {
        if (p.value.trim()) {
          customizations[p.placeholder] = p.value;
        }
      });

      const response = await fetch(`${API_BASE_URL}/templates/customize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template,
          customizations,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setCustomizedTemplate(data.template);
        setPreviewOpen(true);
      }
    } catch (error) {
      logger.error("Failed to customize template:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = () => {
    if (customizedTemplate && onComplete) {
      onComplete(customizedTemplate);
    }
  };

  const handleReset = () => {
    setPlaceholders((prev) => prev.map((p) => ({ ...p, value: "" })));
    setCustomizedTemplate(null);
  };

  const handleCopyPlaceholder = (placeholder: string) => {
    navigator.clipboard.writeText(placeholder);
  };

  // Group placeholders by section
  const groupedPlaceholders = placeholders.reduce(
    (acc, p) => {
      if (!acc[p.section]) {
        acc[p.section] = [];
      }
      acc[p.section].push(p);
      return acc;
    },
    {} as { [section: string]: PlaceholderValue[] },
  );

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Edit3 className="w-4 h-4" />
            Customize Template
          </CardTitle>
          <Badge
            variant={validationStatus.complete ? "default" : "outline"}
            className="ml-auto"
          >
            {validationStatus.complete ? (
              <>
                <CheckCircle className="w-3 h-3 mr-1" />
                Ready
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3 mr-1" />
                {validationStatus.missing} remaining
              </>
            )}
          </Badge>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          Fill in the placeholders below to customize your template
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Template Info */}
        <div className="border rounded-lg p-3 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900">
                {template.classification} - {template.category}
              </p>
              <p className="text-xs text-blue-700">
                {template.language === "en" ? "English" : "Français"}
              </p>
            </div>
            <Badge className="bg-blue-100 text-blue-800">
              {placeholders.length} placeholders
            </Badge>
          </div>
        </div>

        {/* Placeholder Input Sections */}
        <ScrollArea className="h-[400px] pr-4">
          <Accordion type="multiple" className="space-y-2">
            {Object.entries(groupedPlaceholders).map(
              ([section, sectionPlaceholders]) => (
                <AccordionItem key={section} value={section}>
                  <AccordionTrigger className="text-sm font-medium">
                    <div className="flex items-center gap-2">
                      <ChevronRight className="w-4 h-4" />
                      {section}
                      <Badge variant="outline" className="ml-2">
                        {
                          sectionPlaceholders.filter((p) => p.value.trim())
                            .length
                        }
                        /{sectionPlaceholders.length}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3 pt-2">
                      {sectionPlaceholders.map((p, idx) => (
                        <div key={idx} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs font-medium">
                              {p.placeholder}
                            </Label>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 text-xs"
                              onClick={() =>
                                handleCopyPlaceholder(p.placeholder)
                              }
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                          </div>
                          {p.placeholder.length > 50 ? (
                            <Textarea
                              placeholder={`Enter value for ${p.placeholder}`}
                              value={p.value}
                              onChange={(e) =>
                                handlePlaceholderChange(
                                  p.placeholder,
                                  e.target.value,
                                )
                              }
                              className="text-sm min-h-[80px]"
                            />
                          ) : (
                            <Input
                              placeholder={`Enter value for ${p.placeholder}`}
                              value={p.value}
                              onChange={(e) =>
                                handlePlaceholderChange(
                                  p.placeholder,
                                  e.target.value,
                                )
                              }
                              className="text-sm"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ),
            )}
          </Accordion>
        </ScrollArea>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleGeneratePreview}
            disabled={loading}
            className="flex-1"
            size="sm"
          >
            {loading ? (
              <>Loading...</>
            ) : (
              <>
                <Eye className="w-3 h-3 mr-1" />
                Generate Preview
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={placeholders.every((p) => !p.value.trim())}
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Reset
          </Button>
        </div>

        {/* Quick Actions */}
        {onCancel && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
            className="w-full"
          >
            Cancel
          </Button>
        )}
      </CardContent>

      {/* Preview Dialog */}
      {customizedTemplate && (
        <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                Customized Template Preview
              </DialogTitle>
              <DialogDescription>
                {customizedTemplate.classification} -{" "}
                {customizedTemplate.category}
              </DialogDescription>
            </DialogHeader>

            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                {Object.entries(customizedTemplate.sections).map(
                  ([sectionId, section]) => (
                    <div
                      key={sectionId}
                      className="border-b pb-4 last:border-0"
                    >
                      <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                        <ChevronRight className="w-4 h-4" />
                        {section.title}
                      </h4>
                      <div className="text-sm text-gray-700 whitespace-pre-line pl-6 bg-gray-50 rounded p-3">
                        {section.content}
                      </div>

                      {/* Show remaining placeholders if any */}
                      {section.content.includes("[") && (
                        <div className="mt-2 pl-6">
                          <Badge variant="outline" className="text-xs">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Contains unfilled placeholders
                          </Badge>
                        </div>
                      )}
                    </div>
                  ),
                )}
              </div>

              {/* Customization Metadata */}
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                <p className="text-xs text-green-800">
                  <CheckCircle className="w-3 h-3 inline mr-1" />
                  {customizedTemplate.metadata.customizations_applied}{" "}
                  customizations applied
                </p>
              </div>
            </ScrollArea>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setPreviewOpen(false)}>
                Close
              </Button>
              <Button onClick={handleApplyTemplate}>
                <CheckCircle className="w-3 h-3 mr-1" />
                Apply Template
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Card>
  );
};
