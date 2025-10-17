# Web Experience Toolkit (WET) Integration Plan

**Project**: JDDB - Job Description Database
**Target**: Phase 3.1 (Q1) - Decision-dependent implementation
**Status**: Planning / Evaluation Required
**Last Updated**: October 1, 2025

---

## Executive Summary

The Web Experience Toolkit (WET) is Canada's official front-end framework for building accessible, bilingual government websites. This document outlines the strategic decision points, implementation options, and technical approach for potentially integrating WET into the JDDB application.

**Key Decision**: Is this a Government of Canada project requiring federal web standards compliance?

- **YES** → Full WET Integration (Option A) - Mandatory
- **MAYBE** → Hybrid Approach (Option B) - Leverage WET accessibility
- **NO** → WET-Inspired Patterns (Option C) - Learn from best practices

---

## WET Overview

### What is WET?

The Web Experience Toolkit (WET) is an award-winning front-end framework developed by the Government of Canada. It provides:

- **Accessibility**: WCAG 2.0 Level AA compliant components with WAI-ARIA support
- **Bilingualism**: Native English/French with 32 additional languages
- **Interoperability**: Works with Drupal, WordPress, SharePoint, and modern frameworks
- **Open Source**: Openly managed on GitHub with community contributions
- **Standards Compliance**: Aligns with GC Web Standards and Treasury Board requirements

### Official Resources

- **Website**: https://wet-boew.github.io/wet-boew/index-en.html
- **GitHub**: https://github.com/wet-boew
- **Documentation**: https://wet-boew.github.io/wet-boew-documentation/
- **React Package**: https://www.npmjs.com/package/@arcnovus/wet-boew-react
- **Alternative React**: https://www.npmjs.com/package/wet-react

### Browser/Device Support

- **Modern Browsers**: Edge, Firefox, Chrome, Safari, Opera
- **Mobile**: Responsive design with touchscreen support
- **Assistive Tech**: JAWS, NVDA, VoiceOver compatible
- **Devices**: Desktop, tablet, mobile (all screen sizes)

---

## Strategic Decision Framework

### Question 1: Is this a Government of Canada project?

**If YES:**
- **Requirement**: Federal web standards compliance mandatory
- **Recommendation**: Option A (Full WET Integration)
- **Timeline**: 4-6 weeks
- **Priority**: CRITICAL
- **Benefits**: Legal compliance, reduced risk, GC branding

**If NO:** → Continue to Question 2

### Question 2: Is WCAG 2.0 Level AA compliance legally required?

**If YES:**
- **Requirement**: Accessibility legislation compliance (e.g., ADA, AODA, European EAA)
- **Recommendation**: Option B (Hybrid Approach)
- **Timeline**: 2-3 weeks
- **Priority**: HIGH
- **Benefits**: Proven accessible components, reduced testing burden

**If NO:** → Continue to Question 3

### Question 3: Is bilingual (EN/FR) support critical?

**If YES:**
- **Requirement**: Full bilingual support with language switching
- **Recommendation**: Option A or B (WET provides superior i18n)
- **Timeline**: 2-6 weeks
- **Priority**: HIGH
- **Benefits**: Battle-tested bilingual infrastructure, date/number formatting

**If NO:**
- **Recommendation**: Option C (WET-Inspired Patterns)
- **Timeline**: 1-2 weeks
- **Priority**: MEDIUM
- **Benefits**: Learn accessibility best practices without migration overhead

---

## Implementation Options

### Option A: Full WET Integration ⭐ Recommended for GC Projects

**Overview**: Migrate to WET as the primary design system, replacing current custom components.

**When to Choose**:
- Government of Canada project
- Federal web standards compliance required
- Bilingual (EN/FR) support critical
- Long-term maintenance and updates needed

**Pros**:
- ✅ Full WCAG 2.0 Level AA compliance out-of-the-box
- ✅ Government of Canada branding and visual identity
- ✅ Superior bilingual infrastructure (34 languages)
- ✅ Battle-tested components used across federal websites
- ✅ Centrally maintained and updated by GC team
- ✅ Reduced custom development and testing

