# Phase 2 Frontend Architecture - Dual-Pane Editor
*React Component Architecture for Collaborative Editing*

## Overview

This document outlines the React/TypeScript component architecture for JDDB Phase 2's dual-pane collaborative editing system, supporting side-by-side editing, translation concordance, and real-time collaboration.

## Current Frontend Foundation

### Existing Architecture (Phase 1)
- **Framework**: React 18 + TypeScript + Bun
- **UI Library**: Radix UI + Tailwind CSS
- **State Management**: Zustand
- **Routing**: Next.js App Router
- **Testing**: Jest + Testing Library + Playwright

### Current Components Structure
```
src/
├── components/
│   ├── ui/            # Reusable UI components (Radix UI based)
│   ├── JobList.tsx    # Job listing with filters
│   ├── JobDetails.tsx # Single job view
│   ├── SearchInterface.tsx
│   ├── BulkUpload.tsx
│   └── StatsDashboard.tsx
├── lib/
│   ├── api.ts         # API client
│   ├── store.ts       # Zustand state management
│   └── types.ts       # TypeScript types
└── hooks/             # Custom React hooks
```

## Phase 2 Component Architecture

### 1. Dual-Pane Editor Core Components

```typescript
// src/components/editing/DualPaneEditor.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useCollaboration } from '@/hooks/useCollaboration';
import { useWebSocket } from '@/hooks/useWebSocket';
import { DocumentEditor } from './DocumentEditor';
import { CollaborationPanel } from './CollaborationPanel';
import { AIAssistantPanel } from './AIAssistantPanel';

interface DualPaneEditorProps {
  jobId: number;
  sessionId: string;
  mode: 'editing' | 'translation' | 'comparison';
  readonly?: boolean;
}

export const DualPaneEditor: React.FC<DualPaneEditorProps> = ({
  jobId,
  sessionId,
  mode,
  readonly = false
}) => {
  const [leftPaneContent, setLeftPaneContent] = useState<string>('');
  const [rightPaneContent, setRightPaneContent] = useState<string>('');
  const [syncScroll, setSyncScroll] = useState(true);
  const [layout, setLayout] = useState<'horizontal' | 'vertical'>('horizontal');

  const leftEditorRef = useRef<HTMLDivElement>(null);
  const rightEditorRef = useRef<HTMLDivElement>(null);

  const {
    collaborators,
    userCursors,
    comments,
    isConnected,
    sendDocumentChange,
    sendCursorPosition
  } = useCollaboration(sessionId);

  const handleLeftPaneChange = (content: string, change: DocumentChange) => {
    setLeftPaneContent(content);
    if (!readonly) {
      sendDocumentChange('left', change);
    }
  };

  const handleRightPaneChange = (content: string, change: DocumentChange) => {
    setRightPaneContent(content);
    if (!readonly) {
      sendDocumentChange('right', change);
    }
  };

  const handleSyncScroll = (pane: 'left' | 'right', scrollPosition: number) => {
    if (!syncScroll) return;

    const targetRef = pane === 'left' ? rightEditorRef : leftEditorRef;
    if (targetRef.current) {
      targetRef.current.scrollTop = scrollPosition;
    }
  };

  return (
    <div className="dual-pane-editor h-full flex flex-col">
      <EditorToolbar
        layout={layout}
        onLayoutChange={setLayout}
        syncScroll={syncScroll}
        onSyncScrollChange={setSyncScroll}
        collaborators={collaborators}
        isConnected={isConnected}
      />

      <div className={`flex-1 flex ${layout === 'vertical' ? 'flex-col' : 'flex-row'}`}>
        <ResizablePane initialSize={50}>
          <DocumentEditor
            ref={leftEditorRef}
            content={leftPaneContent}
            onChange={handleLeftPaneChange}
            onScroll={(pos) => handleSyncScroll('left', pos)}
            title={mode === 'translation' ? 'Source Document' : 'Original'}
            language={mode === 'translation' ? 'en' : undefined}
            readonly={readonly}
            collaborators={collaborators}
            userCursors={userCursors.filter(c => c.pane === 'left')}
            comments={comments.filter(c => c.pane === 'left')}
          />
        </ResizablePane>

        <PaneDivider orientation={layout} />

        <ResizablePane initialSize={50}>
          <DocumentEditor
            ref={rightEditorRef}
            content={rightPaneContent}
            onChange={handleRightPaneChange}
            onScroll={(pos) => handleSyncScroll('right', pos)}
            title={mode === 'translation' ? 'Target Document' : 'Enhanced'}
            language={mode === 'translation' ? 'fr' : undefined}
            readonly={readonly}
            collaborators={collaborators}
            userCursors={userCursors.filter(c => c.pane === 'right')}
            comments={comments.filter(c => c.pane === 'right')}
          />
        </ResizablePane>
      </div>

      {mode === 'editing' && (
        <AIAssistantPanel
          leftContent={leftPaneContent}
          rightContent={rightPaneContent}
          onSuggestionApply={(pane, suggestion) => {
            if (pane === 'left') {
              setLeftPaneContent(suggestion.appliedText);
            } else {
              setRightPaneContent(suggestion.appliedText);
            }
          }}
        />
      )}

      <CollaborationPanel
        collaborators={collaborators}
        comments={comments}
        onCommentAdd={(comment) => {
          // Handle comment addition
        }}
      />
    </div>
  );
};
```

