# PHASE Week 6 Codex: 온톨로지 확장 방향성 분석

**작성일**: 2026-05-25  
**대상**: Phase 4 Week 3.5 ~ Week 6 Codex 프론트엔드 작업  
**관점**: 온톨로지 확장성, RDF/External Ontology 연계, 운영 안정성

---

## 종합 평가

지금까지 수행한 Codex 작업은 온톨로지 확장 관점에서 방향이 잘 잡혀 있다.

다만 현재 상태는 “외부 온톨로지 확장을 지원할 수 있는 프론트엔드 구조와 검증 기반을 구축한 상태”에 가깝다. 아직 “실제 외부 온톨로지가 내부 도메인 모델에 의미적으로 병합되는 기능이 완성된 상태”라고 보기는 어렵다.

즉, Codex 작업은 온톨로지 확장 기능의 UI, 검증, 운영 기반을 준비하는 데 성공적이며, 의미 병합과 스키마 거버넌스는 후속 백엔드/API 작업과 함께 보완되어야 한다.

---

## 잘하고 있는 점

### 1. RDF/External Ontology 확장 축을 UI에 반영

Week 4에서 구현한 `RDFWorkbench`, `RDFGraphViewer`, `OntologyImporter`, `LinkedDataViewer`는 온톨로지 확장 개념에 잘 부합한다.

특히 DBpedia, Wikidata, RDF File을 import source로 분리한 점은 “외부 지식 소스 → 내부 도메인 온톨로지 연결” 구조를 준비한 것이다.

### 2. RDF 그래프 시각화 도입

온톨로지는 단순 테이블보다 노드/엣지 구조가 핵심이다.

Cytoscape 기반 그래프 뷰어를 도입한 것은 엔티티, 속성, 리터럴, 외부 리소스를 구분해서 볼 수 있게 하므로 확장된 온톨로지의 탐색성과 설명 가능성에 도움이 된다.

### 3. SPARQL Workbench 안정화

SPARQL은 온톨로지 확장의 검증 도구다.

Week 5에서 SPARQL 엣지 케이스, 오류 메시지, 결과 표시 안정성을 강화한 것은 확장된 RDF/온톨로지 데이터를 질의하고 검증하는 데 필요한 기반이다.

### 4. DLQ/WriteBack 안정장치와 운영 안정성 확보

온톨로지 확장은 외부 시스템 동기화와 충돌하기 쉽다.

Week 3.5의 DLQ Dashboard는 직접적인 온톨로지 모델링 기능은 아니지만, 확장된 온톨로지 변경 사항이 외부 write-back 과정에서 유실되지 않도록 운영 안정성을 보강한다.

### 5. 성능 최적화 방향이 적절함

Week 6에서 RDF/Cytoscape/ReactFlow를 lazy loading으로 분리한 것은 매우 적절하다.

온톨로지 확장 기능은 그래프 라이브러리 때문에 무거워지기 쉬운데, 초기 번들을 크게 줄인 것은 실사용 관점에서 중요하다.

실제 빌드 기준:

| 항목 | 최적화 전 | 최적화 후 |
|------|----------|----------|
| `/` First Load JS | 약 334 kB | 96.1 kB |
| `/rdf` First Load JS | 약 247 kB | 97.2 kB |

---

## 아직 부족한 점

### 1. Ontology Import가 아직 UI + fallback 수준

현재 `OntologyImporter`는 DBpedia/Wikidata/RDF File import UI와 API 계약을 준비했지만, 실제 의미 병합은 백엔드가 수행해야 한다.

따라서 현재는 “확장 인터페이스”는 만들었지만, “확장 로직”이 완성됐다고 보기는 어렵다.

### 2. 외부 URI와 내부 엔티티 매핑 규칙 부족

온톨로지 확장의 핵심은 외부 리소스와 내부 엔티티 사이의 관계를 명확히 정의하는 것이다.

예:
- `owl:sameAs`
- `skos:exactMatch`
- `skos:closeMatch`
- `skos:broader`
- `skos:narrower`
- `relatedTo`

