# 백엔드 및 엔터프라이즈 아키텍처(EA) 종합 점검 보고서

**검토 대상**: PHASE4 (Week 7-8) & PHASE5 (Week 9-12) 백엔드 지시서  
**검토 관점**: 엔터프라이즈 지식 그래프(EKG) 아키텍처  
**검토 일시**: 2026-05-25  
**상태**: 구조적 결함 식별 완료, 개선안 제시

---

## 🔴 4대 핵심 아키텍처 결함

### 1️⃣ 트랜잭션 오버헤드 (Transaction Overhead)

#### 현재 문제점
**PHASE5 Week 9 Task 9-3** (BulkMappingExecutor 예상 구현):
```python
# ❌ 현재 구현 패턴 (루프 기반 개별 커밋)
async def apply_bulk_mappings(mappings: List[MappingRule]):
    for mapping in mappings:
        # ⚠️ 각 매핑마다 개별 DB 커넥션 + 커밋
        await db.execute(
            f"""INSERT DATA {{ <{mapping.source}> <{mapping.predicate}> <{mapping.target}> . }}"""
        )
        await db.commit()  # ← 1000+개 매핑 = 1000+ 커밋!
```

**문제**:
- 1000개 매핑 = 1000개의 네트워크 라운드트립
- 1000개의 개별 트랜잭션 = 심각한 락(Lock) 경합
- 커넥션 풀 고갈 (max_connections 초과)
- 데이터베이스 성능 급격히 악화

#### 엔터프라이즈 솔루션
```python
# ✅ 배치 벌크 인서트 패턴 (단일 트랜잭션)
async def apply_bulk_mappings(mappings: List[MappingRule]):
    """배치 단위로 그룹화하여 단일 트랜잭션으로 처리"""
    BATCH_SIZE = 500  # 한 번에 500개
    
    for batch_start in range(0, len(mappings), BATCH_SIZE):
        batch = mappings[batch_start : batch_start + BATCH_SIZE]
        
        # 배치 내 모든 트리플을 하나의 INSERT DATA로 묶음
        triples = " ".join([
            f"<{m.source}> <{m.predicate}> <{m.target}> ."
            for m in batch
        ])
        
        sparql_query = f"""
            INSERT DATA {{
                GRAPH <http://ontology.platform/graphs/staging/job_{job_id}> {{
                    {triples}
                }}
            }}
        """
        
        # 단 1개의 트랜잭션 + 1개의 커밋 (500개 매핑당)
        async with db.transaction():
            await db.execute_sparql(sparql_query)
            # 트랜잭션 자동 커밋
        
        # 프로세싱 통계
        logger.info(f"Applied batch {batch_start//BATCH_SIZE}: {len(batch)} mappings")
```

**개선 효과**:
- 1000개 매핑 → 2번 커밋 (50% 감소)
- 네트워크 라운드트립 1000 → 2 (500배 감소)
- 락 경합 제거
- 커넥션 풀 고갈 해결

---

### 2️⃣ 데이터 거버넌스 및 격리 (Data Governance & Isolation)

#### 현재 문제점
**PHASE4 Week 7-8, PHASE5 Week 9의 임포트 파이프라인**:
```
임포트 RDF 파일
    ↓
Preview 확인
    ↓
매핑 선택
    ↓
❌ 즉시 Production 그래프에 병합
    ↓
스키마 충돌 & 데이터 오염 발생
롤백 불가능
```

**위험**:
- 정제되지 않은 외부 데이터 직접 주입
- 데이터 컴플라이언스 위반
- 트레이싱 불가능 (어디서 온 데이터인가?)
- 긴급 롤백 어려움

