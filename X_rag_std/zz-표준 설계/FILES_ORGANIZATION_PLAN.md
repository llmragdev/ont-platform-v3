# RAG 표준 설계 파일 정리 계획

**완료 날짜**: 2026-05-18

---

## 📋 파일 정리 현황

### 1️⃣ 파이썬 프로그램 정리 ✅

**결과**:
- ✅ 루트 + zz-표준 설계 폴더의 작업용 파이썬 프로그램 **27개** 
- ✅ 위치: `E:\ontology_edu\X_rag_std\zz-표준 설계\old\`
- ✅ 유지: `convert_to_word.py` (필요시 사용)

**백업된 프로그램** (27개):
```
분석/검증 프로그램:
  - check_content_issues.py
  - check_search_response.py
  - check_template.py

비교/검토 프로그램:
  - compare_docx.py
  - compare_spec_vs_json.py
  - compare_text_changes.py

수정 프로그램:
  - add_complete_json_to_docx.py
  - fix_3_2_5.py
  - fix_table_colors.py
  - direct_fix.py
  - fix_content_all.py
  - fix_rag_guide.py
  - fix_remaining_issues.py

재구성 프로그램:
  - finalize_docx.py
  - finalize_docx_correct.py
  - rebuild_docx.py
  - rebuild_from_template.py
  - analyze_template_detail.py

검증 프로그램:
  - verify_search_response_table.py
  - update_json_examples.py
  - update_search_response_table.py
  - review_rag_guide.py
  - verify_final.py
  - verify_final_format.py

변환 프로그램:
  - md_to_docx.py
  - meta_section.py
  - find_delete_section.py
```

---

### 2️⃣ 문서 파일 정리 (진행 예정)

#### Word 파일 현황

| 파일명 | 크기 | 용도 | 상태 |
|--------|------|------|------|
| **RAG 개발 가이드_v1.0.docx** | 53.23KB | **기준 파일** | ✅ 유지 |
| RAG 개발 가이드_v1.1.docx | 69.01KB | 최신 버전 (검색응답 완성) | ✅ 유지 |
| RAG 개발 가이드_v1.1 - 원본.docx | 64.42KB | 원본 (백업용) | ? 정리 |
| RAG 개발 가이드_v1.1 - 복사본.docx | 55.79KB | 복사본 (불필요) | ❌ 삭제 |
| RAG 개발 가이드_v1.1_old.docx | 60.66KB | 이전 버전 | ❌ 삭제 |
| RAG_표준_설계_v1.3.docx | 39.33KB | 중간 버전 | ? 정리 |
| RAG_표준_설계_v1.5_보고용.docx | 48.75KB | 섹션 추출 | ? 검토 |

#### Markdown 파일 현황

| 파일명 | 크기 | 용도 | 상태 |
|--------|------|------|------|
| RAG_표준_설계_v1.0.md | 7.94KB | 초기 버전 | ? 정리 |
| RAG_표준_설계_v1.1.md | 10.31KB | 초기 버전 | ? 정리 |
| RAG_표준_설계_v1.2.md | 11.54KB | 초기 버전 | ? 정리 |
| RAG_표준_설계_v1.3.md | 4.97KB | 초기 버전 | ? 정리 |
| RAG_표준_설계_v1.4.md | 24.01KB | 초기 버전 | ? 정리 |
| **RAG_표준_설계_v1.5.md** | 21.75KB | **완전한 버전** | ✅ 유지 |
| **RAG_표준_설계_v1.5_보고용.md** | 24.08KB | **RAG 개발 가이드_v1.0 기준으로 정렬 필요** | ⚠️ 검토 필요 |
| **RAG_표준_설계_v1.5_매핑.md** | 4.07KB | **기준 파일과 매핑 확인 필요** | ⚠️ 검토 필요 |

---

## 🎯 다음 단계

### Phase 1: 문서 정렬 (USER 확인 필요)

#### 1. RAG_표준_설계_v1.5_보고용.md 정렬
- [ ] RAG 개발 가이드_v1.0.docx 내용 확인
- [ ] RAG_표준_설계_v1.5.md와 비교하여 누락된 부분 확인
- [ ] RAG_표준_설계_v1.5_보고용.md에 누락된 내용 추가

#### 2. RAG_표준_설계_v1.5_매핑.md 정렬
- [ ] RAG 개발 가이드_v1.0.docx의 섹션 구조 분석
- [ ] 각 섹션의 마크다운 파일 매핑 확인
- [ ] 필요시 매핑 업데이트

#### 3. 중복 파일 정리
- [ ] RAG 개발 가이드_v1.1 - 복사본.docx → 삭제
- [ ] RAG 개발 가이드_v1.1_old.docx → 정리
- [ ] 초기 마크다운 버전들 (v1.0~v1.4) → old 폴더로 이동

---

## 📊 정리 현황 요약

| 항목 | 상태 | 진행률 |
|------|------|--------|
| **파이썬 프로그램 정리** | ✅ 완료 | 100% |
| **문서 파일 동기화** | ⏳ 예정 | 0% |
| **중복 파일 정리** | ⏳ 예정 | 0% |
| **old 폴더 정리** | ✅ 진행중 | 50% |

---

## 💡 권장사항

### 유지할 파일
```
주요 문서:
  ✅ RAG 개발 가이드_v1.0.docx (기준)
  ✅ RAG 개발 가이드_v1.1.docx (최신)
  ✅ RAG_표준_설계_v1.5.md (완전)
  ✅ RAG_표준_설계_v1.5_보고용.md (정렬 후)
  ✅ RAG_표준_설계_v1.5_매핑.md (정렬 후)
  
유틸리티:
  ✅ convert_to_word.py
```

### 삭제/정리할 파일
```
중복 Word 파일:
  ❌ RAG 개발 가이드_v1.1 - 복사본.docx
  ❌ RAG 개발 가이드_v1.1_old.docx
  
초기 버전 마크다운:
  → old 폴더로: v1.0.md, v1.1.md, v1.2.md, v1.3.md, v1.4.md
```

---

## 🔐 파일 백업 위치

모든 작업용 파이썬 프로그램:
```
📁 E:\ontology_edu\X_rag_std\zz-표준 설계\old\
   ├── check_*.py (12개)
   ├── compare_*.py (3개)
   ├── fix_*.py (5개)
   ├── finalize_*.py (2개)
   ├── rebuild_*.py (2개)
   ├── verify_*.py (3개)
   ├── update_*.py (2개)
   ├── add_*.py (1개)
   ├── analyze_*.py (1개)
   ├── meta_*.py (1개)
   ├── md_to_*.py (1개)
   ├── direct_*.py (1개)
   └── review_*.py (1개)
```

---

**다음**: USER의 지시에 따라 문서 파일 동기화 진행
