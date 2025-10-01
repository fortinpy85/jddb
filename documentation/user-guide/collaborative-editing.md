# Collaborative Editing User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Interface Overview](#interface-overview)
4. [Real-time Collaboration](#real-time-collaboration)
5. [Translation Memory](#translation-memory)
6. [Document Management](#document-management)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [FAQ](#frequently-asked-questions)

## Introduction

The JDDB Collaborative Editing feature enables multiple users to simultaneously edit job descriptions in real-time. This guide will help you navigate the dual-pane editor, understand collaboration features, and make the most of the translation memory system.

### Key Features

- **Real-time collaboration** with multiple simultaneous editors
- **Dual-pane editing** for side-by-side English/French editing
- **Translation memory** with intelligent suggestions
- **Live presence indicators** showing who's actively editing
- **Automatic conflict resolution** for concurrent changes
- **Instant synchronization** across all connected users

## Getting Started

### Accessing the Collaborative Editor

1. **Navigate to the Edit tab** in the main JDDB interface
2. **Select a job description** from the list to begin editing
3. **The dual-pane editor will open** with the current document content
4. **Your presence will be visible** to other users editing the same document

![Collaborative Editor Interface](../images/collaborative-editor-overview.png)

### Authentication Requirements

- **Valid user account** with editing permissions
- **Document access rights** for the specific job description
- **Active network connection** for real-time features

## Interface Overview

### Dual-Pane Layout

The collaborative editor features a side-by-side layout:

```
┌─────────────────┬─────────────────┐
│   English Pane  │   French Pane   │
│                 │                 │
│  [Document      │  [Document      │
│   Content]      │   Content]      │
│                 │                 │
│  [Status Bar]   │  [Status Bar]   │
└─────────────────┴─────────────────┘
```

#### Left Pane (English)
- Primary editing area for English content
- Section-based navigation (General Accountability, Organization Structure, etc.)
- Word count and character limits
- Real-time collaboration indicators

#### Right Pane (French)
- Synchronized French translation area
- Translation memory suggestions
- Glossary integration
- Quality indicators for translations

### Collaboration Panel

Located on the right side of the interface:

- **Active Users**: Shows who's currently editing
- **Recent Activity**: Live feed of editing actions
- **Comments & Discussions**: Contextual collaboration
- **Version History**: Document change tracking

### Translation Memory Panel

Intelligent translation assistance:

- **Fuzzy Matches**: Similar phrase suggestions
- **Exact Matches**: Previously translated identical content
- **Glossary Terms**: Standardized terminology
- **Quality Scores**: Translation confidence ratings

## Real-time Collaboration

### User Presence

#### Active User Indicators
- **User avatars** with colored borders show active editors
- **Live cursors** display where other users are typing
- **Selection highlights** show what others have selected
- **Activity timestamps** indicate last action time

#### Understanding User Status

| Status | Indicator | Meaning |
|--------|-----------|---------|
| 🟢 Active | Green avatar border | Currently editing |
| 🟡 Idle | Yellow avatar border | Connected but inactive (5+ min) |
| 🔴 Away | Red avatar border | Away or inactive (15+ min) |
| ⚫ Offline | Grayed out avatar | Disconnected |

### Concurrent Editing

#### How It Works
- **Operational Transformation**: Automatic conflict resolution
- **Character-level synchronization**: Changes appear in real-time
- **Optimistic updates**: Your changes appear immediately
- **Conflict resolution**: Automatic merging of simultaneous edits

#### Visual Feedback
- **Your changes**: Immediate local display
- **Remote changes**: Highlighted with user's color
- **Conflicts**: Temporarily highlighted in orange
- **Resolved conflicts**: Automatically merged

### Making Edits

1. **Click in any text area** to start editing
2. **Type normally** - changes sync automatically
3. **See others' changes** highlighted in their colors
4. **Conflicts are resolved** automatically using operational transformation

### Commenting and Discussion

#### Adding Comments
1. **Select text** you want to comment on
2. **Click the comment icon** or press `Ctrl+Shift+C`
3. **Type your comment** in the popup
4. **Tag users** with `@username` for notifications

#### Viewing Comments
- **Comment indicators** appear as colored highlights
- **Hover to preview** comment content
- **Click to open** full comment thread
- **Resolve comments** when addressed

## Translation Memory

### Understanding Translation Suggestions

The translation memory system provides intelligent assistance:

#### Match Types

1. **100% Match** (Green)
   - Identical source text previously translated
   - High confidence, likely accurate
   - Can be accepted directly

2. **Fuzzy Match** (Blue)
   - Similar but not identical content
   - Shows similarity percentage (e.g., 85% match)
   - Requires review and potential modification

3. **Glossary Term** (Purple)
   - Standardized terminology from approved glossary
   - Mandatory translations for consistency
   - Cannot be overridden without approval

4. **Context Match** (Orange)
   - Same phrase in similar document context
   - Medium confidence
   - Suggested for consideration

### Using Translation Suggestions

#### Accepting Suggestions
1. **Select text** in the source language pane
2. **Review suggestions** in the translation memory panel
3. **Click "Accept"** to insert the translation
4. **Edit if needed** for context-specific adjustments

#### Reviewing Suggestions
- **Quality score**: Algorithm-based confidence rating
- **Usage count**: How often this translation was used
- **Last used**: Recency of the translation
- **Contributors**: Who created/approved the translation

### Contributing to Translation Memory

#### Creating New Translations
1. **Translate text** in the target language pane
2. **System automatically saves** approved translations
3. **Peer review** may be required for complex terms
4. **Becomes available** for future use

#### Quality Assurance
- **Review translations** before publishing
- **Flag incorrect** or inappropriate content
- **Suggest improvements** through the comment system
- **Approve translations** if you have reviewer permissions

## Document Management

### Saving and Auto-save

#### Auto-save Features
- **Automatic saving** every 30 seconds
- **Change tracking** for version history
- **Draft preservation** if browser closes unexpectedly
- **Conflict resolution** for simultaneous saves

#### Manual Save
- **Ctrl+S** to save immediately
- **Save indicator** shows last save time
- **Version number** increments with each save

### Version History

#### Accessing Previous Versions
1. **Click "History"** in the toolbar
2. **Browse versions** by date/time
3. **Compare changes** between versions
4. **Restore specific version** if needed

#### Understanding Changes
- **Added content**: Highlighted in green
- **Removed content**: Highlighted in red
- **Modified content**: Highlighted in blue
- **Author information**: Who made each change

### Document Status

#### Status Indicators

| Status | Icon | Description |
|--------|------|-------------|
| Draft | 📝 | Work in progress, not submitted |
| Review | 👁️ | Submitted for review |
| Approved | ✅ | Reviewed and approved |
| Published | 🌐 | Live and publicly available |
| Archived | 📦 | Historical version, read-only |

### Permissions and Access Control

#### User Roles

1. **Viewer**
   - Read-only access
   - Can view comments
   - Cannot edit content

2. **Editor**
   - Full editing capabilities
   - Can add comments
   - Can save drafts

3. **Reviewer**
   - All editor permissions
   - Can approve/reject changes
   - Can publish documents

4. **Administrator**
   - All permissions
   - Can manage user access
   - Can configure settings

## Troubleshooting

### Connection Issues

#### "Connection Lost" Message
1. **Check internet connection**
2. **Refresh the page** (Ctrl+F5)
3. **Clear browser cache** if problem persists
4. **Contact support** if issue continues

#### Sync Problems
- **Changes not appearing**: Wait 5-10 seconds for sync
- **Conflicting edits**: System will auto-resolve
- **Lost changes**: Check auto-save recovery

### Performance Issues

#### Slow Loading
- **Large documents**: May take longer to load
- **Many active users**: Can affect performance
- **Network speed**: Check connection quality

#### Browser Compatibility
- **Chrome**: Fully supported
- **Firefox**: Fully supported
- **Safari**: Supported with minor limitations
- **Edge**: Fully supported
- **IE**: Not supported

### Feature-Specific Issues

#### Translation Memory Not Working
1. **Refresh the page**
2. **Check document language settings**
3. **Verify translation memory permissions**
4. **Report to system administrator**

#### Comments Not Saving
1. **Ensure internet connection**
2. **Check editing permissions**
3. **Try refreshing and re-adding**
4. **Contact support if persistent**

## Best Practices

### Effective Collaboration

#### Communication
- **Use comments** for questions and suggestions
- **Tag specific users** when input is needed
- **Be clear and concise** in comments
- **Resolve comments** when addressed

#### Editing Etiquette
- **Coordinate major changes** with team members
- **Work in different sections** to minimize conflicts
- **Save frequently** to preserve work
- **Use descriptive save messages**

### Translation Quality

#### Consistency
- **Use translation memory** suggestions when appropriate
- **Follow glossary terms** for standardized language
- **Maintain consistent tone** across documents
- **Review context** before accepting suggestions

#### Quality Assurance
- **Proofread translations** before saving
- **Check cultural appropriateness**
- **Verify technical terminology**
- **Get peer review** for complex content

### Document Organization

#### Structure
- **Use clear section headings**
- **Follow established templates**
- **Maintain consistent formatting**
- **Include all required sections**

#### Metadata
- **Add descriptive titles**
- **Include relevant tags**
- **Set appropriate status**
- **Update version notes**

## Keyboard Shortcuts

### General Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save document |
| `Ctrl+Z` | Undo last change |
| `Ctrl+Y` | Redo last change |
| `Ctrl+F` | Find text |
| `Ctrl+H` | Find and replace |

### Collaboration

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+C` | Add comment |
| `Ctrl+Shift+U` | Show active users |
| `Ctrl+Shift+H` | Show version history |
| `Ctrl+Shift+T` | Toggle translation memory |

### Navigation

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` | Go to English pane |
| `Ctrl+2` | Go to French pane |
| `Ctrl+3` | Go to comments panel |
| `Tab` | Switch between panes |

### Translation

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Show translation suggestions |
| `Ctrl+Enter` | Accept top suggestion |
| `Ctrl+Shift+Enter` | Accept with modification |
| `F2` | Add to glossary |

## Frequently Asked Questions

### General Usage

**Q: How many people can edit a document simultaneously?**
A: Up to 10 users can actively edit the same document at once. Additional users can view in read-only mode.

**Q: Are my changes saved if I lose internet connection?**
A: Yes, the system saves changes locally and syncs when connection is restored. Auto-recovery will restore your work.

**Q: Can I see who made specific changes?**
A: Yes, version history shows all changes with author information and timestamps.

### Translation Memory

**Q: How accurate are translation suggestions?**
A: Accuracy varies by match type:
- 100% matches: 95%+ accuracy
- Fuzzy matches: 70-90% accuracy
- Context matches: 60-80% accuracy

**Q: Can I override suggested translations?**
A: Yes, except for mandatory glossary terms which require approval to change.

**Q: How does the system learn from my translations?**
A: Approved translations are automatically added to the memory and become available for future suggestions.

### Technical Issues

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, and Edge. Internet Explorer is not supported.

**Q: Why do I see a "rate limit" message?**
A: This prevents spam. Wait 1 minute and try again. Contact admin if issue persists.

**Q: How do I report bugs or request features?**
A: Use the feedback button in the interface or contact your system administrator.

### Permissions and Access

**Q: Who can see my edits in real-time?**
A: Only users with access to the same document who are currently online.

**Q: Can I edit documents offline?**
A: Limited offline editing is available. Changes sync when connection is restored.

**Q: How do I get reviewer or admin permissions?**
A: Contact your organization's JDDB administrator to request elevated permissions.

## Support and Contact

### Getting Help

- **In-app help**: Click the "?" icon in the interface
- **User forum**: Access community discussions
- **Documentation**: Complete guides and tutorials
- **Video tutorials**: Step-by-step visual guides

### Technical Support

- **Email**: support@jddb.gc.ca
- **Phone**: 1-800-JDDB-HELP
- **Live chat**: Available during business hours
- **Ticket system**: Submit detailed technical issues

### Training and Resources

- **Onboarding sessions**: New user orientation
- **Advanced workshops**: Power user features
- **Best practices guides**: Optimization tips
- **Release notes**: Latest feature updates

---

*This guide covers the essential features of the JDDB Collaborative Editing system. For more detailed information, consult the technical documentation or contact support.*
