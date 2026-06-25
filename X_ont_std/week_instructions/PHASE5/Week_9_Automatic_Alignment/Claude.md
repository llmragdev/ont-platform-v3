# Phase 5 Week 9: ?먮룞 ?뺣젹 ?붿쭊 (諛깆뿏??
## Claude (Backend) ?섑뻾 吏?쒖꽌

**湲곌컙**: 2026-07-22 ~ 2026-07-26 (5??  
**?좊떦**: 80% (二쇰떦 24-30?쒓컙)  
**紐⑺몴**: LLM 湲곕컲 ?먮룞 留ㅽ븨 異붿쿇 ?붿쭊 援ы쁽 諛??좊ː???ㅼ퐫?대쭅

---

## 媛쒖슂

Phase 4?먯꽌 援ъ텞???⑦넧濡쒖? 留ㅽ븨 湲곕뒫??湲곕컲?쇰줈, **Claude API瑜??쒖슜???먮룞 留ㅽ븨 異붿쿇 ?붿쭊**??援ы쁽?⑸땲?? ?몃? ?⑦넧濡쒖???媛쒕뀗(concept)???대? ?꾨찓??紐⑤뜽怨??먮룞?쇰줈 留ㅽ븨?섍퀬, 媛?留ㅽ븨??????좊ː???먯닔? 洹쇨굅瑜??쒓났?⑸땲??

### Week 9??3媛吏 ?듭떖 湲곕뒫

1. **LLM 湲곕컲 留ㅽ븨 異붿쿇** (Task 9-1): Claude API瑜??쒖슜???섎? 湲곕컲 媛쒕뀗 留ㅽ븨
2. **?좊ː???ㅼ퐫?대쭅** (Task 9-2): ?ㅼ쨷 ?좊ː??吏??label similarity, embedding, LLM confidence) 湲곕컲 醫낇빀 ?먯닔
3. **留ㅽ븨 罹먯떛 & 理쒖쟻??* (Task 9-3): LLM API ?몄텧 理쒖냼?? ?꾨쿋??踰≫꽣 ??? 諛곗튂 泥섎━

---

## ?뵩 ?섍꼍 ?ㅼ젙 (?꾩닔)

```bash
# Conda ?섍꼍 ?쒖꽦??conda activate claud_be

# ?묒뾽 ?붾젆?좊━
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# ?섏〈???ㅼ튂
pip install openai anthropic sentence-transformers redis

# 媛쒕컻 ?쒕쾭 ?쒖옉
uvicorn main:app --reload --port 8001

# ?뚯뒪??pytest tests/phase5/week9_auto_mapping_test.py -v
```

---

## Task 9-1: LLM 湲곕컲 留ㅽ븨 異붿쿇 ?붿쭊

