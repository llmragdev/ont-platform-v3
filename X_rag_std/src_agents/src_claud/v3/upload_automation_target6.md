# AI Lab 6개 PDF 업로드 자동화

이 문서는 `E:\ai_lab_SIT\target_doc`의 NLP PDF 6개를 `src_claud/v3` RAG 서버에 자동 업로드하는 절차를 정리한다.

이 작업은 QA 통합테스트 전에 수행하는 **사전 준비 자동화**이다. 검색 품질, 벡터화 품질, 답변 정확도 평가는 이 문서의 범위가 아니다.

## 대상 스크립트

```text
upload_automation_target6.py
```

## 대상 파일

기본 대상 폴더:

```text
E:\ai_lab_SIT\target_doc
```

업로드 대상 6개:

```text
NLP - [03] 온톨로지이질성문제를해결하기위한온톨로지매칭방법-2024.pdf
NLP - [06] 정적 언어모델부터 생성형AI까지, 텍스트를 다시 쓰는 기술에 대하여 - 2025.pdf
NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf
NLP - [08] NLP - 한국근대문인 데이터베이스 구축 방법탐색-2025.pdf
NLP - [09] NLP - 실시간 문맥 인식 감성 분석을 위한 모듈형 아키텍처 설계-2025.pdf
NLP - 온톨로지 기반의 의미 속성 및 감성 판별 - 2025 - 안은희 안정국.pdf
```

## 업로드 설정

스크립트는 아래 설정으로 업로드한다.

| 항목 | 값 |
|---|---|
| RAG 서버 | `http://localhost:8000` |
| Tenant | `company_abc` |
| Org | `0200` |
| project_code | `TECH001` |
| category_mid | `ontology` |
| category_low | `ai_lab_nlp` |
| vector_db_id | `vdb_ontology_01` |

헤더:

```text
X-Tenant-ID: company_abc
X-Org-ID: 0200
```

## 1. Conda 환경 준비

처음 한 번만 수행한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
conda create --prefix ./env python=3.11 -y
conda activate ./env
pip install -r requirements.txt
```

이미 `env`가 있으면 아래만 수행한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
conda activate ./env
```

## 2. RAG 서버 실행

업로드 자동화만 확인할 때는 `local_json` 모드로 충분하다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
conda activate ./env
set VECTOR_DB_ENGINE=local_json
uvicorn app.main:app --port 8000 --reload
```

서버 터미널은 종료하지 않고 그대로 둔다.

## 3. 업로드 자동화 실행

다른 PowerShell 터미널을 열고 실행한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
conda activate ./env
python upload_automation_target6.py
```

성공 시 다음 흐름이 출력된다.

```text
[OK] RAG 서버 연결 확인
[STEP 1] 파일 업로드
[1/6] ...
  [OK] doc_id=... status=... vector_db=...
...
[STEP 2] 문서 목록 확인
  이번 대상 파일 매칭 수: 6/6
```

## 4. 결과 확인

스크립트는 업로드 후 `/api/v1/documents`를 호출해 대상 6개 파일이 문서 목록에 있는지 확인한다.

성공 기준:

```text
업로드 성공: 6/6
이번 대상 파일 매칭 수: 6/6
```

## 5. QA 플랫폼 연동

업로드와 벡터화 준비가 끝난 뒤 로컬 기준선인 0조를 QA 비교에 포함하려면 `E:\ai_lab_SIT\configs\team_apis.json`에서 아래 설정을 활성화한다.

```json
{
  "team": "team0_local_rag",
  "enabled": true
}
```

이후 QA 플랫폼에서 v2 평가를 실행한다.

```powershell
cd E:\ai_lab_SIT\src_codex
python -m uvicorn main_sit_app:app --host 0.0.0.0 --port 8002 --reload
```

다른 터미널:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8002/v2/eval/round" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"round_name":"standard","dry_run":false,"auto_evaluate":true}'
```

## 6. 범위와 주의사항

- 이 자동화는 파일 업로드와 문서 목록 확인까지만 수행한다.
- 검색 품질 평가는 수행하지 않는다.
- LLM Gateway와 ChromaDB는 업로드 확인만 할 때 필수는 아니다.
- `local_json` 모드는 로컬 검증용이다.
- 운영 수준 검색 성능을 보려면 ChromaDB와 Gemini Gateway 구성을 별도로 확인한다.
