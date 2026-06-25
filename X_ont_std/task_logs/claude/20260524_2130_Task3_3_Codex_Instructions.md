# Task 3-3 Phase 2: Codex Frontend E2E Tests - Instructions

**Date**: 2026-05-24 21:30  
**For**: Codex Team (Frontend/UI)  
**Task**: Browser-based E2E tests for SPARQL query console  
**Timeline**: 2026-06-10 ~ 06-12 (2 days)  
**Deliverable**: `task_logs/claude/YYYYMMDD_HHMM_Codex_Week3_E2E_Complete.md`

---

## 📋 Overview

Backend (Claude) has completed PostgreSQL E2E tests - all 8 patterns working. Now validate that:
1. Frontend correctly sends SPARQL queries to backend
2. UI displays results correctly
3. Graph visualization renders properly
4. Performance metrics are displayed
5. No console errors or crashes

---

## 🎯 Success Criteria

- ✅ All 8 query patterns execute end-to-end
- ✅ Results displayed correctly in Table tab
- ✅ Graph visualization renders in Graph tab
- ✅ Performance metrics displayed
- ✅ No console errors
- ✅ Responsive design works

---

## 🚀 Getting Started

### Step 1: Start Backend API (If Not Running)

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
conda activate claud_be
uvicorn main:app --reload --port 8001
```

Verify backend is running:
```bash
curl http://localhost:8001/health
```

### Step 2: Start Frontend Dev Server

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
conda activate claud_fe
npm run dev
```

Frontend should be available at http://localhost:3001

### Step 3: Verify Manual Testing (Smoke Test)

1. Open http://localhost:3001 in browser
2. Navigate to `/sparql-console`
3. Test Pattern #18 manually:
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?name WHERE {
       ex:ship1 ex:name ?name
   }
   ```
4. Click "Execute"
5. Verify result appears in Table tab
6. Click "Graph" tab - should show entity visualization

---

## ✅ Test Suite: SPARQL Console E2E

### File Location
`ont_platform/v3/src/frontend/e2e/sparql.spec.ts` (Cypress)

### Test Structure (8 tests, one per pattern)

```typescript
// Example test template:
describe('SPARQL Console E2E', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3001/sparql-console');
  });

  it('Pattern #18: Simple ID lookup', () => {
    // 1. Type SPARQL query in console
    cy.get('[data-testid="query-input"]').type(
      `PREFIX ex: <http://test.org/>
       SELECT ?name WHERE { ex:ship1 ex:name ?name }`
    );
    
    // 2. Click Execute button
    cy.get('[data-testid="execute-btn"]').click();
    
    // 3. Verify results in Table tab
    cy.get('[data-testid="table-tab"]').should('be.visible');
    cy.get('[data-testid="result-table"] tbody').should('have.length.greaterThan', 0);
    
    // 4. Verify performance metric
    cy.get('[data-testid="execution-time"]').should('contain', 'ms');
  });

  // Similar tests for patterns #19-26...
});
```

### Tests to Create

1. **Pattern #18: Simple ID Lookup**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?name WHERE { ex:ship1 ex:name ?name }
   ```
   - Verify: Table shows entity name
   - Tab check: Graph tab renders
   - Performance: Displayed

2. **Pattern #19: Type Filtering**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?ship WHERE { ?ship a ex:Ship }
   ```
   - Verify: Multiple results in table
   - Count: ≥50 ships

3. **Pattern #20: Numeric Comparison**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?part ?cost WHERE {
       ?part ex:cost ?cost
       FILTER (?cost > 500)
   }
   ```
   - Verify: Only parts with cost > 500 shown
   - Check: Numeric filtering applied

4. **Pattern #21: Equality Filter**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?ship WHERE { ?ship ex:status "Active" }
   ```
   - Verify: Only "Active" ships shown
   - Count: Approximately 50 results

5. **Pattern #24: 1-Hop + Filter**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?part ?cost WHERE {
       ex:supplier1 ex:supplies ?part .
       ?part ex:cost ?cost
       FILTER (?cost > 500)
   }
   ```
   - Verify: Joined results from supplier
   - Graph: Shows relationship path