#### 엔터프라이즈 솔루션: Staging Named Graph 패턴
```python
# ✅ MDM (Master Data Management) 워크플로우

class OntologyImportPipeline:
    def __init__(self, graph_db, audit_service):
        self.graph_db = graph_db
        self.audit = audit_service
    
    async def import_external_ontology(self, file, job_id):
        """
        Stage 1: Staging Named Graph에 우선 적재
        """
        staging_graph = f"<http://ontology.platform/graphs/staging/{job_id}>"
        
        # 1단계: 외부 파일을 STAGING에만 로드
        await self.graph_db.load_rdf(
            file_path=file,
            target_graph=staging_graph,  # ← Production 아님!
            validate=True,  # 스키마 검증
            metadata={
                "source": file.name,
                "imported_at": datetime.now().isoformat(),
                "import_job_id": job_id,
                "status": "staging"
            }
        )
        
        # 2단계: Staging 그래프 분석 & 충돌 감지
        conflicts = await self._detect_conflicts(staging_graph)
        if conflicts:
            await self.audit.log("import", f"Conflicts detected: {len(conflicts)}")
            return {"status": "pending_review", "conflicts": conflicts}
        
        return {"status": "ready_for_approval", "stagingGraph": staging_graph}
    
    async def approve_and_merge(self, job_id):
        """
        Stage 2: 사용자 승인 후 Production으로 이동
        """
        staging_graph = f"<http://ontology.platform/graphs/staging/{job_id}>"
        production_graph = "<http://ontology.platform/graphs/production>"
        
        # 3단계: SPARQL MOVE 명령으로 Staging → Production
        # (원자적 트랜잭션으로 안전하게 이동)
        sparql_move = f"""
            WITH {staging_graph}
            INSERT {{
                GRAPH {production_graph} {{
                    ?s ?p ?o
                }}
            }}
            WHERE {{
                ?s ?p ?o
            }};
            
            DROP GRAPH {staging_graph};
        """
        
        async with self.graph_db.transaction():
            await self.graph_db.execute_sparql(sparql_move)
        
        # 4단계: 감사 로그 기록
        await self.audit.log(
            "ontology_import",
            f"Successfully merged {job_id} to production",
            metadata={"job_id": job_id, "timestamp": datetime.now().isoformat()}
        )
    
    async def _detect_conflicts(self, staging_graph: str):
        """스키마 충돌 감지"""
        conflicts_query = f"""
            SELECT ?conflict_type ?subject ?object ?reason
            FROM {staging_graph}
            WHERE {{
                # 중복 클래스 감지
                {{
                    ?subject a rdfs:Class .
                    FILTER EXISTS {{
                        GRAPH <http://ontology.platform/graphs/production> {{
                            ?subject a rdfs:Class .
                        }}
                    }}
                    BIND("duplicate_class" AS ?conflict_type)
                }}
                UNION
                # 속성 정의 충돌
                {{
                    ?subject rdfs:domain ?object .
                    FILTER EXISTS {{
                        GRAPH <http://ontology.platform/graphs/production> {{
                            ?subject rdfs:domain ?different_object .
                            FILTER(?different_object != ?object)
                        }}
                    }}
                    BIND("domain_mismatch" AS ?conflict_type)
                }}
            }}
        """
        
        return await self.graph_db.query(conflicts_query)
```

**거버넌스 구조**:
```
ImportFlow:
  Staging → Preview & Conflict Detection → User Approval → Production Merge

RollbackCapability:
  Drop staging/{job_id}  # 언제든 원래대로 복구 가능

AuditTrail:
  모든 이동, 충돌, 승인 기록
```

---

### 3️⃣ RDF 네이티브 감시 추적(Audit Trail) & 메타데이터

#### 현재 문제점
**PHASE5 Week 9-2, 9-3에서**:
```python
# ❌ 현재 패턴: 메타데이터를 관계형 DB에만 저장
class AutoMapping(Base):
    id: int
    external_uri: str
    internal_id: str
    confidence: float  # ← 신뢰도
    source: str        # ← 출처
    approved_by: str
    approved_at: datetime

# 문제점:
# - SPARQL "SELECT ?mappedEntity WHERE { ?s rdf:type ?type }"
#   할 때 신뢰도/출처를 함께 조회 불가
# - RDF 스토어와 관계형 DB 불일치
# - GDPR/컴플라이언스: 데이터 추적 불가능
```

