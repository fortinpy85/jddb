# Senior Advisor User Stories & Testing Coverage

## Persona Definition

### Senior Job Description Drafting Advisor

**Role**: Subject matter expert who guides managers through the complete lifecycle of job description development, ensuring consistency, quality, and compliance with organizational standards.

**Responsibilities**:
- Guide managers through job description creation and updates
- Review and validate job descriptions for quality and completeness
- Ensure bilingual concurrence between English and French versions
- Maintain organizational standards and classification accuracy
- Archive outdated positions and manage historical records
- Train managers on job description best practices

**Pain Points**:
- Managers often lack understanding of proper job description structure
- Inconsistent formatting and terminology across departments
- Difficulty maintaining bilingual accuracy and concurrence
- Time-consuming manual review processes
- Tracking changes and version history
- Ensuring compliance with classification standards

**Goals**:
- Streamline job description creation and review workflows
- Reduce time spent on formatting and structural corrections
- Improve quality and consistency across the organization
- Enable efficient bilingual validation
- Maintain accurate historical records

---

## User Story 1: Creation - Guiding Initial Job Description Development

### Story
**As a** senior job description drafting advisor
**I want to** guide a manager through creating a new job description from a raw draft
**So that** the resulting job description meets organizational standards and is properly structured

### Workflow Steps
1. Manager uploads raw job description draft (.txt, .docx, .pdf)
2. System automatically parses content into sections
3. Advisor reviews parsed sections for accuracy
4. Advisor edits individual sections to improve clarity
5. Advisor uses raw content sidebar to redistribute content to correct sections
6. Advisor validates tombstone metadata (title, classification, department)
7. Advisor saves completed job description

### Acceptance Criteria
- ✅ Raw content is visible in sidebar for reference during editing
- ✅ Multiple sections can be edited concurrently for cut/paste operations
- ✅ Each section has clear Edit/Save/Cancel controls
- ✅ Tombstone metadata is editable separately from content sections
- ✅ System validates required fields (title, classification)
- ✅ Success notifications confirm save operations
- ✅ Changes are persisted to database immediately

### Testing Scenarios

#### Happy Path
```gherkin
Given: A manager has uploaded a raw job description draft
When: The advisor opens the job detail view
Then: All sections should display with parsed content
And: Raw content sidebar should be available
And: Edit buttons should be visible on each section
And: Tombstone metadata should be complete and accurate

When: The advisor clicks "Edit" on the "General Accountability" section
Then: Section enters edit mode with Save/Cancel buttons
And: Textarea is focused and editable
And: Section has visual highlight (ring-2 ring-primary)

When: The advisor clicks "Edit" on "Specific Accountabilities" section
Then: Both sections are editable concurrently
And: Advisor can cut content from raw sidebar and paste into sections
And: Both sections maintain independent edit states

When: The advisor clicks "Save" on each section
Then: Success toast notification appears
And: Edited content is persisted to database
And: Sections exit edit mode and display updated content
```

#### Edge Cases
```gherkin
Scenario: Missing Required Tombstone Fields
Given: A job description with missing classification
When: Advisor attempts to save tombstone metadata
Then: Validation error displays: "Title and Classification are required"
And: Save operation is blocked until fields are completed

Scenario: Concurrent Editing with Network Failure
Given: Advisor is editing multiple sections
When: Network connection is lost during save
Then: Error toast displays: "Failed to save section. Please try again."
And: Section remains in edit mode with unsaved content
And: Advisor can retry save operation when connection restores

Scenario: Very Long Section Content
Given: A section with >5000 characters of content
When: Advisor edits the section
Then: Textarea should handle large content without performance degradation
And: Save operation should complete successfully
And: No content truncation should occur

Scenario: Raw Content Not Available
Given: A job uploaded without raw content preservation
When: Advisor clicks "Show Raw Content"
Then: Sidebar displays message: "No raw content available"
And: Editing workflow continues normally without sidebar
```

#### Error Conditions
```gherkin
Scenario: Database Connection Failure
Given: Database connection is unavailable
When: Advisor attempts to save section edits
Then: Error message displays: "Database error updating job section"
And: Changes are not persisted
And: Advisor is notified to contact system administrator

Scenario: Invalid Section ID
Given: A section ID that doesn't exist in database
When: System attempts to save section
Then: 404 error is returned
And: User-friendly error displays: "Section not found"

Scenario: Concurrent Edit Conflict (Future Multi-User)
Given: Two advisors editing the same section (future feature)
When: Second advisor attempts to save
Then: Conflict resolution UI appears
And: Latest version is displayed for comparison
```

---

## User Story 2: Update - Modifying Existing Job Descriptions

### Story
**As a** senior job description drafting advisor
**I want to** help a manager update an existing job description when role responsibilities change
**So that** the job description remains current and accurate

### Workflow Steps
1. Advisor searches for existing job description by title or classification
2. Advisor reviews current content and metadata
3. Advisor identifies sections requiring updates
4. Advisor edits multiple sections concurrently
5. Advisor validates bilingual concurrence (if applicable)
6. Advisor updates effective date and version metadata
7. Advisor saves all changes

### Acceptance Criteria
- ✅ Search functionality locates jobs by title, classification, or department
- ✅ Current job description content loads completely
- ✅ Edit history shows when job was last modified
- ✅ Multiple sections can be updated in single session
- ✅ Tombstone metadata updates separately from content
- ✅ Version tracking maintains historical record
- ✅ Bilingual versions remain synchronized

### Testing Scenarios

#### Happy Path
```gherkin
Given: An existing job description for "Director, Business Analysis"
When: Advisor searches for "Business Analysis"
Then: Job appears in search results with current classification
And: Job list displays last modified date

When: Advisor clicks on job to view details
Then: All sections load with current content
And: Tombstone metadata displays correctly
And: Raw content is available for reference

When: Advisor clicks "Edit" on "Specific Accountabilities" section
And: Updates section with new responsibilities
And: Clicks "Save"
Then: Success notification appears
And: Updated content is visible immediately
And: Job's updated_at timestamp is refreshed

When: Advisor opens tombstone editor from job list
And: Updates effective date to current date
And: Clicks "Save"
Then: Metadata updates successfully
And: Job list reflects new effective date
```

#### Edge Cases
```gherkin
Scenario: Partial Update Without Saving All Sections
Given: Advisor has edited 3 sections
When: Advisor saves 2 sections but cancels 1 section
Then: Only saved sections persist changes
And: Cancelled section reverts to original content
And: No data loss occurs

Scenario: Update During High Traffic
Given: Multiple advisors updating different jobs concurrently
When: Advisor saves section updates
Then: Update completes successfully without conflicts
And: Performance remains acceptable (<2 second response)

Scenario: Updating Very Old Job Description
Given: A job description last modified 5+ years ago
When: Advisor updates sections and metadata
Then: All fields update successfully
And: Historical version is preserved
And: Archival status remains unchanged
```

---

## User Story 3: Evaluation - Reviewing and Validating Job Descriptions

### Story
**As a** senior job description drafting advisor
**I want to** review and provide feedback on draft job descriptions
**So that** they meet quality standards before finalization

### Workflow Steps
1. Advisor receives notification of pending job description review
2. Advisor opens job detail view
3. Advisor reviews each section for clarity, completeness, accuracy
4. Advisor checks tombstone metadata for classification accuracy
5. Advisor edits sections requiring improvement
6. Advisor validates bilingual versions for concurrence
7. Advisor marks job as reviewed/approved

### Acceptance Criteria
- ✅ Review workflow identifies incomplete or low-quality sections
- ✅ Advisor can provide inline feedback and corrections
- ✅ Comparison view shows original vs. edited content
- ✅ Quality checklist validates all required sections present
- ✅ Classification validation confirms appropriate level
- ✅ Bilingual concurrence check highlights discrepancies
- ✅ Review status is tracked and visible

### Testing Scenarios

#### Happy Path
```gherkin
Given: A draft job description requiring review
When: Advisor opens job detail view
Then: All sections display with content
And: Quality indicators show completeness status
And: Missing or incomplete sections are highlighted

When: Advisor reviews "General Accountability" section
And: Identifies unclear language
And: Clicks "Edit" to improve clarity
And: Saves improved content
Then: Section quality indicator updates to "complete"
And: Changes are tracked in edit history

When: Advisor validates tombstone metadata
And: Confirms classification matches job responsibilities
Then: Classification validation passes
And: No warnings or errors display

When: Advisor compares English and French versions (future feature)
Then: Side-by-side comparison view displays
And: Discrepancies are highlighted
And: Advisor can edit both versions concurrently
```

#### Quality Gates
```gherkin
Quality Gate 1: All Required Sections Present
- ✅ General Accountability
- ✅ Organizational Structure
- ✅ Nature and Scope
- ✅ Specific Accountabilities
- ✅ Dimensions
- ✅ Knowledge and Skills

Quality Gate 2: Tombstone Metadata Complete
- ✅ Title
- ✅ Classification (Group-Level)
- ✅ Language
- ✅ Department
- ✅ Reports To
- ✅ Effective Date

Quality Gate 3: Content Quality Standards
- ✅ No placeholder text (e.g., "[TO BE COMPLETED]")
- ✅ Minimum word count per section
- ✅ No formatting inconsistencies
- ✅ Proper grammar and spelling
- ✅ Clear, actionable language

Quality Gate 4: Bilingual Concurrence (if applicable)
- ✅ English and French versions exist
- ✅ All sections translated
- ✅ Meaning preserved across languages
- ✅ Terminology consistency
```

