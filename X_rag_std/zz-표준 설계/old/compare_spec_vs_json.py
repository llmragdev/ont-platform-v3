#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare specification table vs actual JSON example"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 표에 정의된 필드들
spec_fields = [
    "status",
    "error",
    "data.query",
    "data.answer",
    "data.used_chunks[].chunk_id",
    "data.used_chunks[].content",
    "data.used_chunks[].similarity_score",
    "data.used_chunks[].metadata.source_name",
    "data.used_chunks[].metadata.source_url",
    "data.used_chunks[].metadata.page_no",
    "data.used_chunks[].metadata.category_large",
    "data.used_chunks[].metadata.category_mid",
    "data.used_chunks[].metadata.vector_db_id",
    "data.used_chunks[].metadata.tenant_id",
    "data.used_chunks[].metadata.org_id",
    "data.used_chunks[].metadata.dept_code",
    "data.debug_info.execution_time_ms",
    "data.debug_info.candidate_chunks",
]

# 현재 JSON에 있는 항목들 (분석)
current_json_items = {
    "root": ["status", "error"],
    "data": ["query", "answer"],
    "used_chunks": ["1개만 있음 (배열이지만 1개 원소)"],
    "chunk_fields": [
        "chunk_id",
        "content",
        "similarity_score",
        "metadata (모든 필드 포함)"
    ],
    "debug_info": [
        "execution_time_ms ✓",
        "candidate_chunks (주석만 있음, 실제 배열 아님)"
    ]
}

print("=" * 80)
print("표 vs JSON 예시 비교")
print("=" * 80)

print("\n📋 표에 정의된 필드: 18개")
for i, field in enumerate(spec_fields, 1):
    print(f"  {i:2d}. {field}")

print("\n\n📊 현재 JSON 예시의 문제점:")
print("\n❌ 1. candidate_chunks 형식 오류")
print("   현재: [\"// debug_mode: true 시에만 노출 — 미채택 청크 포함\"]")
print("   문제: 주석 문자열일 뿐, 실제 미채택 청크 배열이 아님")
print("   필요: 실제 청크 객체들의 배열")

print("\n❌ 2. used_chunks 개수 부족")
print("   현재: 1개만 있음")
print("   필요: 여러 개 청크 예시 (예: 3개)")
print("        - top_k=5 지정했으니 최대 5개까지 가능")
print("        - 실제 응답은 여러 청크 반환 예상")

print("\n❌ 3. 에러 응답 예시 없음")
print("   현재: 성공(status=success) 경우만 있음")
print("   필요: 실패(status=error) 경우 예시")
print("        - error.code와 error.message 형식")

print("\n\n✅ 현재 JSON에 있는 항목: 18개 필드 모두 포함됨")
print("   (구조적으로는 모두 있지만, 데이터 수가 부족)")

print("\n" + "=" * 80)
print("개선안")
print("=" * 80)

improvements = """
1️⃣  candidate_chunks 실제 예시 추가
   - chunk_id, content, similarity_score, metadata 포함
   - 2~3개 미채택 청크 예시

2️⃣  used_chunks 복수 청크 표시
   - 최소 2~3개 청크 포함
   - 각 청크마다 모든 metadata 필드 포함

3️⃣  에러 응답 예시 추가 (선택)
   - status="error" 케이스
   - error={code, message} 형식
"""

print(improvements)

print("\n" + "=" * 80)
print("수정된 JSON 구조")
print("=" * 80)

corrected_example = '''
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면...",
    "used_chunks": [
      {
        "chunk_id": "doc_a1b2c3d4#chunk4",
        "content": "LLM이 정답 생성에 채택한 텍스트 1...",
        "similarity_score": 0.89,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 12,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk5",
        "content": "LLM이 정답 생성에 채택한 텍스트 2...",
        "similarity_score": 0.78,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 13,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk6",
        "content": "LLM이 정답 생성에 채택한 텍스트 3...",
        "similarity_score": 0.71,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 14,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": [
        {
          "chunk_id": "doc_a1b2c3d4#chunk2",
          "content": "미채택 청크 텍스트...",
          "similarity_score": 0.65,
          "metadata": { ... }
        },
        {
          "chunk_id": "doc_a1b2c3d4#chunk7",
          "content": "미채택 청크 텍스트...",
          "similarity_score": 0.58,
          "metadata": { ... }
        }
      ]
    }
  },
  "error": null
}
'''

print(corrected_example)

print("\n" + "=" * 80)
print("결론")
print("=" * 80)
print("""
📌 문제:
   - JSON 예시가 표의 모든 필드를 실제 데이터로 보여주지 못함
   - candidate_chunks가 주석 문자열 (실제 배열이 아님)
   - used_chunks가 1개만 있음 (배열의 특성 미반영)

✅ 해결:
   - used_chunks: 2~3개 청크로 확장
   - candidate_chunks: 실제 청크 객체 배열로 수정
   - (선택) 에러 응답 예시 추가
""")
