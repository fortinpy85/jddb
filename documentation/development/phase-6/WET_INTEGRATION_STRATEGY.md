# WET Integration Strategy for JDDB

**Phase 6 - Government Compliance & Accessibility Enhancement**

## Executive Summary

This document outlines the strategy for integrating the Government of Canada's Web Experience Toolkit (WET-BOEW) into the Job Description Database (JDDB) application to achieve full government compliance, bilingual support, and WCAG 2.0 Level AA accessibility.

## Table of Contents

1. [What is WET-BOEW?](#what-is-wet-boew)
2. [Why WET Integration?](#why-wet-integration)
3. [Integration Options Analysis](#integration-options-analysis)
4. [Recommended Approach](#recommended-approach)
5. [Implementation Plan](#implementation-plan)
6. [Bilingual Support Strategy](#bilingual-support-strategy)
7. [Accessibility Compliance](#accessibility-compliance)
8. [Technical Considerations](#technical-considerations)
9. [Migration Path](#migration-path)
10. [Success Criteria](#success-criteria)

---

## What is WET-BOEW?

**Web Experience Toolkit (WET-BOEW)** is an award-winning front-end framework for building accessible, usable, and multilingual websites, developed and maintained by the Government of Canada.

### Key Features

- **Accessibility**: WCAG 2.0 Level AA compliance
- **Bilingual**: Full English/French support (+ 32 other languages)
- **Responsive**: Mobile-first design
- **Browser Support**: Edge, Firefox, Chrome, Safari, Opera
- **Open Source**: MIT License, collaborative development on GitHub
- **Themeable**: 5 different themes including Canada.ca theme

### Core Components

- Flexible templates and layouts
- Reusable UI components (alerts, tabs, modals, tables, etc.)
- Accessibility plugins (aria enhancements, keyboard navigation)
- Form validation and error handling
- Bilingual language toggle
- Print-friendly styles
- Structured data support (RDFa, Schema.org)

---

## Why WET Integration?

### Compliance Requirements

1. **Government Standards**: Federal government websites must use WET or be WET-compatible
2. **Accessibility**: Mandatory WCAG 2.0 Level AA compliance for government services
3. **Official Languages Act**: Full English/French bilingual support required
4. **Brand Consistency**: Alignment with Canada.ca design system

### Business Benefits

1. **Accessibility**: Ensures all users can access the system
2. **Legal Compliance**: Meets government regulatory requirements
3. **User Trust**: Professional, recognizable government interface
4. **Maintenance**: Leverages well-tested, government-supported components
5. **Future-Proofing**: Stays aligned with evolving government standards

### Current Gaps in JDDB

- ❌ No WET framework integration
- ❌ Limited WCAG 2.0 AA compliance
- ⚠️ Partial bilingual support (content only, not UI)
- ❌ Missing government-standard components
- ❌ No Canada.ca theme consistency

---

## Integration Options Analysis

### Option 1: Full WET jQuery-Based Implementation

**Description**: Replace existing React UI with traditional WET HTML + jQuery templates.

**Pros**:
- ✅ 100% WET compliance guaranteed
- ✅ Leverages all official WET components
- ✅ Well-documented, proven approach
- ✅ Government-approved pattern

**Cons**:
- ❌ Requires complete UI rewrite
- ❌ Abandons existing React infrastructure
- ❌ Loss of modern React features (hooks, context, lazy loading)
- ❌ jQuery dependency conflicts with modern tooling
- ❌ Difficult to maintain with Bun + React architecture

**Verdict**: ❌ **Not Recommended** - Too disruptive, incompatible with existing architecture

---

### Option 2: @arcnovus/wet-boew-react Wrapper

**Description**: Use community-built React wrapper around WET components.

**Pros**:
- ✅ React-native API (JSX, hooks, props)
- ✅ TypeScript support
- ✅ Wraps official WET functionality
- ✅ Maintains modern development workflow
- ✅ WetProvider context pattern

**Cons**:
- ⚠️ Community-maintained (not official GC project)
- ⚠️ Limited documentation
- ⚠️ May lag behind WET updates
- ⚠️ No published releases yet (GitHub repo active but early stage)
- ⚠️ Potential compatibility issues with Bun runtime

**Verdict**: ⚠️ **Evaluate Further** - Promising but needs maturity assessment

---

### Option 3: Hybrid Approach (Recommended)

**Description**: Integrate WET styles, accessibility patterns, and components selectively while maintaining React architecture.

**Approach**:
1. **Adopt WET Styles**: Use WET CSS/SCSS for consistent Canada.ca theming
2. **Component Mapping**: Map existing components to WET design patterns
3. **Accessibility Layer**: Implement WCAG 2.0 AA standards using WET guidelines
4. **Bilingual Infrastructure**: Build on WET's language toggle pattern
5. **Progressive Enhancement**: Add WET plugins where beneficial (tables, modals, etc.)

**Pros**:
- ✅ Maintains React architecture and performance
- ✅ Achieves compliance without full rewrite
- ✅ Leverages WET standards and accessibility patterns
- ✅ Compatible with Bun + React + TypeScript stack
- ✅ Incremental migration path
- ✅ Custom implementation means full control

**Cons**:
- ⚠️ Requires custom development effort
- ⚠️ Need to ensure ongoing compliance with WET updates
- ⚠️ Manual testing required for accessibility
- ⚠️ Some WET JavaScript plugins may need adaptation

**Verdict**: ✅ **Recommended** - Best balance of compliance and practicality

---

## Recommended Approach

### Three-Phase Hybrid Integration

#### Phase 1: Foundation (2-3 weeks)

**Goal**: Establish WET theming and accessibility infrastructure

1. **WET CSS Integration**
   - Download WET 4.0.x distribution
   - Include WET CSS in build pipeline
   - Apply Canada.ca theme to base layout
   - Map color palette, typography, spacing

2. **Accessibility Audit**
   - Run axe-core accessibility testing
   - Identify WCAG 2.0 AA violations
   - Document remediation requirements
   - Create accessibility testing checklist

3. **Bilingual Foundation**
   - Implement i18n infrastructure (react-i18next)
   - Create English/French translation files
   - Build language toggle component (WET pattern)
   - Translate all UI strings

**Deliverables**:
- WET CSS integrated and applied
- Accessibility audit report
- Bilingual UI infrastructure
- Language toggle component

---

#### Phase 2: Component Compliance (3-4 weeks)

**Goal**: Align existing components with WET design patterns and accessibility standards

1. **Component Mapping**
   - Map all existing components to WET equivalents
   - Identify gaps and custom needs
   - Document design decisions

2. **Core Component Updates**
   - **Forms**: Adopt WET form patterns (validation, error display)
   - **Buttons**: Apply WET button styles and states
   - **Alerts**: Use WET alert/notification patterns
   - **Modals**: Implement WET modal accessibility
   - **Tables**: Apply WET table patterns (sortable, filterable)
   - **Navigation**: Adopt WET navigation and breadcrumb patterns
   - **Cards**: Use WET panel/well patterns

3. **Accessibility Enhancements**
   - Add ARIA labels and roles
   - Implement keyboard navigation
   - Ensure focus management
   - Add skip links
   - Test with screen readers (NVDA, JAWS)

4. **Responsive Design**
   - Verify mobile breakpoints match WET
   - Test touch interactions
   - Optimize for small screens

**Deliverables**:
- Component mapping documentation
- WET-compliant component library
- Accessibility test results
- Responsive design validation

---

#### Phase 3: Advanced Features & Validation (2-3 weeks)

**Goal**: Implement advanced WET features and validate full compliance

1. **Advanced Components**
   - Date picker (WET pattern)
   - Data tables with sorting/filtering
   - Wizards/steppers
   - Charts and graphs (accessible)
   - File upload (accessible)

2. **Bilingual Content**
   - Translate all static content
   - Implement bilingual job descriptions
   - Add language-specific routing
   - Test language persistence

3. **Print Styles**
   - Implement WET print CSS
   - Test print layouts
   - Ensure accessibility in print

4. **Compliance Validation**
   - Full WCAG 2.0 AA audit (automated + manual)
   - Cross-browser testing (Edge, Firefox, Chrome, Safari)
   - Screen reader testing (NVDA, JAWS, VoiceOver)
   - Mobile device testing
   - Performance benchmarking
   - Government review (if available)

**Deliverables**:
- Complete WET-compliant application
- WCAG 2.0 AA compliance report
- Cross-browser test results
- Screen reader test results
- Performance report
- Government compliance sign-off

---

## Implementation Plan

### Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  JDDB Application                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          React Components (Bun Runtime)          │  │
│  │                                                  │  │
│  │  ├─ Existing: JobList, JobDetails, etc.        │  │
│  │  ├─ Enhanced: WET-compliant styling            │  │
│  │  ├─ New: Language Toggle, Accessible Forms     │  │
│  │  └─ Bilingual: i18next integration             │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         ├─────────────┐                 │
│                         ▼             ▼                 │
│  ┌───────────────────────────┐  ┌─────────────────┐    │
│  │    WET CSS/SCSS           │  │  Accessibility  │    │
│  │  - Canada.ca theme        │  │  - ARIA labels  │    │
│  │  - Typography             │  │  - Keyboard nav │    │
│  │  - Components             │  │  - Focus mgmt   │    │
│  │  - Responsive grid        │  │  - Skip links   │    │
│  └───────────────────────────┘  └─────────────────┘    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Bilingual Infrastructure                 │  │
│  │  ├─ react-i18next                               │  │
│  │  ├─ Language detection                          │  │
│  │  ├─ Translation files (en.json, fr.json)       │  │
│  │  └─ URL-based language routing                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── wet/
│   ├── styles/
│   │   ├── theme-gcweb.scss       # Canada.ca theme
│   │   ├── components.scss         # WET components
│   │   └── overrides.scss          # Custom overrides
│   ├── components/
│   │   ├── LanguageToggle.tsx      # Bilingual switcher
│   │   ├── SkipLinks.tsx           # Accessibility
│   │   ├── WETAlert.tsx            # WET-style alerts
│   │   ├── WETButton.tsx           # WET-style buttons
│   │   ├── WETModal.tsx            # Accessible modals
│   │   └── WETTable.tsx            # Accessible tables
│   └── utils/
│       ├── accessibility.ts        # ARIA utilities
│       └── bilingual.ts            # Language helpers
├── locales/
│   ├── en/
│   │   ├── common.json             # Common UI strings
│   │   ├── jobs.json               # Job-related strings
│   │   └── errors.json             # Error messages
│   └── fr/
│       ├── common.json
│       ├── jobs.json
│       └── errors.json
└── i18n/
    ├── config.ts                   # i18next setup
    └── types.ts                    # Type definitions
```

---

## Bilingual Support Strategy

### Implementation with react-i18next

1. **Installation**
   ```bash
   bun add react-i18next i18next i18next-browser-languagedetector
   ```

2. **Configuration** (src/i18n/config.ts)
   ```typescript
   import i18n from 'i18next';
   import { initReactI18next } from 'react-i18next';
   import LanguageDetector from 'i18next-browser-languagedetector';

   i18n
     .use(LanguageDetector)
     .use(initReactI18next)
     .init({
       resources: {
         en: {
           common: require('../locales/en/common.json'),
           jobs: require('../locales/en/jobs.json'),
         },
         fr: {
           common: require('../locales/fr/common.json'),
           jobs: require('../locales/fr/jobs.json'),
         },
       },
       fallbackLng: 'en',
       defaultNS: 'common',
       interpolation: {
         escapeValue: false, // React already escapes
       },
     });

   export default i18n;
   ```

3. **Usage in Components**
   ```typescript
   import { useTranslation } from 'react-i18next';

   function JobList() {
     const { t } = useTranslation('jobs');

     return (
       <h1>{t('title')}</h1>
       <p>{t('description')}</p>
     );
   }
   ```

4. **Language Toggle Component** (WET Pattern)
   ```typescript
   export function LanguageToggle() {
     const { i18n } = useTranslation();
     const currentLang = i18n.language;
     const toggleLang = currentLang === 'en' ? 'fr' : 'en';
     const label = currentLang === 'en' ? 'Français' : 'English';

     return (
       <button
         onClick={() => i18n.changeLanguage(toggleLang)}
         className="btn btn-link"
         lang={toggleLang}
         aria-label={`Switch to ${label}`}
       >
         {label}
       </button>
     );
   }
   ```

### Translation Management

1. **Translation Files Structure**
   - Namespace by feature area (common, jobs, analytics, etc.)
   - Use nested keys for organization
   - Support pluralization and interpolation
   - Include contextual comments for translators

2. **Translation Workflow**
   - Developer creates English strings
   - Translation files submitted to official GC translation services
   - Translated files reviewed and integrated
   - Automated testing ensures all keys exist in both languages

3. **Content Translation**
   - Job descriptions: Store both EN and FR versions in database
   - Dynamic content: API returns content in requested language
   - Fallback: Show English if French not available (with notice)

---

## Accessibility Compliance

### WCAG 2.0 Level AA Requirements

#### Perceivable

1. **Text Alternatives** (1.1)
   - Alt text for all images
   - ARIA labels for icon-only buttons
   - Descriptive link text

2. **Time-based Media** (1.2)
   - Captions for videos (if applicable)
   - Audio descriptions (if applicable)

3. **Adaptable** (1.3)
   - Semantic HTML (headings, lists, tables)
   - Proper heading hierarchy (h1 → h2 → h3)
   - Form labels associated with inputs
   - ARIA landmarks (navigation, main, aside, etc.)

4. **Distinguishable** (1.4)
   - Color contrast ratios (4.5:1 for normal text, 3:1 for large text)
   - No information conveyed by color alone
   - Text resizable up to 200% without loss of functionality
   - Focus indicators visible

#### Operable

1. **Keyboard Accessible** (2.1)
   - All functionality via keyboard
   - No keyboard traps
   - Skip links to main content

2. **Enough Time** (2.2)
   - No time limits (or adjustable)
   - Session timeout warnings

3. **Seizures** (2.3)
   - No flashing content (> 3 flashes/second)

4. **Navigable** (2.4)
   - Bypass blocks (skip links)
   - Page titles descriptive
   - Focus order logical
   - Link purpose clear from context
   - Multiple navigation methods (menu, search, breadcrumbs)
   - Focus visible
   - Current location indicated

#### Understandable

1. **Readable** (3.1)
   - Language of page declared (`<html lang="en">`)
   - Language of parts declared (bilingual content)

2. **Predictable** (3.2)
   - Consistent navigation
   - Consistent identification
   - No changes on focus
   - No changes on input (without warning)

3. **Input Assistance** (3.3)
   - Error identification
   - Labels or instructions
   - Error suggestions
   - Error prevention (confirmation for important actions)

#### Robust

1. **Compatible** (4.1)
   - Valid HTML
   - Proper ARIA usage
   - Status messages announced

### Testing Tools

1. **Automated**:
   - axe-core (integrated into Playwright tests)
   - WAVE browser extension
   - Lighthouse accessibility audit

2. **Manual**:
   - Keyboard-only navigation testing
   - Screen reader testing (NVDA, JAWS, VoiceOver)
   - Color contrast verification (Colour Contrast Analyser)
   - Zoom testing (200%, 400%)

3. **Government Validation**:
   - Submit to Shared Services Canada for review (if available)
   - Use GC Accessibility Testing Guide

---

## Technical Considerations

### WET CSS Integration with Tailwind

**Challenge**: JDDB uses Tailwind CSS; WET has its own CSS framework.

**Solution**: Scoped Integration
```typescript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  important: true, // Increase Tailwind specificity
  theme: {
    extend: {
      colors: {
        // Map WET colors to Tailwind
        'gc-blue': '#26374a',
        'gc-red': '#af3c43',
        'gc-link': '#284162',
      },
    },
  },
  // Prefix custom utilities to avoid conflicts
  prefix: 'tw-',
};
```

**CSS Loading Order**:
1. WET base styles (typography, reset)
2. WET components (forms, buttons, etc.)
3. Tailwind utilities
4. Custom overrides

### Bun Runtime Compatibility

**WET JavaScript Plugins**: Some WET plugins use jQuery.

**Options**:
1. **Include jQuery for WET plugins** (simplest, adds ~30kb)
2. **Vanilla JS alternatives** (re-implement needed plugins)
3. **React component wrappers** (componentDidMount trigger)

**Recommendation**: Option 1 for Phase 1-2, migrate to Option 3 long-term.

### Performance Impact

**WET CSS**: ~200kb minified + gzipped (~40kb)
**WET JS (if used)**: ~100kb minified + gzipped (~30kb)

**Mitigation**:
- Tree-shake unused WET CSS
- Lazy load WET JS plugins only where needed
- Use CDN for WET assets (Canada.ca CDN)

### TypeScript Support

**Challenge**: WET lacks TypeScript definitions.

**Solution**: Create custom type definitions
```typescript
// src/types/wet.d.ts
declare module 'wet-boew' {
  export interface WETConfig {
    theme: 'gcweb' | 'base' | 'ogpl';
    language: 'en' | 'fr';
  }
  // ... other types
}
```

---

## Migration Path

### Incremental Rollout Strategy

**Week 1-2**: Foundation
- Integrate WET CSS
- Set up i18next
- Create language toggle
- Run accessibility audit

**Week 3-4**: Core Components
- Update forms (validation, errors)
- Update buttons and links
- Add ARIA labels
- Implement skip links

**Week 5-6**: Layout & Navigation
- Apply WET header/footer patterns
- Update navigation with breadcrumbs
- Implement responsive grid
- Add focus management

**Week 7-8**: Advanced Features
- Accessible tables (sort, filter)
- Accessible modals
- Date pickers
- Charts (if applicable)

**Week 9-10**: Content Translation
- Translate UI strings
- Add bilingual job description support
- Test language switching
- Validate translations

**Week 11-12**: Testing & Validation
- Full WCAG 2.0 AA audit
- Cross-browser testing
- Screen reader testing
- Performance optimization
- Government review

### Backward Compatibility

- Maintain existing React component APIs
- Use feature flags for gradual rollout
- Support English-only mode during translation
- Provide fallbacks for unsupported browsers

---

## Success Criteria

### Compliance Metrics

✅ **WCAG 2.0 Level AA**: 0 violations in automated testing
✅ **Screen Reader**: Full functionality with NVDA, JAWS, VoiceOver
✅ **Keyboard Navigation**: All features accessible without mouse
✅ **Bilingual**: 100% UI translated, language toggle functional
✅ **Browser Support**: Full functionality in Edge, Firefox, Chrome, Safari
✅ **Mobile**: Responsive design, touch-friendly interactions
✅ **Performance**: Lighthouse accessibility score ≥ 95

### User Acceptance

✅ **Accessibility**: Users with disabilities can complete all tasks
✅ **Bilingual**: Seamless switching between English and French
✅ **Usability**: No degradation in user experience
✅ **Performance**: Page load time ≤ 3 seconds

### Technical Quality

✅ **Code Quality**: TypeScript strict mode, 0 errors
✅ **Test Coverage**: ≥ 80% coverage for accessibility features
✅ **Documentation**: Complete WET integration guide
✅ **Maintainability**: Clear separation of concerns, modular architecture

---

## Next Steps

1. **Approval**: Review and approve this strategy with stakeholders
2. **Resource Allocation**: Assign developers, testers, translators
3. **Timeline**: Finalize implementation schedule (recommended 12 weeks)
4. **Kickoff**: Begin Phase 1 - Foundation setup
5. **Monitoring**: Weekly progress reviews, bi-weekly demos

---

## Resources

- [WET-BOEW Official Site](https://wet-boew.github.io/wet-boew/index-en.html)
- [Canada.ca Design System](https://www.canada.ca/en/government/about/design-system.html)
- [WCAG 2.0 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [GC Accessibility Testing Guide](https://www.canada.ca/en/treasury-board-secretariat/services/government-communications/canada-content-style-guide.html)
- [react-i18next Documentation](https://react.i18next.com/)
- [@arcnovus/wet-boew-react](https://github.com/arcdev1/wet-boew-react)

---

**Document Version**: 1.0
**Last Updated**: October 7, 2025
**Author**: JDDB Development Team
**Status**: Draft for Review