### 2. Rich Text Document Editor

```typescript
// src/components/editing/DocumentEditor.tsx
import React, { useImperativeHandle, forwardRef, useCallback, useEffect } from 'react';
import { EditorContent, useEditor, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Collaboration from '@tiptap/extension-collaboration';
import CollaborationCursor from '@tiptap/extension-collaboration-cursor';
import { Comment } from '@tiptap/extension-comment';
import { Placeholder } from '@tiptap/extension-placeholder';

interface DocumentEditorProps {
  content: string;
  onChange: (content: string, change: DocumentChange) => void;
  onScroll: (position: number) => void;
  onCursorChange?: (position: number) => void;
  title: string;
  language?: string;
  readonly?: boolean;
  collaborators: Collaborator[];
  userCursors: UserCursor[];
  comments: DocumentComment[];
}

export const DocumentEditor = forwardRef<HTMLDivElement, DocumentEditorProps>(({
  content,
  onChange,
  onScroll,
  onCursorChange,
  title,
  language,
  readonly = false,
  collaborators,
  userCursors,
  comments
}, ref) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Start typing your job description...',
      }),
      Comment.configure({
        HTMLAttributes: {
          class: 'comment',
        },
      }),
      // Real-time collaboration extensions would be configured here
    ],
    content,
    editable: !readonly,
    onUpdate: ({ editor }) => {
      const newContent = editor.getHTML();
      const change = calculateDocumentChange(content, newContent);
      onChange(newContent, change);
    },
    onSelectionUpdate: ({ editor }) => {
      const { from } = editor.state.selection;
      onCursorChange?.(from);
    },
  });

  useImperativeHandle(ref, () => ({
    scrollTop: 0,
    scrollTo: (position: number) => {
      // Implement scroll synchronization
    }
  }));

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = event.currentTarget.scrollTop;
    onScroll(scrollTop);
  }, [onScroll]);

  // Render user cursors
  const renderUserCursors = () => {
    return userCursors.map(cursor => (
      <UserCursorIndicator
        key={cursor.userId}
        user={cursor.user}
        position={cursor.position}
        color={cursor.color}
      />
    ));
  };

  return (
    <div className="document-editor h-full flex flex-col border rounded-lg">
      <div className="editor-header bg-gray-50 p-3 border-b flex justify-between items-center">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">{title}</h3>
          {language && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
              {language.toUpperCase()}
            </span>
          )}
          {readonly && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
              Read Only
            </span>
          )}
        </div>
        <EditorToolbar editor={editor} readonly={readonly} />
      </div>

      <div
        className="editor-content flex-1 relative overflow-auto"
        onScroll={handleScroll}
        ref={ref}
      >
        <EditorContent
          editor={editor}
          className="prose max-w-none p-4 min-h-full focus:outline-none"
        />

        {/* User cursors overlay */}
        <div className="absolute inset-0 pointer-events-none">
          {renderUserCursors()}
        </div>

        {/* Comments overlay */}
        <CommentsOverlay comments={comments} editor={editor} />
      </div>

      <EditorFooter
        wordCount={editor?.storage.characterCount.words() || 0}
        characterCount={editor?.storage.characterCount.characters() || 0}
        collaborators={collaborators}
      />
    </div>
  );
});
```