**Cons**:
- ❌ Longer migration timeline (4-6 weeks)
- ❌ Learning curve for team
- ❌ Potential bundle size increase
- ❌ May require design changes to match GC standards
- ❌ Less flexibility for custom branding

**Technical Approach**:

#### Phase A1: Research & Setup (Week 1)
```bash
# Install WET React package (TypeScript, no jQuery)
bun add @arcnovus/wet-boew-react

# Alternative (early stage, removes jQuery)
bun add wet-react
```

**Tasks**:
- [ ] Evaluate WET 4.x vs WET 5.x (next-gen)
- [ ] Review WET component library documentation
- [ ] Map JDDB components to WET equivalents
- [ ] Create component migration checklist
- [ ] Setup development branch for WET integration

#### Phase A2: Core Infrastructure (Week 1-2)

**App Wrapper**:
```typescript
// src/app/page.tsx or root layout
import { WetProvider } from '@arcnovus/wet-boew-react';

export default function App() {
  return (
    <WetProvider
      language="en" // or "fr"
      theme="gcweb" // Government of Canada Web theme
      cdtsEnvironment="prod" // Centrally Deployed Template System
    >
      {/* Existing app content */}
      <HomePage />
    </WetProvider>
  );
}
```

**Tasks**:
- [ ] Wrap application with `<WetProvider>`
- [ ] Configure CDTS (Centrally Deployed Template System)
- [ ] Setup language switching mechanism
- [ ] Test WET CSS/JS injection
- [ ] Verify no style conflicts

#### Phase A3: Header/Navigation Migration (Week 2)

**Replace AppHeader**:
```typescript
// Use WET header component
import { Header, Navigation } from '@arcnovus/wet-boew-react';

<Header
  title="Job Description Database"
  subtitle="AI-Powered Management System"
  language={currentLanguage}
  onLanguageChange={handleLanguageChange}
/>

<Navigation
  items={[
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Jobs', href: '/jobs' },
    { label: 'Upload', href: '/upload' },
    // ...
  ]}
/>
```

**Tasks**:
- [ ] Migrate AppHeader to WET Header component
- [ ] Implement WET Navigation with menu items
- [ ] Add bilingual labels (EN/FR)
- [ ] Test responsive navigation (mobile menu)
- [ ] Verify accessibility (keyboard navigation, ARIA)

#### Phase A4: Forms Migration (Week 2-3)

**Replace Form Components**:
```typescript
// WET form components
import { FormGroup, Input, Select, Checkbox } from '@arcnovus/wet-boew-react';

<FormGroup label="Job Code" required>
  <Input
    id="job-code"
    name="jobCode"
    value={jobCode}
    onChange={handleChange}
    aria-describedby="job-code-error"
  />
</FormGroup>
```

**Tasks**:
- [ ] Replace search forms with WET form components
- [ ] Migrate upload form to WET inputs
- [ ] Update job editing forms
- [ ] Add WET validation messages
- [ ] Test form accessibility

#### Phase A5: Data Tables (Week 3)

**Replace JobsTable**:
```typescript
// WET DataTable component
import { DataTable } from '@arcnovus/wet-boew-react';

<DataTable
  columns={[
    { header: 'Job Code', accessor: 'job_code' },
    { header: 'Classification', accessor: 'classification' },
    // ...
  ]}
  data={jobs}
  sortable
  filterable
  pagination
/>
```

**Tasks**:
- [ ] Migrate JobsTable to WET DataTable
- [ ] Configure sorting and filtering
- [ ] Setup pagination
- [ ] Test responsive table behavior
- [ ] Verify keyboard navigation

#### Phase A6: UI Components (Week 3-4)

**Migrate Remaining Components**:
- [ ] Replace buttons with WET Button component
- [ ] Migrate cards to WET panels/wells
- [ ] Update alerts to WET Alert component
- [ ] Migrate tabs to WET Tabs widget
- [ ] Replace modals with WET overlays

