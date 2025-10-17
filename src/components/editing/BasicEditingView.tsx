/**
 * Basic Editing View Component
 * Multi-card workspace where each section of the job description is displayed separately
 * Includes collaborative features, AI assistance, and properties panel
 */

"use client";

import React, { useState, useEffect } from "react";
import { TwoPanelLayout } from "@/components/layout/TwoPanelLayout";
import { PropertiesPanel } from "@/components/editing/PropertiesPanel";
import { AIAssistantPanel } from "@/components/ai/AIAssistantPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import {
  ChevronLeft,
  Save,
  CheckCircle,
  Undo,
  Sparkles,
  Users,
  PanelRightOpen,
  PanelRightClose,
  Edit,
  Eye,
  EyeOff,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";
import { LoadingState, ErrorState } from "@/components/ui/states";

interface BasicEditingViewProps {
  jobId?: number;
  initialContent?: string;
  onBack?: () => void;
  onAdvancedEdit?: () => void;
  className?: string;
  onUnsavedChangesChange?: (hasUnsavedChanges: boolean) => void;
}

interface JobSection {
  id: string;
  type: string;
  title: string;
  content: string;
  lastModified?: Date;
  modifiedBy?: string;
}

interface Collaborator {
  id: number;
  name: string;
  initials: string;
  color: string;
  active: boolean;
}