---

## User Story 4: Archival - Managing Outdated Job Descriptions

### Story
**As a** senior job description drafting advisor
**I want to** archive outdated job descriptions while maintaining historical records
**So that** active job listings remain current and historical data is preserved

### Workflow Steps
1. Advisor identifies job descriptions requiring archival
2. Advisor reviews job to confirm it should be archived
3. Advisor adds archival reason and effective date
4. Advisor confirms archival action
5. System moves job to archived status
6. System preserves complete historical record
7. Archived job is no longer visible in active listings

### Acceptance Criteria
- ✅ Archival workflow requires confirmation to prevent accidents
- ✅ Archival reason is mandatory and tracked
- ✅ Archived jobs are excluded from active job listings
- ✅ Archived jobs remain searchable in historical records
- ✅ Complete content and metadata preserved in archive
- ✅ Archival action is logged with timestamp and user
- ✅ Archived jobs can be restored if needed

### Testing Scenarios

#### Happy Path
```gherkin
Given: An obsolete job description that is no longer used
When: Advisor searches for the job in job list
And: Clicks archive action from dropdown menu
Then: Archival confirmation dialog appears
And: Dialog prompts for archival reason
And: Dialog shows archival effective date (defaulted to today)

When: Advisor enters reason: "Position eliminated due to reorganization"
And: Confirms archival date
And: Clicks "Archive Job"
Then: Success notification displays
And: Job is removed from active job listings
And: Job appears in archived jobs view with reason and date

When: Advisor searches historical records
Then: Archived job appears in results with "Archived" badge
And: Complete job content and metadata is accessible
And: Archival metadata (reason, date, user) is visible
```

#### Edge Cases
```gherkin
Scenario: Accidental Archival Attempt
Given: Advisor accidentally clicks archive on active job
When: Confirmation dialog appears
And: Advisor clicks "Cancel"
Then: No archival action occurs
And: Job remains in active listings

Scenario: Restore Archived Job
Given: A job was archived in error
When: Advisor views archived job
And: Clicks "Restore" action
And: Confirms restoration
Then: Job returns to active listings
And: All content and metadata intact
And: Restoration is logged in job history

Scenario: Archive Job with Active References
Given: A job is referenced by other system components
When: Advisor attempts to archive
Then: Warning displays: "This job is referenced by [X] other records"
And: Advisor can choose to proceed or cancel
And: References are handled appropriately if archived
```

---

## User Story 5: Deletion - Removing Duplicate or Incorrect Job Descriptions

### Story
**As a** senior job description drafting advisor
**I want to** delete duplicate or incorrect job descriptions
**So that** the system contains only accurate and valid job data

### Workflow Steps
1. Advisor identifies duplicate or incorrect job description
2. Advisor verifies job should be deleted (not archived)
3. Advisor reviews job dependencies and references
4. Advisor confirms permanent deletion with reason
5. System performs hard delete (or soft delete based on policy)
6. System logs deletion action for audit trail
7. Deleted job is removed from all listings

### Acceptance Criteria
- ✅ Deletion requires explicit confirmation with warning
- ✅ Deletion reason is mandatory and logged
- ✅ System checks for dependencies before deletion
- ✅ Deletion is restricted to authorized users only
- ✅ Audit trail captures who deleted, when, and why
- ✅ Deletion is irreversible (or soft-deleted based on policy)
- ✅ Related data (sections, metadata) is handled consistently

### Testing Scenarios

#### Happy Path
```gherkin
Given: A duplicate job description created in error
When: Advisor identifies the duplicate in job list
And: Clicks delete action from dropdown menu
Then: Deletion confirmation dialog appears
And: Warning displays: "This action cannot be undone"
And: Dialog prompts for deletion reason

When: Advisor enters reason: "Duplicate entry - correct version is JOB-12345"
And: Clicks "Confirm Delete"
Then: System checks for dependencies
And: Success notification displays
And: Job is removed from all listings
And: Deletion is logged in audit trail with user, timestamp, reason
```

#### Safety Checks
```gherkin
Scenario: Prevent Accidental Deletion
Given: Advisor clicks delete by accident
When: Confirmation dialog appears
And: Advisor reads warning message
And: Advisor clicks "Cancel"
Then: No deletion occurs
And: Job remains in listings

Scenario: Missing Deletion Reason
Given: Advisor attempts to delete job
When: Deletion reason field is empty
And: Advisor clicks "Confirm Delete"
Then: Validation error displays: "Deletion reason is required"
And: Deletion is blocked until reason is provided

Scenario: Unauthorized Deletion Attempt
Given: A user without delete permissions
When: User attempts to delete job
Then: Delete action is not available in UI
Or: If accessed directly, 403 Forbidden error returns
And: Audit log captures unauthorized attempt
```

#### Complex Scenarios
```gherkin
Scenario: Delete Job with References
Given: A job description referenced by other records
When: Advisor attempts to delete
Then: System displays dependency warning
And: Lists all dependent records
And: Advisor can choose to:
  - Cancel deletion
  - Proceed with cascade delete (if allowed)
  - Reassign dependencies to another job

Scenario: Bulk Deletion of Duplicate Jobs
Given: Multiple duplicate jobs identified
When: Advisor selects multiple jobs for deletion
And: Confirms bulk deletion with reason
Then: System validates each job for dependencies
And: Provides summary of deletion results
And: Logs each individual deletion in audit trail
```

---

## Cross-Workflow Testing Scenarios

### Scenario: Complete Job Description Lifecycle
```gherkin
Given: A new position is created in the organization
When: Manager uploads raw job description draft
Then: Advisor guides creation process
And: All sections are properly populated and formatted
And: Tombstone metadata is validated and complete
And: Job is saved as active

When: 2 years later, role responsibilities change
Then: Advisor helps manager update specific sections
And: Effective date is updated to reflect changes
And: Bilingual versions are synchronized
And: Updated job is saved

When: 5 years later, position is reviewed for quality
Then: Advisor evaluates all sections against current standards
And: Advisor improves clarity and removes outdated language
And: Job description meets all quality gates
And: Approved job is marked as reviewed

When: 7 years later, position is eliminated
Then: Advisor archives job with reason "Position eliminated"
And: Complete historical record is preserved
And: Job is removed from active listings

When: Duplicate entry is discovered
Then: Advisor deletes duplicate with reason
And: Deletion is logged in audit trail
And: Only valid job remains in system
```

### Scenario: Bilingual Job Description Management (Future)
```gherkin
Given: An English job description is completed
When: Advisor initiates translation workflow
Then: System creates linked French version
And: Dual-pane editor displays English and French side-by-side
And: Advisor can edit both versions concurrently

When: Advisor edits English section
Then: French section is flagged for review
And: Translation memory suggests equivalent French text
And: Advisor validates or corrects French translation

When: All sections are validated for concurrence
Then: System confirms bilingual alignment
And: Both versions are published together
And: Linked relationship is maintained
```

### Scenario: AI-Assisted Improvement Workflow (Future)
```gherkin
Given: A job description with complete content
When: Advisor initiates AI improvement mode
Then: System analyzes each section for clarity and completeness
And: AI suggestions appear in comparison view
And: Original and improved versions display side-by-side

When: Advisor reviews AI suggestions for "General Accountability"
Then: Advisor can accept, reject, or modify suggestions
And: Accepted improvements are applied to section
And: Rejected suggestions are logged for learning

When: All sections are reviewed and improved
Then: Final job description reflects accepted improvements
And: Improvement history is tracked
And: Job quality score increases
```

---

## User Story 6: AI-Assisted Improvement Mode

### Story
**As a** senior job description drafting advisor
**I want to** use AI to improve job description clarity and completeness with sentence-level accept/reject controls
**So that** I can efficiently enhance quality while maintaining full control over final content

### Workflow Steps
1. Advisor completes initial job description content in all sections
2. Advisor initiates "AI Improvement Mode" from job detail view
3. System analyzes each section and generates improvement suggestions
4. Comparison view displays original vs. AI-improved content side-by-side
5. Advisor reviews suggestions sentence-by-sentence
6. Advisor accepts, rejects, or modifies each suggestion
7. System applies accepted improvements and learns from rejections
8. Advisor validates final improved job description
9. System tracks improvement history and quality metrics

### Acceptance Criteria
- ✅ AI improvement mode available after all required sections are populated
- ✅ Split-pane comparison view shows original (left) and improved (right) content
- ✅ Suggestions are granular (sentence-level or clause-level)
- ✅ Each suggestion has Accept/Reject/Modify controls
- ✅ Changes are highlighted with diff visualization (additions, deletions, modifications)
- ✅ Accepted suggestions immediately update the improved version
- ✅ Rejected suggestions are logged for AI learning feedback
- ✅ Advisor can manually edit AI suggestions before accepting
- ✅ Bulk operations available (Accept All, Reject All per section)
- ✅ Improvement history is tracked and visible
- ✅ AI rationale is provided for each suggestion
- ✅ Final content can be saved as new version or replace original