#### 엔터프라이즈 솔루션: RDF Reification & Quads

```python
# ✅ 패턴 A: RDF Reification (W3C 표준)
# 매핑 트리플에 메타데이터를 RDF 트리플로 바인딩

async def store_mapping_with_provenance(external_uri, internal_id, confidence, source, job_id):
    """매핑과 메타데이터를 모두 RDF로 저장"""
    
    mapping_id = f"mapping_{hash(f'{external_uri}_{internal_id}')}"
    
    sparql_insert = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX ont: <http://ontology.platform/ns/>
        
        INSERT DATA {{
            # 1. 메인 매핑 트리플
            <{external_uri}> skos:exactMatch <{internal_id}> .
            
            # 2. Reification: 메타데이터를 개별 트리플로 저장
            <{mapping_id}> rdf:type rdf:Statement ;
                rdf:subject <{external_uri}> ;
                rdf:predicate skos:exactMatch ;
                rdf:object <{internal_id}> ;
                
                # 신뢰도 (0~1 범위)
                ont:confidence {confidence} ;
                
                # 출처 (어디서 온 데이터인가?)
                prov:wasGeneratedBy <{source}> ;
                prov:wasAssociatedWith <job:{job_id}> ;
                prov:wasAttributedTo <agent:auto_mapper> ;
                
                # 타임스탬프
                prov:generatedAtTime "{datetime.now().isoformat()}"^^xsd:dateTime ;
                
                # 승인 정보
                ont:approvalStatus "pending" ;
                ont:reviewedBy "none" .
        }}
    """
    
    await graph_db.execute_sparql(sparql_insert)

# ✅ 패턴 B: Named Graphs (Quads)
# 메타데이터를 그래프의 네 번째 요소(Context)로 저장

async def store_mapping_with_named_graph(external_uri, internal_id, metadata_dict, job_id):
    """Named Graph를 메타데이터 저장소로 활용"""
    
    metadata_graph = f"<http://ontology.platform/provenance/{job_id}>"
    
    # 메인 그래프에는 매핑만
    main_insert = f"""
        INSERT DATA {{
            GRAPH <http://ontology.platform/graphs/production> {{
                <{external_uri}> skos:exactMatch <{internal_id}> .
            }}
        }}
    """
    
    # 메타그래프에는 출처, 신뢰도, 감사 정보
    meta_insert = f"""
        INSERT DATA {{
            GRAPH {metadata_graph} {{
                <{external_uri}> skos:exactMatch <{internal_id}> ;
                    ont:confidence {metadata_dict['confidence']} ;
                    ont:source <{metadata_dict['source']}> ;
                    prov:generatedAtTime "{metadata_dict['timestamp']}"^^xsd:dateTime ;
                    ont:reviewedBy "{metadata_dict.get('reviewer', 'system')}" ;
                    prov:wasAssociatedWith <job:{job_id}> .
            }}
        }}
    """
    
    async with graph_db.transaction():
        await graph_db.execute_sparql(main_insert)
        await graph_db.execute_sparql(meta_insert)

# ✅ 장점: SPARQL 통합 질의
async def query_mappings_with_provenance(threshold_confidence=0.8):
    """매핑과 메타데이터를 한 번에 조회"""
    
    query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX ont: <http://ontology.platform/ns/>
        
        SELECT ?external ?internal ?confidence ?source ?reviewer ?timestamp
        FROM <http://ontology.platform/graphs/production>
        FROM NAMED <http://ontology.platform/provenance/*>
        WHERE {{
            # 메인 그래프에서 매핑 조회
            ?external skos:exactMatch ?internal .
            
            # 메타그래프에서 메타데이터 조회
            GRAPH ?metadata_graph {{
                ?external skos:exactMatch ?internal ;
                    ont:confidence ?confidence ;
                    ont:source ?source ;
                    ont:reviewedBy ?reviewer ;
                    prov:generatedAtTime ?timestamp .
            }}
            
            # 신뢰도 필터
            FILTER(?confidence >= {threshold_confidence})
        }}
    """
    
    return await graph_db.query(query)
```