### 3. Real-time Collaboration Components

```typescript
// src/components/editing/CollaborationPanel.tsx
import React, { useState } from 'react';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface CollaborationPanelProps {
  collaborators: Collaborator[];
  comments: DocumentComment[];
  onCommentAdd: (comment: NewComment) => void;
  onCommentReply: (commentId: string, reply: string) => void;
  onCommentResolve: (commentId: string) => void;
}

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({
  collaborators,
  comments,
  onCommentAdd,
  onCommentReply,
  onCommentResolve
}) => {
  const [newComment, setNewComment] = useState('');
  const [showAddComment, setShowAddComment] = useState(false);

  return (
    <div className="collaboration-panel w-80 bg-white border-l flex flex-col">
      {/* Active Collaborators */}
      <Card className="m-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Active Collaborators ({collaborators.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {collaborators.map(collaborator => (
              <div key={collaborator.id} className="flex items-center gap-2">
                <Avatar className="w-6 h-6">
                  <AvatarImage src={collaborator.avatar} />
                  <AvatarFallback>{collaborator.name.charAt(0)}</AvatarFallback>
                </Avatar>
                <span className="text-xs">{collaborator.name}</span>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: collaborator.color }}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Comments Section */}
      <Card className="mx-4 flex-1">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <CardTitle className="text-sm">Comments ({comments.length})</CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowAddComment(!showAddComment)}
            >
              Add Comment
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {showAddComment && (
            <div className="space-y-2">
              <Textarea
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="min-h-[80px]"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    onCommentAdd({
                      text: newComment,
                      position: 0, // Current cursor position
                      pane: 'left' // Current active pane
                    });
                    setNewComment('');
                    setShowAddComment(false);
                  }}
                >
                  Add
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setNewComment('');
                    setShowAddComment(false);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {comments.map(comment => (
              <CommentThread
                key={comment.id}
                comment={comment}
                onReply={(reply) => onCommentReply(comment.id, reply)}
                onResolve={() => onCommentResolve(comment.id)}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// src/components/editing/CommentThread.tsx
const CommentThread: React.FC<{
  comment: DocumentComment;
  onReply: (reply: string) => void;
  onResolve: () => void;
}> = ({ comment, onReply, onResolve }) => {
  const [showReply, setShowReply] = useState(false);
  const [replyText, setReplyText] = useState('');

  return (
    <div className="comment-thread border rounded p-3 space-y-2">
      <div className="flex items-start gap-2">
        <Avatar className="w-6 h-6">
          <AvatarFallback>{comment.author.name.charAt(0)}</AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">{comment.author.name}</span>
            <span className="text-xs text-gray-500">
              {formatTimestamp(comment.createdAt)}
            </span>
          </div>
          <p className="text-sm">{comment.text}</p>

          {comment.referencedText && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
              "{comment.referencedText}"
            </div>
          )}

          <div className="flex gap-2 mt-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-6 px-2 text-xs"
              onClick={() => setShowReply(!showReply)}
            >
              Reply
            </Button>
            {comment.status === 'open' && (
              <Button
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-xs"
                onClick={onResolve}
              >
                Resolve
              </Button>
            )}
          </div>
        </div>
      </div>

      {comment.replies && comment.replies.length > 0 && (
        <div className="ml-8 space-y-2">
          {comment.replies.map(reply => (
            <div key={reply.id} className="flex items-start gap-2">
              <Avatar className="w-5 h-5">
                <AvatarFallback>{reply.author.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium">{reply.author.name}</span>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(reply.createdAt)}
                  </span>
                </div>
                <p className="text-xs">{reply.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {showReply && (
        <div className="ml-8 space-y-2">
          <Textarea
            placeholder="Write a reply..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            className="min-h-[60px] text-sm"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => {
                onReply(replyText);
                setReplyText('');
                setShowReply(false);
              }}
            >
              Reply
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setReplyText('');
                setShowReply(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
```