#### Phase A7: Bilingual Content (Week 4)

**Language Strings**:
```typescript
// Create bilingual content files
// src/i18n/en.json
{
  "dashboard.title": "Dashboard",
  "jobs.table.jobCode": "Job Code",
  // ...
}

// src/i18n/fr.json
{
  "dashboard.title": "Tableau de bord",
  "jobs.table.jobCode": "Code d'emploi",
  // ...
}
```

**Tasks**:
- [ ] Create English language strings
- [ ] Translate all UI text to French
- [ ] Implement language toggle in header
- [ ] Setup WET bilingual utilities
- [ ] Test language switching across all views
- [ ] Verify date/number formatting in both languages

#### Phase A8: Testing & Validation (Week 4)

**Accessibility Testing**:
- [ ] Run automated WCAG 2.0 AA tests (aXe, Lighthouse)
- [ ] Manual keyboard navigation testing
- [ ] Screen reader testing (JAWS, NVDA)
- [ ] Color contrast verification
- [ ] Focus indicator visibility
- [ ] ARIA label completeness

**Cross-Browser Testing**:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Mobile browsers (Android/iOS)

**Performance Testing**:
- [ ] Measure bundle size impact
- [ ] Test page load times
- [ ] Verify no performance regressions

**Effort**: 4-6 weeks full-time
**Cost**: High (development time + potential design changes)
**Risk**: Medium (migration complexity, team learning curve)

---

### Option B: Hybrid Approach ⚖️ Balanced Solution

**Overview**: Integrate WET components selectively while maintaining existing custom UI.

**When to Choose**:
- Accessibility compliance required but not GC-specific
- Want WET's proven accessible components
- Need to maintain custom branding/design
- Shorter timeline than full migration

**Pros**:
- ✅ Leverage WET's accessible components where needed
- ✅ Keep custom design for dashboard/visualization
- ✅ Faster implementation (2-3 weeks)
- ✅ Use WET utilities without full migration
- ✅ Flexible branding

**Cons**:
- ❌ May have styling inconsistencies
- ❌ Two component libraries to maintain
- ❌ Partial compliance (not full GC standards)
- ❌ More complex dependency management

**Technical Approach**:

#### Phase B1: Strategic Component Selection (Week 1)

**Use WET For**:
- Forms (input, select, checkbox, radio, date picker)
- Alerts/notifications
- Accessibility utilities
- Language toggle
- Breadcrumbs

**Keep Custom**:
- Dashboard cards and visualizations
- Data tables (unless WET DataTable is superior)
- Navigation (already implemented well)
- Page transitions and animations

**Tasks**:
- [ ] Audit current components
- [ ] Identify WET component replacements
- [ ] Create component mapping document
- [ ] Plan phased rollout

#### Phase B2: WET Utilities Integration (Week 1)

```bash
bun add @arcnovus/wet-boew-react
```

```typescript
// Import only what you need
import { WetProvider, FormGroup, Input, Alert } from '@arcnovus/wet-boew-react';
import '@arcnovus/wet-boew-react/dist/wet.css'; // WET styles

// Scope WET styles to avoid conflicts
import './custom-styles.css'; // Load custom styles after WET
```

**Tasks**:
- [ ] Install WET React package
- [ ] Import WET CSS framework
- [ ] Scope WET styles to avoid conflicts
- [ ] Setup CSS modules for custom components
- [ ] Test style isolation

#### Phase B3: Form Components Migration (Week 1-2)

**Replace Form Inputs**:
```typescript
// Old: Custom input
<input type="text" name="jobCode" />

// New: WET FormGroup + Input
<FormGroup label="Job Code" required>
  <Input
    id="job-code"
    name="jobCode"
    aria-describedby="job-code-help"
  />
</FormGroup>
```

**Tasks**:
- [ ] Replace search form inputs
- [ ] Migrate upload form
- [ ] Update job editing form fields
- [ ] Add WET validation messaging
- [ ] Test accessibility

