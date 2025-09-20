import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  Users,
  MessageCircle,
  Plus,
  Send,
  CheckCircle,
  Clock,
  AlertCircle,
  MoreHorizontal
} from 'lucide-react';

interface Collaborator {
  id: string;
  name: string;
  avatar?: string;
  color: string;
  isActive: boolean;
  role: 'editor' | 'reviewer' | 'admin';
  lastSeen?: string;
}

interface DocumentComment {
  id: string;
  text: string;
  author: Collaborator;
  createdAt: string;
  position: number;
  pane: 'left' | 'right';
  referencedText?: string;
  status: 'open' | 'resolved';
  replies?: DocumentComment[];
}

interface CollaborationPanelProps {
  className?: string;
}

// Mock data
const mockCollaborators: Collaborator[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    color: '#3B82F6',
    isActive: true,
    role: 'admin',
    lastSeen: new Date().toISOString()
  },
  {
    id: '2',
    name: 'Bob Smith',
    color: '#10B981',
    isActive: true,
    role: 'editor',
    lastSeen: new Date(Date.now() - 5 * 60 * 1000).toISOString()
  },
  {
    id: '3',
    name: 'Carol Wilson',
    color: '#F59E0B',
    isActive: false,
    role: 'reviewer',
    lastSeen: new Date(Date.now() - 30 * 60 * 1000).toISOString()
  }
];