### 4. AI Assistant Integration

```typescript
// src/components/editing/AIAssistantPanel.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, CheckCircle, XCircle } from 'lucide-react';

interface AIAssistantPanelProps {
  leftContent: string;
  rightContent: string;
  onSuggestionApply: (pane: 'left' | 'right', suggestion: AISuggestion) => void;
}

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  leftContent,
  rightContent,
  onSuggestionApply
}) => {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeProvider, setActiveProvider] = useState<AIProvider>('openai');

  const requestSuggestions = async (type: SuggestionType) => {
    setIsLoading(true);
    try {
      const response = await aiService.getSuggestions({
        content: leftContent,
        type,
        provider: activeProvider
      });
      setSuggestions(response.suggestions);
    } catch (error) {
      console.error('Failed to get AI suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="ai-assistant-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          AI Assistant
        </CardTitle>
        <div className="flex gap-2">
          {(['openai', 'claude', 'copilot'] as AIProvider[]).map(provider => (
            <Button
              key={provider}
              size="sm"
              variant={activeProvider === provider ? 'default' : 'outline'}
              onClick={() => setActiveProvider(provider)}
              className="h-6 text-xs"
            >
              {provider}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => requestSuggestions('grammar')}
            disabled={isLoading}
          >
            Grammar Check
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => requestSuggestions('style')}
            disabled={isLoading}
          >
            Style Improve
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => requestSuggestions('compliance')}
            disabled={isLoading}
          >
            Compliance
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => requestSuggestions('enhancement')}
            disabled={isLoading}
          >
            Enhance
          </Button>
        </div>

        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            Getting AI suggestions...
          </div>
        )}

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {suggestions.map(suggestion => (
            <AISuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              onApply={(pane) => onSuggestionApply(pane, suggestion)}
              onDismiss={() => {
                setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

const AISuggestionCard: React.FC<{
  suggestion: AISuggestion;
  onApply: (pane: 'left' | 'right') => void;
  onDismiss: () => void;
}> = ({ suggestion, onApply, onDismiss }) => {
  return (
    <div className="border rounded p-3 space-y-2">
      <div className="flex items-center justify-between">
        <Badge variant="secondary" className="text-xs">
          {suggestion.type}
        </Badge>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          Confidence: {Math.round(suggestion.confidence * 100)}%
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-sm">
          <div className="text-gray-600 text-xs mb-1">Original:</div>
          <div className="bg-red-50 p-2 rounded text-red-800">
            {suggestion.originalText}
          </div>
        </div>

        <div className="text-sm">
          <div className="text-gray-600 text-xs mb-1">Suggested:</div>
          <div className="bg-green-50 p-2 rounded text-green-800">
            {suggestion.suggestedText}
          </div>
        </div>

        {suggestion.explanation && (
          <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
            {suggestion.explanation}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => onApply('left')}
          className="h-6 text-xs"
        >
          <CheckCircle className="w-3 h-3 mr-1" />
          Apply to Left
        </Button>
        <Button
          size="sm"
          onClick={() => onApply('right')}
          className="h-6 text-xs"
        >
          <CheckCircle className="w-3 h-3 mr-1" />
          Apply to Right
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onDismiss}
          className="h-6 text-xs"
        >
          <XCircle className="w-3 h-3 mr-1" />
          Dismiss
        </Button>
      </div>
    </div>
  );
};
```

### 5. Translation-Specific Components

