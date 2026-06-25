"""스킬 시스템 API"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.models.skill import Skill, SkillConfig, SkillCatalog
from app.models.tenant_context import TenantContext
from app.dependencies import get_tenant_context
from app.services.skill_service import SkillService

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
async def list_skills(ctx: TenantContext = Depends(get_tenant_context)) -> dict:
    """
    모든 스킬 조회 (Built-in + Custom)

    Returns:
        dict: {builtinSkills: [...], customSkills: [...]}
    """
    try:
        service = SkillService(ctx)
        builtin = service.list_builtin_skills()
        custom = service.list_custom_skills()

        return {
            "builtinSkills": builtin,
            "customSkills": custom,
            "total": len(builtin) + len(custom)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}")
async def get_skill(skill_id: str, ctx: TenantContext = Depends(get_tenant_context)) -> Skill:
    """
    특정 스킬 조회

    Args:
        skill_id: 스킬 ID

    Returns:
        Skill: 스킬 정의
    """
    try:
        service = SkillService(ctx)
        skill = service.get_skill(skill_id)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

        return skill
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom")
async def create_custom_skill(skill: Skill, ctx: TenantContext = Depends(get_tenant_context)) -> dict:
    """
    커스텀 스킬 생성

    Args:
        skill: 스킬 정의

    Returns:
        dict: {skillId: ..., created: true}
    """
    try:
        if not skill.id:
            raise HTTPException(status_code=400, detail="skill.id is required")

        service = SkillService(ctx)
        service.save_custom_skill(skill)

        return {
            "skillId": skill.id,
            "created": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/custom/{skill_id}")
async def update_custom_skill(
    skill_id: str,
    skill: Skill,
    ctx: TenantContext = Depends(get_tenant_context)
) -> dict:
    """
    커스텀 스킬 수정

    Args:
        skill_id: 스킬 ID
        skill: 수정할 스킬 정의

    Returns:
        dict: {skillId: ..., updated: true}
    """
    try:
        if skill.id != skill_id:
            raise HTTPException(status_code=400, detail="skill.id mismatch")

        service = SkillService(ctx)
        service.save_custom_skill(skill)

        return {
            "skillId": skill_id,
            "updated": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/custom/{skill_id}")
async def delete_custom_skill(skill_id: str, ctx: TenantContext = Depends(get_tenant_context)) -> dict:
    """
    커스텀 스킬 삭제

    Args:
        skill_id: 스킬 ID

    Returns:
        dict: {skillId: ..., deleted: true}
    """
    try:
        service = SkillService(ctx)
        service.delete_custom_skill(skill_id)

        return {
            "skillId": skill_id,
            "deleted": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-expression")
async def validate_expression(data: dict) -> dict:
    """
    표현식 검증 ({{nodes.xxx.output.yyy}} 형식)

    Args:
        data: {expression: "...", executionContext: {...}}

    Returns:
        dict: {valid: true/false, value: ..., error: ...}
    """
    try:
        from app.services.expression_renderer import validate_expression

        expr = data.get("expression")
        context = data.get("executionContext", {})

        result = validate_expression(expr, context)

        return {
            "valid": True,
            "value": result
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
