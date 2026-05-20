# Frontend

온톨로지 중심 Next.js 프론트엔드를 개발할 위치입니다.

`claud_통합/frontend`를 참조하되, 첫 화면 구조는 온톨로지 관리와 객체/관계 탐색을 중심으로 둡니다.

우선 메뉴:

- 온톨로지 관리
- 객체 탐색
- 관계 탐색
- AI 질의
- 워크플로우 그래프
- 감사 로그

## 현재 구현

- 온톨로지 관리: 객체 타입, 관계 타입, 액션 타입 조회
- 객체 탐색: 타입별 객체 목록과 범용 객체 컨텍스트 조회
- 관계 관리: 관계 인스턴스 목록과 샘플 관계 추가
- AI 질의: 객체 ID 추출, 관계 컨텍스트, 근거 문서, trace 표시

## 실행

```powershell
cd E:\ontology_edu\Codex-통합\frontend
npm install
npm run dev
```

기본 API 주소는 `http://localhost:8001`입니다. 필요하면 `.env.local`에 다음을 설정합니다.

```text
NEXT_PUBLIC_API_BASE=http://localhost:8001
```

접속 주소:

```text
http://localhost:3100
```
