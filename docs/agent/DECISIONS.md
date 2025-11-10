# Architecture Decision Records

## ADR-001: Table Layout Strategy
**Date**: 2025-11-10  
**Status**: Accepted

### Context
Need to make data tables responsive across screen sizes (1366px-2560px) and browser zoom levels (90%-125%) without backend changes.

### Decision
Implement:
1. Sticky header + first column using CSS `position: sticky`
2. Priority-based column visibility (.col--high, .col--med, .col--low)
3. Optional "row card" mode for containers ≤820px using CSS container queries
4. Zoom-friendly typography with rem and clamp()
5. localStorage persistence for user preferences

### Alternatives Considered
- **Full virtualized table** (react-window/tanstack-virtual): Deferred due to dependency overhead
- **Server-side responsive data shapes**: Rejected to avoid backend changes
- **CSS Grid reflow**: Not suitable for complex tables with many columns

### Rationale
- Minimal dependencies (vanilla JS + CSS)
- Fast rollout without architectural changes
- Graceful degradation
- No impact on existing functionality

### Consequences
- CSS bundle increases by ~8-10KB
- JS bundle increases by ~3-4KB
- One-time template update required for all table pages
- Users get progressive enhancement based on viewport/zoom

---

## ADR-002: Container Queries vs Media Queries
**Date**: 2025-11-10  
**Status**: Accepted

### Context
Need to trigger column visibility and density changes based on table container size, not just viewport.

### Decision
Use CSS Container Queries as primary mechanism with @media fallback:
```css
.tbl-wrap { container-type: inline-size; }

@container (max-width: 1200px) {
  .tbl .col--low { display: none; }
}

/* Fallback for older browsers */
@media (max-width: 1200px) {
  .tbl-wrap .tbl .col--low { display: none; }
}
```

### Alternatives
- Media queries only: Doesn't account for container constraints
- JavaScript-based size detection: More overhead and re-render issues

### Rationale
- Container queries provide true component-level responsiveness
- Modern browser support (Chrome 105+, Firefox 110+, Safari 16+)
- Graceful degradation to media queries for older browsers

---

## ADR-003: Column Priority Classification
**Date**: 2025-11-10  
**Status**: Accepted

### Decision
Three-tier priority system:

**High Priority (.col--high)**: Always visible on ≥1080p
- Exercise name
- Routine
- Sets, Reps (Min/Max), Weight
- Date (for log/summary pages)
- Action buttons

**Medium Priority (.col--med)**: Visible on ≥1366px, hidden on smaller or ≥110% zoom
- Primary Muscle
- RIR, RPE
- Notes/Comments

**Low Priority (.col--low)**: First to collapse (≥1440px only)
- Secondary/Tertiary Muscles
- Stabilizers, Synergists
- Grips
- Utility/other metadata

### Rationale
- Based on user workflow analysis
- High priority = data needed to execute workout
- Medium = context that aids planning
- Low = supplementary information available on demand

---

## ADR-004: Card Mode Threshold
**Date**: 2025-11-10  
**Status**: Accepted

### Decision
Activate "row card" stacked mode at:
- Container width ≤ 820px
- OR explicit user preference toggle

### Rationale
- 820px chosen as breakpoint where even high-priority columns become cramped
- User toggle allows power users to stay in table mode if preferred
- Cards provide better mobile/tablet experience

---

## ADR-005: Persistence Strategy
**Date**: 2025-11-10  
**Status**: Accepted

### Decision
Use localStorage with page-specific keys:
```javascript
{
  "workout_plan": { "hidden": ["col--low-1", "col--med-2"], "density": "compact" },
  "workout_log": { "hidden": [], "density": "comfortable" }
}
```

### Alternatives
- Server-side user preferences: Requires backend changes (out of scope)
- sessionStorage: Doesn't persist across browser sessions
- Cookies: Size limitations and privacy concerns

### Rationale
- No backend changes required
- Per-page preferences give users fine-grained control
- Easy to clear/reset
- Widely supported