export function BasicEditingView({
  jobId,
  initialContent,
  onBack,
  onAdvancedEdit,
  className,
  onUnsavedChangesChange,
}: BasicEditingViewProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [showPropertiesPanel, setShowPropertiesPanel] = useState(true);
  const [showAIPanel, setShowAIPanel] = useState(true);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    onUnsavedChangesChange?.(hasUnsavedChanges);
  }, [hasUnsavedChanges, onUnsavedChangesChange]);

  // Mock data - in production, fetch from API and WebSocket
  const [sections, setSections] = useState<JobSection[]>(() => {
    if (initialContent) {
      return [
        {
          id: "1",
          type: "merged_content",
          title: "Merged Content",
          content: initialContent,
        },
      ];
    }
    return [
      {
        id: "1",
        type: "general_accountability",
        title: "General Accountability",
        content:
          "The Director of Business Analysis is accountable for leading the business analysis function across the organization, ensuring alignment with strategic objectives and delivering value through data-driven insights.",
        lastModified: new Date(),
        modifiedBy: "Alice Johnson",
      },
      {
        id: "2",
        type: "organization_structure",
        title: "Organization Structure",
        content:
          "Reports to: Chief Operating Officer\nDirect Reports: 5 Senior Business Analysts, 3 Business Analysts\nDotted Line Reports: Project Managers in all departments",
        lastModified: new Date(),
        modifiedBy: "Bob Smith",
      },
      {
        id: "3",
        type: "nature_scope",
        title: "Nature and Scope",
        content:
          "This position requires strategic thinking, analytical expertise, and leadership capabilities to drive business intelligence initiatives. The role involves collaborating with executive leadership, managing a team of analysts, and implementing data-driven solutions.",
        lastModified: new Date(),
        modifiedBy: "Alice Johnson",
      },
      {
        id: "4",
        type: "specific_accountabilities",
        title: "Specific Accountabilities",
        content:
          "• Lead and mentor a team of business analysts\n• Develop and implement business analysis strategies\n• Conduct complex data analysis and provide insights\n• Collaborate with stakeholders across the organization\n• Ensure quality and accuracy of analytical outputs",
        lastModified: new Date(),
        modifiedBy: "Alice Johnson",
      },
    ];
  });

  const [collaborators] = useState<Collaborator[]>([
    {
      id: 1,
      name: "Alice Johnson",
      initials: "AJ",
      color: "bg-blue-500",
      active: true,
    },
    {
      id: 2,
      name: "Bob Smith",
      initials: "BS",
      color: "bg-green-500",
      active: true,
    },
    {
      id: 3,
      name: "Carol White",
      initials: "CW",
      color: "bg-purple-500",
      active: false,
    },
  ]);

  const activeCollaborators = collaborators.filter((c) => c.active);

  // Handle section content change
  const handleSectionChange = (sectionId: string, newContent: string) => {
    setSections(
      sections.map((s) =>
        s.id === sectionId ? { ...s, content: newContent } : s,
      ),
    );
    setHasUnsavedChanges(true);
  };

  // Handle save
  const handleSave = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      addToast({
        title: "Changes Saved",
        description: "Your edits have been saved successfully",
        type: "success",
      });
      setHasUnsavedChanges(false);
    } catch (error) {
      addToast({
        title: "Save Failed",
        description: "Failed to save changes. Please try again.",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle approve
  const handleApprove = () => {
    addToast({
      title: "Job Approved",
      description: "This job description has been approved",
      type: "success",
    });
  };

  // Handle undo
  const handleUndo = () => {
    addToast({
      title: "Changes Reverted",
      description: "Your last change has been undone",
      type: "info",
    });
  };

  // Render right panel content
  const renderRightPanel = () => {
    return (
      <div className="h-full flex flex-col">
        {/* Panel toggles */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Panels
            </h3>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setShowRightPanel(false)}
            >
              <PanelRightClose className="w-4 h-4" />
            </Button>
          </div>
          <div className="space-y-2">
            <Button
              variant={showPropertiesPanel ? "default" : "outline"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setShowPropertiesPanel(!showPropertiesPanel)}
            >
              {showPropertiesPanel ? (
                <Eye className="w-4 h-4 mr-2" />
              ) : (
                <EyeOff className="w-4 h-4 mr-2" />
              )}
              Properties
            </Button>
            <Button
              variant={showAIPanel ? "default" : "outline"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setShowAIPanel(!showAIPanel)}
            >
              {showAIPanel ? (
                <Eye className="w-4 h-4 mr-2" />
              ) : (
                <EyeOff className="w-4 h-4 mr-2" />
              )}
              AI Assistant
            </Button>
          </div>
        </div>

        {/* Panels */}
        <div className="flex-1 overflow-y-auto">
          {showPropertiesPanel && (
            <div className="border-b border-slate-200 dark:border-slate-700">
              <PropertiesPanel jobId={jobId} />
            </div>
          )}
          {showAIPanel && (
            <div>
              <AIAssistantPanel suggestions={[]} overallScore={null} />
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return <LoadingState message="Loading job description..." />;
  }

  return (
    <div className={cn("h-full", className)}>
      <TwoPanelLayout
        rightPanel={showRightPanel ? renderRightPanel() : null}
        showRightPanel={showRightPanel}
        rightPanelCollapsible={true}
        rightPanelWidth={360}
        contentClassName="p-0"
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="sticky top-0 z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" onClick={onBack}>
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Back
                </Button>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Edit Job Description
                  </h2>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Collaborative editing workspace
                  </p>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center space-x-2">
                {/* User presence */}
                {activeCollaborators.length > 0 && (
                  <div className="flex items-center space-x-1 mr-2">
                    <Users className="w-4 h-4 text-slate-400" />
                    <div className="flex -space-x-2">
                      {activeCollaborators.map((collab) => (
                        <Avatar
                          key={collab.id}
                          className="w-6 h-6 border-2 border-white dark:border-slate-900"
                        >
                          <AvatarFallback
                            className={cn("text-xs text-white", collab.color)}
                          >
                            {collab.initials}
                          </AvatarFallback>
                        </Avatar>
                      ))}
                    </div>
                  </div>
                )}

                <Separator orientation="vertical" className="h-6" />

                <Button variant="outline" size="sm" onClick={handleUndo}>
                  <Undo className="w-4 h-4 mr-2" />
                  Undo
                </Button>
                <Button variant="outline" size="sm" onClick={onAdvancedEdit}>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Advanced Edit
                </Button>
                <Button variant="outline" size="sm" onClick={handleApprove}>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Approve
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleSave}
                  disabled={saving}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? "Saving..." : "Save"}
                </Button>
                {!showRightPanel && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRightPanel(true)}
                  >
                    <PanelRightOpen className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Editing sections */}
          <div className="px-4 pb-6 space-y-4">
            {sections.map((section) => (
              <EditableSectionCard
                key={section.id}
                section={section}
                isEditing={editingSection === section.id}
                onEdit={() => setEditingSection(section.id)}
                onSave={() => setEditingSection(null)}
                onChange={(content) => handleSectionChange(section.id, content)}
              />
            ))}

            {/* Add section button */}
            <Button variant="outline" className="w-full">
              <Edit className="w-4 h-4 mr-2" />
              Add New Section
            </Button>
          </div>
        </div>
      </TwoPanelLayout>
    </div>
  );
}

/**
 * Editable Section Card Component
 */
interface EditableSectionCardProps {
  section: JobSection;
  isEditing: boolean;
  onEdit: () => void;
  onSave: () => void;
  onChange: (content: string) => void;
}

function EditableSectionCard({
  section,
  isEditing,
  onEdit,
  onSave,
  onChange,
}: EditableSectionCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <span className="capitalize">{section.title}</span>
            {section.lastModified && (
              <Badge variant="secondary" className="text-xs font-normal">
                Modified by {section.modifiedBy}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center space-x-2">
            {isEditing ? (
              <Button variant="default" size="sm" onClick={onSave}>
                <CheckCircle className="w-4 h-4 mr-1" />
                Save
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={onEdit}>
                <Edit className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <Textarea
            value={section.content}
            onChange={(e) => onChange(e.target.value)}
            className="min-h-[150px] font-sans"
            placeholder={`Enter ${section.title.toLowerCase()} content...`}
          />
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
              {section.content}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
