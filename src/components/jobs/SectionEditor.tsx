/**
 * Section Editor Component
 * Editable job description section with Save/Cancel actions
 * Supports concurrent editing of multiple sections for cut/paste operations
 */

import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useTranslation } from "react-i18next";
import { Edit, Save, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SectionEditorProps {
  sectionId: number;
  sectionType: string;
  initialContent: string;
  onSave: (sectionId: number, content: string) => Promise<void>;
  onCancel?: () => void;
  isEditing?: boolean;
  onEditToggle?: (editing: boolean) => void;
  className?: string;
}

export function SectionEditor({
  sectionId,
  sectionType,
  initialContent,
  onSave,
  onCancel,
  isEditing: externalIsEditing,
  onEditToggle,
  className,
}: SectionEditorProps) {
  const { t } = useTranslation(["jobs", "common"]);
  const [internalIsEditing, setInternalIsEditing] = useState(false);
  const [content, setContent] = useState(initialContent);
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Determine which editing state to use (external or internal)
  const isEditing =
    externalIsEditing !== undefined ? externalIsEditing : internalIsEditing;

  // Sync internal content with prop changes when not editing
  useEffect(() => {
    if (!isEditing) {
      setContent(initialContent);
    }
  }, [initialContent, isEditing]);

  // Auto-focus textarea when entering edit mode
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      // Move cursor to end
      textareaRef.current.setSelectionRange(content.length, content.length);
    }
  }, [isEditing]);

  const handleEditClick = () => {
    const newEditingState = !isEditing;
    if (onEditToggle) {
      onEditToggle(newEditingState);
    } else {
      setInternalIsEditing(newEditingState);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(sectionId, content);
      // Exit edit mode after successful save
      if (onEditToggle) {
        onEditToggle(false);
      } else {
        setInternalIsEditing(false);
      }
    } catch (error) {
      console.error("Failed to save section:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Revert to original content
    setContent(initialContent);
    if (onCancel) {
      onCancel();
    }
    if (onEditToggle) {
      onEditToggle(false);
    } else {
      setInternalIsEditing(false);
    }
  };

  const formatSectionTitle = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-all",
        isEditing && "ring-2 ring-primary ring-offset-2",
        className,
      )}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg">{formatSectionTitle(sectionType)}</span>
          {!isEditing ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEditClick}
              aria-label={t("jobs:actions.editSectionAria", {
                section: formatSectionTitle(sectionType),
              })}
            >
              <Edit className="w-4 h-4 mr-2" />
              {t("jobs:actions.edit")}
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={isSaving}
                aria-label={t("common:actions.cancel")}
              >
                <X className="w-4 h-4 mr-2" />
                {t("common:actions.cancel")}
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSave}
                disabled={isSaving || content === initialContent}
                aria-label={t("common:actions.save")}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t("common:actions.saving")}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {t("common:actions.save")}
                  </>
                )}
              </Button>
            </div>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <Textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[200px] font-mono text-sm resize-y"
            placeholder={t("jobs:placeholders.sectionContent")}
            disabled={isSaving}
          />
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
              {content || t("jobs:messages.noContent")}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