#### Phase B4: Alerts and Messaging (Week 2)

**Replace AlertBanner**:
```typescript
// WET Alert component
import { Alert } from '@arcnovus/wet-boew-react';

<Alert
  type="info" // success, warning, error, info
  heading="Phase 2.1 UI Modernization Complete"
  dismissible
  onDismiss={handleDismiss}
>
  The JDDB interface has been updated with a streamlined design...
</Alert>
```

**Tasks**:
- [ ] Replace AlertBanner with WET Alert
- [ ] Update toast notifications
- [ ] Migrate validation messages
- [ ] Test dismiss functionality

#### Phase B5: Bilingual Setup (Week 2)

**Language Toggle**:
```typescript
// WET language toggle
import { LanguageToggle } from '@arcnovus/wet-boew-react';

<LanguageToggle
  currentLanguage={language}
  onLanguageChange={handleLanguageChange}
  labels={{
    en: 'English',
    fr: 'Français'
  }}
/>
```

**Tasks**:
- [ ] Implement WET language toggle
- [ ] Create bilingual content files
- [ ] Translate form labels and messages
- [ ] Setup language persistence
- [ ] Test language switching

#### Phase B6: Accessibility Enhancements (Week 2-3)

**Apply WET Patterns**:
- [ ] Use WET skip links
- [ ] Add WET focus management
- [ ] Implement WET keyboard shortcuts
- [ ] Apply WET ARIA patterns to custom components
- [ ] Test with screen readers

**Effort**: 2-3 weeks
**Cost**: Medium (selective migration)
**Risk**: Low-Medium (styling conflicts possible)

---

### Option C: WET-Inspired Patterns 💡 Learning Approach

**Overview**: Use WET as a design reference and accessibility guide without direct integration.

**When to Choose**:
- Not a government project
- No legal accessibility requirements (but want to improve)
- Want to learn accessibility best practices
- Minimal disruption to current implementation

**Pros**:
- ✅ Fastest implementation (1-2 weeks)
- ✅ Learn accessibility patterns from WET
- ✅ No library dependencies
- ✅ Full control over design
- ✅ No migration required

**Cons**:
- ❌ No automated compliance
- ❌ Manual accessibility implementation
- ❌ More testing required
- ❌ No bilingual infrastructure
- ❌ Higher maintenance burden

**Technical Approach**:

#### Phase C1: Design Token Extraction (Week 1)

**Study WET Design System**:
```css
/* Extract WET design tokens */
:root {
  /* WET color palette */
  --color-primary: #26374a; /* GC primary blue */
  --color-accent: #284162;
  --color-text: #333;

  /* WET typography */
  --font-family: 'Noto Sans', sans-serif;
  --font-size-base: 16px;
  --line-height-base: 1.5;

  /* WET spacing */
  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;
}
```

**Tasks**:
- [ ] Extract WET design tokens (colors, typography, spacing)
- [ ] Create CSS variables matching WET
- [ ] Document alignment with GC Web Standards
- [ ] Apply tokens to existing components

#### Phase C2: Accessibility Pattern Library (Week 1-2)

**Study WET Accessibility**:
- [ ] Review WET keyboard navigation patterns
- [ ] Study WET ARIA label usage
- [ ] Analyze WET focus management
- [ ] Learn WET skip link implementation
- [ ] Document WET accessible form patterns

**Apply to JDDB**:
- [ ] Add skip links to header
- [ ] Improve keyboard navigation
- [ ] Add comprehensive ARIA labels
- [ ] Implement focus trapping in modals
- [ ] Test with screen readers

#### Phase C3: Bilingual Infrastructure (Week 1)

**i18n Setup** (without WET):
```bash
bun add i18next react-i18next
```

```typescript
// i18n configuration
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      fr: { translation: frTranslations }
    },
    lng: 'en',
    fallbackLng: 'en',
  });
```

**Tasks**:
- [ ] Setup i18next for bilingual support
- [ ] Create EN/FR translation files
- [ ] Implement language toggle
- [ ] Test language switching

