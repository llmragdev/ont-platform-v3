"""스킬 실행 엔진"""

import json
import requests
from typing import Any, Dict, Optional
import logging

from app.models.skill import Skill, SkillImplementation, MCPHttpConfig
from app.models.tenant_context import TenantContext
from app.services.expression_renderer import prepare_skill_input, validate_skill_schema
from app.services.ontology import OntologyService
from app.services.vector_search import VectorSearchService
from app.services.llm_client import LlmClient

logger = logging.getLogger(__name__)


class SkillExecutionError(Exception):
    """스킬 실행 오류"""
    pass


class SkillExecutor:
    """워크플로우 스킬 실행기"""

    def __init__(self, ctx: Optional[TenantContext] = None):
        self.ctx = ctx
        self.timeout_seconds = 30
        self.ontology_svc = OntologyService() if ctx else None
        self.vector_svc = VectorSearchService() if ctx else None
        self.llm_client = LlmClient() if ctx else None

    def execute(
        self,
        skill: Skill,
        input_data: Dict[str, Any],
        skill_config: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        스킬을 실행합니다.

        Args:
            skill: 스킬 정의
            input_data: 입력 데이터 (이미 렌더링된 것으로 가정)
            skill_config: 워크플로우 노드의 skillConfig
            execution_context: 워크플로우 실행 컨텍스트 (표현식 렌더링용)

        Returns:
            실행 결과 dict

        Raises:
            SkillExecutionError: 실행 중 오류 발생
        """
        try:
            impl = skill.implementation

            # 입력 데이터 렌더링 (skillConfig의 inputMapping 적용)
            if skill_config and execution_context:
                prepared_input = prepare_skill_input(skill_config, execution_context)
                # 기본 input_data와 merge
                input_data = {**input_data, **prepared_input}

            # 스키마 검증
            is_valid, error = validate_skill_schema(skill.inputSchema, input_data)
            if not is_valid:
                raise SkillExecutionError(f"Input validation failed: {error}")

            logger.info(f"Executing skill: {skill.id} with input: {input_data}")

            # 타입별 실행
            if impl.type == "builtin":
                return self._execute_builtin(skill, input_data)
            elif impl.type == "http":
                return self._execute_http(impl, input_data)
            elif impl.type == "mcp_http":
                return self._execute_mcp_http(impl, input_data)
            elif impl.type == "custom":
                raise SkillExecutionError("Custom code execution not available in Phase 1")
            else:
                raise SkillExecutionError(f"Unknown skill type: {impl.type}")

        except SkillExecutionError:
            raise
        except Exception as e:
            logger.error(f"Skill execution error: {e}", exc_info=True)
            raise SkillExecutionError(f"Execution failed: {str(e)}")

    def _execute_builtin(self, skill: Skill, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Built-in 스킬 실행 (온톨로지, RAG 등 내부 기능)

        Args:
            skill: 스킬 정의
            input_data: 입력 데이터

        Returns:
            실행 결과
        """
        skill_id = skill.id

        if skill_id == "ontology-write":
            return self._builtin_ontology_write(input_data)
        elif skill_id == "rag-ontology-lookup":
            return self._builtin_rag_lookup(input_data)
        elif skill_id == "fault-recurrence-check":
            return self._builtin_fault_recurrence_check(input_data)
        elif skill_id == "request-classify":
            return self._builtin_request_classify(input_data)
        else:
            raise SkillExecutionError(f"Unknown built-in skill: {skill_id}")

    def _builtin_ontology_write(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """온톨로지 저장"""
        try:
            entity_type = input_data.get("entityType", "Unknown")
            properties = input_data.get("properties", {})
            relations = input_data.get("relations", [])

            if not self.ontology_svc or not self.ctx:
                raise SkillExecutionError("Ontology service not available")

            # TODO: 실제 온톨로지 저장 구현
            # 현재는 데이터 검증 후 반환
            entity_id = f"entity_{hash(str(properties)) & 0x7fffffff}"

            return {
                "entityId": entity_id,
                "saved": True,
                "entityType": entity_type,
                "propertiesCount": len(properties),
                "relationsCount": len(relations)
            }
        except Exception as e:
            raise SkillExecutionError(f"Ontology write failed: {str(e)}")

    def _builtin_rag_lookup(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """RAG/온톨로지 조회"""
        try:
            query = input_data.get("query", "")
            limit = input_data.get("limit", 5)
            entity_types = input_data.get("entityTypes", [])

            if not self.vector_svc or not self.ctx:
                raise SkillExecutionError("Vector search service not available")

            # TODO: 실제 벡터 검색 및 온톨로지 조회
            # 현재는 조회 파라미터 검증 후 샘플 반환
            return {
                "documents": [
                    {
                        "content": f"Sample document about {query}",
                        "score": 0.92,
                        "source": "knowledge-base"
                    }
                ],
                "entities": [
                    {
                        "id": "entity_sample",
                        "type": entity_types[0] if entity_types else "Unknown",
                        "name": "Sample Entity",
                        "relevance": 0.88
                    }
                ],
                "total": 1,
                "limit": limit
            }
        except Exception as e:
            raise SkillExecutionError(f"RAG lookup failed: {str(e)}")

    def _builtin_fault_recurrence_check(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """반복 고장 확인"""
        try:
            equipment_id = input_data.get("equipmentId", "")
            fault_type = input_data.get("faultType", "")

            if not self.ontology_svc or not self.ctx:
                raise SkillExecutionError("Ontology service not available")

            # TODO: 실제 온톨로지 조회로 반복 고장 패턴 분석
            # 현재는 파라미터 검증 후 샘플 반환
            if not equipment_id or not fault_type:
                raise SkillExecutionError("equipmentId and faultType are required")

            return {
                "equipmentId": equipment_id,
                "faultType": fault_type,
                "isRecurring": False,
                "occurrenceCount": 1,
                "lastOccurrence": "2026-06-14T00:00:00Z",
                "frequency": "unknown",
                "pattern": None
            }
        except Exception as e:
            raise SkillExecutionError(f"Fault recurrence check failed: {str(e)}")

    def _builtin_request_classify(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """요청 분류"""
        try:
            text = input_data.get("text", "")
            categories = input_data.get("categories", [])

            if not self.llm_client or not self.ctx:
                raise SkillExecutionError("LLM client not available")

            if not text:
                raise SkillExecutionError("text is required for classification")

            if not categories:
                categories = ["unknown"]

            # TODO: 실제 LLM 분류 로직
            # 현재는 입력 검증 후 샘플 반환
            return {
                "text": text,
                "category": categories[0] if categories else "unknown",
                "confidence": 0.85,
                "alternativeCategories": [
                    {"category": c, "confidence": 0.05} for c in categories[1:2]
                ]
            }
        except Exception as e:
            raise SkillExecutionError(f"Request classification failed: {str(e)}")

    def _execute_http(self, impl: SkillImplementation, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP 기반 스킬 실행

        Args:
            impl: 구현 설정
            input_data: 입력 데이터

        Returns:
            실행 결과
        """
        endpoint = impl.endpoint
        if not endpoint:
            raise SkillExecutionError("HTTP skill requires endpoint")

        method = impl.auth or impl.auth.get("type", "POST").upper() if impl.auth else "POST"
        headers = {"Content-Type": "application/json"}

        # 인증 정보 추가 (Phase 1: 기본 구현)
        if impl.auth:
            auth = impl.auth
            if auth.type == "basic":
                import base64
                credentials = base64.b64encode(
                    f"{auth.username}:{auth.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
            elif auth.type == "bearer":
                # {{...}} 형식의 토큰은 여기서 처리
                token = auth.password or ""
                headers["Authorization"] = f"Bearer {token}"

        try:
            if method.upper() == "POST":
                response = requests.post(
                    endpoint,
                    json=input_data,
                    headers=headers,
                    timeout=self.timeout_seconds
                )
            elif method.upper() == "GET":
                response = requests.get(
                    endpoint,
                    params=input_data,
                    headers=headers,
                    timeout=self.timeout_seconds
                )
            else:
                raise SkillExecutionError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            raise SkillExecutionError(f"HTTP request timeout after {self.timeout_seconds}s")
        except requests.RequestException as e:
            raise SkillExecutionError(f"HTTP request failed: {str(e)}")

    def _execute_mcp_http(self, impl: SkillImplementation, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP HTTP 기반 스킬 실행

        현재 v5 구조:
        - callStyle: "tool_endpoint" (현재) vs "jsonrpc_proxy" (향후)
        - tool_endpoint: /mcp/tools/{tool}에 직접 arguments 전송
        - jsonrpc_proxy: /mcp에 JSON-RPC wrapper로 감싼 tools/call 전송

        Args:
            impl: 구현 설정 (MCPHttpConfig)
            input_data: 입력 데이터

        Returns:
            실행 결과
        """
        if not isinstance(impl.mcpConfig, MCPHttpConfig):
            raise SkillExecutionError("MCP HTTP requires mcpConfig")

        mcp_config = impl.mcpConfig
        endpoint = mcp_config.endpoint
        if not endpoint:
            raise SkillExecutionError("MCP HTTP requires endpoint")

        method = mcp_config.method or "POST"
        headers = {"Content-Type": "application/json"}
        timeout = (mcp_config.timeout or 10000) / 1000  # ms to seconds

        try:
            # tool_endpoint vs jsonrpc_proxy 구분
            if mcp_config.callStyle == "jsonrpc_proxy":
                # Phase 2+: JSON-RPC wrapper
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": mcp_config.tool,
                        "arguments": input_data
                    }
                }
            else:
                # Phase 1 (기본): tool_endpoint - 직접 arguments 전송
                payload = input_data

            logger.debug(f"MCP HTTP call: {endpoint} with {mcp_config.callStyle}")

            if method.upper() == "POST":
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
            else:
                response = requests.get(
                    endpoint,
                    params=payload,
                    headers=headers,
                    timeout=timeout
                )

            response.raise_for_status()
            result = response.json()

            # JSON-RPC 응답에서 result 추출
            if mcp_config.callStyle == "jsonrpc_proxy" and "result" in result:
                return result.get("result", {})

            return result

        except requests.Timeout:
            raise SkillExecutionError(f"MCP HTTP timeout after {timeout}s")
        except requests.RequestException as e:
            raise SkillExecutionError(f"MCP HTTP request failed: {str(e)}")
        except json.JSONDecodeError:
            raise SkillExecutionError("MCP HTTP response is not valid JSON")
