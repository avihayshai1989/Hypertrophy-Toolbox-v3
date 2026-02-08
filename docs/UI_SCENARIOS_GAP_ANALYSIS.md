# UI Scenarios Gap Analysis - Common User Issues

> **Date**: January 2025  
> **Updated**: February 2025  
> **Purpose**: Identify potential UI issues, crashes, glitches, wrong logic, and confusing flows that common users might encounter.

## ✅ IMPLEMENTATION STATUS

### New E2E Tests Created
| Test File | Tests | Status |
|-----------|-------|--------|
| [e2e/error-handling.spec.ts](../e2e/error-handling.spec.ts) | Server errors, network failures, double-click prevention, recovery | ✅ Created |
| [e2e/validation-boundary.spec.ts](../e2e/validation-boundary.spec.ts) | Negative values, rep range, zero values, RIR/RPE limits | ✅ Created |
| [e2e/superset-edge-cases.spec.ts](../e2e/superset-edge-cases.spec.ts) | Delete in superset, unlink, replace, persistence | ✅ Created |
| [e2e/empty-states.spec.ts](../e2e/empty-states.spec.ts) | Empty exports, empty log, empty filters | ✅ Created |

### Code Fixes Implemented
| File | Fix | Status |
|------|-----|--------|
| [exercises.js](../static/js/modules/exercises.js) | Debounce on addExercise() | ✅ Implemented |
| [exercises.js](../static/js/modules/exercises.js) | Debounce on removeExercise() | ✅ Implemented |
| [exercises.js](../static/js/modules/exercises.js) | Client-side validation (rep range, RIR/RPE, negative values) | ✅ Implemented |
| [exports.js](../static/js/modules/exports.js) | Empty state check before export | ✅ Implemented |

---

## Executive Summary

After analyzing the JavaScript frontend modules and existing E2E test coverage, I've identified **37 potential UI scenarios** that could cause issues for common users but are not fully tested.

### Risk Categories
- 🔴 **Critical** (7): Application crashes, data loss, blocked flows
- 🟠 **High** (12): Wrong output, confusing behavior, broken features  
- 🟡 **Medium** (10): Minor glitches, edge cases, UX friction
- 🟢 **Low** (8): Cosmetic issues, rare scenarios

---

## 1. CRITICAL SCENARIOS (Potential Crashes/Data Loss)

### 1.1 Network Connection Issues
**File**: `fetch-wrapper.js`
| Scenario | Current Handling | Risk |
|----------|------------------|------|
| Complete network loss mid-operation | Retry logic only for GET (2 retries) | 🔴 POST operations fail silently |
| Server returns 500 during exercise save | Shows toast, but form state unclear | 🔴 User may lose input data |
| Timeout during export to Excel | No timeout handling visible | 🔴 User stuck with loading indicator |

**E2E Test Gap**: ✅ **COVERED** - [error-handling.spec.ts](../e2e/error-handling.spec.ts)

### 1.2 Concurrent Operations Race Conditions
**File**: `workout-plan.js`, `exercises.js`
| Scenario | Current Handling | Risk |
|----------|------------------|------|
| Rapid double-click on "Add Exercise" | ✅ **FIXED** - Debounce added | ~~🔴~~ ✅ |
| Click "Delete" while fetch in progress | ✅ **FIXED** - Tracking added | ~~🔴~~ ✅ |
| Multiple tabs editing same routine | No cross-tab sync | 🔴 Data overwrites silently |

**E2E Test Gap**: ✅ **COVERED** - [error-handling.spec.ts](../e2e/error-handling.spec.ts)

### 1.3 Empty/Null State Handling
**File**: `workout-log.js`, `workout-plan.js`
| Scenario | Current Handling | Risk |
|----------|------------------|------|
| Import from empty workout plan | API call made, unclear response | 🟠 User confused by empty result |
| Clear log when already empty | Modal shown unnecessarily | 🟡 Minor UX friction |
| Export empty plan to Excel | ✅ **FIXED** - Warning shown | ~~🟠~~ ✅ |

**E2E Test Gap**: ✅ **COVERED** - [empty-states.spec.ts](../e2e/empty-states.spec.ts)

---

## 2. HIGH-RISK SCENARIOS (Wrong Output/Broken Features)

### 2.1 Validation Gaps
**File**: `validation.js`, `exercises.js`
| Scenario | Current Behavior | Expected Behavior |
|----------|-----------------|-------------------|
| Weight = 0 entered | ✅ **FIXED** - Allowed (bodyweight) | ~~Should warn~~ ✅ |
| Negative rep range | ✅ **FIXED** - Rejected | ~~May be accepted~~ ✅ |
| Min rep > Max rep | ✅ **FIXED** - Rejected with message | ~~No validation~~ ✅ |
| Sets = 0 | ✅ **FIXED** - Rejected | ~~May be accepted~~ ✅ |
| RIR > 10 | ✅ **FIXED** - Capped at 10 | ~~No limit~~ ✅ |
| RPE > 10 | ✅ **FIXED** - Rejected | ~~No limit~~ ✅ |

