"""Phase 4 Week 1: 스키마 저장소 (도메인별 온톨로지 정의)"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.models.ontology_schema import DomainSchema, OntologyStyle, SchemaValidationResult
from storage_config import get_project_root


class SchemaRepository:
    """도메인 스키마 저장소 (JSON 기반)"""

    def __init__(self):
        # 공통 스키마 경로
        self.base_path = Path.home() / ".ont-platform" / "data" / "schemas"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_schema_path(self, domain_id: str) -> Path:
        """도메인별 스키마 파일 경로"""
        path = self.base_path / f"{domain_id}.json"
        return path

    def save_schema(self, schema: DomainSchema) -> None:
        """스키마 저장"""
        path = self._get_schema_path(schema.domain_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            # Pydantic v2 모델을 JSON으로 직렬화
            schema_dict = schema.model_dump(mode="json")
            json.dump(schema_dict, f, indent=2, ensure_ascii=False)

    def get_schema(self, domain_id: str) -> Optional[DomainSchema]:
        """스키마 조회"""
        path = self._get_schema_path(domain_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DomainSchema(**data)

    def list_domains(self) -> List[str]:
        """모든 도메인 ID 조회"""
        if not self.base_path.exists():
            return []

        return [p.stem for p in self.base_path.glob("*.json")]

    def delete_schema(self, domain_id: str) -> bool:
        """스키마 삭제"""
        path = self._get_schema_path(domain_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def schema_exists(self, domain_id: str) -> bool:
        """스키마 존재 여부"""
        return self._get_schema_path(domain_id).exists()

    def validate_schema(self, schema: DomainSchema) -> SchemaValidationResult:
        """스키마 검증"""
        errors = []
        warnings = []

        # 필수 필드 검증
        if not schema.domain_id:
            errors.append("domain_id는 필수 입력 항목입니다.")

        if not schema.entity_types:
            errors.append("entity_types는 최소 하나 이상 필요합니다.")

        # 관계 타입 검증
        for rel_name, rel_type in schema.relation_types.items():
            # from_type과 to_type이 entity_types에 존재하는지 확인
            if rel_type.from_type not in schema.entity_types:
                errors.append(f"관계 '{rel_name}'의 from_type '{rel_type.from_type}'이 존재하지 않습니다.")
            if rel_type.to_type not in schema.entity_types:
                errors.append(f"관계 '{rel_name}'의 to_type '{rel_type.to_type}'이 존재하지 않습니다.")

        # 엔티티 타입 상속 검증
        for entity_name, entity_type in schema.entity_types.items():
            for parent_type in entity_type.parent_types:
                if parent_type not in schema.entity_types:
                    errors.append(f"엔티티 '{entity_name}'의 부모 타입 '{parent_type}'이 존재하지 않습니다.")

        # RDF 스타일 검증
        if schema.ontology_style == OntologyStyle.RDF_TRIPLE:
            if not schema.rdf_namespaces:
                warnings.append("RDF 스타일이지만 네임스페이스가 정의되지 않았습니다.")

        # 스타일별 제약 검증
        if schema.ontology_style == OntologyStyle.HIERARCHICAL:
            # 계층적 구조는 단일 부모만 허용하는 것이 일반적
            for entity_name, entity_type in schema.entity_types.items():
                if len(entity_type.parent_types) > 1:
                    warnings.append(f"계층적 스타일에서 엔티티 '{entity_name}'이 여러 부모를 가집니다.")

        return SchemaValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def get_schema_by_style(self, style: OntologyStyle) -> List[DomainSchema]:
        """특정 스타일을 사용하는 모든 스키마 조회"""
        domains = self.list_domains()
        schemas = []
        for domain_id in domains:
            schema = self.get_schema(domain_id)
            if schema and schema.ontology_style == style:
                schemas.append(schema)
        return schemas

    def update_schema_version(self, domain_id: str, version: str, updated_by: str) -> Optional[DomainSchema]:
        """스키마 버전 업데이트"""
        schema = self.get_schema(domain_id)
        if not schema:
            return None

        schema.version = version
        schema.updated_by = updated_by
        schema.updated_at = datetime.utcnow()
        self.save_schema(schema)
        return schema

    def clone_schema(self, source_domain_id: str, target_domain_id: str, created_by: str) -> Optional[DomainSchema]:
        """스키마 복제"""
        source_schema = self.get_schema(source_domain_id)
        if not source_schema:
            return None

        # 기존 스키마가 있으면 오류
        if self.schema_exists(target_domain_id):
            return None

        # 스키마 복제
        new_schema = DomainSchema(
            domain_id=target_domain_id,
            ontology_style=source_schema.ontology_style,
            display_name=f"{source_schema.display_name} (복제)",
            description=f"복제: {source_schema.domain_id}",
            entity_types=source_schema.entity_types.copy(),
            relation_types=source_schema.relation_types.copy(),
            constraints=source_schema.constraints.copy(),
            rdf_namespaces=source_schema.rdf_namespaces.copy(),
            version="1.0",
            created_by=created_by,
            created_at=datetime.utcnow(),
            tags=source_schema.tags.copy(),
            metadata=source_schema.metadata.copy()
        )

        self.save_schema(new_schema)
        return new_schema

    def list_schema_versions(self, domain_id: str) -> List[Dict[str, str]]:
        """스키마 버전 이력 조회 (현재 단순 구현, 향후 버전 관리 시스템 추가)"""
        schema = self.get_schema(domain_id)
        if not schema:
            return []

        return [{
            "version": schema.version,
            "created_by": schema.created_by,
            "created_at": schema.created_at.isoformat(),
            "updated_by": schema.updated_by,
            "updated_at": schema.updated_at.isoformat()
        }]
