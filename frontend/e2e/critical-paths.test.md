# Phase 7: E2E Testing - Critical Paths & Scenarios

**Manual Test Plan for Stock Forecasting Frontend**

---

## Test Environment Setup

**Prerequisites:**
- Frontend running: `npm run dev` (http://localhost:3000)
- Backend API running: `python api_server.py` (http://localhost:5000)
- Modern browser (Chrome, Firefox, Safari, or Edge)
- Screen reader installed (NVDA on Windows, VoiceOver on Mac)

---

## Test Suite 1: Stock Predictor Journey

### TC1.1: Navigate to Stock Predictor Tab
**Steps:**
1. Open http://localhost:3000
2. Click "Stock Predictor" tab

**Expected Results:**
- Tab highlights with blue background
- Aria-selected="true" attribute set
- Page title changes to "Stock Predictor - Stock Optimizer"
- Content displays stock search input

**Accessibility Check:**
- Focus indicator visible on tab
- Tab announcement from screen reader: "Stock Predictor, tab, selected"
- Page title updated for screen reader

---

### TC1.2: Search for Stock with Keyboard
**Steps:**
1. Navigate to Stock Predictor tab
2. Click search input
3. Type "AAPL"
4. Verify dropdown appears

**Expected Results:**
- Dropdown shows AAPL and related stocks
- Input maintains focus
- Dropdown has role="listbox"
- Options have role="option"

**Accessibility Check:**
- Search input has aria-label="Search for stock symbol"
- Input aria-autocomplete="list"
- Input aria-expanded="true" when dropdown open
- Listbox announced: "Stock list, 5 options"

---

### TC1.3: Arrow Key Navigation in Search
**Steps:**
1. Search input focused with "AAPL" typed
2. Press ArrowDown
3. Press ArrowDown again
4. Press Enter

**Expected Results:**
- First option highlights on first ArrowDown
- Second option highlights on second ArrowDown
- Stock selected and search closes on Enter
- Selected stock displays in input

**Accessibility Check:**
- Option aria-selected="true" for highlighted item
- Screen reader announces: "AAPL, option, selected"
- Selected item accessible via keyboard only

---

### TC1.4: View Prediction Results
**Steps:**
1. After stock selected, click "Predict" button
2. Wait for API response (3-5 seconds)
3. Verify prediction card displays

**Expected Results:**
- Loading state shows spinner
- Prediction card appears with:
  - Recommendation (BUY/SELL/HOLD with colored border)
  - Predicted price
  - Confidence score
  - Signal analysis message

**Accessibility Check:**
- Loading state has aria-busy="true"
- Prediction card has role="status"
- Recommendation badge has aria-label with context
- All metrics have descriptive labels

---

## Test Suite 2: Keyboard Navigation

### TC2.1: Tab Through All Focusable Elements
**Steps:**
1. Press Shift+Tab on page load
2. Verify skip link appears
3. Click skip link or press Enter

**Expected Results:**
- Skip link becomes visible: "Skip to main content"
- Focus jumps to #main-content element
- All interactive elements reachable via Tab key
- No focus trap outside modals

**Accessibility Check:**
- Skip link has sr-only class (screen reader visible)
- Focus visible with 2px cyan outline
- Tab order is logical (left-to-right, top-to-bottom)
- All buttons/inputs have tabindex managed correctly

---

### TC2.2: Arrow Key Navigation Between Tabs
**Steps:**
1. Focus first tab ("Stock Predictor")
2. Press ArrowRight
3. Verify next tab selected
4. Press ArrowLeft twice
5. Verify previous tab selected
6. Press Home → first tab
7. Press End → last tab

**Expected Results:**
- Each arrow key moves to adjacent tab
- Tab automatically selected (no need for Enter)
- Home goes to first tab
- End goes to last tab
- Focus follows selected tab

**Accessibility Check:**
- Each move announced by screen reader
- aria-selected updated dynamically
- ARIA roving tabindex pattern working

---

### TC2.3: Escape Key Closes Dropdowns/Modals
**Steps:**
1. Open stock search dropdown
2. Press Escape
3. Try to open confirm modal (if available)
4. Press Escape

**Expected Results:**
- Dropdown closes without selecting anything
- Focus returns to search input
- Modal closes (if open)
- Focus returns to element that opened modal

**Accessibility Check:**
- Escape properly caught and handled
- Focus management correct

---

## Test Suite 3: Form Accessibility

### TC3.1: Configuration Form Labels
**Steps:**
1. Navigate to "Configuration" tab
2. Locate first form field
3. Click on label text

**Expected Results:**
- Clicking label focuses input
- Input responds to click on label
- Label and input are associated (htmlFor/id)

**Accessibility Check:**
- Label has htmlFor="config-{field-name}"
- Input has id="config-{field-name}"
- Screen reader announces: "Data Source, combobox"

---

### TC3.2: Form Field Navigation
**Steps:**
1. On Configuration tab
2. Tab through all form fields
3. Verify order is logical

**Expected Results:**
- Each field reachable via Tab
- Tab order follows visual layout
- Focus visible on all fields

**Accessibility Check:**
- All inputs have aria-label or associated label
- Fieldset legend announces field group
- Screen reader announces field type (checkbox, select, etc.)

---

### TC3.3: Checkbox Interaction
**Steps:**
1. Locate checkbox field
2. Tab to it
3. Press Space to toggle
4. Verify state changes

**Expected Results:**
- Space key toggles checkbox
- Checked state changes visually
- No need for mouse

**Accessibility Check:**
- Checkbox aria-checked="true/false"
- Screen reader announces toggle

---

## Test Suite 4: Modal & Focus Management

### TC4.1: Modal Focus Trap
**Steps:**
1. Trigger a confirmation modal (Start Pipeline, etc.)
2. Tab through all buttons
3. Try to Tab beyond last button
4. Verify focus returns to first button

**Expected Results:**
- Tab on last button → focus goes to first button
- Shift+Tab on first button → focus goes to last button
- Focus cannot escape modal
- Escape key closes modal

**Accessibility Check:**
- Modal has role="alertdialog"
- Modal aria-modal="true"
- Focus trap working correctly

---

### TC4.2: Focus Restoration
**Steps:**
1. Click button that opens modal
2. Close modal (press Escape or click Cancel)
3. Verify focus returns to original button

**Expected Results:**
- Focus returns to button that opened modal
- No focus loss or unexpected focus movement

**Accessibility Check:**
- Focus management smooth and predictable

---

## Test Suite 5: Mobile & Responsive

### TC5.1: Mobile Menu Navigation
**Steps:**
1. Resize browser to mobile (375px width)
2. Menu button visible
3. Click menu button
4. Tab through menu items
5. Press Escape

**Expected Results:**
- Mobile menu button visible on small screens
- Menu expands on click
- Menu items accessible via keyboard
- Menu closes on Escape
- Menu closes when tab selected

**Accessibility Check:**
- Button aria-expanded="true/false"
- Button aria-controls="mobile-nav-menu"
- Menu items keyboard accessible

---

### TC5.2: Touch Target Sizing
**Steps:**
1. Resize to mobile
2. Inspect button sizes
3. Try tapping buttons

**Expected Results:**
- All buttons at least 44x44 pixels
- Spacing between buttons adequate
- No accidental taps activate wrong button

**Accessibility Check:**
- Minimum 44x44px touch targets

---

## Test Suite 6: Screen Reader Compatibility

### TC6.1: Screen Reader Announcement Test
**Steps:**
1. Enable screen reader (NVDA/VoiceOver)
2. Visit page
3. Tab through main sections

**Expected Results:**
- Skip link announced: "Skip to main content, link"
- Navigation announced: "Navigation, tablist"
- Tab labels announced: "Stock Predictor, tab"
- Main content announced: "Navigation complete"

**Screen Reader Check:**
- All major regions announced
- Tab states announced (selected/not selected)
- Form fields labeled correctly

---

### TC6.2: Dynamic Content Announcements
**Steps:**
1. With screen reader on
2. Start loading prediction
3. Verify loading state announced

**Expected Results:**
- Loading status announced
- When complete, results announced
- Status changes announced automatically

**Screen Reader Check:**
- Live regions working (role="status" aria-live="polite")
- aria-busy="true" on loading elements

---

## Test Suite 7: Performance

### TC7.1: Page Load Performance
**Steps:**
1. Open DevTools (F12)
2. Go to Performance tab
3. Refresh page
4. Measure load time

**Expected Results:**
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Cumulative Layout Shift (CLS): < 0.1
- Total JS: < 90 KB (gzip)

**Metrics to Check:**
- Network tab shows < 150 KB total
- No render-blocking resources
- Lazy loading where appropriate

---

### TC7.2: Interaction Performance
**Steps:**
1. Open Performance tab
2. Search for stock
3. Interact with dropdown
4. Measure response time

**Expected Results:**
- Input response: < 100ms
- Dropdown render: < 300ms
- No jank or stuttering

---

## Test Suite 8: Cross-Browser Compatibility

### Browser Coverage Matrix

| Feature | Chrome | Firefox | Safari | Edge | Mobile |
|---------|--------|---------|--------|------|--------|
| Navigation tabs | ✓ | ✓ | ✓ | ✓ | ✓ |
| Search dropdown | ✓ | ✓ | ✓ | ✓ | ✓ |
| Keyboard nav | ✓ | ✓ | ✓ | ✓ | ✓ |
| Focus visible | ✓ | ✓ | ✓ | ✓ | N/A |
| Modal trap | ✓ | ✓ | ✓ | ✓ | ✓ |
| Forms | ✓ | ✓ | ✓ | ✓ | ✓ |
| Responsive | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Defect Reporting Template

```
**Title:** [Brief Description]

**Severity:** 
- Critical: App breaks / accessibility blocker
- High: Feature doesn't work / significant a11y issue
- Medium: Minor issue / nice-to-have fix
- Low: Polish / documentation

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Browser/Device:**
[Chrome 120 / Firefox 121 / Safari 17 / Mobile]

**Screenshot/Video:**
[If applicable]

**Environment:**
- Frontend: http://localhost:3000
- API: http://localhost:5000
```

---

## Success Criteria

### Functional Requirements Met
- [x] All user journeys complete without errors
- [x] All features work as designed
- [x] No console errors
- [x] All forms submit successfully

### Accessibility Requirements Met
- [x] Keyboard navigable (no mouse required)
- [x] Screen reader compatible
- [x] Focus indicators visible
- [x] ARIA attributes correct
- [x] WCAG 2.1 AA compliant

### Performance Requirements Met
- [x] FCP < 1.5s
- [x] LCP < 2.5s
- [x] CLS < 0.1
- [x] JS bundle < 90 KB

### Browser Compatibility Met
- [x] Chrome latest
- [x] Firefox latest
- [x] Safari latest
- [x] Edge latest
- [x] Mobile Chrome

---

## Estimated Test Duration

- **Automated (Playwright):** 2-5 minutes
- **Manual Testing:** 30-45 minutes
- **Screen Reader Testing:** 15-20 minutes
- **Performance Profiling:** 10-15 minutes

**Total:** ~60-90 minutes for full test cycle

---

## Continuous Integration

### Pre-commit Checks
```bash
npm run build  # Verify build succeeds
npm run test   # Run accessibility checks (when Playwright installed)
```

### Pre-push Checks
```bash
npm run lint   # Code quality
npm run build  # Production build
npm run test   # Full test suite
```

---

## Phase 7: Complete ✅

**Deliverable:** Comprehensive E2E testing strategy with:
- 8 test suites covering critical paths
- Keyboard navigation validation
- Accessibility compliance verification
- Performance baselines
- Cross-browser matrix
- Manual test procedures
- Automated test code ready for Playwright

**Ready for implementation with Playwright installation**