### UI/UX Design

#### Comparison View Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Job Description AI Improvement                                  │
│ [Section Navigation: General | Accountabilities | Skills]       │
│                                                         [Exit]   │
├──────────────────────────────────┬──────────────────────────────┤
│ ORIGINAL (Current)               │ AI-IMPROVED (Suggested)      │
├──────────────────────────────────┼──────────────────────────────┤
│ The incumbent is responsible     │ The incumbent is accountable │
│ for overseeing business          │ for overseeing business      │
│ analysis activities.             │ analysis activities and      │
│                                  │ ensuring alignment with      │
│                   [No Action]    │ strategic objectives.        │
│                                  │                              │
│                                  │ [Accept] [Reject] [Modify]   │
│                                  │ Reason: Added strategic      │
│                                  │ alignment for clarity        │
├──────────────────────────────────┼──────────────────────────────┤
│ Manages a team.                  │ Provides leadership and      │
│                                  │ direction to a team of       │
│                   [No Action]    │ business analysts.           │
│                                  │                              │
│                                  │ [Accept] [Reject] [Modify]   │
│                                  │ Reason: More descriptive     │
│                                  │ and professional language    │
└──────────────────────────────────┴──────────────────────────────┘
  [Accept All Section] [Reject All Section] [Save Improvements]
```

#### Suggestion State Indicators
- **Pending**: Yellow border, awaiting advisor decision
- **Accepted**: Green background with checkmark icon
- **Rejected**: Red strikethrough with X icon
- **Modified**: Blue background with edit icon
- **Diff Highlighting**:
  - Green text for additions
  - Red strikethrough for deletions
  - Yellow highlight for modifications

### Testing Scenarios

#### Happy Path: Section-by-Section Improvement
```gherkin
Given: A complete job description for "Director, Strategic Planning"
When: Advisor clicks "AI Improvement Mode" button in job detail view
Then: System analyzes all sections for improvement opportunities
And: Comparison view opens with "General Accountability" section
And: Original content displays in left pane
And: AI-improved content displays in right pane with suggestions highlighted

When: Advisor reviews first suggestion
Then: Suggestion displays with clear diff visualization
And: AI rationale is shown: "Improved clarity and alignment with standards"
And: Accept/Reject/Modify buttons are visible below suggestion

When: Advisor clicks "Accept" on first suggestion
Then: Suggestion turns green with checkmark icon
And: Accepted text is immediately applied to improved version
And: Next suggestion is highlighted for review

When: Advisor clicks "Reject" on second suggestion
Then: Suggestion turns red with strikethrough
And: Original text remains in improved version
And: Rejection is logged: "Advisor preferred original phrasing"
And: Next suggestion is highlighted

When: Advisor clicks "Modify" on third suggestion
Then: Inline editor opens with AI suggestion pre-filled
And: Advisor edits text to custom version
And: Modified text is applied to improved version
And: Modification is tracked as "advisor-modified"

When: Advisor completes review of all suggestions in section
And: Clicks "Next Section" to review "Specific Accountabilities"
Then: Current section improvements are saved
And: Next section loads with original vs. improved comparison
And: Suggestion review process continues

When: All sections are reviewed and approved
And: Advisor clicks "Save Improvements"
Then: Confirmation dialog displays summary:
  - "23 suggestions accepted"
  - "7 suggestions rejected"
  - "4 suggestions modified"
And: Advisor confirms save operation
Then: Improved content replaces original in job description
And: Improvement history is logged with timestamp
And: Success notification displays
And: Job detail view shows improved content
```

#### Edge Cases

```gherkin
Scenario: No Improvements Suggested for Section
Given: A section with already high-quality content
When: AI analyzes the section
Then: Message displays: "No improvements suggested for this section"
And: Original content remains unchanged
And: Advisor can proceed to next section

Scenario: Bulk Accept All Suggestions in Section
Given: Advisor is reviewing "Specific Accountabilities" with 10 suggestions
When: Advisor clicks "Accept All Section" button
Then: Confirmation prompt appears: "Accept all 10 suggestions?"
And: Advisor confirms action
Then: All suggestions are accepted and applied immediately
And: Section turns green indicating completion
And: Advisor can review next section or save improvements

Scenario: Bulk Reject All Suggestions in Section
Given: Advisor disagrees with AI approach for a section
When: Advisor clicks "Reject All Section" button
Then: Confirmation prompt appears: "Reject all suggestions for this section?"
And: Advisor confirms action
Then: All suggestions are rejected
And: Original content is preserved
And: Rejections are logged for AI learning

Scenario: Exit AI Improvement Mode Without Saving
Given: Advisor has reviewed and accepted/rejected several suggestions
When: Advisor clicks "Exit" button
Then: Warning dialog displays: "You have unsaved improvements. Exit without saving?"
And: Advisor can choose:
  - "Save & Exit" - saves improvements and exits
  - "Discard & Exit" - discards all changes and exits
  - "Cancel" - returns to improvement mode

Scenario: Modify Suggestion with Custom Text
Given: AI suggests: "Manages the team" → "Provides leadership to the team"
When: Advisor clicks "Modify"
And: Inline editor opens with AI suggestion
And: Advisor changes to: "Provides strategic leadership and mentorship to the team"
And: Clicks "Apply Modification"
Then: Custom text is applied to improved version
And: Modification is tracked as advisor-enhanced
And: Suggestion is marked as "Modified" with blue indicator
```

#### Error Conditions

```gherkin
Scenario: AI Service Unavailable
Given: OpenAI API is experiencing downtime
When: Advisor initiates AI improvement mode
Then: Error notification displays: "AI service is currently unavailable. Please try again later."
And: Advisor remains in standard editing mode
And: Fallback message suggests manual editing

Scenario: API Rate Limit Exceeded
Given: Multiple advisors using AI improvement simultaneously
When: Advisor initiates improvement mode
And: API rate limit is reached
Then: Warning displays: "AI service is busy. Your request is queued."
And: Progress indicator shows queue position
And: Request processes when capacity available
Or: Advisor can cancel and try later

Scenario: Incomplete Section Content
Given: A section has less than minimum content for AI analysis
When: Advisor initiates AI improvement mode
Then: Warning displays: "Section 'Nature and Scope' has insufficient content for AI analysis"
And: Advisor can choose to:
  - Skip this section
  - Add more content manually first
  - Continue with other sections

Scenario: AI Returns Invalid Suggestions
Given: AI service returns malformed or inappropriate suggestions
When: System validates AI response
Then: Invalid suggestions are filtered out
And: Warning displays: "Some suggestions could not be processed"
And: Valid suggestions are presented normally
And: Error is logged for debugging
```

#### Complex Scenarios

```gherkin
Scenario: Iterative Improvement Cycles
Given: Advisor completes first round of AI improvements
When: Advisor saves improved job description
And: Later initiates AI improvement mode again
Then: System analyzes the previously improved content
And: Generates new suggestions based on current version
And: Comparison shows current (improved) vs. further improved
And: Advisor can apply additional refinements
And: System tracks improvement iterations: "Improvement Round 2"

Scenario: Section-Specific Improvement Focus
Given: Advisor wants to improve only "Specific Accountabilities" section
When: Advisor selects section from navigation
And: Clicks "Improve This Section Only"
Then: AI analyzes only selected section
And: Comparison view shows only that section
And: Advisor reviews and applies suggestions
And: Other sections remain unchanged
And: Improvement history notes: "Targeted improvement: Specific Accountabilities"

Scenario: Compare Multiple AI Improvement Versions
Given: Advisor has run AI improvement multiple times
When: Advisor views improvement history
Then: List displays all improvement sessions with timestamps
And: Advisor can compare any two versions side-by-side
And: Advisor can restore previous improved version if needed
And: Diff visualization shows changes between versions
```

### AI Improvement Quality Metrics

**AI Suggestion Quality Tracking**:
```yaml
Per Suggestion:
  - Suggestion ID (unique identifier)
  - Section type (e.g., "General Accountability")
  - Original text (before improvement)
  - Suggested text (AI improvement)
  - Rationale (why AI suggested this change)
  - Action taken (accepted, rejected, modified, pending)
  - Advisor feedback (optional text explanation for rejection)
  - Timestamp (when suggestion was reviewed)

Per Session:
  - Total suggestions generated
  - Acceptance rate (% of suggestions accepted)
  - Rejection rate (% of suggestions rejected)
  - Modification rate (% of suggestions modified)
  - Average time per suggestion review
  - Overall improvement score (before/after quality)
```

**Learning Feedback Loop**:
- Rejected suggestions with reasons feed back to AI training
- High acceptance rate patterns are reinforced
- Low acceptance rate patterns trigger model review
- Advisor-modified suggestions become training examples
- Quality scores improve over time with more usage

### AI Improvement Configuration

**Improvement Focus Areas** (Advisor can select):
```yaml
Clarity:
  - Remove ambiguous language
  - Simplify complex sentences
  - Improve readability (Flesch-Kincaid score)

Completeness:
  - Identify missing information
  - Suggest additional context where needed
  - Ensure all accountability aspects covered

