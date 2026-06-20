"""스킬 관리 서비스"""

import json
import logging
from typing import List, Optional
from pathlib import Path

from app.models.skill import Skill
from app.models.tenant_context import TenantContext
from storage_config import get_project_root

logger = logging.getLogger(__name__)


class SkillService:
    """스킬 관리 서비스"""

    BUILTIN_SKILLS_PATH = Path("app/config/skills/builtin_skills.json")

    def __init__(self, ctx: TenantContext):
        self.ctx = ctx
        self._builtin_skills: Optional[List[Skill]] = None

    def _load_builtin_skills(self) -> List[Skill]:
        """Built-in 스킬을 로드합니다."""
        if self._builtin_skills is not None:
            return self._builtin_skills

        try:
            with open(self.BUILTIN_SKILLS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            skills = []
            for skill_dict in data.get('builtinSkills', []):
                try:
                    skill = Skill(**skill_dict)
                    skills.append(skill)
                except Exception as e:
                    logger.warning(f"Failed to load skill {skill_dict.get('id')}: {e}")

            self._builtin_skills = skills
            logger.info(f"Loaded {len(skills)} built-in skills")
            return skills

        except FileNotFoundError:
            logger.warning(f"Built-in skills file not found: {self.BUILTIN_SKILLS_PATH}")
            return []
        except Exception as e:
            logger.error(f"Failed to load built-in skills: {e}")
            return []

    def _custom_skill_file(self) -> Path:
        """프로젝트별 커스텀 스킬 파일 경로를 반환합니다."""
        root = get_project_root(self.ctx.company_id, self.ctx.project_id)
        skills_dir = root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        return skills_dir / "custom_skills.json"

    def _load_custom_skills(self) -> List[Skill]:
        """프로젝트의 커스텀 스킬을 로드합니다."""
        skill_file = self._custom_skill_file()

        if not skill_file.exists():
            return []

        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            skills = []
            for skill_dict in data.get('customSkills', []):
                try:
                    skill = Skill(**skill_dict)
                    skills.append(skill)
                except Exception as e:
                    logger.warning(f"Failed to load custom skill {skill_dict.get('id')}: {e}")

            logger.info(f"Loaded {len(skills)} custom skills for {self.ctx.company_id}/{self.ctx.project_id}")
            return skills

        except json.JSONDecodeError as e:
            logger.error(f"Invalid custom skills JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load custom skills: {e}")
            return []

    def list_builtin_skills(self) -> List[Skill]:
        """Built-in 스킬 목록을 반환합니다."""
        return self._load_builtin_skills()

    def list_custom_skills(self) -> List[Skill]:
        """프로젝트의 커스텀 스킬 목록을 반환합니다."""
        return self._load_custom_skills()

    def list_skills(self) -> tuple[List[Skill], List[Skill]]:
        """Built-in과 Custom 스킬을 모두 반환합니다."""
        return self.list_builtin_skills(), self.list_custom_skills()

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """
        스킬을 조회합니다 (Built-in + Custom).

        Args:
            skill_id: 스킬 ID

        Returns:
            Skill 또는 None
        """
        # Built-in 먼저 조회
        for skill in self.list_builtin_skills():
            if skill.id == skill_id:
                return skill

        # Custom 조회
        for skill in self.list_custom_skills():
            if skill.id == skill_id:
                return skill

        return None

    def save_custom_skill(self, skill: Skill) -> None:
        """
        커스텀 스킬을 저장합니다.

        Args:
            skill: 저장할 스킬
        """
        skill_file = self._custom_skill_file()

        # 기존 스킬 로드
        custom_skills = self._load_custom_skills()

        # 기존 스킬 중 동일 ID 제거
        custom_skills = [s for s in custom_skills if s.id != skill.id]

        # 새 스킬 추가
        custom_skills.append(skill)

        # 파일에 저장
        try:
            data = {
                "version": "1.0",
                "customSkills": [s.model_dump(mode='json') for s in custom_skills]
            }

            with open(skill_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved custom skill {skill.id} for {self.ctx.company_id}/{self.ctx.project_id}")

        except Exception as e:
            logger.error(f"Failed to save custom skill: {e}")
            raise

    def delete_custom_skill(self, skill_id: str) -> None:
        """
        커스텀 스킬을 삭제합니다.

        Args:
            skill_id: 삭제할 스킬 ID
        """
        skill_file = self._custom_skill_file()

        if not skill_file.exists():
            logger.warning(f"Custom skills file not found: {skill_file}")
            return

        # 기존 스킬 로드
        custom_skills = self._load_custom_skills()

        # 해당 스킬 제거
        original_count = len(custom_skills)
        custom_skills = [s for s in custom_skills if s.id != skill_id]

        if len(custom_skills) == original_count:
            logger.warning(f"Skill {skill_id} not found")
            return

        # 파일에 저장
        try:
            data = {
                "version": "1.0",
                "customSkills": [s.model_dump(mode='json') for s in custom_skills]
            }

            with open(skill_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Deleted custom skill {skill_id} for {self.ctx.company_id}/{self.ctx.project_id}")

        except Exception as e:
            logger.error(f"Failed to delete custom skill: {e}")
            raise

    def get_skill_by_executor(self, executor: str) -> Optional[Skill]:
        """
        실행기(executor) 이름으로 스킬을 조회합니다 (향후 사용).

        Args:
            executor: 실행기 이름

        Returns:
            Skill 또는 None
        """
        # TODO: 향후 executor 매핑 구현
        return None