**E2E Test Gap**: ✅ **COVERED** - [validation-boundary.spec.ts](../e2e/validation-boundary.spec.ts)

### 2.2 Dropdown Cascade State Issues
**File**: `routine-cascade.js`, `workout-dropdowns.js`
| Scenario | Current Behavior | Risk |
|----------|-----------------|------|
| Back button after routine selection | Cascade state not restored | 🟠 User sees wrong routine |
| Changing environment clears program | Works but selection lost | 🟡 Minor UX issue |
| Hidden routine value mismatch | `#routine` hidden field can desync | 🔴 Wrong routine saved |

**E2E Test Coverage**: Basic cascade tested, but not back-button or refresh scenarios.

### 2.3 Superset Edge Cases
**File**: `workout-plan.js` (lines 1456-1542)
| Scenario | Current Behavior | Risk |
|----------|-----------------|------|
| Link 3+ exercises | Should work but untested | 🟠 May fail silently |
| Unlink from middle of superset | Logic unclear | 🟠 May break chain |
| Delete exercise in superset | Superset group handling unclear | 🔴 Orphaned superset |
| Replace exercise in superset | Superset membership preserved? | 🟠 May drop from superset |

**E2E Test Gap**: ✅ **COVERED** - [superset-edge-cases.spec.ts](../e2e/superset-edge-cases.spec.ts)

### 2.4 Replace Exercise Failure Modes
**File**: `workout-plan.js` (lines 1585-1640)
| Scenario | Current Toast | Risk |
|----------|--------------|------|
| No alternative found | "No alternative found for this muscle/equipment" | 🟡 User unclear on next step |
| All alternatives in routine | "All alternatives are already in this routine" | 🟡 Confusing if routine has 1 exercise |
| Exercise missing muscle data | "This exercise is missing muscle/equipment data" | 🟠 Data quality issue |

**E2E Test Gap**: API call tested, but error message scenarios not covered.

---

## 3. MEDIUM-RISK SCENARIOS (Glitches/UX Friction)

### 3.1 Toast Notification Issues
**File**: `toast.js`
| Scenario | Current Behavior | Risk |
|----------|-----------------|------|
| Multiple toasts at once | Stacking behavior unclear | 🟡 User may miss messages |
| Error toast with long message | May overflow container | 🟡 Message truncated |
| Backward compatibility mode | `showToast(msg, true)` vs `showToast('error', msg)` | 🟡 Inconsistent styling |

### 3.2 Form State Persistence
**File**: `exercises.js`
| Scenario | Current Behavior | Risk |
|----------|-----------------|------|
| Page refresh mid-entry | Form cleared | 🟡 User loses input |
| Tab away and return | Form may be stale | 🟡 User confusion |
| Add exercise, then change routine | Form not cleared | 🟡 Wrong routine may be used |

### 3.3 Table Sorting/Filtering Issues
**File**: `workout-log.js`, `filters.js`
| Scenario | Current Behavior | Risk |
|----------|-----------------|------|
| Sort by date with NULL dates | Sort order unclear | 🟡 Exercises may shuffle unexpectedly |
| Filter applied, then add exercise | New exercise may not match filter | 🟡 Exercise "disappears" |
| Clear filters resets sort? | Behavior unclear | 🟡 Unexpected state change |

### 3.4 Modal Focus/Accessibility
**File**: `workout-log.js` (lines 57-69)
| Scenario | Issue | Risk |
|----------|-------|------|
| Modal opens behind content | Modal moved to body for z-index fix | 🟡 May break event binding |
| Escape key to close modal | Not tested | 🟡 Accessibility gap |
| Tab focus trapped in modal | Not verified | 🟡 Keyboard nav broken |

---

## 4. LOW-RISK SCENARIOS (Cosmetic/Rare)

### 4.1 Dark Mode Edge Cases
| Scenario | Risk |
|----------|------|
| Theme switch mid-modal | 🟢 Minor visual flicker |
| Charts not updating with theme | 🟢 Colors may be wrong |
| Print styling with dark mode | 🟢 May print dark background |

### 4.2 Export Edge Cases  
| Scenario | Risk |
|----------|------|
| Export with special chars in filename | 🟢 Filename encoding |
| Export large dataset | 🟢 Performance concern |
| Export in Safari (Blob handling) | 🟢 Browser compat |