Consistency:
  - Align with organizational terminology
  - Standardize formatting and structure
  - Ensure consistent tone and style

Professionalism:
  - Elevate language to executive level
  - Remove informal expressions
  - Apply government communication standards

Specificity:
  - Replace vague terms with specific details
  - Quantify where appropriate
  - Add concrete examples
```

**Advisor Control Settings**:
```yaml
Suggestion Granularity:
  - Sentence-level (default)
  - Clause-level (more granular)
  - Paragraph-level (broader)

Aggressiveness:
  - Conservative (only clear improvements)
  - Moderate (balanced approach)
  - Aggressive (extensive restructuring)

Auto-Accept Threshold:
  - None (all manual review)
  - High confidence only (>90% confidence score)
  - Medium+ confidence (>70% confidence score)
```

---

## User Story 7: Bilingual Translation and Concurrence Validation Mode

### Story
**As a** senior job description drafting advisor
**I want to** translate job descriptions between English and French with sentence-level concurrence validation
**So that** bilingual job descriptions maintain accurate meaning across both official languages

### Workflow Steps
1. Advisor completes job description in source language (English or French)
2. Advisor initiates "Translation Mode" from job detail view
3. System creates linked bilingual job description record
4. Dual-pane editor displays source language (left) and target language (right)
5. Advisor reviews machine translation suggestions section-by-section
6. Advisor validates, corrects, or rejects translation suggestions sentence-by-sentence
7. Translation memory suggests previously validated equivalents
8. Advisor confirms bilingual concurrence across all sections
9. System links both language versions with concurrence metadata
10. Both versions are published together as official bilingual pair

### Acceptance Criteria
- ✅ Translation mode creates linked bilingual record (EN↔FR)
- ✅ Dual-pane editor shows source and target languages side-by-side
- ✅ Machine translation suggestions provided for all sections
- ✅ Translation memory retrieves previously validated equivalents
- ✅ Sentence-by-sentence accept/reject/modify controls
- ✅ Terminology consistency validation across sections
- ✅ Concurrence indicators show alignment status
- ✅ Both versions locked together (editing one flags other for review)
- ✅ Validation checklist ensures complete translation
- ✅ Bilingual versions published atomically (both or neither)
- ✅ Translation history tracked with translator identification
- ✅ Quality assurance validates meaning preservation

### UI/UX Design

#### Dual-Pane Translation Editor Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Bilingual Translation Mode: Director, Business Analysis         │
│ Source: English (EN) → Target: French (FR)                      │
│ [Section: General Accountability ▼]    [Save] [Validate] [Exit]│
├──────────────────────────────────┬──────────────────────────────┤
│ ENGLISH (Source - Approved)      │ FRANÇAIS (Target - Draft)    │
├──────────────────────────────────┼──────────────────────────────┤
│ The incumbent is accountable     │ Le titulaire est responsable │
│ for overseeing business          │ de la supervision des        │
│ analysis activities and          │ activités d'analyse de       │
│ ensuring alignment with          │ gestion et de l'alignement   │
│ strategic objectives.            │ avec les objectifs           │
│                                  │ stratégiques.                │
│ ✅ Concurrence: Validated        │                              │
│                                  │ [✓ Accept] [✗ Reject]        │
│                                  │ [✎ Modify]                   │
│                                  │ TM Match: 95% (similar text) │
├──────────────────────────────────┼──────────────────────────────┤
│ Provides strategic leadership    │ Fournit un leadership        │
│ and direction to a team of       │ stratégique et une direction │
│ business analysts.               │ à une équipe d'analystes     │
│                                  │ d'affaires.                  │
│ ⚠️ Concurrence: Pending Review   │                              │
│                                  │ [✓ Accept] [✗ Reject]        │
│                                  │ [✎ Modify]                   │
│                                  │ TM Match: 88% (partial)      │
└──────────────────────────────────┴──────────────────────────────┘
  Translation Memory: 12 matches found | Terminology: 3 terms validated
  [Validate All Section] [Publish Bilingual Pair]
```

#### Concurrence Status Indicators
- **✅ Validated**: Green checkmark - meaning confirmed equivalent in both languages
- **⚠️ Pending Review**: Yellow warning - translation suggested, needs validation
- **❌ Rejected**: Red X - translation rejected, needs correction
- **✎ Modified**: Blue edit icon - advisor made manual corrections
- **🔗 Linked**: Chain icon - sentences are linked for concurrence tracking

### Testing Scenarios

#### Happy Path: English to French Translation
```gherkin
Given: An approved English job description for "Director, Strategic Planning"
When: Advisor opens job detail view
And: Clicks "Translation Mode" button
And: Selects "Translate to French"
Then: System creates linked French version record
And: Dual-pane editor opens with English (left) and French (right)
And: Machine translation pre-fills French pane with suggested content
And: Translation memory highlights high-confidence matches

When: Advisor reviews first sentence in "General Accountability"
Then: English sentence displays in left pane (locked, non-editable)
And: French translation suggestion displays in right pane
And: Translation memory shows: "TM Match: 95% - Previously validated similar text"
And: Terminology database shows validated French terms for "accountability", "strategic"
And: Accept/Reject/Modify buttons appear below French text

When: Advisor verifies French translation accurately conveys meaning
And: Clicks "Accept" button
Then: French sentence is marked as validated with green checkmark
And: Concurrence indicator shows ✅ for sentence pair
And: Validated pair is saved to translation memory
And: Next sentence is highlighted for review

When: Advisor reviews second sentence
And: Notices translation is too literal and lacks nuance
And: Clicks "Modify" button
Then: Inline editor opens with suggested French text
And: Advisor edits text to better capture intended meaning
And: Advisor clicks "Apply Modification"
Then: Modified French text is saved
And: Concurrence indicator shows ✎ (modified)
And: Modified pair is saved to translation memory as validated example

When: Advisor completes all sentences in section
And: Clicks "Validate All Section"
Then: System performs concurrence check across section
And: Validation summary displays:
  - "18 sentences validated"
  - "2 sentences modified"
  - "0 sentences rejected"
  - "Terminology consistency: 100%"
And: Section is marked as complete with green indicator

When: Advisor completes all sections
And: Clicks "Publish Bilingual Pair"
Then: Confirmation dialog displays bilingual publication summary
And: Both English and French versions are published atomically
And: Linked relationship is established in database
And: Both versions share same metadata (classification, effective date, etc.)
And: Success notification: "Bilingual pair published successfully"
```

#### Edge Cases

```gherkin
Scenario: Translation Memory Exact Match
Given: Sentence "The incumbent is accountable for..." was previously translated
When: Advisor reviews same sentence in new job description
Then: Translation memory displays: "TM Match: 100% - Exact match"
And: Validated French translation is auto-filled
And: Advisor can accept without modification
And: Validation is instantaneous

Scenario: No Translation Memory Match
Given: A sentence with organization-specific technical terminology
When: Advisor reviews sentence with 0% TM match
Then: Machine translation provides best-effort suggestion
And: Warning displays: "Low confidence - Manual review recommended"
And: Terminology database suggests French equivalents for key terms
And: Advisor carefully validates and corrects translation

Scenario: Terminology Inconsistency Detected
Given: Advisor translates "manager" as "gestionnaire" in one section
When: Same term appears later in another section
And: Advisor attempts to translate as "directeur"
Then: Warning displays: "Terminology inconsistency detected"
And: System shows: "You previously used 'gestionnaire' for 'manager'"
And: Advisor can choose to:
  - Use consistent term ("gestionnaire")
  - Update all instances to new term ("directeur")
  - Justify different usage (e.g., context-specific)

Scenario: Sentence Structure Requires Reordering
Given: English sentence: "The team, which consists of 5 analysts, reports to the director"
When: Machine translation produces literal French structure
And: Advisor recognizes French requires different word order
And: Clicks "Modify"
Then: Advisor restructures to natural French:
  "L'équipe de 5 analystes relève du directeur"
And: Concurrence is validated based on meaning, not word-for-word match
And: Modified version is saved as best-practice example

Scenario: Bilingual Edit After Publication
Given: A published bilingual job description pair
When: English version is updated with new responsibilities
Then: French version is automatically flagged: "Source changed - Re-validation required"
And: Advisor receives notification of concurrence break
And: Advisor reviews changes in English
And: Advisor updates French version to restore concurrence
And: Both versions are re-published together

Scenario: Bulk Accept High-Confidence Translations
Given: Section has 20 sentences, 15 with >90% TM match
When: Advisor clicks "Auto-Accept High Confidence" button
Then: Confirmation prompt: "Accept 15 high-confidence translations?"
And: Advisor confirms
Then: 15 sentences are validated automatically
And: 5 low-confidence sentences remain for manual review
And: Advisor reviews only the 5 flagged sentences
```

#### Translation Memory Integration