const mockComments: DocumentComment[] = [
  {
    id: '1',
    text: 'This section needs clarification on the reporting structure. Can we be more specific about the number of direct reports?',
    author: mockCollaborators[0],
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    position: 150,
    pane: 'left',
    referencedText: 'Reports to Director',
    status: 'open',
    replies: [
      {
        id: '1-1',
        text: 'Good point! I\'ll update this with the specific number.',
        author: mockCollaborators[1],
        createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        position: 150,
        pane: 'left',
        status: 'open'
      }
    ]
  },
  {
    id: '2',
    text: 'The qualifications section looks comprehensive. Should we add language requirements?',
    author: mockCollaborators[2],
    createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    position: 300,
    pane: 'right',
    referencedText: 'Required qualifications',
    status: 'resolved'
  }
];

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({ className }) => {
  const [collaborators] = useState<Collaborator[]>(mockCollaborators);
  const [comments, setComments] = useState<DocumentComment[]>(mockComments);
  const [newComment, setNewComment] = useState('');
  const [showAddComment, setShowAddComment] = useState(false);
  const [replyText, setReplyText] = useState<{ [key: string]: string }>({});

  const formatLastSeen = (dateString?: string) => {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'admin': return 'default';
      case 'editor': return 'secondary';
      case 'reviewer': return 'outline';
      default: return 'secondary';
    }
  };

  const handleAddComment = () => {
    if (!newComment.trim()) return;

    const comment: DocumentComment = {
      id: `comment-${Date.now()}`,
      text: newComment,
      author: collaborators[0], // Current user
      createdAt: new Date().toISOString(),
      position: 0,
      pane: 'left',
      status: 'open'
    };

    setComments(prev => [comment, ...prev]);
    setNewComment('');
    setShowAddComment(false);
  };

  const handleReply = (commentId: string) => {
    const reply = replyText[commentId];
    if (!reply?.trim()) return;

    setComments(prev => prev.map(comment => {
      if (comment.id === commentId) {
        const newReply: DocumentComment = {
          id: `${commentId}-${Date.now()}`,
          text: reply,
          author: collaborators[0],
          createdAt: new Date().toISOString(),
          position: comment.position,
          pane: comment.pane,
          status: 'open'
        };

        return {
          ...comment,
          replies: [...(comment.replies || []), newReply]
        };
      }
      return comment;
    }));

    setReplyText(prev => ({ ...prev, [commentId]: '' }));
  };

  const handleResolveComment = (commentId: string) => {
    setComments(prev => prev.map(comment =>
      comment.id === commentId ? { ...comment, status: 'resolved' as const } : comment
    ));
  };

  const activeCollaborators = collaborators.filter(c => c.isActive);
  const openComments = comments.filter(c => c.status === 'open');

  return (
    <div className={`w-80 bg-white border-l flex flex-col ${className}`}>
      {/* Active Collaborators */}
      <Card className="m-4 mb-2">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Users className="w-4 h-4" />
            Active Collaborators ({activeCollaborators.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-3">
            {collaborators.map(collaborator => (
              <div key={collaborator.id} className="flex items-center gap-3">
                <div className="relative">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback
                      className="text-xs"
                      style={{ backgroundColor: `${collaborator.color}20`, color: collaborator.color }}
                    >
                      {collaborator.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  {collaborator.isActive && (
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{collaborator.name}</span>
                    <Badge variant={getRoleBadgeVariant(collaborator.role)} className="text-xs">
                      {collaborator.role}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-500">
                    {collaborator.isActive ? 'Active now' : `Last seen ${formatLastSeen(collaborator.lastSeen)}`}
                  </div>
                </div>

                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: collaborator.color }}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Separator className="mx-4" />

      {/* Comments Section */}
      <Card className="mx-4 mt-2 flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle className="text-sm flex items-center gap-2">
              <MessageCircle className="w-4 h-4" />
              Comments ({comments.length})
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowAddComment(!showAddComment)}
            >
              <Plus className="w-3 h-3" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pt-0 flex-1 flex flex-col">
          {/* Add new comment */}
          {showAddComment && (
            <div className="space-y-2 mb-4 p-3 border rounded-lg bg-gray-50">
              <Textarea
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="min-h-[60px] text-sm"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAddComment} disabled={!newComment.trim()}>
                  <Send className="w-3 h-3 mr-1" />
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

          {/* Comments list */}
          <div className="space-y-3 flex-1 overflow-y-auto">
            {comments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No comments yet</p>
                <p className="text-xs">Start a discussion about this document</p>
              </div>
            ) : (
              comments.map(comment => (
                <CommentThread
                  key={comment.id}
                  comment={comment}
                  replyText={replyText[comment.id] || ''}
                  onReplyChange={(text) => setReplyText(prev => ({ ...prev, [comment.id]: text }))}
                  onReply={() => handleReply(comment.id)}
                  onResolve={() => handleResolveComment(comment.id)}
                />
              ))
            )}
          </div>

          {/* Summary */}
          {comments.length > 0 && (
            <div className="pt-3 border-t">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{openComments.length} open</span>
                <span>{comments.length - openComments.length} resolved</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const CommentThread: React.FC<{
  comment: DocumentComment;
  replyText: string;
  onReplyChange: (text: string) => void;
  onReply: () => void;
  onResolve: () => void;
}> = ({ comment, replyText, onReplyChange, onReply, onResolve }) => {
  const [showReply, setShowReply] = useState(false);

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className={`border rounded-lg p-3 space-y-2 ${
      comment.status === 'resolved' ? 'bg-green-50 border-green-200' : 'bg-white'
    }`}>
      <div className="flex items-start gap-2">
        <Avatar className="w-6 h-6 mt-1">
          <AvatarFallback
            className="text-xs"
            style={{ backgroundColor: `${comment.author.color}20`, color: comment.author.color }}
          >
            {comment.author.name.charAt(0)}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">{comment.author.name}</span>
            <Badge variant="outline" className="text-xs">
              {comment.pane}
            </Badge>
            {comment.status === 'resolved' && (
              <CheckCircle className="w-3 h-3 text-green-600" />
            )}
          </div>

          <p className="text-sm text-gray-700">{comment.text}</p>

          {comment.referencedText && (
            <div className="mt-2 p-2 bg-gray-100 rounded text-xs border-l-2 border-gray-300">
              "{comment.referencedText}"
            </div>
          )}

          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimestamp(comment.createdAt)}
            </span>

            {comment.status === 'open' && (
              <>
                <button
                  onClick={() => setShowReply(!showReply)}
                  className="hover:text-blue-600 transition-colors"
                >
                  Reply
                </button>
                <button
                  onClick={onResolve}
                  className="hover:text-green-600 transition-colors"
                >
                  Resolve
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="ml-8 space-y-2 border-l-2 border-gray-200 pl-3">
          {comment.replies.map(reply => (
            <div key={reply.id} className="flex items-start gap-2">
              <Avatar className="w-5 h-5 mt-1">
                <AvatarFallback
                  className="text-xs"
                  style={{ backgroundColor: `${reply.author.color}20`, color: reply.author.color }}
                >
                  {reply.author.name.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium">{reply.author.name}</span>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(reply.createdAt)}
                  </span>
                </div>
                <p className="text-xs text-gray-700">{reply.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reply input */}
      {showReply && comment.status === 'open' && (
        <div className="ml-8 space-y-2">
          <Textarea
            placeholder="Write a reply..."
            value={replyText}
            onChange={(e) => onReplyChange(e.target.value)}
            className="min-h-[50px] text-sm"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => {
                onReply();
                setShowReply(false);
              }}
              disabled={!replyText.trim()}
            >
              <Send className="w-3 h-3 mr-1" />
              Reply
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                onReplyChange('');
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