**Effort**: 1-2 weeks
**Cost**: Low (minimal changes)
**Risk**: Low (no migration)

---

## Technical Considerations

### React/TypeScript Compatibility

**Recommended Package**: `@arcnovus/wet-boew-react`

**Why**:
- ✅ TypeScript-native (written in TypeScript + JSX)
- ✅ No jQuery dependency (unlike WET 4.x)
- ✅ React-first architecture
- ✅ WetProvider HOC pattern
- ✅ Actively maintained

**Installation**:
```bash
bun add @arcnovus/wet-boew-react
```

### Bun Compatibility

**Status**: ✅ Compatible

WET React packages are standard npm packages that work with Bun:
- Bun supports npm package installation
- No special configuration needed
- Standard React component usage

### Bundle Size Impact

| Approach | Bundle Size Increase | Mitigation |
|----------|---------------------|------------|
| Option A (Full) | +200-400KB | Code splitting, tree shaking, lazy loading |
| Option B (Hybrid) | +100-200KB | Import only needed components |
| Option C (Inspired) | +0KB | No library added |

**Optimization Strategies**:
- Lazy load WET components
- Code-split by route
- Tree-shake unused components
- Use WET CDN for static assets

### Styling Conflicts

**Risk**: WET CSS may conflict with current Tailwind CSS setup

**Mitigation**:
```typescript
// Option 1: Scope WET styles
<div className="wet-scope">
  <WetComponent />
</div>

// Option 2: CSS Modules
import wetStyles from './wet-components.module.css';

// Option 3: CSS-in-JS
import styled from '@emotion/styled';
const WetWrapper = styled.div`
  /* WET styles */
`;
```

### Performance Considerations

**Lighthouse Score Target**: 90+

**Metrics to Monitor**:
- First Contentful Paint (FCP): < 1.8s
- Largest Contentful Paint (LCP): < 2.5s
- Total Blocking Time (TBT): < 200ms
- Cumulative Layout Shift (CLS): < 0.1

---

## Decision Matrix

| Criteria | Option A (Full) | Option B (Hybrid) | Option C (Inspired) |
|----------|----------------|-------------------|---------------------|
| **GC Compliance** | ✅ Full | ⚠️ Partial | ❌ None |
| **Accessibility** | ✅ WCAG 2.0 AA | ✅ High | ⚠️ Manual |
| **Bilingual** | ✅ Built-in | ✅ Built-in | ⚠️ Custom |
| **Timeline** | 4-6 weeks | 2-3 weeks | 1-2 weeks |
| **Cost** | High | Medium | Low |
| **Risk** | Medium | Low-Medium | Low |
| **Flexibility** | Low | Medium | High |
| **Maintenance** | Low | Medium | High |

---

## Resource Requirements

### Option A (Full Integration)
- **Frontend Developer**: 1 FTE × 4-6 weeks
- **Accessibility Specialist**: 0.25 FTE × 4 weeks (testing)
- **Bilingual Translator**: Contract (translate all UI strings)
- **UX Designer**: 0.25 FTE × 2 weeks (review WET patterns)

### Option B (Hybrid)
- **Frontend Developer**: 1 FTE × 2-3 weeks
- **Accessibility Specialist**: 0.25 FTE × 2 weeks
- **Bilingual Translator**: Contract (translate form/alert strings)

### Option C (Inspired)
- **Frontend Developer**: 1 FTE × 1-2 weeks
- **Accessibility Specialist**: 0.25 FTE × 1 week (audit)

---

## Success Criteria

### Accessibility Metrics
- **Lighthouse Score**: 95+ (accessibility)
- **WCAG 2.0 AA**: 0 violations (automated testing)
- **Screen Reader**: 100% functional with JAWS/NVDA
- **Keyboard Navigation**: All interactive elements accessible

### Performance Metrics
- **Page Load**: < 2 seconds (no regression)
- **Bundle Size**: Increase < 400KB (after compression)
- **First Paint**: < 1.8 seconds
- **Time to Interactive**: < 3.5 seconds