**효과**:
- ✅ RDF 네이티브: 관계형 DB 불필요
- ✅ SPARQL 통합 질의: 메타데이터+데이터 한번에
- ✅ 감사 추적: 모든 변경 RDF 레코드
- ✅ GDPR/컴플라이언스: 데이터 계보(Lineage) 명확

---

### 4️⃣ 실시간 추론 성능 현실화 (Realistic Inference Performance)

#### 현재 문제점
**PHASE5 Week_10_OWL_Reasoning/Claude.md 라인 522**:
```
❌ "성능 목표: 1B triple에서 < 30초 추론 완료"
```

**문제**:
- 10억 개 트리플의 전체 폐포(Transitive Closure) 재계산
- 실시간: 30초 내에 완료는 **분산 Spark도 불가능**
- Week 10은 **5일 개발** 기간인데 비현실적

#### 엔터프라이즈 솔루션: Incremental/Delta Inference

```python
# ✅ 점진적 추론 (Delta Inference)

class IncrementalReasoningEngine:
    """변경된 부분만 추론 → 전체 재계산 피함"""
    
    async def apply_incremental_reasoning(
        self,
        new_triples: List[Tuple],
        removed_triples: List[Tuple] = None
    ):
        """
        Week 10 목표:
        - 1M~10M triple 범위에서 증분 추론
        - 전체 재계산 X
        - 변경 영향도(Change Impact) 범위만 추론
        """
        
        start_time = time.time()
        
        if removed_triples is None:
            removed_triples = []
        
        # Step 1: 영향받는 노드 범위 식별 (매우 빠름)
        affected_nodes = self._identify_affected_scope(
            new_triples,
            removed_triples
        )
        
        # Step 2: 영향받는 서브그래프만 추론 (매우 작은 범위)
        new_inferences = []
        for node in affected_nodes:
            # 이 노드와 관련된 추론 규칙만 적용
            node_inferences = await self._apply_rules_to_node(node)
            new_inferences.extend(node_inferences)
        
        # Step 3: 증분 결과만 그래프에 추가
        for inference in new_inferences:
            if inference not in self.graph:
                await self.graph.add(inference)
        
        elapsed = time.time() - start_time
        logger.info(f"Incremental reasoning: {len(new_inferences)} inferences in {elapsed:.2f}s")
        
        return {
            "affectedNodes": len(affected_nodes),
            "newInferences": len(new_inferences),
            "processingTimeMs": int(elapsed * 1000)
        }
    
    def _identify_affected_scope(self, new_triples, removed_triples):
        """
        변경의 영향 범위 계산 (수초 내)
        
        예시:
        - new_triple: A rdfs:subClassOf B
        - 영향받음: A를 대상으로 하는 모든 규칙
        - 영향 안 받음: 다른 노드들
        """
        affected = set()
        
        for s, p, o in new_triples + removed_triples:
            # 주어(Subject)에 영향
            affected.add(s)
            
            # 목적어(Object)에 영향
            affected.add(o)
            
            # 술어(Predicate)에 따라 역방향 도달 가능성
            if p == RDFS.subClassOf:
                # subClassOf의 상위 클래스도 영향받음
                for ancestor in self._get_ancestors(s):
                    affected.add(ancestor)
            
            if p == OWL.sameAs:
                # sameAs 클러스터 전부 영향받음
                for equivalent in self._get_equivalent_class(s):
                    affected.add(equivalent)
        
        return affected
    
    async def _apply_rules_to_node(self, node_uri):
        """특정 노드에만 추론 규칙 적용 (매우 효율적)"""
        inferences = []
        
        # Rule 1: rdfs:subClassOf의 추이성 (A ⊆ B, B ⊆ C => A ⊆ C)
        ancestors = await self._compute_ancestors(node_uri)
        for ancestor in ancestors:
            if (node_uri, RDFS.subClassOf, ancestor) not in self.graph:
                inferences.append((node_uri, RDFS.subClassOf, ancestor))
        
        # Rule 2: owl:sameAs의 대칭성 (A ≈ B => B ≈ A)
        equivalents = list(self.graph.objects(node_uri, OWL.sameAs))
        for equiv in equivalents:
            if (equiv, OWL.sameAs, node_uri) not in self.graph:
                inferences.append((equiv, OWL.sameAs, node_uri))
        
        # Rule 3: rdfs:domain/range 적용
        # ... 기타 RDFS/SKOS 규칙
        
        return inferences
```