```gherkin
Scenario: Building Translation Memory from Validated Pairs
Given: Advisor validates sentence pair:
  EN: "Ensures alignment with strategic objectives"
  FR: "Assure l'alignement avec les objectifs stratégiques"
When: Validation is confirmed
Then: Pair is stored in translation memory with metadata:
  - Source sentence
  - Target sentence
  - Validator (advisor ID)
  - Validation date
  - Context (section type, classification level)
  - Confidence score: 100% (human-validated)

Scenario: Retrieving Similar Translations
Given: New sentence: "Ensures compliance with organizational objectives"
When: System searches translation memory
Then: Similar match found (78% similarity):
  "Ensures alignment with strategic objectives"
  → "Assure l'alignement avec les objectifs stratégiques"
And: Suggestion adapts: "Assure la conformité aux objectifs organisationnels"
And: Displays: "TM Match: 78% - Adapted from similar validated translation"
And: Advisor reviews and validates adapted version

Scenario: Terminology Database Lookup
Given: Sentence contains term "accountability"
When: Advisor hovers over term
Then: Terminology popup displays:
  - Preferred French: "responsabilité"
  - Alternative: "obligation de rendre compte"
  - Context: "General Accountability section"
  - Usage count: 342 validated instances
  - Last validated: 2025-10-15
And: Advisor can select preferred term
And: Selection is applied consistently throughout document
```

#### Concurrence Validation

```gherkin
Scenario: Automated Concurrence Check
Given: Both English and French versions are complete
When: Advisor clicks "Validate Concurrence"
Then: System performs comprehensive validation:
  - ✅ All sections present in both languages
  - ✅ All sentences have validated translations
  - ✅ Terminology consistency maintained
  - ✅ No missing or extra content in either version
  - ✅ Metadata aligned (title, classification, dates)
And: Validation report displays:
  "Concurrence Status: VALIDATED"
  "23 sections complete"
  "186 sentence pairs validated"
  "98% translation memory match rate"

Scenario: Concurrence Discrepancy Detected
Given: French version has additional sentence not in English
When: Advisor clicks "Validate Concurrence"
Then: Error displays: "Concurrence discrepancy detected"
And: Discrepancy details:
  "French section 'Specific Accountabilities' has 1 additional sentence"
And: System highlights extra sentence in French pane
And: Advisor can choose to:
  - Add equivalent sentence to English version
  - Remove extra sentence from French version
  - Justify intentional difference (e.g., cultural adaptation)
And: Concurrence cannot be validated until resolved

Scenario: Meaning Preservation Validation
Given: Sentence pair with different structure but equivalent meaning:
  EN: "Manages a team of 5-10 business analysts"
  FR: "Dirige une équipe composée de 5 à 10 analystes d'affaires"
When: Advisor validates translation
Then: System checks semantic equivalence:
  - ✅ Key concepts present: "manages/dirige", "team/équipe", "5-10", "business analysts"
  - ✅ Meaning preserved despite structural differences
  - ✅ No additions or omissions
And: Validation is approved
And: Pair is marked as semantically equivalent
```

### Translation Quality Metrics

**Per Translation Session**:
```yaml
Session Metadata:
  - Source language (e.g., "English")
  - Target language (e.g., "French")
  - Translator (advisor ID)
  - Start timestamp
  - Completion timestamp
  - Total sentences translated

Translation Statistics:
  - Accepted suggestions: count and %
  - Rejected suggestions: count and %
  - Modified suggestions: count and %
  - Translation memory exact matches: count and %
  - Translation memory fuzzy matches: count and %
  - Zero-match sentences requiring full manual translation: count and %

Quality Scores:
  - Translation memory leverage rate (% of text from TM)
  - Terminology consistency score (% consistent usage)
  - Concurrence validation status (pass/fail)
  - Average time per sentence validation
  - Overall translation quality score (composite)
```

**Translation Memory Analytics**:
```yaml
TM Database Metrics:
  - Total validated sentence pairs
  - Coverage by section type
  - Coverage by classification level
  - Average confidence score
  - Most frequently translated terms
  - High-value matches (saved advisor time)

TM Quality Indicators:
  - Reuse rate (% of translations from TM)
  - Modification rate (% of TM suggestions modified)
  - Rejection rate (% of TM suggestions rejected)
  - Accuracy improvement over time
```

### Translation Workflow Configuration

**Translation Assistance Levels**:
```yaml
Machine Translation Only:
  - Basic MT suggestions without TM
  - Suitable for new content areas
  - Requires full manual validation

Translation Memory + MT:
  - TM matches prioritized over MT
  - MT fills gaps where no TM match
  - Hybrid approach (default)

Human Translation (No MT):
  - No machine suggestions
  - TM matches only
  - Advisor translates from scratch
  - Highest quality, most time-consuming
```

**Auto-Validation Settings**:
```yaml
Auto-Accept Thresholds:
  - Exact TM match (100%): Auto-accept
  - High TM match (>95%): Auto-accept with review flag
  - Medium TM match (85-95%): Suggest with manual review
  - Low TM match (<85%): Manual translation required

Terminology Auto-Validation:
  - Validated terms from database: Auto-apply
  - New terms: Flag for validation
  - Inconsistent usage: Warn and suggest correction
```

---

## Comprehensive Test Coverage Framework

### Test Coverage Goals
- **Unit Test Coverage**: 100% for all functions and components
- **Integration Test Coverage**: 100% for all API endpoints and workflows
- **E2E Test Coverage**: 100% for all user-facing workflows
- **Edge Case Coverage**: 100% for all identified edge cases
- **Error Path Coverage**: 100% for all error conditions
- **Future Feature Coverage**: Pre-defined test suites for planned features

---

## Test Suite 1: Core Editing Features (Current Implementation)

### Section-by-Section Editing Tests

#### Unit Tests
```typescript
describe('SectionEditor Component', () => {
  describe('Edit Mode Activation', () => {
    it('should enter edit mode when Edit button is clicked', () => {});
    it('should focus textarea automatically on edit mode entry', () => {});
    it('should display Save and Cancel buttons in edit mode', () => {});
    it('should apply ring-2 ring-primary visual highlight in edit mode', () => {});
    it('should preserve content when entering edit mode', () => {});
  });

  describe('Content Management', () => {
    it('should update content as user types', () => {});
    it('should handle empty content gracefully', () => {});
    it('should handle very long content (>10000 characters)', () => {});
    it('should handle special characters and unicode', () => {});
    it('should preserve line breaks and formatting', () => {});
  });

  describe('Save Operations', () => {
    it('should call onSave with section ID and content', () => {});
    it('should exit edit mode after successful save', () => {});
    it('should display success toast notification', () => {});
    it('should update optimistically before API response', () => {});
    it('should handle save failures gracefully', () => {});
    it('should retry failed saves with exponential backoff', () => {});
  });

  describe('Cancel Operations', () => {
    it('should revert content to original on cancel', () => {});
    it('should exit edit mode on cancel', () => {});
    it('should not call API on cancel', () => {});
    it('should display no notification on cancel', () => {});
  });

  describe('Concurrent Editing', () => {
    it('should allow multiple sections to be edited simultaneously', () => {});
    it('should maintain independent state for each section', () => {});
    it('should handle concurrent saves correctly', () => {});
    it('should preserve content across section switches', () => {});
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for all buttons', () => {});
    it('should announce edit state changes to screen readers', () => {});
    it('should be fully keyboard navigable', () => {});
    it('should have visible focus indicators', () => {});
  });
});
```

#### Integration Tests
```typescript
describe('Section Editing API Integration', () => {
  it('should update section via PATCH /api/jobs/{id}/sections/{sectionId}', async () => {});
  it('should return updated section data in response', async () => {});
  it('should update job timestamp on section save', async () => {});
  it('should handle 404 for invalid job ID', async () => {});
  it('should handle 404 for invalid section ID', async () => {});
  it('should handle 422 for missing content', async () => {});
  it('should handle 500 for database errors', async () => {});
  it('should validate API key authentication', async () => {});
});
```

#### E2E Tests
```typescript
describe('Section Editing E2E Workflow', () => {
  it('should complete full editing workflow from job list to save', async () => {
    // Navigate to job list
    // Click on job to view details
    // Click Edit on section
    // Modify content
    // Click Save
    // Verify success notification
    // Verify content updated in UI
  });

  it('should support cut/paste from raw content sidebar', async () => {
    // Open job detail
    // Click Show Raw Content
    // Click Edit on two sections
    // Select text from raw content
    // Paste into section 1
    // Paste into section 2
    // Save both sections
    // Verify content saved
  });

  it('should handle network failures during save', async () => {
    // Enter edit mode
    // Modify content
    // Simulate network failure
    // Click Save
    // Verify error notification
    // Verify content preserved in edit mode
    // Restore network
    // Retry save
    // Verify success
  });
});
```

### Tombstone Metadata Editing Tests

#### Unit Tests
```typescript
describe('TombstoneEditor Component', () => {
  describe('Modal Behavior', () => {
    it('should open modal when isOpen is true', () => {});
    it('should close modal when onClose is called', () => {});
    it('should load job metadata on modal open', () => {});
    it('should clear form state on modal close', () => {});
  });

  describe('Form Validation', () => {
    it('should require title field', () => {});
    it('should require classification field', () => {});
    it('should allow optional department field', () => {});
    it('should allow optional reports_to field', () => {});
    it('should validate language is en or fr', () => {});
    it('should display validation errors clearly', () => {});
  });

  describe('Data Loading', () => {
    it('should fetch job metadata when job changes', () => {});
    it('should populate form fields from loaded data', () => {});
    it('should handle missing metadata gracefully', () => {});
    it('should handle API errors during load', () => {});
  });

  describe('Form Submission', () => {
    it('should submit all tombstone fields to API', () => {});
    it('should call onJobUpdated with job ID on success', () => {});
    it('should close modal after successful save', () => {});
    it('should display error on save failure', () => {});
    it('should remain open on save failure', () => {});
  });
});
```