```typescript
// src/components/translation/TranslationWorkspace.tsx
import React, { useState, useEffect } from 'react';
import { DualPaneEditor } from '../editing/DualPaneEditor';
import { TranslationMemoryPanel } from './TranslationMemoryPanel';
import { TerminologyPanel } from './TerminologyPanel';
import { AlignmentVisualization } from './AlignmentVisualization';

interface TranslationWorkspaceProps {
  translationPairId: string;
  sourceJobId: number;
  targetJobId: number;
  sourceLanguage: string;
  targetLanguage: string;
}

export const TranslationWorkspace: React.FC<TranslationWorkspaceProps> = ({
  translationPairId,
  sourceJobId,
  targetJobId,
  sourceLanguage,
  targetLanguage
}) => {
  const [translationMemoryMatches, setTranslationMemoryMatches] = useState<TMMatch[]>([]);
  const [terminologyMatches, setTerminologyMatches] = useState<TermMatch[]>([]);
  const [alignmentData, setAlignmentData] = useState<AlignmentData | null>(null);

  return (
    <div className="translation-workspace h-full flex">
      <div className="flex-1">
        <DualPaneEditor
          jobId={sourceJobId}
          sessionId={translationPairId}
          mode="translation"
        />
      </div>

      <div className="w-96 bg-white border-l flex flex-col">
        <TranslationMemoryPanel
          matches={translationMemoryMatches}
          onMatchSelect={(match) => {
            // Apply translation memory match
          }}
        />

        <TerminologyPanel
          matches={terminologyMatches}
          sourceLanguage={sourceLanguage}
          targetLanguage={targetLanguage}
          onTermSelect={(term) => {
            // Apply terminology
          }}
        />

        <AlignmentVisualization
          alignmentData={alignmentData}
          onAlignmentUpdate={(newAlignment) => {
            setAlignmentData(newAlignment);
          }}
        />
      </div>
    </div>
  );
};
```

### 6. State Management Integration

```typescript
// src/lib/store/editingStore.ts
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

interface EditingSession {
  sessionId: string;
  jobId: number;
  collaborators: Collaborator[];
  documentState: DocumentState;
  comments: DocumentComment[];
  isConnected: boolean;
}

interface EditingStore {
  // State
  activeSessions: Map<string, EditingSession>;
  currentSessionId: string | null;

  // Actions
  createSession: (sessionId: string, jobId: number) => void;
  joinSession: (sessionId: string) => void;
  leaveSession: (sessionId: string) => void;
  updateDocumentContent: (sessionId: string, pane: 'left' | 'right', content: string) => void;
  addCollaborator: (sessionId: string, collaborator: Collaborator) => void;
  removeCollaborator: (sessionId: string, userId: number) => void;
  addComment: (sessionId: string, comment: DocumentComment) => void;
  updateConnectionStatus: (sessionId: string, isConnected: boolean) => void;
}

export const useEditingStore = create<EditingStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      activeSessions: new Map(),
      currentSessionId: null,

      createSession: (sessionId, jobId) => {
        set((state) => {
          const newSession: EditingSession = {
            sessionId,
            jobId,
            collaborators: [],
            documentState: { left: '', right: '' },
            comments: [],
            isConnected: false
          };

          const newSessions = new Map(state.activeSessions);
          newSessions.set(sessionId, newSession);

          return {
            activeSessions: newSessions,
            currentSessionId: sessionId
          };
        });
      },

      joinSession: (sessionId) => {
        set(() => ({ currentSessionId: sessionId }));
      },

      leaveSession: (sessionId) => {
        set((state) => {
          const newSessions = new Map(state.activeSessions);
          newSessions.delete(sessionId);

          return {
            activeSessions: newSessions,
            currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId
          };
        });
      },

      updateDocumentContent: (sessionId, pane, content) => {
        set((state) => {
          const session = state.activeSessions.get(sessionId);
          if (!session) return state;

          const updatedSession = {
            ...session,
            documentState: {
              ...session.documentState,
              [pane]: content
            }
          };

          const newSessions = new Map(state.activeSessions);
          newSessions.set(sessionId, updatedSession);

          return { activeSessions: newSessions };
        });
      },

      // ... other actions
    })),
    { name: 'editing-store' }
  )
);
```

### 7. Custom Hooks for Real-time Features

