# 🔴 시스템 장애 보고서: 파일 업로드 500에러 (AttributeError)

**작성일자:** 2026년 6월 20일  
**작성자:** Antigravity (백엔드 엔지니어 AI)  
**장애 발생 컴포넌트:** Backend (`app/main.py`, `app/services/document.py`)

---

## 1. 장애 개요
* **현상:** 파일 업로드 완료 후 레지스트리에 상태를 기록하는 도중 `500 Internal Server Error` 발생.
* **에러 로그:** `AttributeError: 'dict' object has no attribute 'company_id'`

## 2. 원인 분석
* **함수 인자 순서 역전 오류:** `DocumentService`의 `_save_registry(self, ctx: TenantContext, registry: dict)` 메서드를 호출할 때, `app/main.py` 라인 112에서 `svc._save_registry(registry, ctx)`로 인자를 반대로 전달함.
* 이로 인해 `_save_registry` 내부에서 딕셔너리 객체를 `TenantContext` 객체로 취급하여 `ctx.company_id`를 참조하려다 에러가 발생함.

## 3. 조치 내역
* `app/main.py` 파일 내 `upload_document` 및 `vectorize_document` API의 `_save_registry` 호출부 파라미터 순서를 `(ctx, registry)`로 올바르게 재수정 완료.

## 4. 재발 방지 대책
* Python의 Type Hinting을 주의 깊게 확인하고, 객체와 데이터 페이로드를 전달할 때 반드시 선언된 인자 순서와 타입을 지키도록 코드 작성 시 한 번 더 검증하겠습니다.
