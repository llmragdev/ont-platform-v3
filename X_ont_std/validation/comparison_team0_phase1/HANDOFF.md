# Team0 Comparison Phase 1 - Handoff Instructions

**Document**: HANDOFF.md  
**Version**: 1.1  
**Date**: 2026-06-07 (Reviewed by Antigravity)  
**For**: Antigravity (Performance Optimization Team)

---

## 📌 Project Overview

### Objective
Build a **Document Validation & Analysis Program** using ontology-based techniques to:
1. Load and process 8 PDF documents (ontology, NLP, defense topics)
2. Extract metadata and build ontology graphs
3. Vectorize content and create semantic relationships
4. Compare performance with Team0 RAG system
5. Generate performance comparison report

### Key Point
- **Team0 is a reference/comparison baseline**, not the main focus
- **Main focus**: Validate our ontology-based approach on target documents
- **Deliverable**: Comparison analysis report (our solution vs Team0)

---

## 📂 Project Structure

```
E:\ontology_edu\X_ont_std\validation\comparison_team0_phase1\
├── README.md                    ← Project overview (read first)
├── PLAN.md                      ← Detailed implementation plan
├── CHECKLIST.md                 ← Daily tasks & completion tracking
├── config.py                    ← Configuration (ready to use)
├── requirements.txt             ← Python dependencies
├── loaders/                     ← PDF loading module
├── extractors/                  ← Metadata & chunk extraction  
├── builders/                    ← Vector & ontology building
├── evaluators/                  ← Performance analysis
├── clients/                     ← Team0 API client
└── results/                     ← Output (vectors, ontology, reports)
```

---

## 🎯 What's Already Done

✅ **Planning & Documentation**
- README.md: Project architecture & overview
- PLAN.md: Detailed implementation plan (Phase 1-5, Day-by-day)
- CHECKLIST.md: Task tracking with success criteria
- config.py: All configuration constants defined

✅ **Project Structure**
- Folder structure created
- All subfolders ready
- Python package structure initialized (__init__.py files)
- requirements.txt prepared

✅ **Reference Documents**
- Team0 source code available at: `E:\ai_lab_SIT\team0_rag_source\`
- Target documents available at: `E:\ai_lab_SIT\target_doc\` (8 PDFs)

---

## 🚀 What You Need to Do

### Quick Start (First Steps)

```bash
# 1. Navigate to project
cd E:\ontology_edu\X_ont_std\validation\comparison_team0_phase1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Read the documentation
# - Start with README.md (5-10 min)
# - Review PLAN.md (15-20 min)
# - Reference CHECKLIST.md while working
```

---

## 📋 Implementation Timeline

### **Phase 1: Setup** (Day 1 - 2 hours)
**Goal**: Environment and test queries ready

- [ ] Read README.md and PLAN.md
- [ ] Verify environment setup
- [ ] Create test_queries.json with 30 test questions
- [ ] Confirm all dependencies installed

**Checklist**: See CHECKLIST.md "Day 1" section

**Success Criteria**: 
- ✓ All dependencies installed
- ✓ 30 test queries defined (12 ontology, 12 NLP, 6 defense)
- ✓ No import errors when loading config.py

---

### **Phase 2: Core Modules Development** (Day 2-3 - 8 hours)

#### Day 2: PDF & Text Processing (4 hours)
- [ ] Implement `loaders/pdf_loader.py`
  - Load 8 PDFs from target_doc/
  - Extract text and metadata automatically
  - Output: documents_metadata.json

- [ ] Implement `extractors/metadata_extractor.py`
  - Extract: title, year, keywords, authors, category
  - Output: metadata_analysis.json
  
- [ ] Implement `extractors/chunk_extractor.py`
  - Split text into semantic chunks (512 tokens)
  - Assign metadata to each chunk
  - Output: chunks.json (~350 chunks expected)

#### Day 3: Vectorization & Ontology (4 hours)
- [ ] Implement `builders/vector_builder.py`
  - Call Gemini Embedding API (3072 dimensions)
  - Vectorize all chunks
  - Output: vectors.json

- [ ] Implement `builders/ontology_builder.py`
  - Build concept graph from metadata
  - Find document relationships
  - Build concept relationships
  - Output: ontology.json

**Checklist**: See CHECKLIST.md "Day 2" and "Day 3" sections

**Success Criteria**:
- ✓ 8 PDFs loaded successfully
- ✓ 300+ chunks created
- ✓ All chunks vectorized (3072D)
- ✓ 20+ document relationships found

---

### **Phase 3: Team0 Testing & Evaluation** (Day 4 - 6-8 hours)

#### Step 1: Setup Team0 Client (1 hour)
- [ ] Implement `clients/team0_client.py`
- [ ] Connect to Team0 API (port 8002)
- [ ] Test connection with 1 sample query

#### Step 2: Build Evaluators (2 hours)
- [ ] Implement `evaluators/accuracy_evaluator.py`
- [ ] Implement `evaluators/performance_evaluator.py`
- [ ] Implement `evaluators/metadata_analyzer.py`
- [ ] Implement `evaluators/ontology_analyzer.py`

#### Step 3: Run Tests (3-5 hours)
- [ ] Create `test_suite.py` (main program)
- [ ] Run 30 test queries against Team0
- [ ] Measure accuracy, response time, success rate
- [ ] Save results: test_results.json

#### Step 4: Evaluate Results (2 hours)
- [ ] Run accuracy evaluation
- [ ] Run performance analysis
- [ ] Run metadata potential analysis
- [ ] Run ontology potential analysis

**Checklist**: See CHECKLIST.md "Day 4" section

**Success Criteria**:
- ✓ All 30 queries executed successfully
- ✓ Team0 baseline accuracy measured (~58.54%)
- ✓ All evaluation reports generated

---

### **Phase 4: Final Report** (Day 5 - 4 hours)

- [ ] Analyze all results
- [ ] Create `results/validation_report.md`
  - Executive summary
  - Baseline performance (Team0)
  - Category analysis
  - Metadata analysis
  - Ontology analysis
  - Comparison & recommendations

- [ ] Generate `results/detailed_results.json`
  - All metrics and data

**Checklist**: See CHECKLIST.md "Day 5" section

**Success Criteria**:
- ✓ validation_report.md complete (public-shareable)
- ✓ All analysis sections included
- ✓ Clear comparison: our solution vs Team0

---

## 📚 Documentation Guide

### Read in This Order:
1. **HANDOFF.md** (this file) - 5 min
2. **README.md** - 10 min (architecture & overview)
3. **PLAN.md** - 20 min (detailed implementation guide)
4. **CHECKLIST.md** - Reference while working (daily tasks)

### Key Files:
- `config.py` - All constants and paths already configured
- `PLAN.md` - Code snippets and class structures provided
- `CHECKLIST.md` - Success criteria for each task

---

## 🔧 Prerequisites & Environment

### Required
- Python 3.8+
- Team0 server running on port 8002
- LLM Gateway running on port 8011 (Gemini Embedding API)
- Internet connection (for Gemini API calls)

### Setup Verification
```bash
# 1. Check Python
python --version