```typescript
// src/hooks/useCollaboration.ts
import { useEffect, useState } from 'react';
import { useWebSocket } from './useWebSocket';
import { useEditingStore } from '@/lib/store/editingStore';

export const useCollaboration = (sessionId: string) => {
  const {
    activeSessions,
    addCollaborator,
    removeCollaborator,
    updateDocumentContent,
    updateConnectionStatus
  } = useEditingStore();

  const session = activeSessions.get(sessionId);

  const {
    isConnected,
    send,
    lastMessage
  } = useWebSocket(`/editing/${sessionId}`);

  useEffect(() => {
    updateConnectionStatus(sessionId, isConnected);
  }, [isConnected, sessionId]);

  useEffect(() => {
    if (lastMessage) {
      handleWebSocketMessage(lastMessage.data);
    }
  }, [lastMessage]);

  const handleWebSocketMessage = (message: string) => {
    const data = JSON.parse(message);

    switch (data.type) {
      case 'user_join':
        addCollaborator(sessionId, data.user);
        break;
      case 'user_leave':
        removeCollaborator(sessionId, data.userId);
        break;
      case 'document_change':
        updateDocumentContent(sessionId, data.pane, data.content);
        break;
      // ... handle other message types
    }
  };

  const sendDocumentChange = (pane: 'left' | 'right', change: DocumentChange) => {
    send(JSON.stringify({
      type: 'document_change',
      pane,
      change,
      timestamp: Date.now()
    }));
  };

  const sendCursorPosition = (pane: 'left' | 'right', position: number) => {
    send(JSON.stringify({
      type: 'cursor_position',
      pane,
      position,
      timestamp: Date.now()
    }));
  };

  return {
    collaborators: session?.collaborators || [],
    userCursors: [], // Derived from real-time data
    comments: session?.comments || [],
    isConnected: session?.isConnected || false,
    sendDocumentChange,
    sendCursorPosition
  };
};

// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (endpoint: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const connect = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/ws${endpoint}`;

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        setLastMessage(event);
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        attemptReconnect();
      };

      ws.current.onerror = (error) => {
        setError('WebSocket connection error');
        setIsConnected(false);
      };
    } catch (error) {
      setError('Failed to create WebSocket connection');
    }
  };

  const attemptReconnect = () => {
    if (reconnectAttempts.current < 5) {
      const delay = Math.pow(2, reconnectAttempts.current) * 1000;
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current++;
        connect();
      }, delay);
    }
  };

  const send = (data: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(data);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    ws.current?.close();
  };

  useEffect(() => {
    connect();
    return disconnect;
  }, [endpoint]);

  return {
    isConnected,
    lastMessage,
    error,
    send,
    disconnect
  };
};
```

## Component Integration with Existing Architecture

### Updated Main Application Structure

```typescript
// src/app/page.tsx - Updated with editing capabilities
export default function HomePage() {
  const [activeTab, setActiveTab] = useState("dashboard");

  // Add new tabs for Phase 2
  const tabOrder = [
    "dashboard",
    "jobs",
    "upload",
    "search",
    "editing",     // New: Document editing workspace
    "translation", // New: Translation workspace
    "collaboration", // New: Collaboration management
    "compare",
    "stats"
  ];

  return (
    <ThemeProvider>
      <ToastProvider>
        <ErrorBoundaryWrapper>
          <div className="min-h-screen bg-background">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-8">
                {/* Updated tab list with new editing tabs */}
              </TabsList>

              {/* Existing tabs... */}

              <TabsContent value="editing" className="mt-6">
                <EditingWorkspace />
              </TabsContent>

              <TabsContent value="translation" className="mt-6">
                <TranslationWorkspace />
              </TabsContent>

              <TabsContent value="collaboration" className="mt-6">
                <CollaborationDashboard />
              </TabsContent>
            </Tabs>
          </div>
        </ErrorBoundaryWrapper>
      </ToastProvider>
    </ThemeProvider>
  );
}
```

This comprehensive frontend architecture provides the foundation for Phase 2's collaborative editing features while maintaining compatibility with the existing codebase and following React best practices.