현재 UI는 외부 리소스를 보여주지만, 사용자가 “이 외부 개념을 내부 엔티티와 어떤 관계로 연결할지” 정하는 화면은 아직 부족하다.

### 3. 스키마/클래스 확장 흐름이 명확하지 않음

외부 RDF를 가져오면 새 class/property가 생길 수 있다.

현재는 RDF graph viewer와 importer가 있지만 다음 흐름은 아직 약하다:
- 새 property를 내부 스키마에 등록할지 결정
- 충돌 property 처리
- 외부 class와 내부 entity type 매핑
- import 전후 schema diff 확인

### 4. Provenance/신뢰도 표시 보강 필요

외부 온톨로지 확장에서는 출처가 매우 중요하다.

현재 `LinkedDataViewer`에 source badge는 있지만 다음 정보가 더 필요하다:
- confidence score
- imported_at
- source version
- mapping rule
- reviewer/approval status
- external URI 변경 이력

### 5. 대규모 그래프 확장 전략은 아직 초기

Week 6에서 lazy loading은 잘했지만, 실제 수천~수만 triple 그래프에서는 추가 전략이 필요하다:
- graph clustering
- neighborhood expansion
- server-side graph slicing
- progressive loading
- node degree 제한
- subgraph caching

현재는 mock/prototype 수준의 RDF graph rendering에 가깝다.

---

## 후속 보완 제안

### 우선순위 1: 외부 URI ↔ 내부 엔티티 매핑 UI

외부 온톨로지 확장의 핵심 화면으로 다음 기능을 추가하는 것이 좋다:
- 내부 엔티티 선택
- 외부 URI 선택
- 관계 유형 선택
- 매핑 confidence 입력/표시
- 승인/반려 워크플로우 연결

### 우선순위 2: Import Preview/Diff

RDF import 전에 다음을 미리 보여줘야 한다:
- 추가될 class 수
- 추가될 property 수
- 추가될 triple 수
- 충돌 가능 schema
- 기존 엔티티와 중복되는 URI
- 자동 매핑 후보

### 우선순위 3: Schema Conflict Resolution

외부 RDF를 내부 모델에 병합할 때 다음 충돌을 다뤄야 한다:
- 동일 label, 다른 URI
- 동일 URI, 다른 type
- property range/domain 충돌
- literal datatype 충돌
- 다국어 label 우선순위

### 우선순위 4: Provenance/Lineage 강화

확장된 온톨로지 객체마다 다음 정보를 표시해야 한다:
- 출처
- import job id
- source version
- created_by
- reviewed_by
- last_synced_at
- rollback 가능 여부

### 우선순위 5: 대규모 RDF 그래프 렌더링 전략

그래프 전체를 한 번에 렌더링하기보다 다음 방식이 필요하다:
- 선택 노드 기준 1-hop/2-hop 탐색
- expand on click
- high-degree node collapse
- external resource group node
- backend pagination
- viewport 기반 graph loading

---

## 결론

Codex 작업은 온톨로지 확장이라는 큰 방향에 잘 부합하고 있다.

특히 RDF Lab, 외부 import UI, Linked Data Viewer, SPARQL 안정화, DLQ 운영 안정장치, 성능 최적화는 “확장 가능한 UI/운영 기반”을 성공적으로 깔고 있는 작업이다.

다만 온톨로지 확장을 완성하려면 다음 단계가 필요하다:

- 외부 URI와 내부 엔티티의 의미 매핑
- schema diff 및 conflict resolution
- provenance/confidence 관리
- import 승인 워크플로우
- 대규모 RDF graph loading 전략

따라서 현재 평가는 다음과 같이 정리할 수 있다.

> Codex는 온톨로지 확장을 위한 프론트엔드 기반과 검증 체계를 잘 구축하고 있다.  
> 후속 단계에서는 의미 병합, 매핑 거버넌스, 출처/신뢰도 관리 기능을 추가해야 실제 온톨로지 확장 기능으로 완성된다.
