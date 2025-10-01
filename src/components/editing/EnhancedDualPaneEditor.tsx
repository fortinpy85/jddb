"use client";

import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
  WorkflowSteps,
  TRANSLATION_WORKFLOW,
} from "@/components/ui/workflow-steps";
import { SidebarNav, TRANSLATION_NAV } from "@/components/ui/sidebar-nav";
import {
  ArrowLeftRight,
  Sparkles,
  Book,
  ClipboardCopy,
  Share2,
  Languages,
  Copy,
  RotateCcw,
  Settings,
  Palette,
  FileText,
  ChevronDown,
  Globe,
  Zap,
  Users,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useCollaborativeEditor } from "@/hooks/useCollaborativeEditor";
import {
  CollaboratorList,
  type CollaboratorInfo,
} from "@/components/collaboration/CollaboratorList";
import {
  TypingIndicator,
  useTypingIndicator,
  type TypingUser,
} from "@/components/collaboration/TypingIndicator";

interface EnhancedDualPaneEditorProps {
  jobId?: number;
  sessionId?: string;
  userId?: number;
  mode: "editing" | "translation" | "comparison";
  readonly?: boolean;
  initialLeftContent?: string;
  initialRightContent?: string;
  enableCollaboration?: boolean;
  onContentChange?: (pane: "left" | "right", content: string) => void;
  onSave?: (leftContent: string, rightContent: string) => void;
}