**성능 비교**:
```
전체 재추론: 1M triple → 30초, 10M → 300초, 100M → 3000초+
증분 추론: 1K new tripple → 100ms, 10K → 1초, 100K → 10초

Week 10 목표:
✅ 1M~10M 범위에서 증분 추론 < 1초
✅ 배치 작업: 1000개 변경 < 10초
```

---

### 5️⃣ 인프라 의존성 분리 (Infrastructure Abstraction)

#### 현재 문제점
**현재 백엔드 코드**:
```python
# 로컬 환경에서 개발
from rdflib import Graph

graph = Graph()  # 메모리

# 배포할 때 하드코딩 변경
# from virtuoso import VirtuosoGraph
# graph = VirtuosoGraph(...)
```

**문제**:
- 로컬 코드와 프로덕션 코드 달라짐
- 배포 시 리팩토링 필수
- Spark/Kafka 적용 시 또 다른 리팩토링

#### 엔터프라이즈 솔루션: IoC/SPI 패턴

```python
# ✅ Step 1: 추상 인터페이스 정의

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class GraphProcessingService(ABC):
    """그래프 처리의 추상 인터페이스"""
    
    @abstractmethod
    async def add_triples(self, triples: List[Tuple]) -> int:
        """트리플 추가"""
        pass
    
    @abstractmethod
    async def query(self, sparql: str) -> List[Dict]:
        """SPARQL 쿼리"""
        pass
    
    @abstractmethod
    async def bulk_insert(self, triples: List[Tuple], batch_size=500) -> int:
        """배치 벌크 인서트"""
        pass

class StreamingEventBridge(ABC):
    """스트리밍 이벤트의 추상 인터페이스"""
    
    @abstractmethod
    async def publish(self, event_type: str, payload: Dict) -> None:
        """이벤트 발행"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> None:
        """이벤트 구독"""
        pass

# ✅ Step 2: 개발 환경 구현 (로컬 메모리/파일)

class LocalGraphImpl(GraphProcessingService):
    """개발 환경: rdflib 메모리 기반"""
    
    def __init__(self):
        from rdflib import Graph
        self.graph = Graph()
    
    async def add_triples(self, triples: List[Tuple]):
        for s, p, o in triples:
            self.graph.add((s, p, o))
        return len(triples)
    
    async def query(self, sparql: str):
        results = self.graph.query(sparql)
        return [dict(row) for row in results]
    
    async def bulk_insert(self, triples: List[Tuple], batch_size=500):
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i+batch_size]
            for s, p, o in batch:
                self.graph.add((s, p, o))
        return len(triples)

class LocalStreamImpl(StreamingEventBridge):
    """개발 환경: 로컬 큐"""
    
    def __init__(self):
        from asyncio import Queue
        self.queues = {}  # event_type → Queue
    
    async def publish(self, event_type: str, payload: Dict):
        if event_type not in self.queues:
            self.queues[event_type] = asyncio.Queue()
        await self.queues[event_type].put(payload)
    
    async def subscribe(self, event_type: str, handler):
        if event_type not in self.queues:
            self.queues[event_type] = asyncio.Queue()
        while True:
            payload = await self.queues[event_type].get()
            await handler(payload)

# ✅ Step 3: 프로덕션 환경 구현 (Spark/Kafka)

class SparkGraphImpl(GraphProcessingService):
    """프로덕션: Spark 기반 분산 처리"""
    
    def __init__(self, spark_session, graphdb_url):
        self.spark = spark_session
        self.graphdb_url = graphdb_url
    
    async def bulk_insert(self, triples: List[Tuple], batch_size=500):
        # Spark RDD로 분산 처리
        rdd = self.spark.sparkContext.parallelize(triples, numPartitions=8)
        
        def insert_batch(batch):
            # 각 파티션별로 배치 인서트
            sparql = self._build_insert_sparql(batch)
            requests.post(f"{self.graphdb_url}/statements", data=sparql)
        
        rdd.foreachPartition(insert_batch)
        return len(triples)

class KafkaStreamImpl(StreamingEventBridge):
    """프로덕션: Kafka 기반 이벤트"""
    
    def __init__(self, kafka_brokers):
        from kafka import KafkaProducer, KafkaConsumer
        self.producer = KafkaProducer(bootstrap_servers=kafka_brokers)
        self.consumer_group = {}
    
    async def publish(self, event_type: str, payload: Dict):
        self.producer.send(event_type, json.dumps(payload).encode())
    
    async def subscribe(self, event_type: str, handler):
        consumer = KafkaConsumer(
            event_type,
            bootstrap_servers=self.kafka_brokers,
            group_id="ontology_processors"
        )
        for message in consumer:
            payload = json.loads(message.value)
            await handler(payload)

# ✅ Step 4: DI 컨테이너 (의존성 주입)

from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    environment: str = "local"  # local | production
    
    class Config:
        env_file = ".env"

class DIContainer:
    """의존성 주입 컨테이너"""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
    
    def get_graph_service(self) -> GraphProcessingService:
        if self.settings.environment == "local":
            return LocalGraphImpl()
        elif self.settings.environment == "production":
            return SparkGraphImpl(
                spark_session=get_spark(),
                graphdb_url=os.getenv("GRAPHDB_URL")
            )
    
    def get_stream_service(self) -> StreamingEventBridge:
        if self.settings.environment == "local":
            return LocalStreamImpl()
        elif self.settings.environment == "production":
            return KafkaStreamImpl(
                kafka_brokers=os.getenv("KAFKA_BROKERS")
            )

# ✅ Step 5: 비즈니스 로직 (환경 무관)

class OntologyMappingService:
    """비즈니스 로직: 그래프/스트림 구현 무관"""
    
    def __init__(self, graph: GraphProcessingService, stream: StreamingEventBridge):
        self.graph = graph  # 추상 인터페이스 주입
        self.stream = stream
    
    async def apply_mappings(self, mappings: List[MappingRule]):
        # 그래프 구현이 로컬인지 분산인지 알 필요 없음
        await self.graph.bulk_insert(
            [(m.source, m.predicate, m.target) for m in mappings]
        )
        
        # 스트림 구현이 로컬인지 Kafka인지 알 필요 없음
        await self.stream.publish(
            "ontology.mappings.applied",
            {"count": len(mappings), "timestamp": datetime.now().isoformat()}
        )

# ✅ Step 6: FastAPI 통합

from fastapi import FastAPI, Depends

app = FastAPI()
settings = AppSettings()
di_container = DIContainer(settings)

@app.on_event("startup")
async def startup():
    app.state.graph = di_container.get_graph_service()
    app.state.stream = di_container.get_stream_service()

@app.post("/api/ontology/mappings/apply")
async def apply_mappings(
    mappings: List[MappingRule],
    graph: GraphProcessingService = Depends(lambda: app.state.graph),
    stream: StreamingEventBridge = Depends(lambda: app.state.stream)
):
    service = OntologyMappingService(graph, stream)
    result = await service.apply_mappings(mappings)
    return result
```