**湲곌컙**: 07-22 ~ 07-23 (1.5??

### 紐⑺몴

Claude API瑜??쒖슜?섏뿬 ?몃? ?⑦넧濡쒖? 媛쒕뀗???대? ?뷀떚?곗? ?먮룞?쇰줈 留ㅽ븨

### 援ы쁽 ??ぉ

#### 1) ?먮룞 留ㅽ븨 異붿쿇 API

```python
# src/backend/app/services/auto_mapping_service.py
from anthropic import Anthropic
from typing import List, Dict, Tuple
import json

class AutomaticMappingService:
    def __init__(self, cache_client=None):
        self.client = Anthropic()
        self.cache = cache_client
        self.model = "claude-3-5-sonnet-20241022"
        
    async def recommend_mappings(
        self,
        external_uri: str,
        external_label: str,
        external_description: str,
        internal_entities: List[Dict],
        relationship_types: List[str] = None
    ) -> List[Dict]:
        """
        ?몃? 媛쒕뀗??????대? ?뷀떚??留ㅽ븨 異붿쿇
        
        Args:
            external_uri: ?몃? 媛쒕뀗 URI (e.g., http://dbpedia.org/ontology/Company)
            external_label: ?몃? 媛쒕뀗 ?덉씠釉?(e.g., "Company")
            external_description: ?몃? 媛쒕뀗 ?ㅻ챸
            internal_entities: ?대? ?뷀떚??由ъ뒪??                [{
                    "id": "entity_id",
                    "label": "Entity Label",
                    "description": "Entity description",
                    "type": "organization"
                }, ...]
            relationship_types: 媛?ν븳 愿怨????                [skos:exactMatch, skos:closeMatch, skos:broader, ...]
        
        Returns:
            List of mapping recommendations:
            [{
                "suggestedInternalId": "entity_id",
                "suggestedInternalLabel": "Entity Label",
                "relationshipType": "skos:exactMatch",
                "confidence": 0.95,
                "evidence": ["?뺥솗???쇰꺼 留ㅼ묶", "?ㅻ챸 ?섎? ?쇱튂"],
                "alternatives": [...]
            }, ...]
        """
        
        # 罹먯떆 ?뺤씤
        cache_key = f"auto_mapping:{external_uri}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # ?대? ?뷀떚??而⑦뀓?ㅽ듃 援ъ꽦
        entities_context = "\n".join([
            f"- {e['label']} (ID: {e['id']}, Type: {e.get('type', 'unknown')})"
            f"\n  Description: {e.get('description', 'N/A')}"
            for e in internal_entities[:10]  # ?곸쐞 10媛쒕쭔
        ])
        
        # 留ㅽ븨 愿怨??ㅻ챸
        relationship_guide = """
        - skos:exactMatch: ?뺥솗???숈씪??媛쒕뀗
        - skos:closeMatch: 留ㅼ슦 ?좎궗?섏?留??쎄컙??李⑥씠 ?덉쓬
        - skos:broader: ?몃? 媛쒕뀗???대? 媛쒕뀗蹂대떎 ???볦? 踰붿＜
        - skos:narrower: ?몃? 媛쒕뀗???대? 媛쒕뀗蹂대떎 ??醫곸? 踰붿＜
        - rdfs:subClassOf: ?몃? 媛쒕뀗???대? 媛쒕뀗??遺遺?        - owl:sameAs: ?⑦넧濡쒖??곸쑝濡??숈씪??媛쒕뀗
        """
        
        prompt = f"""?뱀떊? ?⑦넧濡쒖? 留ㅽ븨 ?꾨Ц媛?낅땲??
        
?ㅼ쓬 ?몃? ?⑦넧濡쒖? 媛쒕뀗???대? ?꾨찓??紐⑤뜽 ?뷀떚?곗? 留ㅽ븨?댁＜?몄슂.

=== ?몃? 媛쒕뀗 ===
URI: {external_uri}
?쇰꺼: {external_label}
?ㅻ챸: {external_description}

=== ?대? ?뷀떚???꾨낫 ===
{entities_context}

=== 留ㅽ븨 愿怨????===
{relationship_guide}

=== ?묒뾽 ===
媛???곸젅???대? ?뷀떚?곕? 理쒕? 3媛쒓퉴吏 ?좏깮?섍퀬, 媛곴컖?????
1. 異붿쿇 ?댁쑀 (理쒖냼 3媛吏 洹쇨굅)
2. ?좊ː???먯닔 (0.0 ~ 1.0)
3. 異붿쿇?섎뒗 愿怨????
JSON ?뺤떇?쇰줈 ?ㅼ쓬怨?媛숈씠 ?묐떟?섏꽭??
{{
  "recommendations": [
    {{
      "internalId": "entity_id",
      "internalLabel": "Entity Label",
      "relationshipType": "skos:exactMatch",
      "confidence": 0.95,
      "evidence": ["洹쇨굅1", "洹쇨굅2", "洹쇨굅3"],
      "reasoning": "?곸꽭 ?ㅻ챸"
    }},
    ...
  ]
}}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # ?묐떟 ?뚯떛
        result_text = response.content[0].text
        try:
            # JSON 異붿텧 (留덊겕?ㅼ슫 肄붾뱶釉붾줉 泥섎━)
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0]
            else:
                json_str = result_text
            
            result = json.loads(json_str)
            recommendations = result.get("recommendations", [])
        except (json.JSONDecodeError, IndexError):
            recommendations = []
        
        # 罹먯떆 ???(24?쒓컙)
        if self.cache:
            await self.cache.setex(
                cache_key,
                86400,
                json.dumps(recommendations)
            )
        
        return recommendations
    
    async def recommend_batch_mappings(
        self,
        external_graph: List[Dict],
        internal_entities: List[Dict]
    ) -> List[Dict]:
        """
        ??됱쓽 ?몃? 媛쒕뀗???쇨큵 留ㅽ븨
        諛곗튂 泥섎━濡?LLM API ?몄텧 理쒖냼??        """
        results = []
        
        # ?좎궗??湲곕컲 ?ъ쟾 ?꾪꽣留?(LLM ?몄텧 ??
        filtered_candidates = await self._filter_candidates_by_similarity(
            external_graph,
            internal_entities
        )
        
        # 媛??몃? 媛쒕뀗?????異붿쿇 ?앹꽦
        for external_concept in external_graph:
            candidates = filtered_candidates.get(
                external_concept['uri'],
                internal_entities[:10]
            )
            
            recommendations = await self.recommend_mappings(
                external_uri=external_concept['uri'],
                external_label=external_concept['label'],
                external_description=external_concept.get('description', ''),
                internal_entities=candidates
            )
            
            results.append({
                "externalUri": external_concept['uri'],
                "externalLabel": external_concept['label'],
                "recommendations": recommendations
            })
        
        return results
    
    async def _filter_candidates_by_similarity(
        self,
        external_graph: List[Dict],
        internal_entities: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        ?꾨쿋??湲곕컲 ?좎궗???ъ쟾 ?꾪꽣留?        """
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # ?꾨쿋??怨꾩궛
        external_embeddings = {}
        for concept in external_graph:
            text = f"{concept['label']} {concept.get('description', '')}"
            external_embeddings[concept['uri']] = model.encode(text)
        
        internal_embeddings = {}
        for entity in internal_entities:
            text = f"{entity['label']} {entity.get('description', '')}"
            internal_embeddings[entity['id']] = model.encode(text)
        
        # ?좎궗??湲곕컲 ?꾪꽣留?(top-5)
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        filtered_candidates = {}
        for ext_uri, ext_emb in external_embeddings.items():
            similarities = []
            for int_id, int_emb in internal_embeddings.items():
                sim = cosine_similarity(
                    [ext_emb],
                    [int_emb]
                )[0][0]
                similarities.append((int_id, sim))
            
            # top-5 ?좏깮
            top_candidates = sorted(
                similarities,
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            filtered_candidates[ext_uri] = [
                next(e for e in internal_entities if e['id'] == int_id)
                for int_id, _ in top_candidates
            ]
        
        return filtered_candidates
```

#### 2) 留ㅽ븨 異붿쿇 API ?붾뱶?ъ씤??
```python
# src/backend/app/api/v1/endpoints/auto_mapping.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/api/ontology", tags=["auto-mapping"])

@router.post("/auto-mappings/recommend", response_model=List[Dict])
async def recommend_mappings(
    request: RecommendMappingRequest,
    db: AsyncSession = Depends(get_db),
    mapping_service: AutomaticMappingService = Depends(get_auto_mapping_service)
):
    """
    ?몃? 媛쒕뀗?????留ㅽ븨 異붿쿇 ?앹꽦
    
    Request:
    {
        "externalUri": "http://dbpedia.org/ontology/Company",
        "externalLabel": "Company",
        "externalDescription": "A company is an organized group...",
        "importJobId": "job_123"
    }
    """
    # ?대? ?뷀떚??濡쒕뱶
    internal_entities = await db.execute(
        select(Entity).limit(50)
    )
    
    recommendations = await mapping_service.recommend_mappings(
        external_uri=request.externalUri,
        external_label=request.externalLabel,
        external_description=request.externalDescription,
        internal_entities=[e.to_dict() for e in internal_entities.scalars()]
    )
    
    return recommendations


@router.get("/auto-mappings/{import_job_id}")
async def get_auto_mappings(
    import_job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    import job??????먮룞 留ㅽ븨 異붿쿇 紐⑸줉 議고쉶
    """
    # DB?먯꽌 auto_mappings ?뚯씠釉?議고쉶
    mappings = await db.execute(
        select(AutoMapping).where(
            AutoMapping.import_job_id == import_job_id
        ).order_by(AutoMapping.confidence.desc())
    )
    
    results = []
    for mapping in mappings.scalars():
        results.append({
            "id": mapping.id,
            "externalUri": mapping.external_uri,
            "externalLabel": mapping.external_label,
            "suggestedInternalId": mapping.internal_entity_id,
            "suggestedInternalLabel": mapping.internal_label,
            "relationshipType": mapping.relationship_type,
            "confidence": mapping.confidence,
            "evidence": mapping.evidence,  # JSON
            "status": mapping.status,
            "alternatives": mapping.alternatives  # JSON
        })
    
    return {
        "importJobId": import_job_id,
        "mappings": results,
        "total": len(results),
        "approved": len([m for m in results if m["status"] == "approved"]),
        "rejected": len([m for m in results if m["status"] == "rejected"]),
        "pending": len([m for m in results if m["status"] == "pending"])
    }


@router.post("/mappings/{mapping_id}/approve")
async def approve_mapping(
    mapping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """?ъ슜?먭? 留ㅽ븨???뱀씤"""
    mapping = await db.get(AutoMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    mapping.status = "approved"
    db.add(mapping)
    await db.commit()
    
    return {"status": "approved", "mappingId": mapping_id}


@router.post("/mappings/{mapping_id}/reject")
async def reject_mapping(
    mapping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """?ъ슜?먭? 留ㅽ븨??嫄곗젅"""
    mapping = await db.get(AutoMapping, mapping_id)
    mapping.status = "rejected"
    db.add(mapping)
    await db.commit()
    
    return {"status": "rejected", "mappingId": mapping_id}


@router.post("/mappings/{mapping_id}/mark-review")
async def mark_for_review(
    mapping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """留ㅽ븨???섎룞 寃????곸쑝濡??쒖떆"""
    mapping = await db.get(AutoMapping, mapping_id)
    mapping.status = "manual_review"
    db.add(mapping)
    await db.commit()
    
    return {"status": "manual_review", "mappingId": mapping_id}
```

### ?깃났 湲곗? (Task 9-1)
- [ ] Claude API ?듯빀: ?섎? 湲곕컲 媛쒕뀗 留ㅽ븨 援ы쁽
- [ ] 留ㅽ븨 異붿쿇: ?곸쐞 3媛??꾨낫 + ?좊ː??+ 洹쇨굅 諛섑솚
- [ ] API ?붾뱶?ъ씤?? POST /api/ontology/auto-mappings/recommend
- [ ] ?묐떟 ?뺤떇: externalUri, suggestedInternalId, confidence, evidence

---

## Task 9-2: ?좊ː???ㅼ퐫?대쭅 諛??ㅼ쨷 硫뷀듃由?
**湲곌컙**: 07-23 ~ 07-24 (1.5??

### 紐⑺몴

LLM ?좊ː?? ?쇰꺼 ?좎궗?? ?꾨쿋???좎궗?꾨? 醫낇빀?섏뿬 理쒖쥌 ?좊ː???먯닔 ?곗텧

### 援ы쁽 ??ぉ

```python
# src/backend/app/services/confidence_scoring.py
import numpy as np
from typing import Dict, List, Tuple

class ConfidenceScoringEngine:
    
    async def calculate_composite_confidence(
        self,
        llm_confidence: float,
        label_similarity: float,
        embedding_similarity: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        ?ㅼ쨷 ?좊ː??吏?쒕? 醫낇빀?섏뿬 理쒖쥌 ?먯닔 怨꾩궛
        
        Args:
            llm_confidence: Claude API媛 ?쒖떆???좊ː??(0~1)
            label_similarity: ?쇰꺼 臾몄옄???좎궗??(0~1)
            embedding_similarity: ?꾨쿋??踰≫꽣 肄붿궗???좎궗??(0~1)
            weights: 媛?吏?쒖쓽 媛以묒튂 (湲곕낯: 0.5, 0.25, 0.25)
        
        Returns:
            理쒖쥌 ?좊ː???먯닔 (0~1)
        """
        if weights is None:
            weights = {
                "llm": 0.5,
                "label": 0.25,
                "embedding": 0.25
            }
        
        # ?뺢퇋??        normalized_llm = max(0.0, min(1.0, llm_confidence))
        normalized_label = max(0.0, min(1.0, label_similarity))
        normalized_embedding = max(0.0, min(1.0, embedding_similarity))
        
        # 媛以??됯퇏
        composite = (
            weights["llm"] * normalized_llm +
            weights["label"] * normalized_label +
            weights["embedding"] * normalized_embedding
        )
        
        return round(composite, 3)
    
    def calculate_label_similarity(
        self,
        label1: str,
        label2: str
    ) -> float:
        """
        ?쇰꺼 媛?臾몄옄???좎궗??(Jaro-Winkler)
        """
        from textblob import TextBlob
        
        sim = TextBlob(label1.lower()).similarity(
            TextBlob(label2.lower())
        )
        return float(sim) if sim else 0.0
    
    async def calculate_embedding_similarity(
        self,
        text1: str,
        text2: str,
        model_name: str = 'all-MiniLM-L6-v2'
    ) -> float:
        """
        ?꾨쿋??踰≫꽣 肄붿궗???좎궗??        """
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        model = SentenceTransformer(model_name)
        
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)
        
        sim = cosine_similarity([emb1], [emb2])[0][0]
        return float(sim)
    
    async def generate_evidence_summary(
        self,
        llm_evidence: List[str],
        label_sim: float,
        embedding_sim: float
    ) -> List[str]:
        """
        ?щ윭 ?좊ː??吏?쒕줈遺??醫낇빀 洹쇨굅 ?앹꽦
        """
        evidence = []
        
        # LLM 洹쇨굅 異붽?
        evidence.extend(llm_evidence[:2])  # ?곸쐞 2媛?        
        # ?쇰꺼 ?좎궗??洹쇨굅
        if label_sim > 0.9:
            evidence.append("?쇰꺼??嫄곗쓽 ?쇱튂??)
        elif label_sim > 0.7:
            evidence.append("?쇰꺼???좎궗??)
        
        # ?꾨쿋???좎궗??洹쇨굅
        if embedding_sim > 0.8:
            evidence.append("?섎? 踰≫꽣 怨듦컙?먯꽌 ?좎궗")
        
        return evidence[:3]  # ?곸쐞 3媛쒕쭔
```

### ?깃났 湲곗? (Task 9-2)
- [ ] 蹂듯빀 ?좊ː?? LLM + ?쇰꺼 + ?꾨쿋??媛以??됯퇏
- [ ] ?쇰꺼 ?좎궗?? Jaro-Winkler ?뚭퀬由ъ쬁
- [ ] ?꾨쿋???좎궗?? 肄붿궗???좎궗??- [ ] 洹쇨굅 ?앹꽦: ?좊ː??吏?쒕퀎 洹쇨굅 ?붿빟

---

## Task 9-3: 罹먯떛 & 諛곗튂 理쒖쟻??
**湲곌컙**: 07-24 ~ 07-26 (2??

### 紐⑺몴

LLM API ?몄텧 理쒖냼?? ?꾨쿋??踰≫꽣 ??? 諛곗튂 泥섎━濡??깅뒫 理쒖쟻??
### 援ы쁽 ??ぉ

#### 1) 留ㅽ븨 罹먯떆 ?덉씠??
```python
# src/backend/app/services/mapping_cache.py
import redis.asyncio as redis
import json
from typing import Optional, List, Dict

class MappingCacheLayer:
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 86400  # 24?쒓컙
    
    async def get_cached_mapping(
        self,
        external_uri: str,
        internal_id: str
    ) -> Optional[Dict]:
        """留ㅽ븨 罹먯떆 議고쉶"""
        cache_key = f"mapping:{external_uri}:{internal_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_mapping(
        self,
        external_uri: str,
        internal_id: str,
        mapping_data: Dict
    ):
        """留ㅽ븨 寃곌낵 罹먯떆"""
        cache_key = f"mapping:{external_uri}:{internal_id}"
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(mapping_data)
        )
    
    async def get_cached_embeddings(
        self,
        text: str,
        model: str = 'all-MiniLM-L6-v2'
    ) -> Optional[List[float]]:
        """?꾨쿋??踰≫꽣 罹먯떆 議고쉶"""
        cache_key = f"embedding:{model}:{text}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_embeddings(
        self,
        text: str,
        embeddings: List[float],
        model: str = 'all-MiniLM-L6-v2'
    ):
        """?꾨쿋??踰≫꽣 罹먯떆"""
        cache_key = f"embedding:{model}:{text}"
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(embeddings)
        )
```

#### 2) 諛곗튂 泥섎━ 理쒖쟻??
```python
# src/backend/app/services/batch_mapping_processor.py
from asyncio import gather
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BatchMappingProcessor:
    
    def __init__(
        self,
        auto_mapping_service,
        cache_layer,
        batch_size: int = 10
    ):
        self.service = auto_mapping_service
        self.cache = cache_layer
        self.batch_size = batch_size
    
    async def process_batch_mappings(
        self,
        external_graph: List[Dict],
        internal_entities: List[Dict]
    ) -> Dict:
        """
        ??됱쓽 ?몃? 媛쒕뀗??諛곗튂濡?留ㅽ븨 泥섎━
        
        理쒖쟻??
        1. 罹먯떆 ?덊듃 ?뺤씤
        2. ?좎궗???ъ쟾 ?꾪꽣留?        3. 諛곗튂 ?⑥쐞濡?LLM ?몄텧
        4. 寃곌낵 罹먯떆
        """
        results = []
        cache_hits = 0
        llm_calls = 0
        
        # 諛곗튂 ?⑥쐞濡?泥섎━
        for i in range(0, len(external_graph), self.batch_size):
            batch = external_graph[i:i+self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1} ({len(batch)} concepts)")
            
            batch_results = await gather(
                *[
                    self._process_single_mapping(
                        concept,
                        internal_entities
                    )
                    for concept in batch
                ]
            )
            
            for result in batch_results:
                results.append(result)
                if result.get("from_cache"):
                    cache_hits += 1
                else:
                    llm_calls += 1
        
        return {
            "total": len(external_graph),
            "results": results,
            "cacheHits": cache_hits,
            "llmCalls": llm_calls,
            "cacheHitRate": round(cache_hits / len(external_graph), 2)
        }
    
    async def _process_single_mapping(
        self,
        concept: Dict,
        internal_entities: List[Dict]
    ) -> Dict:
        """?⑥씪 媛쒕뀗 留ㅽ븨 泥섎━"""
        
        # 罹먯떆 ?뺤씤
        cached = await self.cache.get_cached_mapping(
            concept['uri'],
            "batch"
        )
        if cached:
            cached['from_cache'] = True
            return cached
        
        # LLM ?몄텧
        recommendations = await self.service.recommend_mappings(
            external_uri=concept['uri'],
            external_label=concept['label'],
            external_description=concept.get('description', ''),
            internal_entities=internal_entities
        )
        
        result = {
            "externalUri": concept['uri'],
            "externalLabel": concept['label'],
            "recommendations": recommendations,
            "from_cache": False
        }
        
        # 罹먯떆 ???        await self.cache.cache_mapping(
            concept['uri'],
            "batch",
            result
        )
        
        return result
```

### ?깃났 湲곗? (Task 9-3)
- [ ] Redis 罹먯떆: 留ㅽ븨 寃곌낵 諛??꾨쿋??踰≫꽣 罹먯떛
- [ ] 諛곗튂 泥섎━: ???留ㅽ븨??諛곗튂 ?⑥쐞濡?蹂묐젹 泥섎━
- [ ] 罹먯떆 ?덊듃?? ??60% (諛섎났 留ㅽ븨)
- [ ] LLM API ?몄텧 理쒖냼?? 諛곗튂 ??1~2???몄텧

---

## ?곗씠?곕쿋?댁뒪 ?ㅽ궎留?(?꾩닔)

```sql
-- auto_mappings ?뚯씠釉?(?좉퇋)
CREATE TABLE auto_mappings (
    id VARCHAR(36) PRIMARY KEY,
    import_job_id VARCHAR(36) NOT NULL,
    external_uri VARCHAR(500) NOT NULL,
    external_label VARCHAR(255) NOT NULL,
    internal_entity_id VARCHAR(36) NOT NULL,
    internal_label VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100),
    confidence FLOAT NOT NULL,
    evidence JSONB,  -- ["洹쇨굅1", "洹쇨굅2", ...]
    alternatives JSONB,  -- ???留ㅽ븨
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, manual_review
    llm_model VARCHAR(100),  -- ?ъ슜??LLM 紐⑤뜽紐?    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_job_id) REFERENCES import_jobs(id),
    FOREIGN KEY (internal_entity_id) REFERENCES entities(id),
    INDEX idx_import_job (import_job_id),
    INDEX idx_status (status),
    INDEX idx_confidence (confidence)
);

-- embedding_cache ?뚯씠釉?CREATE TABLE embedding_cache (
    id VARCHAR(36) PRIMARY KEY,
    text_hash VARCHAR(64) NOT NULL UNIQUE,
    text TEXT NOT NULL,
    model_name VARCHAR(100),
    embedding_vector VECTOR(384),  -- pgvector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name)
);
```

---

## ?깃났 吏??
| 吏??| 紐⑺몴 | ?됯? 湲곗? |
|------|------|----------|
| 留ㅽ븨 ?뺥솗??| ??85% | ?ъ슜??寃??湲곗? |
| ?좊ː???먯닔 ??묒꽦 | 0.9+ ??95%+ ?뱀씤??| ?좊ː?꾨퀎 ?뱀씤??|
| LLM API ?⑥쑉??| 諛곗튂??< 2???몄텧 | 罹먯떆 ?덊듃????60% |
| ?묐떟 ?쒓컙 | < 5珥?(諛곗튂 10媛? | P95 ?묐떟 ?쒓컙 |
| 罹먯떆 硫붾え由?| < 500MB | Redis 硫붾え由??ъ슜??|

---

## ?뚯뒪??泥댄겕由ъ뒪??
```bash
# Unit Tests
pytest tests/phase5/week9_auto_mapping_test.py -v

# ?뚯뒪??耳?댁뒪
- test_recommend_mappings_single_concept
- test_recommend_mappings_batch_processing
- test_confidence_score_calculation
- test_cache_hit_rate
- test_embedding_similarity
- test_api_response_format
- test_error_handling_invalid_json
```

---

## 二쇱쓽?ы빆

### LLM Hallucination 由ъ뒪??- ?좊ː?꾧? ??? 留ㅽ븨(< 0.7)? ?먮룞 ?뱀씤?섏? ?딆쓬
- ?ъ슜??寃???④퀎 ?꾩닔
- ?좊ː???먯닔??洹쇨굅(evidence) ??긽 ?쒖떆

### API 鍮꾩슜 愿由?- 諛곗튂 泥섎━濡??몄텧 ?잛닔 理쒖냼??- 罹먯떆 TTL ?곸젅???ㅼ젙 (24?쒓컙)
- ?꾨쿋?⑹? 濡쒖뺄 紐⑤뜽 ?ъ슜 (API 鍮꾩슜 ?덇컧)

### ?깅뒫 理쒖쟻??- ?꾨쿋??踰≫꽣 ?ъ쟾 怨꾩궛 諛?罹먯떛
- ?洹쒕え dataset? streaming 泥섎━
- Redis ?곌껐 ? ?ш린 理쒖쟻??
---

**?ㅼ쓬 ?④퀎**: Task 9-2 ?좊ː???ㅼ퐫?대쭅 ??Task 9-3 罹먯떛 理쒖쟻???쒖쑝濡?吏꾪뻾

