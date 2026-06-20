"""표현식 렌더링 엔진 ({{nodes.xxx.output.yyy}})"""

import re
from typing import Any, Dict, Optional


# 정규식: 단일 표현식 판별 ({{...}} 하나만 있는 경우)
SINGLE_EXPR_PATTERN = r'^\s*\{\{([^{}]+)\}\}\s*$'

# 정규식: 복합 표현식 판별 (문자열 내에 {{...}} 포함)
EXPR_PATTERN = r'\{\{([^{}]+)\}\}'


def parse_expression_path(expr: str) -> list[str]:
    """
    표현식 경로를 파싱합니다.

    예:
    - "nodes.n-asset.output.equipmentIds" → ["nodes", "n-asset", "output", "equipmentIds"]
    """
    return expr.strip().split('.')


def get_nested_value(obj: Any, path: list[str]) -> Any:
    """
    중첩된 객체에서 값을 가져옵니다.

    Args:
        obj: 객체 (dict 또는 다른 타입)
        path: 경로 리스트 ["nodes", "n-asset", "output", "field"]

    Returns:
        값 또는 None (경로를 찾을 수 없으면)
    """
    current = obj

    for key in path:
        if current is None:
            return None

        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None

    return current


def evaluate_expression(expr: str, execution_context: Dict[str, Any]) -> Any:
    """
    단일 표현식을 평가합니다.

    Args:
        expr: "nodes.n-asset.output.equipmentIds" 형태의 표현식
        execution_context: 실행 컨텍스트

    Returns:
        평가된 값 (찾을 수 없으면 None)

    Examples:
        >>> ctx = {
        ...     'nodes': {
        ...         'n-asset': {
        ...             'output': {'equipmentIds': [1, 2, 3]}
        ...         }
        ...     }
        ... }
        >>> evaluate_expression('nodes.n-asset.output.equipmentIds', ctx)
        [1, 2, 3]
    """
    path = parse_expression_path(expr)
    return get_nested_value(execution_context, path)


def validate_expression(expr: str, execution_context: Dict[str, Any]) -> Any:
    """
    표현식 유효성을 검증하고 값을 반환합니다.

    Args:
        expr: "{{nodes.xxx}}" 형태의 표현식
        execution_context: 실행 컨텍스트

    Returns:
        평가된 값

    Raises:
        ValueError: 표현식 형식이 잘못되었거나 경로를 찾을 수 없으면
    """
    # {{ }} 제거
    inner = expr.strip()
    if inner.startswith('{{') and inner.endswith('}}'):
        inner = inner[2:-2].strip()

    # 평가
    result = evaluate_expression(inner, execution_context)

    if result is None and inner not in execution_context:
        raise ValueError(f"Expression path not found: {inner}")

    return result


def resolve_input_value(value: Any, execution_context: Dict[str, Any]) -> Any:
    """
    입력값을 렌더링합니다. 표현식을 평가하고 타입을 보존합니다.

    핵심 로직:
    - Case A: "{{nodes.x.output.arr}}" (단일 표현식)
      → 원본 타입 유지 [1, 2, 3]

    - Case B: "prefix {{nodes.x}} suffix" (복합 보간)
      → 문자열 변환 "prefix [1, 2, 3] suffix"

    Args:
        value: 렌더링할 값 (string, int, dict, list 등)
        execution_context: 실행 컨텍스트

    Returns:
        렌더링된 값 (타입 보존됨)

    Examples:
        >>> ctx = {'nodes': {'n': {'output': {'arr': [1, 2]}}}}
        >>> resolve_input_value("{{nodes.n.output.arr}}", ctx)
        [1, 2]

        >>> resolve_input_value("prefix {{nodes.n.output.arr}}", ctx)
        'prefix [1, 2]'

        >>> resolve_input_value(42, ctx)
        42
    """
    # 문자열이 아니면 그대로 반환
    if not isinstance(value, str):
        return value

    # Case A: 단일 표현식만 있는 경우 (원본 타입 유지)
    single_match = re.match(SINGLE_EXPR_PATTERN, value)
    if single_match:
        expr_path = single_match.group(1).strip()
        result = evaluate_expression(expr_path, execution_context)
        # 찾을 수 없으면 빈 문자열
        return result if result is not None else ""

    # Case B: 복합 보간 (문자열 내에 표현식 포함)
    if '{{' not in value:
        # 표현식이 없으면 그대로 반환
        return value

    def replacer(match):
        expr_path = match.group(1).strip()
        result = evaluate_expression(expr_path, execution_context)
        # None이면 빈 문자열로 치환
        return str(result) if result is not None else ""

    return re.sub(EXPR_PATTERN, replacer, value)


def prepare_skill_input(
    skill_config: Optional[Dict[str, Any]],
    execution_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    스킬의 inputMapping을 렌더링하여 실제 입력 데이터를 준비합니다.

    Args:
        skill_config: 스킬 설정 (skillConfig)
        execution_context: 워크플로우 실행 컨텍스트
                          {
                            'nodes': {
                              'n-classify': {'output': {...}},
                              'n-asset': {'output': {...}}
                            }
                          }

    Returns:
        렌더링된 입력 데이터

    Examples:
        >>> skill_config = {
        ...     'inputMapping': {
        ...         'category': '{{nodes.n-classify.output.category}}',
        ...         'message': 'Equipment: {{nodes.n-asset.output.name}}'
        ...     }
        ... }
        >>> ctx = {
        ...     'nodes': {
        ...         'n-classify': {'output': {'category': 'equipment_fault'}},
        ...         'n-asset': {'output': {'name': 'Motor-01'}}
        ...     }
        ... }
        >>> result = prepare_skill_input(skill_config, ctx)
        >>> result['category']
        'equipment_fault'
        >>> result['message']
        'Equipment: Motor-01'
    """
    if not skill_config or 'inputMapping' not in skill_config:
        return {}

    input_mapping = skill_config.get('inputMapping', {})
    prepared = {}

    for key, value in input_mapping.items():
        prepared[key] = resolve_input_value(value, execution_context)

    return prepared


def validate_skill_schema(
    input_schema: Dict[str, Any],
    input_data: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    입력 데이터가 inputSchema를 만족하는지 검증합니다.

    Args:
        input_schema: JSON Schema (type: "object" 등)
        input_data: 실제 입력 데이터

    Returns:
        (valid: bool, error_message: Optional[str])

    주의:
    - 완전한 JSON Schema 검증은 하지 않음 (간단한 검증만)
    - 필요시 jsonschema 라이브러리 사용 권장
    """
    if not input_schema:
        return True, None

    # required 필드 확인
    required = input_schema.get('required', [])
    for field in required:
        if field not in input_data:
            return False, f"Required field missing: {field}"

    # properties 타입 확인 (간단한 검증)
    properties = input_schema.get('properties', {})
    for key, value in input_data.items():
        if key not in properties:
            continue

        prop_schema = properties[key]
        expected_type = prop_schema.get('type')

        if expected_type == 'array' and not isinstance(value, list):
            return False, f"Field {key} should be array, got {type(value).__name__}"
        elif expected_type == 'object' and not isinstance(value, dict):
            return False, f"Field {key} should be object, got {type(value).__name__}"
        elif expected_type == 'string' and not isinstance(value, str):
            return False, f"Field {key} should be string, got {type(value).__name__}"
        elif expected_type == 'integer' and not isinstance(value, int):
            return False, f"Field {key} should be integer, got {type(value).__name__}"

    return True, None