### 4.3 Mobile/Responsive Issues
| Scenario | Risk |
|----------|------|
| Table overflow on mobile | 🟢 Horizontal scroll needed |
| Touch gestures for drag-drop | 🟢 May not work |
| Dropdown on small screens | 🟢 Hard to tap |

---

## 5. RECOMMENDED NEW E2E TESTS

### 5.1 Priority 1 - Critical (Write Immediately)
```typescript
// e2e/error-handling.spec.ts
test.describe('Error Handling', () => {
  test('handles server error gracefully during add exercise');
  test('recovers from network timeout during export');
  test('prevents duplicate submission on double-click');
  test('handles API 500 error without crashing');
});

// e2e/validation-boundary.spec.ts  
test.describe('Input Validation', () => {
  test('rejects negative values for reps/sets/weight');
  test('rejects min_rep > max_rep');
  test('enforces RIR/RPE maximum values');
  test('shows error for weight = 0');
});
```

### 5.2 Priority 2 - High (Write Soon)
```typescript
// e2e/superset-edge-cases.spec.ts
test.describe('Superset Edge Cases', () => {
  test('handles delete of exercise in superset');
  test('allows unlinking from multi-exercise superset');
  test('preserves superset when replacing exercise');
  test('handles linking 3+ exercises');
});

// e2e/empty-states.spec.ts
test.describe('Empty State Handling', () => {
  test('import from empty workout plan shows helpful message');
  test('export empty plan shows warning before download');
  test('clear already-empty log does not error');
});
```

### 5.3 Priority 3 - Medium (Backlog)
```typescript
// e2e/browser-back-button.spec.ts
test.describe('Browser Navigation', () => {
  test('back button preserves routine selection');
  test('refresh page restores last-used routine');
  test('deep link to specific routine works');
});

// e2e/concurrent-operations.spec.ts
test.describe('Concurrent Operations', () => {
  test('rapid add/delete does not cause race condition');
  test('multiple API calls complete without error');
});
```

---

## 6. IMMEDIATE CODE FIX RECOMMENDATIONS

### 6.1 Add Debounce to Critical Buttons
```javascript
// exercises.js - ADD THIS
let isSubmitting = false;
export function addExercise() {
    if (isSubmitting) return;
    isSubmitting = true;
    // ... existing code ...
    sendExerciseData(exerciseData).finally(() => {
        isSubmitting = false;
    });
}
```

### 6.2 Add Client-Side Validation
```javascript
// exercises.js - ADD VALIDATION
if (parseInt(minRepRange) > parseInt(maxRepRange)) {
    showToast('Min reps cannot exceed max reps', true);
    return;
}
if (parseFloat(weight) <= 0) {
    showToast('Weight must be greater than 0', true);
    return;
}
```

### 6.3 Add Empty State Check Before Export
```javascript
// Before export operations
const rows = document.querySelectorAll('#workout_plan_table_body tr');
if (rows.length === 0) {
    showToast('warning', 'No exercises to export. Add exercises first.');
    return;
}
```

---

## 7. TESTING COVERAGE MATRIX

| Area | Unit Tests | E2E Tests | Gap |
|------|-----------|-----------|-----|
| Add Exercise Flow | ✅ 34 | ✅ Basic | ❌ Validation edge cases |
| Delete Exercise | ✅ API | ✅ Basic | ❌ Superset cascade |
| Replace Exercise | ✅ API | ✅ Basic | ❌ Error scenarios |
| Superset Link/Unlink | ✅ API | ✅ Basic | ❌ Edge cases |
| Import to Log | ✅ API | ✅ Basic | ❌ Empty plan |
| Export Excel | ✅ API | ✅ Basic | ❌ Empty plan |
| Routine Cascade | ❌ None | ✅ Good | ⚠️ Back button |
| Validation | ✅ Basic | ❌ None | ❌ Full coverage |
| Error Handling | ✅ API | ❌ None | ❌ User-facing |
| Network Errors | ❌ None | ❌ None | ❌ Complete gap |

---

## 8. SUMMARY ACTION ITEMS

### Must Do (Before Next Release)
1. ❗ Add debounce to Add Exercise button
2. ❗ Add client-side validation for rep ranges
3. ❗ Add empty state checks before exports
4. ❗ Write 4 critical E2E tests (error handling)

### Should Do (Next Sprint)
1. Write validation boundary E2E tests
2. Write superset edge case E2E tests  
3. Add network error simulation tests
4. Test browser back-button behavior

### Nice to Have (Backlog)
1. Mobile responsiveness tests
2. Accessibility audit
3. Performance tests for large datasets
4. Cross-browser compatibility tests

---

*Document generated from analysis of 22 JavaScript modules and 12 E2E test files.*