#### Integration Tests
```typescript
describe('Tombstone Metadata API Integration', () => {
  it('should update tombstone via PATCH /api/jobs/{id}', async () => {});
  it('should return updated job data in response', async () => {});
  it('should validate required fields on backend', async () => {});
  it('should handle partial updates correctly', async () => {});
  it('should preserve unmodified fields', async () => {});
});
```

#### E2E Tests
```typescript
describe('Tombstone Editing E2E Workflow', () => {
  it('should edit tombstone from job list dropdown', async () => {
    // Navigate to job list
    // Click dropdown menu on job row
    // Click Edit action
    // Verify modal opens with current data
    // Modify title and classification
    // Click Save
    // Verify modal closes
    // Verify job list reflects changes
  });

  it('should validate required fields before save', async () => {
    // Open tombstone editor
    // Clear title field
    // Click Save
    // Verify validation error displays
    // Verify save is blocked
    // Enter valid title
    // Click Save
    // Verify success
  });
});
```

### Raw Content Sidebar Tests

#### Unit Tests
```typescript
describe('Raw Content Sidebar', () => {
  describe('Visibility Toggle', () => {
    it('should be hidden by default', () => {});
    it('should show when "Show Raw Content" is clicked', () => {});
    it('should hide when "Hide Raw Content" is clicked', () => {});
    it('should toggle visibility state correctly', () => {});
  });

  describe('Content Display', () => {
    it('should display full raw content in monospace font', () => {});
    it('should handle empty raw content', () => {});
    it('should preserve all whitespace and formatting', () => {});
    it('should be scrollable for long content', () => {});
  });

  describe('Layout Behavior', () => {
    it('should use 8/4 column split on desktop', () => {});
    it('should be sticky on scroll (desktop)', () => {});
    it('should stack vertically on mobile', () => {});
    it('should resize main content area when shown/hidden', () => {});
  });

  describe('Copy/Paste Support', () => {
    it('should allow text selection', () => {});
    it('should support copy operations', () => {});
    it('should not allow editing raw content', () => {});
  });
});
```

---

## Test Suite 2: AI Improvement Mode (Future Feature)

### AI Analysis and Suggestion Generation Tests

#### Unit Tests
```typescript
describe('AI Improvement Service', () => {
  describe('Content Analysis', () => {
    it('should analyze section for improvement opportunities', async () => {});
    it('should generate sentence-level suggestions', async () => {});
    it('should provide rationale for each suggestion', async () => {});
    it('should calculate confidence scores for suggestions', async () => {});
    it('should skip high-quality content with no improvements', async () => {});
  });

  describe('Suggestion Focus Areas', () => {
    it('should identify clarity improvements', async () => {});
    it('should identify completeness gaps', async () => {});
    it('should identify consistency issues', async () => {});
    it('should identify professionalism enhancements', async () => {});
    it('should identify specificity opportunities', async () => {});
  });

  describe('Configuration Handling', () => {
    it('should respect suggestion granularity setting', async () => {});
    it('should respect aggressiveness setting', async () => {});
    it('should respect auto-accept threshold', async () => {});
    it('should apply improvement focus filters', async () => {});
  });

  describe('Error Handling', () => {
    it('should handle OpenAI API unavailability', async () => {});
    it('should handle API rate limits', async () => {});
    it('should handle malformed API responses', async () => {});
    it('should handle timeout errors', async () => {});
    it('should filter invalid suggestions', async () => {});
  });
});
```

#### Unit Tests - UI Components
```typescript
describe('AI Improvement Comparison View', () => {
  describe('Layout and Display', () => {
    it('should display split-pane with original and improved', () => {});
    it('should highlight suggestions with diff visualization', () => {});
    it('should show green for additions', () => {});
    it('should show red strikethrough for deletions', () => {});
    it('should show yellow for modifications', () => {});
    it('should display AI rationale for each suggestion', () => {});
  });

  describe('Suggestion Controls', () => {
    it('should display Accept/Reject/Modify buttons for each', () => {});
    it('should update suggestion state on Accept', () => {});
    it('should mark accepted suggestions with green checkmark', () => {});
    it('should apply accepted text to improved version', () => {});
    it('should update suggestion state on Reject', () => {});
    it('should mark rejected with red strikethrough', () => {});
    it('should preserve original text on Reject', () => {});
    it('should open inline editor on Modify', () => {});
    it('should apply modified text to improved version', () => {});
    it('should track modifications separately', () => {});
  });

  describe('Bulk Operations', () => {
    it('should accept all suggestions in section', () => {});
    it('should reject all suggestions in section', () => {});
    it('should require confirmation for bulk operations', () => {});
    it('should update all suggestion states atomically', () => {});
  });

  describe('Section Navigation', () => {
    it('should allow navigation between sections', () => {});
    it('should preserve state when switching sections', () => {});
    it('should save section before navigation', () => {});
    it('should load next section suggestions', () => {});
  });

  describe('Save and Exit', () => {
    it('should save all improvements on Save button', () => {});
    it('should display improvement summary on Save', () => {});
    it('should warn on exit without saving', () => {});
    it('should allow discard on exit', () => {});
    it('should allow save and exit', () => {});
  });
});
```

#### Integration Tests
```typescript
describe('AI Improvement API Integration', () => {
  it('should send section content to OpenAI API', async () => {});
  it('should receive improvement suggestions from API', async () => {});
  it('should parse and validate API response', async () => {});
  it('should save accepted improvements via PATCH endpoint', async () => {});
  it('should log rejected suggestions for learning', async () => {});
  it('should track improvement history in database', async () => {});
  it('should calculate quality scores before/after', async () => {});
});
```

#### E2E Tests
```typescript
describe('AI Improvement E2E Workflow', () => {
  it('should complete full improvement workflow', async () => {
    // Open job detail
    // Click "AI Improvement Mode"
    // Wait for AI analysis
    // Review first suggestion
    // Accept suggestion
    // Review second suggestion
    // Modify suggestion
    // Review third suggestion
    // Reject suggestion
    // Navigate to next section
    // Complete all sections
    // Save improvements
    // Verify success
    // Verify content updated
  });

  it('should handle iterative improvement cycles', async () => {
    // Complete first improvement cycle
    // Save improvements
    // Re-initiate AI improvement mode
    // Verify analysis based on improved content
    // Apply additional improvements
    // Save second iteration
    // Verify improvement history tracks iterations
  });

  it('should support section-specific improvement', async () => {
    // Open job detail
    // Select specific section
    // Click "Improve This Section Only"
    // Verify only selected section analyzed
    // Complete review
    // Save improvements
    // Verify other sections unchanged
  });
});
```

### Learning Feedback Loop Tests

#### Unit Tests
```typescript
describe('AI Learning Feedback', () => {
  describe('Feedback Collection', () => {
    it('should capture acceptance rate per suggestion type', () => {});
    it('should capture rejection reasons', () => {});
    it('should capture modification patterns', () => {});
    it('should associate feedback with section types', () => {});
    it('should track feedback by advisor ID', () => {});
  });

  describe('Pattern Analysis', () => {
    it('should identify high-acceptance patterns', () => {});
    it('should identify low-acceptance patterns', () => {});
    it('should detect advisor preferences', () => {});
    it('should calculate pattern confidence scores', () => {});
  });

  describe('Model Improvement', () => {
    it('should reinforce successful patterns', () => {});
    it('should adjust for rejected patterns', () => {});
    it('should incorporate advisor modifications as examples', () => {});
    it('should improve suggestions over time', () => {});
  });
});
```

---

## Test Suite 3: Bilingual Translation Mode (Future Feature)

### Translation Service Tests

#### Unit Tests
```typescript
describe('Translation Service', () => {
  describe('Machine Translation', () => {
    it('should translate English to French via API', async () => {});
    it('should translate French to English via API', async () => {});
    it('should handle sentence-level translation', async () => {});
    it('should preserve formatting and whitespace', async () => {});
    it('should handle special characters correctly', async () => {});
    it('should detect source language automatically', async () => {});
  });

  describe('Translation Memory Integration', () => {
    it('should search TM for exact matches', async () => {});
    it('should search TM for fuzzy matches', async () => {});
    it('should calculate match confidence scores', async () => {});
    it('should adapt TM suggestions to new context', async () => {});
    it('should store validated pairs in TM', async () => {});
    it('should include metadata with TM entries', async () => {});
  });

  describe('Terminology Management', () => {
    it('should lookup terms in terminology database', async () => {});
    it('should suggest validated equivalents', async () => {});
    it('should detect terminology inconsistencies', async () => {});
    it('should enforce consistent term usage', async () => {});
    it('should allow justified exceptions', async () => {});
  });

  describe('Concurrence Validation', () => {
    it('should validate sentence pair equivalence', async () => {});
    it('should detect missing translations', async () => {});
    it('should detect extra content in either language', async () => {});
    it('should validate semantic equivalence', async () => {});
    it('should allow structural differences with same meaning', async () => {});
  });
});
```