# 2. Check Team0 connection
curl http://localhost:8002/api/v1/health

# 3. Check LLM Gateway
curl http://localhost:8011/api/v1/embed
```

---

## 📝 Important Notes

### Data Sources
- **Target Documents**: 8 PDFs at `E:\ai_lab_SIT\target_doc\`
  - 6 NLP papers
  - 2 Defense papers
  - All ontology-related topics
  
- **Team0 Reference**: Source code at `E:\ai_lab_SIT\team0_rag_source\`
  - Use only for comparison/reference
  - DO NOT modify

### Configuration & Critical Adjustments
- **Path Adjustments in `config.py`**: The current `config.py` defines `TARGET_DOC_DIR` and `TEAM0_SOURCE_DIR` relative to the local parent folder (`E:\ontology_edu\X_ont_std\validation\`), but they are actually located at `E:\ai_lab_SIT\target_doc` and `E:\ai_lab_SIT\team0_rag_source`. These paths must be configured as absolute paths pointing to `E:\ai_lab_SIT\`.
- **Team0 Endpoint Correction**: The search endpoint in `config.py` must be updated from `/api/v1/search` to `/api/v1/rag/search` to match Team0's FastAPI routing prefix and endpoint definition.
- **Required HTTP Headers**: Team0 search requests require the `X-Tenant-ID` header (e.g. `company_abc`) and optionally `X-Org-ID` (e.g. `0200`). Without these, requests will return a 422 error.
- **Test queries template**: Template is provided, but needs to be parsed/processed correctly.

### Success Criteria
- **Minimum**: 8 PDFs loaded, 300+ chunks, all 30 queries executed, comparison report generated
- **Performance**: Ontology insights showing +10-15% improvement potential vs Team0

---

## 📞 Questions & Issues

### Common Issues & Solutions
See PLAN.md section "Expected Problems & Solutions" for:
- Team0 connection failures
- Gemini API connection issues
- Memory issues
- PDF text extraction problems
- Team0 response timeouts

### Getting Help
1. Check PLAN.md troubleshooting section
2. Verify all prerequisites are running
3. Check if task is correctly completed in CHECKLIST.md

---

## ✅ Final Checklist Before Starting

- [ ] I have read HANDOFF.md (this file)
- [ ] I have read README.md
- [ ] I have reviewed PLAN.md structure
- [ ] Python 3.8+ is installed
- [ ] I can navigate to the project folder
- [ ] I understand the 5-day timeline (20-22 hours total)
- [ ] I know where the target documents are (target_doc/)
- [ ] I understand Team0 is a reference/comparison baseline

---

## 🎯 Success Criteria Summary

**When you're done:**
- ✅ 8 PDFs fully processed
- ✅ Ontology graph built with 20+ relationships
- ✅ 30 test queries executed against Team0
- ✅ Performance comparison report generated
- ✅ Analysis showing improvement potential vs Team0

---

## 📊 Expected Outputs

| File | Description | Expected Size |
|------|-------------|---|
| vectors.json | 350 chunks vectorized (3072D) | ~100MB |
| ontology.json | Concept graph & relationships | ~50KB |
| test_results.json | Team0 query results | ~100KB |
| validation_report.md | Final comparison report (public) | ~30KB |
| detailed_results.json | All metrics & analysis | ~50KB |

---

**Let's build this! 💪**

**Start**: Read README.md → Review PLAN.md → Follow CHECKLIST.md Day by day

Good luck! 🚀

---

**Document Version**: 1.1  
**Updated**: 2026-06-07 (by Antigravity)  
**Status**: Reviewed & Clarified  

