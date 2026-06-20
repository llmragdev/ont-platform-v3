# Database Schema (s1_customer_board)

시나리오 1 게시판에 적용된 SQLite 데이터베이스 모델 정의입니다.

---

## 💾 파일 경로
* `s1_customer_board/s1_customer_board.db`

---

## 📊 테이블 구조

### 1. `posts` 테이블 (게시글)
* **목적**: 고객의 문의 질문을 관리합니다.
* **구조**:

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | 게시물 고유 ID (기본 시드: `q-001`) |
| `title` | TEXT | NOT NULL | 문의 제목 |
| `author` | TEXT | NOT NULL | 작성자 이름 (예: `홍길동`) |
| `content` | TEXT | NOT NULL | 문의 내용 상세 |
| `created_at` | TEXT | NOT NULL | 생성 일시 (ISO 8601 UTC string) |

### 2. `comments` 테이블 (댓글)
* **목적**: 게시글에 달리는 솔루션 및 관리자의 답변 댓글을 관리합니다.
* **구조**:

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | 댓글 고유 ID (예: `comment-a1b2c3d4`) |
| `post_id` | TEXT | FOREIGN KEY | `posts(id)` 외래키 (ON DELETE CASCADE) |
| `author` | TEXT | NOT NULL | 작성자 이름 (예: `고객지원팀(MCP-S1)`) |
| `content` | TEXT | NOT NULL | 댓글 본문 내용 |
| `created_at` | TEXT | NOT NULL | 생성 일시 (ISO 8601 UTC string) |

---

## 🗄️ 초기 데이터 (Seed Data)
데이터베이스 생성 시 다음 데이터가 자동으로 인입됩니다.
* **게시물 1 (`q-001`)**: `[시나리오1] 비밀번호 초기화 요청` (작성자: 홍길동)
* **게시물 2 (`UUID`)**: `[시나리오1] 시스템 점검 일정 안내` (작성자: 시스템관리자)
* **댓글 1 (`UUID`)**: `본 게시글은 접수 완료되었습니다. 잠시만 기다려주세요.` (작성자: 시스템봇, 대상: `q-001`)
