# Phase 5 Week 11-12: ?ㅼ떆媛??ㅽ듃由щ컢 & ?먮룞 ?쒕떇
## Antigravity (Performance) ?섑뻾 吏?쒖꽌

**湲곌컙**: 2026-08-05 ~ 2026-08-16 (2二?  
**?좊떦**: 90% (二쇰떦 27-30?쒓컙)  
**紐⑺몴**: ?ㅼ떆媛??ㅽ듃由?泥섎━ (1000+ updates/sec), ?먮룞 ?깅뒫 ?쒕떇, 99.9% SLA

---

## 媛쒖슂

?꾨줈?뺤뀡 ?섍꼍?먯꽌??**諛곗튂 泥섎━?먯꽌 ?ㅽ듃由?泥섎━濡??꾪솚**?댁빞 ?⑸땲?? 留ㅽ븨, 異붾줎, 荑쇰━ 理쒖쟻?붽? ?ㅼ떆媛꾩쑝濡?諛쒖깮?섎ŉ, ?쒖뒪?쒖? ?먮룞?쇰줈 ?깅뒫???쒕떇?댁빞 ?⑸땲??

### Week 11-12??3媛吏 ?듭떖 湲곕뒫

1. **Kafka ?ㅽ듃由?泥섎━** (Task 11-1): ?ㅼ떆媛?留ㅽ븨 ?낅뜲?댄듃 泥섎━
2. **?먮룞 罹먯떆 臾댄슚??* (Task 11-2): 100ms ?대궡 罹먯떆 臾댄슚??3. **AI 湲곕컲 ?먮룞 ?쒕떇** (Task 11-3): 荑쇰━ 理쒖쟻???쒖븞, ?몃뜳???먮룞 ?앹꽦

---

## Task 11-1: Kafka ?ㅽ듃由?泥섎━ ?뚯씠?꾨씪??
**湲곌컙**: 08-05 ~ 08-08 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/kafka_stream_processor.py
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import json
import asyncio
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class KafkaStreamProcessor:
    """
    ?ㅼ떆媛?留ㅽ븨 ?낅뜲?댄듃瑜?Kafka瑜??듯빐 泥섎━
    
    ?꾪궎?띿쿂:
    - Source: mapping-updates ?좏뵿 (?몃? ?쒖뒪?쒖뿉??諛쒗뻾)
    - Processing: 留ㅽ븨 寃利???異붾줎 ?곸슜 ??罹먯떆 臾댄슚??    - Sink: mapping-processed ?좏뵿 (寃곌낵 諛쒗뻾)
    
    ?깅뒫:
    - 泥섎━?? 1000+ updates/sec
    - 吏?곗떆媛? < 100ms (P95)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.consumer = KafkaConsumer(
            'mapping-updates',
            bootstrap_servers=config['kafka_brokers'],
            group_id='ontology-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_records=100,  # 諛곗튂 ?ш린
            session_timeout_ms=30000
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=config['kafka_brokers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # 紐⑤뱺 蹂듭젣蹂??뺤씤
            retries=3
        )
        
        self.stats = {
            'processed': 0,
            'failed': 0,
            'throughput': 0
        }
    
    async def start_stream_processing(self):
        """?ㅽ듃由?泥섎━ ?쒖옉"""
        
        logger.info("Starting Kafka stream processor...")
        
        import time
        last_stats_time = time.time()
        
        for message_batch in self.consumer:
            batch_start = time.time()
            
            # 諛곗튂 泥섎━
            processed_messages = []
            failed_messages = []
            
            for message in message_batch:
                try:
                    result = await self._process_mapping_update(message.value)
                    processed_messages.append(result)
                    self.stats['processed'] += 1
                except Exception as e:
                    failed_messages.append({
                        'error': str(e),
                        'mapping': message.value
                    })
                    self.stats['failed'] += 1
                    logger.error(f"Failed to process mapping: {e}")
            
            # 寃곌낵瑜?sink ?좏뵿??諛쒗뻾
            if processed_messages:
                await self._emit_to_sink(processed_messages)
            
            # ?듦퀎 ?낅뜲?댄듃
            batch_time = time.time() - batch_start
            current_time = time.time()
            
            if current_time - last_stats_time > 10:  # 10珥덈쭏??                self.stats['throughput'] = (
                    self.stats['processed'] / (current_time - last_stats_time)
                )
                logger.info(
                    f"Processed: {self.stats['processed']}, "
                    f"Failed: {self.stats['failed']}, "
                    f"Throughput: {self.stats['throughput']:.1f} events/sec"
                )
                last_stats_time = current_time
    
    async def _process_mapping_update(self, update: Dict) -> Dict:
        """
        ?⑥씪 留ㅽ븨 ?낅뜲?댄듃 泥섎━
        
        ?ㅽ뀦:
        1. 寃利?(< 10ms)
        2. 異붾줎 ?곸슜 (< 50ms)
        3. 罹먯떆 臾댄슚??(< 10ms)
        4. 寃곌낵 諛섑솚 (< 100ms 珥앺빀)
        """
        
        import time
        start_time = time.time()
        
        # 1. 寃利?        validation = self._validate_mapping(update)
        if not validation['valid']:
            raise ValueError(f"Invalid mapping: {validation['error']}")
        
        # 2. 異붾줎 ?곸슜
        inferences = await self._apply_inference_to_update(update)
        
        # 3. 罹먯떆 臾댄슚??        invalidated_keys = await self._invalidate_affected_cache(
            update,
            inferences
        )
        
        # 4. 寃곌낵 諛섑솚
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'mappingId': update['id'],
            'status': 'processed',
            'inferences': len(inferences),
            'cacheKeysInvalidated': invalidated_keys,
            'processingTimeMs': round(processing_time),
            'timestamp': time.time()
        }
    
    def _validate_mapping(self, mapping: Dict) -> Dict:
        """留ㅽ븨 寃利?""
        required_fields = ['externalUri', 'internalUri', 'relationshipType']
        
        for field in required_fields:
            if field not in mapping:
                return {'valid': False, 'error': f"Missing field: {field}"}
        
        return {'valid': True}
    
    async def _apply_inference_to_update(self, update: Dict) -> List:
        """留ㅽ븨 ?낅뜲?댄듃?????異붾줎 ?곸슜"""
        
        inferences = []
        
        # ??留ㅽ븨怨?愿?⑤맂 異붾줎 洹쒖튃 ?곸슜
        external_uri = update['externalUri']
        internal_uri = update['internalUri']
        
        # 1. sameAs transitivity ?뺤씤
        same_as_inferences = await self._find_sameas_transitive_closure(
            external_uri,
            internal_uri
        )
        inferences.extend(same_as_inferences)
        
        # 2. subClass transitivity ?뺤씤
        subclass_inferences = await self._find_subclass_transitive_closure(
            external_uri,
            internal_uri
        )
        inferences.extend(subclass_inferences)
        
        return inferences
    
    async def _invalidate_affected_cache(
        self,
        update: Dict,
        inferences: List
    ) -> int:
        """?곹뼢諛쏅뒗 罹먯떆 臾댄슚??(< 100ms)"""
        
        cache_keys = set()
        
        # ?낅뜲?댄듃??留ㅽ븨 愿??罹먯떆
        cache_keys.add(f"mapping:{update['externalUri']}")
        cache_keys.add(f"mapping:{update['internalUri']}")
        
        # 異붾줎?쇰줈 ?곹뼢諛쏅뒗 媛쒕뀗
        for inference in inferences:
            cache_keys.add(f"neighborhood:{inference['subject']}")
            cache_keys.add(f"neighborhood:{inference['object']}")
        
        # Redis?먯꽌 蹂묐젹濡?臾댄슚??        import asyncio
        await asyncio.gather(*[
            self.cache.delete(key)
            for key in cache_keys
        ])
        
        return len(cache_keys)
    
    async def _emit_to_sink(self, results: List[Dict]):
        """泥섎━??寃곌낵瑜?sink ?좏뵿??諛쒗뻾"""
        
        for result in results:
            self.producer.send(
                'mapping-processed',
                value=result,
                callback=self._on_send_success,
                errback=self._on_send_error
            )
    
    def _on_send_success(self, record_metadata):
        logger.debug(f"Message sent to {record_metadata.topic}")
    
    def _on_send_error(self, exc):
        logger.error(f"Failed to send message: {exc}")
```

### ?깃났 湲곗? (Task 11-1)
- [ ] ?ㅽ듃由?泥섎━: Kafka濡??ㅼ떆媛??대깽??泥섎━
- [ ] 泥섎━?? 1000+ mappings/sec ?ъ꽦
- [ ] 吏?곗떆媛? P95 < 100ms
- [ ] ?덉젙?? 硫붿떆吏 ?먯떎 ?놁쓬 (acks='all')

---

## Task 11-2: ?ㅼ떆媛?罹먯떆 臾댄슚??
**湲곌컙**: 08-08 ~ 08-12 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/realtime_cache_invalidation.py
import asyncio
from typing import Set, List
import time

class RealtimeCacheInvalidationService:
    """
    ?ㅽ듃由?泥섎━ 以?100ms ?대궡??罹먯떆 臾댄슚??    """
    
    def __init__(self, redis_client, invalidation_queue_size: int = 10000):
        self.redis = redis_client
        self.invalidation_queue = asyncio.Queue(maxsize=invalidation_queue_size)
        self.batch_size = 100
        self.batch_timeout_ms = 50  # 50ms留덈떎 諛곗튂 泥섎━
    
    async def start_invalidation_worker(self):
        """罹먯떆 臾댄슚???뚯빱 ?쒖옉"""
        
        while True:
            batch = []
            batch_start = time.time()
            
            try:
                # 諛곗튂 ?섏쭛 (??꾩븘???덉쓬)
                while len(batch) < self.batch_size:
                    try:
                        item = await asyncio.wait_for(
                            self.invalidation_queue.get(),
                            timeout=self.batch_timeout_ms / 1000
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                if not batch:
                    continue
                
                # 諛곗튂 蹂묐젹 臾댄슚??                await self._invalidate_batch(batch)
                
                elapsed = (time.time() - batch_start) * 1000
                
            except Exception as e:
                logger.error(f"Error in cache invalidation: {e}")
    
    async def _invalidate_batch(self, batch: List[str]) -> int:
        """
        諛곗튂 罹먯떆 ??臾댄슚??(蹂묐젹)
        """
        
        # ?⑦꽩蹂꾨줈 洹몃９??        pattern_groups = self._group_by_pattern(batch)
        
        # 蹂묐젹 ??젣
        tasks = [
            self._delete_by_pattern(pattern, keys)
            for pattern, keys in pattern_groups.items()
        ]
        
        results = await asyncio.gather(*tasks)
        return sum(results)
    
    async def _delete_by_pattern(self, pattern: str, keys: List[str]) -> int:
        """?⑦꽩??留욌뒗 ?ㅻ뱾 ??젣"""
        
        if pattern == 'exact':
            # ?뺥솗???? DEL ?ъ슜
            await self.redis.delete(*keys)
            return len(keys)
        else:
            # ?⑦꽩: SCAN + DEL
            deleted = 0
            cursor = 0
            
            while True:
                cursor, scan_keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if scan_keys:
                    await self.redis.delete(*scan_keys)
                    deleted += len(scan_keys)
                
                if cursor == 0:
                    break
            
            return deleted
    
    def _group_by_pattern(self, keys: List[str]) -> dict:
        """罹먯떆 ?ㅻ? ?⑦꽩蹂꾨줈 洹몃９??""
        
        groups = {
            'exact': [],
            'neighborhood:*': [],
            'mapping:*': [],
            'sparql_result:*': []
        }
        
        for key in keys:
            if 'neighborhood' in key:
                groups['neighborhood:*'].append(key)
            elif 'mapping' in key:
                groups['mapping:*'].append(key)
            elif 'sparql' in key:
                groups['sparql_result:*'].append(key)
            else:
                groups['exact'].append(key)
        
        return {k: v for k, v in groups.items() if v}
    
    async def schedule_invalidation(self, keys: Set[str]):
        """罹먯떆 臾댄슚???ㅼ?以?""
        
        for key in keys:
            try:
                await asyncio.wait_for(
                    self.invalidation_queue.put(key),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Invalidation queue full, dropping key: {key}")
```

### ?깃났 湲곗? (Task 11-2)
- [ ] 諛곗튂 臾댄슚?? 100媛???蹂묐젹 泥섎━
- [ ] ?묐떟 ?쒓컙: < 100ms (P95)
- [ ] ?ㅻ（?? 10K+ keys/sec
- [ ] ?뺥솗?? ?⑦꽩 湲곕컲 ?뺥솗??留ㅼ묶

---

## Task 11-3: AI 湲곕컲 ?먮룞 ?쒕떇

**湲곌컙**: 08-12 ~ 08-16 (2??

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/auto_tuning_engine.py
from typing import Dict, List
import numpy as np

class AutoTuningEngine:
    """
    ?쒖뒪??硫뷀듃由?쓣 遺꾩꽍?섏뿬 ?먮룞?쇰줈 理쒖쟻???쒖븞
    """
    
    def __init__(self, metrics_service, optimization_service):
        self.metrics = metrics_service
        self.optimizer = optimization_service
    
    async def analyze_and_recommend(self) -> Dict:
        """
        ?쒖뒪???깅뒫??遺꾩꽍?섍퀬 理쒖쟻???쒖븞
        """
        
        # 1. ?꾩옱 硫뷀듃由??섏쭛
        current_metrics = await self.metrics.get_latest_metrics(
            window_minutes=60
        )
        
        # 2. ?깅뒫 蹂묐ぉ ?앸퀎
        bottlenecks = self._identify_bottlenecks(current_metrics)
        
        # 3. 理쒖쟻???쒖븞 ?앹꽦
        recommendations = []
        for bottleneck in bottlenecks:
            rec = await self._generate_recommendation(bottleneck)
            recommendations.append(rec)
        
        return {
            "recommendations": recommendations,
            "priority": sorted(
                recommendations,
                key=lambda r: r['impact'],
                reverse=True
            )[:5],  # ?곸쐞 5媛?            "analyzedAt": datetime.utcnow().isoformat()
        }
    
    def _identify_bottlenecks(self, metrics: Dict) -> List[str]:
        """蹂묐ぉ ?앸퀎"""
        
        bottlenecks = []
        
        # 1. 荑쇰━ ?묐떟 ?쒓컙???믪쑝硫??몃뜳??異붽? ?쒖븞
        if metrics['query_p95_ms'] > 200:
            bottlenecks.append('slow_queries')
        
        # 2. 罹먯떆 ?덊듃?⑥씠 ??쑝硫?罹먯떆 ?ш린 利앷? ?쒖븞
        if metrics['cache_hit_rate'] < 0.6:
            bottlenecks.append('low_cache_hit_rate')
        
        # 3. CPU ?ъ슜瑜좎씠 ?믪쑝硫?蹂묐젹??議곗젙
        if metrics['cpu_usage'] > 80:
            bottlenecks.append('high_cpu_usage')
        
        # 4. 硫붾え由?遺議깊븯硫??뚰떚????媛먯냼
        if metrics['memory_usage'] > 85:
            bottlenecks.append('memory_pressure')
        
        return bottlenecks
    
    async def _generate_recommendation(
        self,
        bottleneck: str
    ) -> Dict:
        """理쒖쟻???쒖븞 ?앹꽦"""
        
        if bottleneck == 'slow_queries':
            # ?먮┛ 荑쇰━ 遺꾩꽍 諛??몃뜳???쒖븞
            slow_queries = await self.metrics.get_slow_queries(limit=10)
            
            # 媛?荑쇰━?먯꽌 ?묎렐?섎뒗 ?띿꽦 遺꾩꽍
            index_candidates = self._analyze_index_candidates(slow_queries)
            
            return {
                "type": "index_creation",
                "bottleneck": "slow_queries",
                "indices": index_candidates,
                "expectedImprovement": "30-50% faster queries",
                "impact": 0.9,
                "automatable": True
            }
        
        elif bottleneck == 'low_cache_hit_rate':
            # 罹먯떆 ?ш린 利앷? ?쒖븞
            current_cache_size = await self.metrics.get_cache_size()
            
            return {
                "type": "cache_resizing",
                "bottleneck": "low_cache_hit_rate",
                "currentSizeGb": current_cache_size / 1e9,
                "recommendedSizeGb": (current_cache_size * 1.5) / 1e9,
                "expectedImprovement": "cache hit rate +20%",
                "impact": 0.7,
                "automatable": True
            }
        
        elif bottleneck == 'high_cpu_usage':
            # 蹂묐젹??議곗젙
            current_parallelism = await self.metrics.get_parallelism()
            
            return {
                "type": "parallelism_adjustment",
                "bottleneck": "high_cpu_usage",
                "currentParallelism": current_parallelism,
                "recommendedParallelism": max(1, current_parallelism - 2),
                "expectedImprovement": "reduced CPU contention",
                "impact": 0.6,
                "automatable": False  # ?섎룞 ?뱀씤 ?꾩슂
            }
        
        return {}
    
    async def apply_auto_recommendations(self):
        """?먮룞 理쒖쟻???곸슜 (?섎룞 ?뱀씤 遺덊븘??"""
        
        recommendations = await self.analyze_and_recommend()
        
        for rec in recommendations['priority']:
            if rec['automatable']:
                try:
                    await self._apply_recommendation(rec)
                    logger.info(f"Applied recommendation: {rec['type']}")
                except Exception as e:
                    logger.error(f"Failed to apply recommendation: {e}")
    
    async def _apply_recommendation(self, recommendation: Dict):
        """?쒖븞 ?곸슜"""
        
        if recommendation['type'] == 'index_creation':
            for index in recommendation['indices']:
                await self.optimizer.create_index(index)
        
        elif recommendation['type'] == 'cache_resizing':
            new_size = recommendation['recommendedSizeGb'] * 1e9
            await self.optimizer.resize_cache(new_size)
```

### ?깃났 湲곗? (Task 11-3)
- [ ] 蹂묐ぉ ?앸퀎: 6媛吏 二쇱슂 ?깅뒫 ?댁뒋 媛먯?
- [ ] ?쒖븞 ?앹꽦: 援ъ껜?곸씤 理쒖쟻???쒖븞
- [ ] ?먮룞 ?곸슜: ?뱀씤 遺덊븘?뷀븳 ?쒖븞 ?먮룞 ?곸슜
- [ ] ?깅뒫 媛쒖꽑: ?됯퇏 30-50% 媛쒖꽑 ?ъ꽦

---

## SLA 紐⑺몴 諛??ъ꽦 湲곗?

| 硫뷀듃由?| Phase 4 | Phase 5 紐⑺몴 | ?ъ꽦 湲곗? |
|--------|---------|-------------|---------|
| 留ㅽ븨 ?뺥솗??| 80% | ??85% | ?ъ슜??寃??湲곗? |
| 泥섎━ 洹쒕え | 1M triple | 1B triple | 遺꾩궛 異붾줎 ?꾨즺 |
| 異붾줎 ?꾨즺 ?쒓컙 | - | < 30珥?| 1B triple 湲곗? |
| SPARQL P95 ?묐떟 | < 100ms | < 200ms | 罹먯떆 誘몄뒪 ?ы븿 |
| ?ㅼ떆媛?泥섎━ | 諛곗튂 | 1000+ updates/sec | Kafka ?ㅽ듃由?|
| ?쒖뒪??媛?⑹꽦 | 99% | 99.9% | ?붽컙 湲곗? |
| 罹먯떆 ?덊듃??| 60% | ??70% | 諛섎났 荑쇰━ 湲곗? |

---

## 理쒖쥌 寃利?泥댄겕由ъ뒪??
- [ ] ?ㅽ듃由?泥섎━: Kafka ?뚯씠?꾨씪???덉젙??- [ ] 罹먯떆 臾댄슚?? 100ms ?대궡 ?묐떟 ?ъ꽦
- [ ] ?먮룞 ?쒕떇: 二쇱슂 蹂묐ぉ ?먮룞 理쒖쟻??- [ ] SLA 紐⑤땲?곕쭅: 99.9% 媛?⑹꽦 ?ъ꽦
- [ ] ?댁쁺 ?덉젙?? 臾댁쨷??諛고룷 媛??- [ ] 臾몄꽌?? ?댁쁺 媛?대뱶 ?묒꽦
- [ ] 援먯쑁: ?댁쁺? 援먯쑁 ?꾨즺

---

**Phase 5 理쒖쥌 紐⑺몴**: ?꾨줈?뺤뀡湲??⑦넧濡쒖? ?뺤옣 ?뚮옯???꾩꽦

