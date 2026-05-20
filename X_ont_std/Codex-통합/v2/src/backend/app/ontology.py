from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .errors import AppError
from .models import OntologySchema, RelationshipCreate
from .validators import SchemaValidator


TYPE_MAP = {
    "string": str,
    "enum": str,
    "date": str,
    "datetime": str,
    "number": (int, float),
    "boolean": bool,
    "json": (dict, list),
    "list": list,
    "object_ref": str,
    "object_ref_list": list,
}

KOREAN_TYPE_HINTS = {
    "고객": "Customer",
    "거래처": "Customer",
    "주문": "Order",
    "오더": "Order",
    "상품": "Product",
    "제품": "Product",
}

KOREAN_PROPERTY_HINTS = {
    "지역": "region",
    "세그먼트": "segment",
    "등급": "risk_tier",
    "리스크": "risk_tier",
    "위험": "risk_tier",
    "계약": "contract_terms",
    "담당": "owner",
    "상태": "status",
    "금액": "amount",
    "가격": "unit_price",
    "카테고리": "category",
}


class OntologyStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[1] / "config"
        self.schema_path = self.base_dir / "ontology.default.json"
        self.data_path = self.base_dir / "data.default.json"
        self.schema = OntologySchema.model_validate_json(self.schema_path.read_text(encoding="utf-8"))
        self.validator = SchemaValidator(self.schema)
        self.data = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.validate_all()

    def validate_all(self) -> None:
        type_names = {item.name for item in self.schema.object_types}
        if len(type_names) != len(self.schema.object_types):
            raise AppError("INVALID_SCHEMA", "Object type names must be unique.", 500)
        for rel in self.schema.relationship_types:
            if rel.source_type not in type_names or rel.target_type not in type_names:
                raise AppError("INVALID_SCHEMA", f"Invalid relationship type: {rel.name}", 500)
        for type_def in self.schema.object_types:
            for object_id, values in self.data.get("objects", {}).get(type_def.name, {}).items():
                self._validate_object(type_def.name, object_id, values)
        for rel in self.data.get("relationships", []):
            self._validate_relationship(rel)

    def schema_dict(self) -> dict:
        return self.schema.model_dump()

    def overview(self) -> dict:
        objects = self.data.get("objects", {})
        return {
            "object_type_count": len(self.schema.object_types),
            "relationship_type_count": len(self.schema.relationship_types),
            "action_type_count": len(self.schema.action_types),
            "object_count": sum(len(rows) for rows in objects.values()),
            "relationship_count": len(self.data.get("relationships", [])),
        }

    def object_types(self) -> list[dict]:
        return [item.model_dump() for item in self.schema.object_types]

    def relationship_types(self) -> list[dict]:
        return [item.model_dump() for item in self.schema.relationship_types]

    def action_types(self) -> list[dict]:
        return [item.model_dump() for item in self.schema.action_types]

    def list_objects(self, type_name: str | None = None) -> list[dict]:
        rows: list[dict] = []
        objects = self.data.get("objects", {})
        for current_type, typed_objects in objects.items():
            if type_name and current_type != type_name:
                continue
            for object_id, values in typed_objects.items():
                rows.append({"id": object_id, "type": current_type, **values})
        return rows

    def get_object(self, object_id: str) -> dict:
        found = self._find_object(object_id)
        if found is None:
            raise AppError("OBJECT_NOT_FOUND", f"Object not found: {object_id}", 404)
        type_name, values = found
        return {"id": object_id, "type": type_name, **values}

    def list_relationships(self, type_name: str | None = None) -> list[dict]:
        relationships = self.data.get("relationships", [])
        if type_name:
            return [rel for rel in relationships if rel["type"] == type_name]
        return list(relationships)

    def add_relationship(self, body: RelationshipCreate) -> dict:
        payload = {
            "id": f"REL-{uuid.uuid4().hex[:8]}",
            "type": body.type,
            "source_id": body.source_id,
            "target_id": body.target_id,
            "properties": body.properties,
        }
        self._validate_relationship(payload)
        self.data.setdefault("relationships", []).append(payload)
        return payload

    def object_context(self, object_id: str) -> dict:
        obj = self.get_object(object_id)
        incoming = []
        outgoing = []
        for rel in self.data.get("relationships", []):
            rel_type = self._relationship_type(rel["type"])
            if rel["source_id"] == object_id:
                outgoing.append({
                    "relationship": rel["type"],
                    "display_name": rel_type.get("display_name"),
                    "target": self.get_object(rel["target_id"]),
                    "properties": rel.get("properties", {}),
                })
            if rel["target_id"] == object_id:
                incoming.append({
                    "relationship": rel["type"],
                    "display_name": rel_type.get("reverse_display_name") or rel_type.get("display_name"),
                    "source": self.get_object(rel["source_id"]),
                    "properties": rel.get("properties", {}),
                })
        documents = [
            doc for doc in self.data.get("documents", [])
            if obj["type"] in doc.get("related_objects", [])
        ]
        actions = [
            action.model_dump() for action in self.schema.action_types
            if action.target_type == obj["type"]
        ]
        return {
            "object": obj,
            "incoming": incoming,
            "outgoing": outgoing,
            "documents": documents,
            "available_actions": actions,
        }

    def ask(self, question: str, object_id: str | None = None) -> dict:
        detected_id = object_id or self._extract_object_id(question)
        if detected_id is None:
            raise AppError("OBJECT_NOT_FOUND", "No object id was found in the question.", 404)
        context = self.object_context(detected_id)
        evidence = self.search(question, top_k=3)
        action_names = [item["name"] for item in context["available_actions"]]
        answer = (
            f"Object {context['object']['id']} ({context['object']['type']}) was found. "
            f"It has {len(context['incoming'])} incoming and {len(context['outgoing'])} outgoing relationships. "
            f"Available actions: {', '.join(action_names) if action_names else 'none'}. "
            f"Evidence documents: {', '.join(item['title'] for item in evidence)}."
        )
        return {
            "question": question,
            "detected_object_id": detected_id,
            "answer": answer,
            "ontology_context": context,
            "evidence": evidence,
            "trace": [
                "extract_object_id",
                "load_object_context",
                "collect_relationships",
                "search_documents",
                "compose_answer",
            ],
        }

    def hybrid_ask(self, question: str, object_id: str | None = None, top_k: int = 3) -> dict:
        """온톨로지 구조 질의와 문서 검색 근거를 결합한다.

        LLM 없이 실행 가능한 query plan을 만든 뒤, 필터/비교/계산은 온톨로지에서
        결정적으로 처리하고 문서 검색 결과는 RAG evidence로 붙인다.
        """
        plan = self._build_query_plan(question, object_id)
        self.validator.validate_query_plan(plan)
        evidence = self.search(question, top_k=top_k)
        structured = {"headers": [], "rows": []}
        ontology_nodes: list[str] = []
        contexts: list[dict] = []

        if plan["type"] == "object_context":
            context = self.object_context(plan["object_id"])
            contexts = [context]
            ontology_nodes = self._context_node_ids(context)
            structured = self._context_table(context)
        elif plan["type"] == "compare":
            objects = [self.get_object(object_id) for object_id in plan["object_ids"]]
            ontology_nodes = [obj["id"] for obj in objects]
            structured = self._objects_table(objects)
        elif plan["type"] == "calculate":
            objects = self._filter_objects(plan["entity_type"], plan["filters"])
            ontology_nodes = [obj["id"] for obj in objects]
            structured = self._calculate_table(objects, plan["metric"], plan["operation"])
        else:
            objects = self._filter_objects(plan["entity_type"], plan["filters"])
            ontology_nodes = [obj["id"] for obj in objects]
            structured = self._objects_table(objects)

        answer = self._compose_hybrid_answer(question, plan, structured, evidence, ontology_nodes)
        return {
            "question": question,
            "query_type": plan["type"],
            "plan": plan,
            "answer": answer,
            "structured_data": structured,
            "ontology_nodes": ontology_nodes,
            "ontology_contexts": contexts,
            "vector_evidence": evidence,
            "trace": [
                "build_query_plan",
                "execute_ontology_query",
                "search_documents",
                "merge_structured_and_rag_evidence",
                "compose_answer",
            ],
        }

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        terms = {t.lower() for t in re.findall(r"[A-Za-z0-9가-힣]+", query)}
        scored = []
        for doc in self.data.get("documents", []):
            haystack = f"{doc['title']} {doc['text']} {' '.join(doc.get('related_objects', []))}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append({**doc, "score": score})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def _build_query_plan(self, question: str, object_id: str | None = None) -> dict:
        explicit_id = object_id or self._extract_object_id(question)
        ids = self._extract_object_ids(question)
        if explicit_id:
            ids = [explicit_id] + [item for item in ids if item != explicit_id]
        if "비교" in question and len(ids) >= 2:
            return {"type": "compare", "object_ids": ids}
        if explicit_id:
            return {"type": "object_context", "object_id": explicit_id}

        entity_type = self._infer_entity_type(question)
        filters = self._infer_filters(question, entity_type)
        if self._looks_like_calculation(question):
            return {
                "type": "calculate",
                "entity_type": entity_type,
                "filters": filters,
                "metric": self._infer_metric(question, entity_type),
                "operation": self._infer_operation(question),
            }
        return {"type": "filter", "entity_type": entity_type, "filters": filters}

    def _filter_objects(self, type_name: str, filters: list[dict]) -> list[dict]:
        rows = self.list_objects(type_name)
        if not filters:
            return rows
        result = []
        for obj in rows:
            if all(self._matches_filter(obj, item) for item in filters):
                result.append(obj)
        return result

    def _matches_filter(self, obj: dict, filter_def: dict) -> bool:
        value = obj.get(filter_def["property"])
        expected = filter_def["value"]
        op = filter_def.get("op", "contains")
        if value is None:
            return False
        if op in {"gt", "gte", "lt", "lte"}:
            try:
                left = float(value)
                right = float(expected)
            except (TypeError, ValueError):
                return False
            if op == "gt":
                return left > right
            if op == "gte":
                return left >= right
            if op == "lt":
                return left < right
            return left <= right
        return str(expected).lower() in str(value).lower()

    def _objects_table(self, objects: list[dict]) -> dict:
        if not objects:
            return {"headers": ["결과"], "rows": [["조건에 맞는 객체가 없습니다."]]}
        keys = ["id", "type"]
        for obj in objects:
            for key in obj:
                if key not in keys:
                    keys.append(key)
        return {
            "headers": keys,
            "rows": [[self._cell(obj.get(key, "")) for key in keys] for obj in objects],
        }

    def _context_table(self, context: dict) -> dict:
        rows = []
        for item in context["incoming"]:
            rows.append(["incoming", item["relationship"], item["source"]["id"], context["object"]["id"]])
        for item in context["outgoing"]:
            rows.append(["outgoing", item["relationship"], context["object"]["id"], item["target"]["id"]])
        if not rows:
            rows.append(["-", "관계 없음", context["object"]["id"], "-"])
        return {"headers": ["방향", "관계", "출발", "도착"], "rows": rows}

    def _calculate_table(self, objects: list[dict], metric: str, operation: str) -> dict:
        values = [float(obj[metric]) for obj in objects if isinstance(obj.get(metric), (int, float))]
        if not values:
            result = "계산 가능한 값 없음"
        elif operation == "avg":
            result = round(sum(values) / len(values), 2)
        elif operation == "max":
            result = max(values)
        elif operation == "min":
            result = min(values)
        else:
            result = sum(values)
        return {
            "headers": ["operation", "metric", "count", "result"],
            "rows": [[operation, metric, str(len(values)), self._cell(result)]],
        }

    def _compose_hybrid_answer(
        self,
        question: str,
        plan: dict,
        structured: dict,
        evidence: list[dict],
        ontology_nodes: list[str],
    ) -> str:
        row_count = len(structured.get("rows", []))
        evidence_titles = ", ".join(item["title"] for item in evidence) or "없음"
        if plan["type"] == "object_context":
            target = plan["object_id"]
            prefix = f"{target}의 온톨로지 관계 컨텍스트를 조회했습니다."
        elif plan["type"] == "calculate":
            prefix = f"{plan['entity_type']}의 {plan['metric']} 값을 {plan['operation']} 방식으로 계산했습니다."
        else:
            prefix = f"{plan.get('entity_type', '객체')} 기준으로 구조형 조건을 적용했습니다."
        return (
            f"{prefix} 구조형 결과 {row_count}건과 문서 근거 {len(evidence)}건을 함께 사용했습니다. "
            f"관련 온톨로지 노드: {', '.join(ontology_nodes) if ontology_nodes else '없음'}. "
            f"참조 문서: {evidence_titles}. 질문: {question}"
        )

    def _infer_entity_type(self, question: str) -> str:
        for hint, type_name in KOREAN_TYPE_HINTS.items():
            if hint in question:
                return type_name
        for type_def in self.schema.object_types:
            if type_def.name.lower() in question.lower() or (type_def.display_name and type_def.display_name in question):
                return type_def.name
        return "Order" if self._looks_like_calculation(question) else "Customer"

    def _infer_filters(self, question: str, type_name: str) -> list[dict]:
        filters: list[dict] = []
        type_def = self._object_type(type_name)
        for prop in type_def["properties"]:
            name = prop["name"]
            values = prop.get("values") or []
            for value in values:
                if value.lower() in question.lower():
                    filters.append({"property": name, "op": "contains", "value": value})
            if name in {"region", "status", "category"}:
                value = self._value_after_hint(question, name)
                if value:
                    filters.append({"property": name, "op": "contains", "value": value})

        for korean, prop in KOREAN_PROPERTY_HINTS.items():
            if korean in question and prop in {item["name"] for item in type_def["properties"]}:
                prop_def = next((item for item in type_def["properties"] if item["name"] == prop), {})
                if prop_def.get("type") == "number":
                    continue
                value = self._value_after_hint(question, korean)
                if value and not re.fullmatch(r"\d+", value):
                    filters.append({"property": prop, "op": "contains", "value": value})

        amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(이상|초과|이하|미만)", question)
        if amount_match:
            metric = self._infer_metric(question, type_name)
            op_map = {"이상": "gte", "초과": "gt", "이하": "lte", "미만": "lt"}
            filters.append({"property": metric, "op": op_map[amount_match.group(2)], "value": amount_match.group(1)})

        return self._dedupe_filters(filters)

    def _infer_metric(self, question: str, type_name: str) -> str:
        type_def = self._object_type(type_name)
        number_props = [prop["name"] for prop in type_def["properties"] if prop["type"] == "number"]
        if "가격" in question and "unit_price" in number_props:
            return "unit_price"
        if "금액" in question and "amount" in number_props:
            return "amount"
        return number_props[0] if number_props else "amount"

    @staticmethod
    def _infer_operation(question: str) -> str:
        if any(term in question for term in ("평균", "avg", "average")):
            return "avg"
        if any(term in question for term in ("최대", "가장 큰", "max")):
            return "max"
        if any(term in question for term in ("최소", "가장 작은", "min")):
            return "min"
        return "sum"

    @staticmethod
    def _looks_like_calculation(question: str) -> bool:
        return any(term in question for term in ("합계", "총", "평균", "최대", "최소", "계산", "sum", "avg"))

    @staticmethod
    def _value_after_hint(question: str, hint: str) -> str | None:
        match = re.search(rf"{re.escape(hint)}\s*(?:이|가|은|는|:)?\s*([A-Za-z0-9가-힣_-]+)", question)
        if not match:
            return None
        value = match.group(1)
        stopwords = {"고객", "주문", "상품", "제품", "목록", "리스트", "알려줘", "보여줘"}
        return None if value in stopwords else value

    @staticmethod
    def _dedupe_filters(filters: list[dict]) -> list[dict]:
        seen = set()
        deduped = []
        for item in filters:
            key = (item["property"], item.get("op", "contains"), str(item["value"]).lower())
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    @staticmethod
    def _extract_object_ids(question: str) -> list[str]:
        seen = []
        for match in re.findall(r"\b[COPr]\d{3}\b", question, flags=re.IGNORECASE):
            value = match.upper()
            if value not in seen:
                seen.append(value)
        return seen

    @staticmethod
    def _context_node_ids(context: dict) -> list[str]:
        ids = [context["object"]["id"]]
        ids.extend(item["source"]["id"] for item in context["incoming"])
        ids.extend(item["target"]["id"] for item in context["outgoing"])
        return list(dict.fromkeys(ids))

    @staticmethod
    def _cell(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _object_type(self, type_name: str) -> dict:
        for item in self.schema.object_types:
            if item.name == type_name:
                return item.model_dump()
        raise AppError("TYPE_NOT_FOUND", f"Object type not found: {type_name}", 404)

    def _relationship_type(self, type_name: str) -> dict:
        for item in self.schema.relationship_types:
            if item.name == type_name:
                return item.model_dump()
        raise AppError("TYPE_NOT_FOUND", f"Relationship type not found: {type_name}", 404)

    def _find_object(self, object_id: str) -> tuple[str, dict] | None:
        for type_name, typed_objects in self.data.get("objects", {}).items():
            if object_id in typed_objects:
                return type_name, typed_objects[object_id]
        return None

    def _validate_object(self, type_name: str, object_id: str, values: dict) -> None:
        type_def = self._object_type(type_name)
        for prop in type_def["properties"]:
            name = prop["name"]
            if prop.get("required") and name not in values:
                raise AppError("INVALID_OBJECT", f"{object_id} is missing required property {name}", 500)
            if name in values:
                expected = TYPE_MAP.get(prop["type"])
                if expected and not isinstance(values[name], expected):
                    raise AppError("INVALID_OBJECT", f"{object_id}.{name} has invalid type", 500)

    def _validate_relationship(self, rel: dict) -> None:
        rel_type = self._relationship_type(rel["type"])
        source = self._find_object(rel["source_id"])
        target = self._find_object(rel["target_id"])
        if source is None or target is None:
            raise AppError("INVALID_RELATIONSHIP", "Relationship source or target does not exist.", 400)
        if source[0] != rel_type["source_type"] or target[0] != rel_type["target_type"]:
            raise AppError("INVALID_RELATIONSHIP", "Relationship source or target type mismatch.", 400)

    @staticmethod
    def _extract_object_id(question: str) -> str | None:
        match = re.search(r"\b[COPr]\d{3}\b", question, flags=re.IGNORECASE)
        return match.group(0).upper() if match else None
