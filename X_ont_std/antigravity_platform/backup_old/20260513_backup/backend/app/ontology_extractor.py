import json
import logging
import os
from typing import List, Dict, Any

from google import genai
from .engine import OntologyEngine, ObjectInstance

logger = logging.getLogger(__name__)

class OntologyExtractor:
    def __init__(self, engine: OntologyEngine):
        self.engine = engine
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY1")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def _build_prompt(self, text: str) -> str:
        # 엔진의 스키마 정보를 프롬프트에 동적으로 주입
        object_types = [
            f"- {ot.id}: {ot.display_name} (Properties: {[p.name for p in ot.properties]})"
            for ot in self.engine.schema.object_types
        ]
        rel_types = [
            f"- {rt.id}: {rt.display_name} ({rt.source_type} -> {rt.target_type})"
            for rt in self.engine.schema.relationship_types
        ]

        return f"""You are an ontology extraction expert. 
Extract entities and relationships from the text below based on the provided schema.

## Allowed Object Types
{"\n".join(object_types)}

## Allowed Relationship Types
{"\n".join(rel_types)}

## Extraction Rules
1. Only extract information explicitly mentioned in the text.
2. Use the provided IDs for types.
3. Return the result in STRICT JSON format.
4. If a property is not found, omit it.

## Output Format
{{
  "objects": [
    {{ "id": "unique_id", "type": "TYPE_ID", "values": {{ "prop1": "val1" }} }}
  ],
  "relationships": [
    {{ "type": "REL_TYPE_ID", "source_id": "src_id", "target_id": "tgt_id" }}
  ]
}}

## Text to Process
{text[:15000]}
"""

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(text)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        try:
            data = json.loads(raw_text)
            
            # 엔진에 자동 등록
            for obj_data in data.get("objects", []):
                try:
                    obj = ObjectInstance(**obj_data)
                    self.engine.register_object(obj)
                except Exception as e:
                    logger.warning(f"Failed to register object: {e}")
                    
            for rel_data in data.get("relationships", []):
                try:
                    self.engine.link(
                        rel_data["type"], 
                        rel_data["source_id"], 
                        rel_data["target_id"],
                        rel_data.get("values")
                    )
                except Exception as e:
                    logger.warning(f"Failed to link relationship: {e}")
                    
            return data
        except Exception as e:
            logger.error(f"Failed to parse extraction result: {e}")
            return {"objects": [], "relationships": [], "error": str(e)}