export const EnhancedDualPaneEditor: React.FC<EnhancedDualPaneEditorProps> = ({
  jobId,
  sessionId,
  userId = 1, // Default user ID for demo purposes
  mode,
  readonly = false,
  initialLeftContent = "",
  initialRightContent = "",
  enableCollaboration = false,
  onContentChange,
  onSave,
}) => {
  const [leftPaneContent, setLeftPaneContent] =
    useState<string>(initialLeftContent);
  const [rightPaneContent, setRightPaneContent] =
    useState<string>(initialRightContent);
  const [isSyncScroll, setIsSyncScroll] = useState(true);
  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguage, setTargetLanguage] = useState("fr");
  const [formality, setFormality] = useState("default");
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);

  const leftEditorRef = useRef<HTMLTextAreaElement>(null);
  const rightEditorRef = useRef<HTMLTextAreaElement>(null);

  // Typing indicator hook for current user
  const { startTyping, stopTyping } = useTypingIndicator(
    userId,
    (isTyping) => {
      // Send typing status to other collaborators via WebSocket
      if (enableCollaboration && collaboration?.isConnected) {
        // TODO: Send typing_start or typing_stop message
        console.log(`User ${userId} typing:`, isTyping);
      }
    },
    1000,
  );

  // Initialize collaborative editing if enabled
  const collaboration = useCollaborativeEditor(
    enableCollaboration && sessionId && jobId
      ? {
          sessionId,
          userId,
          jobId,
          onDocumentChange: (content) => {
            setLeftPaneContent(content);
            onContentChange?.("left", content);
          },
          onParticipantsChange: (participants) => {
            console.log("Participants updated:", participants);
          },
        }
      : null,
  );

  // Update content when collaborative changes arrive
  useEffect(() => {
    if (enableCollaboration && collaboration?.sessionState?.documentState) {
      setLeftPaneContent(collaboration.sessionState.documentState);
    }
  }, [enableCollaboration, collaboration?.sessionState?.documentState]);

  const handleContentChange = (pane: "left" | "right", content: string) => {
    // Trigger typing indicator
    startTyping();

    if (pane === "left") {
      // Calculate diff and send operation if collaborative mode is enabled
      if (enableCollaboration && collaboration && leftPaneContent !== content) {
        const oldContent = leftPaneContent;
        const newContent = content;

        // Simple diff detection (insert or delete)
        if (newContent.length > oldContent.length) {
          // Insertion detected
          const insertIndex = findDiffIndex(oldContent, newContent);
          const insertedText = newContent.slice(
            insertIndex,
            insertIndex + (newContent.length - oldContent.length),
          );

          collaboration.applyOperation({
            type: "insert",
            position: insertIndex,
            text: insertedText,
          });
        } else if (newContent.length < oldContent.length) {
          // Deletion detected
          const deleteStart = findDiffIndex(oldContent, newContent);
          const deleteEnd =
            deleteStart + (oldContent.length - newContent.length);

          collaboration.applyOperation({
            type: "delete",
            start: deleteStart,
            end: deleteEnd,
          });
        }
      }

      setLeftPaneContent(content);
    } else {
      setRightPaneContent(content);
    }
    onContentChange?.(pane, content);
  };

  // Helper function to find the index where strings differ
  const findDiffIndex = (str1: string, str2: string): number => {
    const minLength = Math.min(str1.length, str2.length);
    for (let i = 0; i < minLength; i++) {
      if (str1[i] !== str2[i]) {
        return i;
      }
    }
    return minLength;
  };

  const handleScroll = (source: "left" | "right") => {
    if (!isSyncScroll) return;

    const sourceRef =
      source === "left" ? leftEditorRef.current : rightEditorRef.current;
    const targetRef =
      source === "left" ? rightEditorRef.current : leftEditorRef.current;

    if (sourceRef && targetRef) {
      const percentage =
        sourceRef.scrollTop / (sourceRef.scrollHeight - sourceRef.clientHeight);
      targetRef.scrollTop =
        percentage * (targetRef.scrollHeight - targetRef.clientHeight);
    }
  };

  const getModeTabs = () => {
    const tabs = [
      {
        id: "text",
        label: "Translate text",
        subtitle: "35 languages",
        icon: <Languages className="w-4 h-4" />,
        active: mode === "translation",
      },
      {
        id: "files",
        label: "Translate files",
        subtitle: ".pdf, .docx, .pptx",
        icon: <FileText className="w-4 h-4" />,
        active: false,
      },
      {
        id: "deepl",
        label: "DeepL Write",
        subtitle: "AI-powered edits",
        icon: <Zap className="w-4 h-4" />,
        active: mode === "editing",
      },
    ];

    return tabs;
  };

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Top Navigation Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex px-6 py-4 justify-between items-center">
          <div className="flex">
            {getModeTabs().map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-3 rounded-lg flex items-center space-x-3 mr-4 transition-all ${
                  tab.active
                    ? "bg-blue-50 border border-blue-200 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                {tab.icon}
                <div className="text-left">
                  <div className="font-medium">{tab.label}</div>
                  <div className="text-xs text-gray-500">{tab.subtitle}</div>
                </div>
              </button>
            ))}
          </div>

          {/* Collaboration Status */}
          {enableCollaboration && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {collaboration?.isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-500" />
                    <span className="text-xs text-green-600 font-medium">
                      Connected
                    </span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-500">Disconnected</span>
                  </>
                )}
              </div>

              {/* Collaborator List */}
              {collaboration?.sessionState &&
                collaboration.sessionState.participants.length > 0 && (
                  <CollaboratorList
                    collaborators={collaboration.sessionState.participants.map(
                      (userId) => ({
                        userId,
                        username: `User ${userId}`,
                        role:
                          userId === collaboration.sessionState?.jobId
                            ? "owner"
                            : "editor",
                        isOnline: true,
                        isTyping: typingUsers.some(
                          (tu) => tu.userId === userId,
                        ),
                        lastActivity: new Date().toISOString(),
                      }),
                    )}
                    currentUserId={userId}
                    maxVisible={3}
                    showRoles={true}
                    showActivity={true}
                  />
                )}

              {/* Typing Indicator */}
              {typingUsers.length > 0 && (
                <TypingIndicator typingUsers={typingUsers} maxVisible={2} />
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          {/* Language Selection */}
          {mode === "translation" && (
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-4">
                  <Select
                    value={sourceLanguage}
                    onValueChange={setSourceLanguage}
                  >
                    <SelectTrigger className="w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English (American)</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button variant="ghost" size="sm" className="p-2">
                    <ArrowLeftRight className="w-4 h-4" />
                  </Button>

                  <Select
                    value={targetLanguage}
                    onValueChange={setTargetLanguage}
                  >
                    <SelectTrigger className="w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="en">English (American)</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}

          {/* Editing Tools */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <Settings className="w-4 h-4 mr-2" />
              Editing tools
            </h3>

            {mode === "translation" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Formality</span>
                  <Select value={formality} onValueChange={setFormality}>
                    <SelectTrigger className="w-28 h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default</SelectItem>
                      <SelectItem value="formal">More formal</SelectItem>
                      <SelectItem value="informal">Less formal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Styles</span>
                  <span className="text-xs text-gray-400">None set</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Show changes</span>
                  <Switch className="scale-75" />
                </div>
              </div>
            )}
          </div>

          {/* Customizations */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">
              Customizations
            </h3>

            <div className="space-y-3">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start text-sm"
              >
                <Settings className="w-4 h-4 mr-2" />
                Custom rules
                <Badge className="ml-auto bg-green-100 text-green-700 text-xs">
                  Pro
                </Badge>
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start text-sm"
              >
                <Book className="w-4 h-4 mr-2" />
                Glossaries
                <span className="ml-auto text-xs text-gray-400">
                  None set →
                </span>
              </Button>
            </div>
          </div>

          {/* Powered by section */}
          <div className="p-6 mt-auto">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Powered by
            </h3>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-sm text-gray-600"
            >
              <Globe className="w-4 h-4 mr-2" />
              Language model
            </Button>
          </div>
        </div>

        {/* Main Editor Area */}
        <div className="flex-1 flex flex-col">
          {/* Main Content */}
          <div className="flex-1 flex">
            {/* Left Pane */}
            <div className="flex-1 flex flex-col bg-white dark:bg-gray-800">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 mb-2">
                  {mode === "translation"
                    ? "Type to translate."
                    : "Type or paste text to see ideas for improvement."}
                </div>
                {mode === "translation" && (
                  <div className="text-xs text-gray-500">
                    Drag and drop to translate PDF, Word (.docx), and PowerPoint
                    (.pptx) files with our document translator.
                  </div>
                )}
              </div>

              <textarea
                ref={leftEditorRef}
                value={leftPaneContent}
                onChange={(e) => handleContentChange("left", e.target.value)}
                onScroll={() => handleScroll("left")}
                className="flex-1 p-4 bg-transparent resize-none focus:outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
                placeholder={
                  mode === "translation"
                    ? "Type to translate."
                    : "Click any word for alternatives or to rephrase a sentence."
                }
                readOnly={readonly}
              />
            </div>

            {/* Right Pane */}
            <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    {mode === "translation" ? "Translation" : "Enhanced text"}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Share2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              <textarea
                ref={rightEditorRef}
                value={rightPaneContent}
                onChange={(e) => handleContentChange("right", e.target.value)}
                onScroll={() => handleScroll("right")}
                className="flex-1 p-4 bg-transparent resize-none focus:outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
                placeholder={
                  mode === "translation"
                    ? "Translation will appear here"
                    : "Enhanced text will appear here"
                }
                readOnly={readonly}
              />
            </div>
          </div>

          {/* Bottom Dictionary Section */}
          {mode === "translation" && (
            <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Book className="w-4 h-4" />
                <span className="font-medium">Dictionary</span>
              </div>
              <div className="mt-2 text-sm text-gray-500">
                The dictionary is unavailable for this language pair.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