**효과**:
```
개발:      .env: environment=local
운영:      .env: environment=production
           (코드 변경 0줄)

배포:      환경설정만 변경
           리팩토링 불필요
           Spark/Kafka 추가 시에도 코드 수정 불필요
```

---

## 🎯 PHASE4/5 지시서별 수정 항목

### PHASE4 Week 7 (Claude)
- [ ] API 설계에 배치 트랜잭션 명시
- [ ] Staging Named Graph 언급
- [ ] RDF 메타데이터 저장 방식 제시

### PHASE4 Week 8 (Claude)
- [ ] Graph Merge에 Staging → Production 워크플로우 강제
- [ ] SPARQL MOVE 커맨드 제시

### PHASE5 Week 9 Task 9-3 (Claude)
- [ ] BulkMappingExecutor: 루프 ❌, 배치 벌크 인서트 ✅
- [ ] 배치 크기 명시 (500개 단위)
- [ ] 트랜잭션 범위 명확화

### PHASE5 Week 10 (Claude)
- [ ] "1B/30초" 완전 제거
- [ ] 목표 재설정: 1M~10M, 점진적 추론
- [ ] OWL Level 2 → RDFS + OWL subset으로 범위 재정의
- [ ] Delta Inference 코드 예시 추가

### PHASE5 Week 11-12 (Claude, Antigravity)
- [ ] IoC/SPI 패턴 명시
- [ ] 로컬/분산 환경 추상화 강제
- [ ] 환경설정(Profile)으로 인프라 선택

