import React, { useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeftRight,
  Sparkles,
  Book,
  ClipboardCopy,
  Share2,
} from "lucide-react";

interface DualPaneEditorProps {
  jobId: number;
  sessionId: string;
  mode: "editing" | "translation" | "comparison";
  readonly?: boolean;
  initialLeftContent?: string;
  initialRightContent?: string;
  onContentChange?: (pane: "left" | "right", content: string) => void;
  onSave?: (leftContent: string, rightContent: string) => void;
}

export const DualPaneEditor: React.FC<DualPaneEditorProps> = ({
  jobId,
  sessionId,
  mode,
  readonly = false,
  initialLeftContent = "",
  initialRightContent = "",
  onContentChange,
  onSave,
}) => {
  const [leftPaneContent, setLeftPaneContent] =
    useState<string>(initialLeftContent);
  const [rightPaneContent, setRightPaneContent] =
    useState<string>(initialRightContent);
  const [isSyncScroll, setIsSyncScroll] = useState(true);

  const leftEditorRef = useRef<HTMLTextAreaElement>(null);
  const rightEditorRef = useRef<HTMLTextAreaElement>(null);

  const handleScroll = (scrollingPane: "left" | "right") => {
    if (!isSyncScroll) return;

    const sourceRef = scrollingPane === "left" ? leftEditorRef : rightEditorRef;
    const targetRef = scrollingPane === "left" ? rightEditorRef : leftEditorRef;

    if (sourceRef.current && targetRef.current) {
      targetRef.current.scrollTop = sourceRef.current.scrollTop;
    }
  };

  const EditorPane = ({
    content,
    setContent,
    title,
    language,
    isSource,
  }: {
    content: string;
    setContent: (content: string) => void;
    title: string;
    language: string;
    isSource?: boolean;
  }) => (
    <div className="flex-1 flex flex-col bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {title}
            </span>
            <Badge variant="outline">{language}</Badge>
          </div>
          {isSource && (
            <Select defaultValue="formal">
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="formal">Formal</SelectItem>
                <SelectItem value="informal">Informal</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>
      </div>
      <textarea
        ref={isSource ? leftEditorRef : rightEditorRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onScroll={() => handleScroll(isSource ? "left" : "right")}
        className="flex-1 p-4 bg-transparent resize-none focus:outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500"
        placeholder={`Enter text in ${language}...`}
      />
      <div className="p-2 border-t border-slate-200 dark:border-slate-700 flex justify-end items-center gap-2">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {content.length} characters
        </span>
        <Button variant="ghost" size="icon">
          <ClipboardCopy className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <header className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
          Dual-Pane Editor
        </h2>
        <div className="flex items-center gap-4">
          <Button variant="outline">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button>
            <Sparkles className="h-4 w-4 mr-2" />
            Enhance
          </Button>
        </div>
      </header>

      <div className="flex flex-col lg:flex-row gap-6">
        <EditorPane
          content={leftPaneContent}
          setContent={setLeftPaneContent}
          title="Source"
          language="English (US)"
          isSource
        />

        <div className="flex items-center justify-center">
          <ArrowLeftRight className="h-6 w-6 text-slate-400 dark:text-slate-500" />
        </div>

        <EditorPane
          content={rightPaneContent}
          setContent={setRightPaneContent}
          title="Translated"
          language="French (FR)"
        />
      </div>

      <footer className="mt-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Book className="h-5 w-5 text-slate-500" />
          <span className="text-sm text-slate-600 dark:text-slate-300">
            Dictionary
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            id="sync-scroll"
            checked={isSyncScroll}
            onCheckedChange={setIsSyncScroll}
          />
          <label
            htmlFor="sync-scroll"
            className="text-sm text-slate-600 dark:text-slate-300"
          >
            Sync Scroll
          </label>
        </div>
      </footer>
    </div>
  );
};