### Bilingual Metrics (if applicable)
- **Coverage**: 100% of UI text in EN/FR
- **Language Switch**: < 500ms transition
- **Accuracy**: Professional translation quality
- **Date/Number Formatting**: Locale-appropriate

### User Metrics
- **Usability**: No decrease in task completion rate
- **Satisfaction**: Maintain or improve user satisfaction scores
- **Accessibility**: Positive feedback from users with disabilities

---

## Timeline & Milestones

### Option A Timeline (4-6 weeks)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1 | Research & Setup | WET installed, migration plan, dev branch |
| 2 | Core Migration | Header, navigation, alert banner migrated |
| 3 | Forms & Tables | All forms and data tables using WET |
| 4 | Bilingual | EN/FR translations complete, language toggle working |
| 5 | Testing | Accessibility audit, cross-browser testing |
| 6 | Polish & Deploy | Performance optimization, production deployment |

### Option B Timeline (2-3 weeks)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1 | Selective Integration | WET forms, alerts, utilities integrated |
| 2 | Bilingual | EN/FR for WET components, language toggle |
| 3 | Testing & Polish | Accessibility testing, style harmonization |

### Option C Timeline (1-2 weeks)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1 | Patterns & Tokens | WET-inspired accessibility patterns applied |
| 2 | Testing | Manual accessibility testing, documentation |

---

## Next Steps

### Immediate Actions

1. **Stakeholder Decision** (1 day)
   - [ ] Determine if this is a GC project
   - [ ] Clarify accessibility requirements
   - [ ] Confirm bilingual needs
   - [ ] Choose Option A, B, or C

2. **Team Preparation** (1 week)
   - [ ] Schedule WET training session
   - [ ] Review WET documentation
   - [ ] Setup development environment
   - [ ] Create Jira/GitHub tickets

3. **Pilot Implementation** (1 week)
   - [ ] Install WET package in dev branch
   - [ ] Migrate one component as proof-of-concept
   - [ ] Test accessibility and performance
   - [ ] Demo to stakeholders

### Phase 3.1 Integration (if approved)

**Week 1-2**: Core setup and planning
**Week 3-4**: Component migration
**Week 5-6**: Testing and refinement (Option A only)

---

## Questions for Stakeholders

1. **Project Classification**: Is JDDB a Government of Canada project subject to federal web standards?

2. **Compliance Requirements**: Are we legally required to meet WCAG 2.0 Level AA accessibility standards?

3. **Bilingual Mandate**: Is English/French bilingual support mandatory for this application?

4. **Timeline Constraints**: What is the deadline for accessibility compliance (if required)?

5. **Budget Availability**: What resources (developer time, translation, testing) are available for WET integration?

6. **Branding Flexibility**: Are we open to adopting Government of Canada branding, or must we maintain custom branding?

7. **Long-term Vision**: Is this application expected to integrate with other GC systems in the future?

---

## Appendix: WET Components Mapping

### JDDB to WET Component Map

| JDDB Component | WET Equivalent | Priority | Effort |
|----------------|----------------|----------|--------|
| AppHeader | WET Header + Navigation | HIGH | 2 days |
| AlertBanner | WET Alert | HIGH | 0.5 days |
| Form Inputs | WET FormGroup + Input | HIGH | 3 days |
| Select Dropdowns | WET Select | HIGH | 1 day |
| Buttons | WET Button | HIGH | 1 day |
| JobsTable | WET DataTable | MEDIUM | 3 days |
| Cards | WET Panel/Well | MEDIUM | 2 days |
| Tabs | WET Tabs Widget | MEDIUM | 1 day |
| Modal Dialogs | WET Overlay | LOW | 2 days |
| Toast Notifications | WET Alert (variant) | LOW | 1 day |

**Total Effort (Option A)**: ~16-20 days development

---

**Document Owner**: Development Team
**Review Cycle**: After stakeholder decision
**Status**: Awaiting decision on Option A/B/C