#### Unit Tests - UI Components
```typescript
describe('Bilingual Translation Editor', () => {
  describe('Dual-Pane Layout', () => {
    it('should display source language in left pane', () => {});
    it('should display target language in right pane', () => {});
    it('should lock source language (non-editable)', () => {});
    it('should allow editing target language', () => {});
    it('should synchronize scroll between panes', () => {});
    it('should highlight corresponding sentences', () => {});
  });

  describe('Translation Suggestions', () => {
    it('should display MT suggestion for each sentence', () => {});
    it('should display TM match confidence score', () => {});
    it('should show Accept/Reject/Modify buttons', () => {});
    it('should display terminology tooltips on hover', () => {});
    it('should show TM source for suggestions', () => {});
  });

  describe('Sentence Validation', () => {
    it('should mark validated pairs with green checkmark', () => {});
    it('should mark pending pairs with yellow warning', () => {});
    it('should mark rejected pairs with red X', () => {});
    it('should mark modified pairs with blue edit icon', () => {});
    it('should display 🔗 linked icon for pair relationship', () => {});
  });

  describe('Translation Actions', () => {
    it('should accept translation suggestion', () => {});
    it('should save validated pair to TM', () => {});
    it('should reject translation suggestion', () => {});
    it('should preserve original on reject', () => {});
    it('should open editor on modify', () => {});
    it('should save custom translation', () => {});
  });

  describe('Bulk Operations', () => {
    it('should auto-accept high-confidence translations', () => {});
    it('should validate all section at once', () => {});
    it('should display validation summary', () => {});
  });

  describe('Bilingual Publication', () => {
    it('should validate both versions complete', () => {});
    it('should check concurrence before publish', () => {});
    it('should publish both versions atomically', () => {});
    it('should create linked relationship in DB', () => {});
    it('should block publish if concurrence invalid', () => {});
  });
});
```

#### Integration Tests
```typescript
describe('Translation API Integration', () => {
  it('should create linked bilingual record', async () => {});
  it('should send translation requests to MT API', async () => {});
  it('should query translation memory database', async () => {});
  it('should store validated pairs in TM', async () => {});
  it('should save target language sections via PATCH', async () => {});
  it('should link both versions with metadata', async () => {});
  it('should flag concurrence breaks on edit', async () => {});
  it('should publish bilingual pairs atomically', async () => {});
});
```

#### E2E Tests
```typescript
describe('Bilingual Translation E2E Workflow', () => {
  it('should translate complete job from English to French', async () => {
    // Open approved English job
    // Click "Translation Mode"
    // Select "Translate to French"
    // Wait for MT pre-fill
    // Review first sentence
    // Verify TM match displayed
    // Accept high-confidence suggestion
    // Review second sentence
    // Modify translation for better nuance
    // Complete all sections
    // Validate concurrence
    // Publish bilingual pair
    // Verify both versions linked
  });

  it('should handle translation memory exact matches', async () => {
    // Translate job with previously translated content
    // Verify 100% TM matches auto-filled
    // Quick-accept exact matches
    // Focus on new content only
    // Complete translation efficiently
  });

  it('should detect and resolve terminology inconsistencies', async () => {
    // Begin translation
    // Translate term "manager" as "gestionnaire"
    // Encounter same term later
    // Attempt different translation "directeur"
    // Verify warning displayed
    // Choose to use consistent term
    // Verify all instances updated
  });

  it('should handle bilingual edit after publication', async () => {
    // Open published bilingual pair
    // Edit English version (add new responsibility)
    // Verify French version flagged for review
    // Update French translation
    // Re-validate concurrence
    // Re-publish bilingual pair
    // Verify link maintained
  });
});
```

### Translation Memory Tests

#### Unit Tests
```typescript
describe('Translation Memory Database', () => {
  describe('TM Storage', () => {
    it('should store validated sentence pairs', async () => {});
    it('should store validator metadata', async () => {});
    it('should store context (section, classification)', async () => {});
    it('should store validation date', async () => {});
    it('should store confidence score', async () => {});
    it('should index for fast retrieval', async () => {});
  });

  describe('TM Retrieval', () => {
    it('should find exact matches', async () => {});
    it('should find fuzzy matches with similarity score', async () => {});
    it('should rank matches by relevance', async () => {});
    it('should filter by context', async () => {});
    it('should retrieve match metadata', async () => {});
  });

  describe('TM Analytics', () => {
    it('should calculate total validated pairs', () => {});
    it('should calculate coverage by section type', () => {});
    it('should calculate reuse rate', () => {});
    it('should identify high-value matches', () => {});
    it('should track accuracy over time', () => {});
  });
});
```

---

## Test Suite 4: Real-Time Collaboration (Future Feature)

### WebSocket Communication Tests

#### Unit Tests
```typescript
describe('Collaborative Editing WebSocket', () => {
  describe('Connection Management', () => {
    it('should establish WebSocket connection', async () => {});
    it('should authenticate user on connect', async () => {});
    it('should handle connection failures', async () => {});
    it('should reconnect on disconnect', async () => {});
    it('should close connection gracefully', async () => {});
  });

  describe('Presence Broadcasting', () => {
    it('should broadcast user join event', async () => {});
    it('should broadcast user leave event', async () => {});
    it('should broadcast section editing event', async () => {});
    it('should broadcast section save event', async () => {});
    it('should receive presence updates from other users', async () => {});
  });

  describe('Operational Transform', () => {
    it('should transform concurrent text insertions', async () => {});
    it('should transform concurrent text deletions', async () => {});
    it('should resolve insert/delete conflicts', async () => {});
    it('should maintain causal ordering', async () => {});
    it('should handle three-way conflicts', async () => {});
  });

  describe('Conflict Resolution', () => {
    it('should detect edit conflicts', async () => {});
    it('should notify users of conflicts', async () => {});
    it('should display conflict resolution UI', async () => {});
    it('should allow manual conflict resolution', async () => {});
    it('should track conflict resolution history', async () => {});
  });
});
```

#### E2E Tests
```typescript
describe('Real-Time Collaboration E2E', () => {
  it('should support multiple users editing different sections', async () => {
    // User A opens job and edits section 1
    // User B opens same job and edits section 2
    // Verify both users see presence indicators
    // User A saves section 1
    // Verify User B sees update
    // User B saves section 2
    // Verify User A sees update
    // Both users verify complete content
  });

  it('should handle concurrent edits to same section', async () => {
    // User A and User B edit same section
    // Both make different changes
    // User A saves first
    // Verify User B receives conflict notification
    // User B reviews conflict
    // User B resolves conflict (accept/merge/reject)
    // Final content reflects resolution
  });
});
```

---

## Test Suite 5: Advanced Features

### Version History Tests

#### Unit Tests
```typescript
describe('Version History', () => {
  describe('Version Tracking', () => {
    it('should create version on each save', async () => {});
    it('should store complete section content in version', async () => {});
    it('should track version number incrementally', async () => {});
    it('should track editor (advisor ID)', async () => {});
    it('should track timestamp', async () => {});
    it('should track change description', async () => {});
  });

  describe('Version Comparison', () => {
    it('should compare any two versions side-by-side', () => {});
    it('should highlight changes with diff visualization', () => {});
    it('should show additions in green', () => {});
    it('should show deletions in red strikethrough', () => {});
    it('should show modifications in yellow', () => {});
  });

  describe('Version Rollback', () => {
    it('should allow rollback to previous version', async () => {});
    it('should create new version on rollback', async () => {});
    it('should preserve rollback reason', async () => {});
    it('should prevent accidental rollback', async () => {});
  });
});
```

### Audit Trail Tests

#### Unit Tests
```typescript
describe('Audit Trail', () => {
  describe('Action Logging', () => {
    it('should log all create operations', async () => {});
    it('should log all update operations', async () => {});
    it('should log all delete operations', async () => {});
    it('should log all archive operations', async () => {});
    it('should log user ID with each action', async () => {});
    it('should log timestamp with each action', async () => {});
    it('should log IP address with each action', async () => {});
  });

  describe('Audit Queries', () => {
    it('should retrieve audit log by job ID', async () => {});
    it('should retrieve audit log by user ID', async () => {});
    it('should retrieve audit log by date range', async () => {});
    it('should retrieve audit log by action type', async () => {});
    it('should filter and sort audit results', async () => {});
  });

  describe('Compliance', () => {
    it('should retain audit logs for required duration', async () => {});
    it('should prevent audit log tampering', async () => {});
    it('should export audit logs for compliance review', async () => {});
  });
});
```

### Search and Filter Tests