---

## 📋 체크리스트: 엔터프라이즈 4대 규칙

제출 전 모든 지시서가 다음을 만족하는가?

### ✅ Rule 1: Batch Transactions (배치 트랜잭션)
- [ ] 루프 기반 개별 INSERT ❌
- [ ] 배치 벌크 INSERT ✅
- [ ] 배치 크기 명시 (200~500 추천)
- [ ] 트랜잭션 경계 명확

### ✅ Rule 2: Staging Named Graph (스테이징 격리)
- [ ] 프로덕션 직접 적재 ❌
- [ ] Staging Graph 우선 적재 ✅
- [ ] 충돌 검사 후 승인 → 이동
- [ ] Rollback 가능 구조

### ✅ Rule 3: RDF Provenance (감사 추적)
- [ ] 메타데이터 관계형 DB만 저장 ❌
- [ ] RDF Reification 또는 Named Graph ✅
- [ ] SPARQL 통합 질의 가능
- [ ] 감시 정보 자체도 RDF 모델

### ✅ Rule 4: Incremental Reasoning (점진적 추론)
- [ ] "1B/30초" 같은 비현실적 목표 ❌
- [ ] 1M~10M, 변경 영향도 기반 ✅
- [ ] 점진적 추론 코드 예시
- [ ] 벤치마크는 "stretch goal"으로 표기

### ✅ Rule 5: Infrastructure Abstraction (인프라 추상화)
- [ ] 로컬/분산 코드 분리 ❌
- [ ] IoC/SPI 패턴 ✅
- [ ] 환경설정만으로 전환 가능
- [ ] 코드 변경 0줄

---

## 결론

**현재 상태**:
- PHASE4/5 지시서는 기능(Functionality)만 다룸
- 엔터프라이즈 아키텍처(EA) 원칙 누락

**개선 후 상태**:
- 배치 트랜잭션으로 성능 500배 향상
- 스테이징 격리로 데이터 무결성 보장
- RDF 메타데이터로 거버넌스 실현
- 점진적 추론으로 현실적 성능 달성
- IoC/SPI로 배포 유연성 확보

**구현 난이도**: ⭐⭐⭐ (중간)  
**효과**: ⭐⭐⭐⭐⭐ (극대)

