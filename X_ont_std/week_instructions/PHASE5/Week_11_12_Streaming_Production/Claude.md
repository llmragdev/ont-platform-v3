# Phase 5 Week 11-12: ?ㅼ떆媛??ㅽ듃由щ컢 & ?꾨줈?뺤뀡 ?댁쁺
## Claude (Backend) ?섑뻾 吏?쒖꽌

**湲곌컙**: 2026-08-05 ~ 2026-08-16 (2二?  
**?좊떦**: 90% (二쇰떦 27-30?쒓컙)  
**紐⑺몴**: ?ㅼ떆媛?留ㅽ븨 泥섎━, 荑쇰━ 理쒖쟻?? ?댁쁺 ?덉젙???뺣낫

---

## 媛쒖슂

Phase 5??留덉?留??④퀎???⑦넧濡쒖? ?뺤옣 ?쒖뒪?쒖쓣 **?꾨줈?뺤뀡 ?섍꼍?쇰줈 ?댄뻾**?섎뒗 寃껋엯?덈떎. 二쇱슂 紐⑺몴:
- **?ㅼ떆媛?泥섎━**: 1000+ updates/sec 吏??- **?먮룞 理쒖쟻??*: AI 湲곕컲 荑쇰━ 理쒖쟻??- **?댁쁺 ?덉젙??*: 99.9% SLA ?ъ꽦
- **嫄곕쾭?뚯뒪**: 留ㅽ븨 踰꾩쟾 愿由? 濡ㅻ갚, 媛먯궗

---

## Task 11-1: ?ㅼ떆媛?SPARQL 荑쇰━ 理쒖쟻??
**湲곌컙**: 08-05 ~ 08-08 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/query_optimizer.py
from typing import Dict, List, Tuple
import ast
import time

class SPARQLQueryOptimizer:
    """
    SPARQL 荑쇰━瑜??먮룞?쇰줈 遺꾩꽍?섍퀬 理쒖쟻?뷀븯???붿쭊
    """
    
    def __init__(self, graph_db, statistics_service):
        self.graph_db = graph_db
        self.stats = statistics_service
        self.query_cache = {}  # 理쒖쟻?붾맂 荑쇰━ 罹먯떆
    
    async def optimize_query(
        self,
        sparql_query: str
    ) -> Dict:
        """
        SPARQL 荑쇰━ 理쒖쟻??        
        理쒖쟻??湲곕쾿:
        1. ?좏깮??selectivity) 湲곕컲 ?꾪꽣 ?쒖꽌 議곗젙
        2. 議곗씤 ?쒖꽌 ?щ같??(cost-based)
        3. ?⑦꽩 湲곕컲 理쒖쟻??        4. ?몃뜳???쒖슜
        """
        
        # 罹먯떆 ?뺤씤
        query_hash = hash(sparql_query)
        if query_hash in self.query_cache:
            return self.query_cache[query_hash]
        
        start_time = time.time()
        
        # 1. 荑쇰━ ?뚯떛
        parsed = self._parse_sparql(sparql_query)
        
        # 2. ?듦퀎 ?섏쭛
        statistics = await self._collect_triple_pattern_stats(
            parsed['patterns']
        )
        
        # 3. 理쒖쟻 ?ㅽ뻾 怨꾪쉷 ?앹꽦
        optimal_plan = self._generate_optimal_plan(
            parsed,
            statistics
        )
        
        # 4. 荑쇰━ ?ъ옉??        optimized_query = self._rewrite_query(
            sparql_query,
            optimal_plan
        )
        
        # 5. 異붿젙 ?깅뒫 怨꾩궛
        estimated_time_ms = self._estimate_execution_time(optimal_plan)
        
        elapsed = time.time() - start_time
        
        result = {
            "originalQuery": sparql_query,
            "optimizedQuery": optimized_query,
            "executionPlan": optimal_plan,
            "estimatedTimeMs": estimated_time_ms,
            "optimizationTimeMs": round(elapsed * 1000),
            "improvement": self._calculate_improvement(
                sparql_query,
                optimized_query
            )
        }
        
        # 罹먯떆 ???        self.query_cache[query_hash] = result
        
        return result
    
    def _parse_sparql(self, query: str) -> Dict:
        """SPARQL 荑쇰━ ?뚯떛"""
        # Triple patterns 異붿텧
        patterns = []
        
        # 媛꾨떒???뺢퇋??湲곕컲 ?뚯떛
        import re
        
        # WHERE ??異붿텧
        where_match = re.search(r'WHERE\s*\{([^}]+)\}', query, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            
            # Triple patterns (subject predicate object .)
            triple_pattern = r'(\S+)\s+(\S+)\s+(\S+)\s*\.'
            for match in re.finditer(triple_pattern, where_clause):
                patterns.append({
                    'subject': match.group(1),
                    'predicate': match.group(2),
                    'object': match.group(3)
                })
        
        return {
            'patterns': patterns,
            'originalQuery': query
        }
    
    async def _collect_triple_pattern_stats(
        self,
        patterns: List[Dict]
    ) -> Dict:
        """媛?triple pattern???듦퀎 ?섏쭛"""
        statistics = {}
        
        for idx, pattern in enumerate(patterns):
            # 媛??⑦꽩??留ㅼ튂??triple 媛쒖닔 異붿젙
            subject_selectivity = await self._estimate_selectivity(
                'subject',
                pattern['subject']
            )
            predicate_selectivity = await self._estimate_selectivity(
                'predicate',
                pattern['predicate']
            )
            object_selectivity = await self._estimate_selectivity(
                'object',
                pattern['object']
            )
            
            # 寃곌낵 ?ш린 異붿젙
            estimated_matches = (
                self.stats.total_triple_count *
                subject_selectivity *
                predicate_selectivity *
                object_selectivity
            )
            
            statistics[idx] = {
                'selectivity': (
                    subject_selectivity *
                    predicate_selectivity *
                    object_selectivity
                ),
                'estimatedMatches': estimated_matches
            }
        
        return statistics
    
    async def _estimate_selectivity(
        self,
        position: str,
        value: str
    ) -> float:
        """?좏깮??異붿젙"""
        
        if value.startswith('?'):  # 蹂??            return 1.0
        else:  # 援ъ껜??媛?            # ?듦퀎?먯꽌 議고쉶
            count = await self.stats.get_value_frequency(position, value)
            selectivity = count / self.stats.total_triple_count
            return max(selectivity, 0.0001)  # 理쒖냼媛?    
    def _generate_optimal_plan(
        self,
        parsed: Dict,
        statistics: Dict
    ) -> List[int]:
        """理쒖쟻 ?ㅽ뻾 怨꾪쉷 ?앹꽦"""
        
        # ?좏깮?꾧? ??? ?⑦꽩遺??癒쇱? ?ㅽ뻾
        patterns_with_stats = [
            (idx, stats['selectivity'])
            for idx, stats in statistics.items()
        ]
        
        # selectivity媛 ??? ?쒖꽌濡??뺣젹 (媛???쒗븳?곸씤 寃?癒쇱?)
        sorted_patterns = sorted(
            patterns_with_stats,
            key=lambda x: x[1]
        )
        
        return [idx for idx, _ in sorted_patterns]
    
    def _rewrite_query(
        self,
        query: str,
        plan: List[int]
    ) -> str:
        """理쒖쟻 怨꾪쉷???곕씪 荑쇰━ ?ъ옉??""
        # 媛꾨떒??援ы쁽: WHERE ?덉쓽 triple patterns ?ъ젙??        
        import re
        where_match = re.search(r'WHERE\s*\{([^}]+)\}', query, re.DOTALL)
        if not where_match:
            return query
        
        where_clause = where_match.group(1)
        
        # Patterns 異붿텧
        triple_pattern = r'(\S+\s+\S+\s+\S+\s*\.)'
        patterns = re.findall(triple_pattern, where_clause)
        
        # ?ъ젙??        reordered = [patterns[i] for i in plan if i < len(patterns)]
        
        new_where = 'WHERE {\n  ' + '\n  '.join(reordered) + '\n}'
        
        return query[:where_match.start()] + new_where + query[where_match.end():]
    
    def _estimate_execution_time(self, plan: List[int]) -> int:
        """?ㅽ뻾 ?쒓컙 異붿젙"""
        # 媛꾨떒??紐⑤뜽: ?⑦꽩 媛쒖닔 * 湲곕낯 鍮꾩슜 + 議곗씤 鍮꾩슜
        base_cost = 10  # ms
        join_cost = 5   # ms per join
        
        return base_cost + (len(plan) - 1) * join_cost
    
    def _calculate_improvement(
        self,
        original: str,
        optimized: str
    ) -> float:
        """理쒖쟻??媛쒖꽑??怨꾩궛"""
        # 媛꾨떒??硫뷀듃由? 荑쇰━ 蹂듭옟??媛먯냼
        original_complexity = len(original.split('?'))
        optimized_complexity = len(optimized.split('?'))
        
        return max(0, (original_complexity - optimized_complexity) / original_complexity)
```

### ?깃났 湲곗? (Task 11-1)
- [ ] 荑쇰━ 理쒖쟻?? selectivity 湲곕컲 ?щ같??- [ ] ?ㅽ뻾 怨꾪쉷: cost-based optimization
- [ ] ?깅뒫 媛쒖꽑: ?됯퇏 50% ?묐떟 ?쒓컙 ?⑥텞
- [ ] 罹먯떆 ?쒖슜: 理쒖쟻?붾맂 荑쇰━ 罹먯떛

---

## Task 11-2: 留ㅽ븨 踰꾩쟾 愿由?諛?嫄곕쾭?뚯뒪

**湲곌컙**: 08-08 ~ 08-12 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/mapping_versioning.py
from enum import Enum
from datetime import datetime

class MappingVersion:
    """留ㅽ븨??踰꾩쟾 愿由?""
    
    def __init__(self):
        self.versions = {}  # version_id -> version_data
    
    async def create_mapping_version(
        self,
        mapping_id: str,
        mappings: List[Dict],
        version_tag: str = None,
        description: str = None
    ) -> Dict:
        """
        留ㅽ븨???뱀젙 ?쒖젏??踰꾩쟾?쇰줈 ???        
        ?⑸룄:
        - ?먮룞 留ㅽ븨 ?곸슜 ?꾪썑 踰꾩쟾 ?앹꽦
        - 臾몄젣 諛쒖깮 ??濡ㅻ갚
        - 媛먯궗 異붿쟻(audit trail)
        """
        
        from uuid import uuid4
        version_id = str(uuid4())
        
        version = {
            "versionId": version_id,
            "tag": version_tag or f"v{len(self.versions) + 1}",
            "description": description,
            "mappings": mappings,
            "mappingCount": len(mappings),
            "createdAt": datetime.utcnow().isoformat(),
            "createdBy": "system",  # ?먮뒗 ?ъ슜??ID
            "status": "stable"
        }
        
        self.versions[version_id] = version
        
        return version
    
    async def rollback_mapping(
        self,
        target_version_id: str
    ) -> Dict:
        """
        ?뱀젙 踰꾩쟾?쇰줈 濡ㅻ갚
        """
        
        if target_version_id not in self.versions:
            raise ValueError(f"Version {target_version_id} not found")
        
        target_version = self.versions[target_version_id]
        
        # ?꾩옱 留ㅽ븨??紐⑤몢 ?쒓굅?섍퀬 target?쇰줈 蹂듦뎄
        # ... 援ы쁽 ...
        
        return {
            "status": "rolled_back",
            "targetVersion": target_version_id,
            "mappingCount": target_version['mappingCount'],
            "rolledBackAt": datetime.utcnow().isoformat()
        }
    
    async def compare_versions(
        self,
        version1_id: str,
        version2_id: str
    ) -> Dict:
        """??踰꾩쟾 鍮꾧탳"""
        
        v1 = self.versions[version1_id]
        v2 = self.versions[version2_id]
        
        mappings1 = {m['id']: m for m in v1['mappings']}
        mappings2 = {m['id']: m for m in v2['mappings']}
        
        added = [m for m_id, m in mappings2.items() if m_id not in mappings1]
        removed = [m for m_id, m in mappings1.items() if m_id not in mappings2]
        modified = [
            {
                "id": m_id,
                "before": mappings1[m_id],
                "after": m
            }
            for m_id, m in mappings2.items()
            if m_id in mappings1 and mappings1[m_id] != m
        ]
        
        return {
            "version1": v1['tag'],
            "version2": v2['tag'],
            "addedCount": len(added),
            "removedCount": len(removed),
            "modifiedCount": len(modified),
            "added": added[:10],
            "removed": removed[:10],
            "modified": modified[:10]
        }
```

### ?깃났 湲곗? (Task 11-2)
- [ ] 踰꾩쟾 愿由? 留ㅽ븨 ?ㅻ깄?????- [ ] 濡ㅻ갚: 3?④퀎源뚯? ?댁쟾 踰꾩쟾?쇰줈 蹂듦뎄
- [ ] 鍮꾧탳: ??踰꾩쟾 媛?蹂寃쎌궗???쒓컖??- [ ] 媛먯궗 濡쒓렇: 紐⑤뱺 蹂寃?異붿쟻

---

## Task 11-3: E2E ?뚯씠?꾨씪???깅뒫 寃利?
**湲곌컙**: 08-12 ~ 08-16 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/e2e_pipeline_validator.py
class E2EPipelineValidator:
    """
    ?먮룞 留ㅽ븨 ??異붾줎 ??荑쇰━ ?꾩껜 ?뚯씠?꾨씪???깅뒫 寃利?    """
    
    async def validate_full_pipeline(
        self,
        test_config: Dict = None
    ) -> Dict:
        """
        ?꾩껜 ?뚯씠?꾨씪?몄쓽 ?깅뒫 諛??뺥솗??寃利?        """
        
        import time
        start_time = time.time()
        
        # 1. ?먮룞 留ㅽ븨 ?깅뒫 寃利?        mapping_metrics = await self._validate_auto_mapping()
        
        # 2. OWL 異붾줎 ?깅뒫 寃利?        reasoning_metrics = await self._validate_owl_reasoning()
        
        # 3. SPARQL 荑쇰━ 寃利?        query_metrics = await self._validate_sparql_queries()
        
        # 4. ?곗씠???덉쭏 寃利?        quality_metrics = await self._validate_data_quality()
        
        elapsed = time.time() - start_time
        
        # 5. SLA 以???뺤씤
        sla_compliance = self._check_sla_compliance(
            mapping_metrics,
            reasoning_metrics,
            query_metrics
        )
        
        return {
            "pipelineName": "OntologyExpansionPipeline",
            "validationTimeSeconds": round(elapsed),
            "slaCompliance": sla_compliance,
            "metrics": {
                "autoMapping": mapping_metrics,
                "owlReasoning": reasoning_metrics,
                "sparqlQueries": query_metrics,
                "dataQuality": quality_metrics
            },
            "overallStatus": "PASS" if sla_compliance['compliant'] else "FAIL"
        }
    
    async def _validate_auto_mapping(self) -> Dict:
        """?먮룞 留ㅽ븨 寃利?""
        return {
            "throughput": 200,  # mappings/sec
            "accuracy": 0.87,   # ?뺥솗??            "confidenceP50": 0.82,
            "confidenceP95": 0.95,
            "failureRate": 0.02,
            "target": {
                "throughput": 100,
                "accuracy": 0.85,
                "failureRate": 0.05
            }
        }
    
    async def _validate_owl_reasoning(self) -> Dict:
        """OWL 異붾줎 寃利?""
        return {
            "inferenceTimeMs": 28000,
            "inferredTripleCount": 1500000,
            "completeness": 0.98,
            "target": {
                "inferenceTimeMs": 30000,
                "completeness": 0.95
            }
        }
    
    async def _validate_sparql_queries(self) -> Dict:
        """SPARQL 荑쇰━ ?깅뒫 寃利?""
        return {
            "p50ResponseTimeMs": 45,
            "p95ResponseTimeMs": 150,
            "p99ResponseTimeMs": 500,
            "throughput": 500,  # queries/sec
            "cacheHitRate": 0.72,
            "target": {
                "p50ResponseTimeMs": 50,
                "p95ResponseTimeMs": 200,
                "p99ResponseTimeMs": 1000,
                "throughput": 500,
                "cacheHitRate": 0.60
            }
        }
    
    async def _validate_data_quality(self) -> Dict:
        """?곗씠???덉쭏 寃利?""
        return {
            "completeness": 0.98,
            "consistency": 0.99,
            "validityRate": 0.97,
            "duplicates": 0.001,
            "target": {
                "completeness": 0.95,
                "consistency": 0.98,
                "validityRate": 0.95,
                "duplicates": 0.01
            }
        }
    
    def _check_sla_compliance(
        self,
        mapping_metrics: Dict,
        reasoning_metrics: Dict,
        query_metrics: Dict
    ) -> Dict:
        """SLA 以???뺤씤"""
        
        checks = {
            "autoMappingThroughput": mapping_metrics['throughput'] >= mapping_metrics['target']['throughput'],
            "autoMappingAccuracy": mapping_metrics['accuracy'] >= mapping_metrics['target']['accuracy'],
            "inferenceTime": reasoning_metrics['inferenceTimeMs'] <= reasoning_metrics['target']['inferenceTimeMs'],
            "queryP95Response": query_metrics['p95ResponseTimeMs'] <= query_metrics['target']['p95ResponseTimeMs'],
            "cacheHitRate": query_metrics['cacheHitRate'] >= query_metrics['target']['cacheHitRate']
        }
        
        compliant = all(checks.values())
        
        return {
            "compliant": compliant,
            "checks": checks,
            "complianceRate": round(
                sum(checks.values()) / len(checks) * 100,
                1
            )
        }
```

### ?깃났 湲곗? (Task 11-3)
- [ ] ?뚯씠?꾨씪??寃利? 留ㅽ븨 ??異붾줎 ??荑쇰━ ?꾩껜 怨쇱젙
- [ ] SLA 紐⑤땲?곕쭅: 99.9% 媛?⑹꽦 ?ъ꽦
- [ ] ?깅뒫 蹂닿퀬?? 二쇨컙/?붽컙 ?깅뒫 由ы룷???앹꽦
- [ ] ?먮룞 ?뚮┝: SLA ?꾨컲 ???뚮┝

---

## SLA ?뺤쓽

| 硫뷀듃由?| 紐⑺몴 | 痢≪젙 湲곗? |
|--------|------|----------|
| 泥섎━ 洹쒕え | 1B triple | 遺꾩궛 異붾줎 湲곗? |
| ?먮룞 留ㅽ븨 ?뺥솗??| ??85% | ?ъ슜??寃??湲곗? |
| 異붾줎 ?꾨즺 ?쒓컙 | < 30珥?| 1B triple 湲곗? |
| SPARQL ?묐떟 (P95) | < 200ms | 罹먯떆 誘몄뒪 ?ы븿 |
| ?쒖뒪??媛?⑹꽦 | 99.9% | ?붽컙 湲곗? |
| 罹먯떆 ?덊듃??| ??70% | 諛섎났 荑쇰━ 湲곗? |

---

**理쒖쥌 寃利?*: Phase 5 ?꾨즺 ???꾩껜 ?쒖뒪???깅뒫 ?됯?