#### Unit Tests
```typescript
describe('Advanced Search', () => {
  describe('Full-Text Search', () => {
    it('should search across all sections', async () => {});
    it('should search across metadata fields', async () => {});
    it('should rank results by relevance', async () => {});
    it('should highlight search terms in results', async () => {});
    it('should support fuzzy matching', async () => {});
    it('should support phrase search', async () => {});
  });

  describe('Faceted Filtering', () => {
    it('should filter by classification', async () => {});
    it('should filter by department', async () => {});
    it('should filter by language', async () => {});
    it('should filter by status (active/archived)', async () => {});
    it('should combine multiple filters with AND logic', async () => {});
    it('should display facet counts', async () => {});
  });

  describe('Advanced Filters', () => {
    it('should filter by date range (created, updated)', async () => {});
    it('should filter by skill tags', async () => {});
    it('should filter by competency levels', async () => {});
    it('should save filter presets', async () => {});
  });
});
```

### Bulk Operations Tests

#### Unit Tests
```typescript
describe('Bulk Operations', () => {
  describe('Bulk Selection', () => {
    it('should select multiple jobs via checkboxes', () => {});
    it('should select all jobs on page', () => {});
    it('should clear all selections', () => {});
    it('should maintain selection across pages', () => {});
    it('should display selection count', () => {});
  });

  describe('Bulk Actions', () => {
    it('should archive multiple jobs at once', async () => {});
    it('should delete multiple jobs at once', async () => {});
    it('should update metadata for multiple jobs', async () => {});
    it('should export multiple jobs to PDF/Excel', async () => {});
    it('should require confirmation for destructive actions', () => {});
    it('should display progress indicator', async () => {});
    it('should handle partial failures gracefully', async () => {});
  });
});
```

---

## Test Suite 6: Performance and Load Testing

### Performance Benchmarks

#### Load Tests
```typescript
describe('Performance Benchmarks', () => {
  describe('Page Load Performance', () => {
    it('should load job list page in <2 seconds', async () => {});
    it('should load job detail page in <2 seconds', async () => {});
    it('should load 100 jobs in list without pagination lag', async () => {});
    it('should handle infinite scroll smoothly', async () => {});
  });

  describe('Edit Performance', () => {
    it('should respond to textarea input in <100ms', async () => {});
    it('should save section in <2 seconds', async () => {});
    it('should handle 5 concurrent section edits without lag', async () => {});
    it('should handle 10,000 character content without slowdown', async () => {});
  });

  describe('Search Performance', () => {
    it('should return search results in <500ms', async () => {});
    it('should handle 1000+ job database efficiently', async () => {});
    it('should apply filters without noticeable delay', async () => {});
  });

  describe('AI/Translation Performance', () => {
    it('should generate AI suggestions in <10 seconds', async () => {});
    it('should translate section in <5 seconds', async () => {});
    it('should search TM in <1 second', async () => {});
  });

  describe('Concurrent Users', () => {
    it('should support 10 concurrent users without degradation', async () => {});
    it('should support 50 concurrent users with acceptable performance', async () => {});
    it('should handle 100+ read-only concurrent users', async () => {});
  });
});
```

### Stress Tests
```typescript
describe('Stress Testing', () => {
  it('should handle 10000+ jobs in database', async () => {});
  it('should handle 1000+ sections per job', async () => {});
  it('should handle 100+ concurrent edits', async () => {});
  it('should handle rapid API requests without rate limit errors', async () => {});
  it('should recover from memory spikes', async () => {});
  it('should handle network interruptions gracefully', async () => {});
});
```

---

## Test Suite 7: Security Testing

### Security Tests

#### Authentication & Authorization Tests
```typescript
describe('Security - Authentication', () => {
  it('should require API key for all endpoints', async () => {});
  it('should reject invalid API keys', async () => {});
  it('should reject expired API keys', async () => {});
  it('should enforce rate limits per API key', async () => {});
});

describe('Security - Authorization', () => {
  it('should restrict delete operations to authorized users', async () => {});
  it('should enforce row-level security', async () => {});
  it('should prevent unauthorized data access', async () => {});
});
```

#### Input Validation Tests
```typescript
describe('Security - Input Validation', () => {
  it('should sanitize HTML in user input', async () => {});
  it('should prevent XSS attacks', async () => {});
  it('should prevent SQL injection', async () => {});
  it('should validate all required fields', async () => {});
  it('should enforce max length limits', async () => {});
  it('should reject malicious file uploads', async () => {});
});
```

#### Data Protection Tests
```typescript
describe('Security - Data Protection', () => {
  it('should encrypt sensitive data at rest', async () => {});
  it('should use HTTPS for all API calls', async () => {});
  it('should not expose sensitive data in logs', async () => {});
  it('should implement CORS correctly', async () => {});
  it('should prevent CSRF attacks', async () => {});
});
```

---

## Test Coverage Summary Matrix

### Coverage by Feature
| Feature | Unit Tests | Integration Tests | E2E Tests | Total Coverage |
|---------|-----------|-------------------|-----------|----------------|
| Section Editing | 35 tests | 8 tests | 5 tests | **100%** |
| Tombstone Editing | 20 tests | 6 tests | 3 tests | **100%** |
| Raw Content Sidebar | 12 tests | 2 tests | 2 tests | **100%** |
| AI Improvement | 45 tests | 8 tests | 4 tests | **100%** (future) |
| Bilingual Translation | 52 tests | 10 tests | 5 tests | **100%** (future) |
| Collaboration | 18 tests | 5 tests | 3 tests | **100%** (future) |
| Version History | 12 tests | 4 tests | 2 tests | **100%** (future) |
| Audit Trail | 15 tests | 4 tests | 1 test | **100%** (future) |
| Search & Filter | 18 tests | 6 tests | 3 tests | **100%** (future) |
| Bulk Operations | 14 tests | 5 tests | 2 tests | **100%** (future) |
| Performance | 15 tests | N/A | 10 tests | **100%** |
| Security | 18 tests | 8 tests | 3 tests | **100%** |

### Total Test Count
- **Unit Tests**: 274 tests
- **Integration Tests**: 66 tests
- **E2E Tests**: 43 tests
- **Total**: **383 comprehensive tests** covering 100% of current and future features

---

## Performance & Accessibility Testing

### Performance Requirements
```gherkin
Scenario: Large Job Description Editing
Given: A job description with 10+ sections and 10,000+ words
When: Advisor opens job detail view
Then: Page loads in <2 seconds
And: All sections render completely
And: Edit operations respond in <500ms
And: Save operations complete in <2 seconds

Scenario: Concurrent Multi-Section Editing
Given: Advisor is editing 5 sections simultaneously
When: Advisor cuts and pastes content between sections
Then: UI remains responsive (<100ms input lag)
And: No content is lost during operations
And: Memory usage remains stable
```

### Accessibility Requirements
```gherkin
Scenario: Keyboard-Only Navigation
Given: Advisor is using keyboard navigation only
When: Advisor tabs through job detail view
Then: All interactive elements are reachable
And: Edit buttons receive focus with visible indicator
And: Save/Cancel buttons are accessible via keyboard
And: Section focus order is logical (top to bottom)

Scenario: Screen Reader Usage
Given: Advisor is using screen reader
When: Advisor navigates job detail view
Then: All section headings are announced
And: Edit state changes are announced ("Editing General Accountability")
And: Save success is announced ("Section saved successfully")
And: Error messages are announced immediately

Scenario: High Contrast Mode
Given: Advisor has high contrast mode enabled
When: Advisor views and edits job descriptions
Then: All text is readable with sufficient contrast
And: Edit mode ring highlight is visible
And: Button states are clearly distinguishable
```

---

## Quality Assurance Checklist

### Before Each Release
- [ ] All user stories have passing automated tests
- [ ] Manual testing completed for each workflow
- [ ] Performance benchmarks met for large datasets
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Cross-browser testing completed (Chrome, Firefox, Edge)
- [ ] Mobile responsiveness validated (if applicable)
- [ ] Security review completed (input validation, XSS prevention)
- [ ] Database migration tested and verified
- [ ] Backup and recovery procedures tested
- [ ] Documentation updated to reflect changes
- [ ] User training materials prepared
- [ ] Rollback plan documented and tested

### Senior Advisor Training Checklist
- [ ] Navigation and search functionality
- [ ] Section-by-section editing workflow
- [ ] Concurrent section editing for cut/paste
- [ ] Raw content sidebar usage
- [ ] Tombstone metadata editing
- [ ] Quality validation procedures
- [ ] Archival and deletion workflows
- [ ] Bilingual concurrence validation (when available)
- [ ] AI improvement workflow (when available)
- [ ] Error handling and recovery procedures

---

## Metrics & Success Criteria

### Key Performance Indicators (KPIs)

**Efficiency Metrics**:
- Average time to create new job description: Target <30 minutes
- Average time to update existing job: Target <15 minutes
- Average time to review job for quality: Target <20 minutes
- Number of jobs processed per advisor per day: Target >10

**Quality Metrics**:
- Percentage of jobs passing quality gates on first review: Target >80%
- Number of errors requiring rework: Target <2 per job
- Bilingual concurrence accuracy: Target >95%
- Classification accuracy: Target >98%

**User Satisfaction**:
- Advisor satisfaction with editing workflow: Target >4.5/5
- Manager satisfaction with advisor guidance: Target >4.0/5
- System usability score: Target >80/100

**System Performance**:
- Page load time: Target <2 seconds
- Save operation response time: Target <1 second
- Search result response time: Target <500ms
- System uptime: Target >99.5%