6. **Pattern #25: 2-Hop Relationship**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?part WHERE {
       ex:ship1 ex:has_block ?block .
       ?block ex:has_part ?part
   }
   ```
   - Verify: Multi-hop traversal works
   - Graph: Shows 2-hop path

7. **Pattern #26: 2-Hop + Filter**
   ```sparql
   PREFIX ex: <http://test.org/>
   SELECT ?part ?rating WHERE {
       ex:project1 ex:involves_supplier ?supplier .
       ?supplier ex:supplies ?part .
       ?part ex:quality_rating ?rating
       FILTER (?rating >= 5)
   }
   ```
   - Verify: Complex multi-hop with filter
   - Check: Only high-quality parts shown

8. **Error Handling: Invalid Query**
   ```sparql
   INVALID SPARQL SYNTAX HERE
   ```
   - Verify: Error message displayed
   - Check: No crash, graceful error handling

---

## 📋 Test Checklist per Pattern

For EACH pattern, verify:

- [ ] Query executes without error
- [ ] Results appear in Table tab (if expected)
- [ ] Graph tab renders visualization
- [ ] Performance time is displayed
- [ ] Result count is correct
- [ ] Browser console has no errors
- [ ] UI is responsive (check width)
- [ ] Keyboard shortcuts work (if implemented)

---

## 🔍 UI Components to Test

### SPARQL Console Input
- [ ] Text area accepts multi-line queries
- [ ] Syntax highlighting (if implemented)
- [ ] Execute button is clickable

### QueryResult Component
- [ ] Table tab: Shows results in table format
- [ ] JSON tab: Shows raw JSON response
- [ ] Graph tab: Renders entity graph visualization
- [ ] Debug tab: Shows SQL translation (if available)
- [ ] Performance chart: Displays execution time

### Graph Visualization (EntityGraph)
- [ ] Nodes render for entities
- [ ] Edges show relationships
- [ ] Node selection shows details
- [ ] Zoom/pan works
- [ ] Legend displays

### Performance Metrics
- [ ] Execution time displayed in ms
- [ ] Chart shows performance history (if multi-query)

---

## 🐛 Common Issues & Fixes

### Issue: Backend not responding
**Fix**: Verify backend is running on port 8001
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy"}
```

### Issue: CORS errors in console
**Fix**: Backend CORS should be configured. Check FastAPI main.py has:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Graph not rendering
**Fix**: Check browser console for errors. Verify EntityGraph component receives results in correct format:
```json
{
  "results": [
    {"name": "Ship 1", "type": "http://test.org/Ship"},
    ...
  ]
}
```

### Issue: Test timeout
**Fix**: Increase Cypress timeout in cypress.config.ts:
```typescript
requestTimeout: 10000,
responseTimeout: 10000,
```

---

## 📝 Deliverable Format

Create completion report: `task_logs/claude/YYYYMMDD_HHMM_Codex_Week3_E2E_Complete.md`

```markdown
# Codex Week 3: Frontend E2E Tests - COMPLETE

Date: 2026-06-XX HH:MM
Status: ✅ COMPLETE

## Test Results
- ✅ 8/8 pattern tests passing
- ✅ Graph visualization working
- ✅ Performance metrics displayed
- ✅ No console errors

## Evidence
- Cypress test execution log
- Screenshots/videos (if applicable)
- Performance benchmark results

## Issues Encountered (if any)
- [List any blockers and how they were resolved]

## Ready For
- Phase 4: Antigravity load tests
- Phase 5: Integration report
```

---

## 🔗 Related Documents

- [Claude E2E Results](./20260524_2130_Task3_3_PostgreSQL_Complete.md) ← PostgreSQL tests reference
- [Task 3-2: API Endpoint](./PHASE2_5_TASK3_2_Claude_FastAPIIntegration_20260524_1930.md) ← Endpoint specification
- [Planning Document](../../majestic-sparking-crab.md) ← Overall Task 3-3 plan
- [SPARQL Console Component](../../ont_platform/v3/src/frontend/src/components/SPARQLWorkbench.tsx) ← Component reference

---

## ✉️ Questions?

Refer to:
1. Component source code in `src/frontend/src/components/`
2. API endpoint specification in Task 3-2 report
3. PHASE2_5_Project_Status_20260524.md for timeline coordination

**Timeline**: Start 2026-06-10, Complete by 2026-06-12  
**Next**: Antigravity begins load testing (2026-06-12 afternoon)
