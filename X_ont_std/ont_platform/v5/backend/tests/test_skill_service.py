"""Skill service tests"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.skill_service import SkillService
from app.models.skill import Skill, SkillImplementation
from app.models.tenant_context import TenantContext


@pytest.fixture
def tenant_context():
    """Create test tenant context"""
    return TenantContext(
        user_id='test-user',
        company_id='test-company',
        project_id='test-project'
    )


@pytest.fixture
def temp_skills_dir():
    """Create temporary directory for skill files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSkillServiceLoadBuiltin:
    """Load built-in skills"""

    def test_load_builtin_skills(self, tenant_context):
        """Load built-in skills from config file"""
        service = SkillService(tenant_context)
        skills = service.list_builtin_skills()

        assert len(skills) > 0
        assert any(s.id == 'customer-comment-create' for s in skills)
        assert any(s.id == 'factory-comment-create' for s in skills)

    def test_builtin_skills_cached(self, tenant_context):
        """Built-in skills are cached"""
        service = SkillService(tenant_context)
        skills1 = service.list_builtin_skills()
        skills2 = service.list_builtin_skills()

        # Should be same object (cached)
        assert skills1 is skills2

    def test_get_builtin_skill(self, tenant_context):
        """Get specific built-in skill"""
        service = SkillService(tenant_context)
        skill = service.get_skill('customer-comment-create')

        assert skill is not None
        assert skill.id == 'customer-comment-create'
        assert skill.name is not None
        assert skill.implementation is not None

    def test_builtin_skill_has_schema(self, tenant_context):
        """Built-in skill has inputSchema and outputSchema"""
        service = SkillService(tenant_context)
        skill = service.get_skill('customer-comment-create')

        assert skill.inputSchema is not None
        assert skill.outputSchema is not None
        assert skill.inputSchema.get('type') == 'object'


class TestSkillServiceCustomSkills:
    """Custom skill management"""

    @patch('app.services.skill_service.get_project_root')
    def test_save_custom_skill(self, mock_get_root, temp_skills_dir, tenant_context):
        """Save custom skill to file"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)
        skill = Skill(
            id='custom-skill-1',
            name='Custom Skill',
            description='A test skill',
            implementation=SkillImplementation(type='http', endpoint='http://example.com/api'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )

        service.save_custom_skill(skill)

        # Verify file was created
        skill_file = temp_skills_dir / 'skills' / 'custom_skills.json'
        assert skill_file.exists()

        # Verify contents
        with open(skill_file) as f:
            data = json.load(f)

        assert len(data['customSkills']) == 1
        assert data['customSkills'][0]['id'] == 'custom-skill-1'

    @patch('app.services.skill_service.get_project_root')
    def test_load_custom_skills(self, mock_get_root, temp_skills_dir, tenant_context):
        """Load custom skills from file"""
        mock_get_root.return_value = temp_skills_dir

        # Create custom skills file
        skills_dir = temp_skills_dir / 'skills'
        skills_dir.mkdir()
        skill_file = skills_dir / 'custom_skills.json'

        skill_data = {
            'version': '1.0',
            'customSkills': [
                {
                    'id': 'custom-1',
                    'name': 'Custom 1',
                    'implementation': {'type': 'http', 'endpoint': 'http://example.com'},
                    'inputSchema': {'type': 'object'},
                    'outputSchema': {'type': 'object'}
                }
            ]
        }
        with open(skill_file, 'w') as f:
            json.dump(skill_data, f)

        service = SkillService(tenant_context)
        skills = service.list_custom_skills()

        assert len(skills) == 1
        assert skills[0].id == 'custom-1'

    @patch('app.services.skill_service.get_project_root')
    def test_update_custom_skill(self, mock_get_root, temp_skills_dir, tenant_context):
        """Update existing custom skill"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)

        # Save first version
        skill = Skill(
            id='custom-skill',
            name='Original',
            implementation=SkillImplementation(type='http', endpoint='http://v1.com'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )
        service.save_custom_skill(skill)

        # Save updated version
        skill.name = 'Updated'
        skill.implementation.endpoint = 'http://v2.com'
        service.save_custom_skill(skill)

        # Verify only one skill with updated data
        skills = service.list_custom_skills()
        assert len(skills) == 1
        assert skills[0].name == 'Updated'

    @patch('app.services.skill_service.get_project_root')
    def test_delete_custom_skill(self, mock_get_root, temp_skills_dir, tenant_context):
        """Delete custom skill"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)

        # Save two skills
        skill1 = Skill(
            id='custom-1',
            name='Skill 1',
            implementation=SkillImplementation(type='http', endpoint='http://example.com'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )
        skill2 = Skill(
            id='custom-2',
            name='Skill 2',
            implementation=SkillImplementation(type='http', endpoint='http://example.com'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )
        service.save_custom_skill(skill1)
        service.save_custom_skill(skill2)

        # Delete first skill
        service.delete_custom_skill('custom-1')

        # Verify only second skill remains
        skills = service.list_custom_skills()
        assert len(skills) == 1
        assert skills[0].id == 'custom-2'

    @patch('app.services.skill_service.get_project_root')
    def test_delete_nonexistent_skill(self, mock_get_root, temp_skills_dir, tenant_context):
        """Delete non-existent skill (should not raise)"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)
        # Should not raise
        service.delete_custom_skill('nonexistent')


class TestSkillServiceGetSkill:
    """Get skill from both built-in and custom"""

    @patch('app.services.skill_service.get_project_root')
    def test_get_builtin_skill_prioritized(self, mock_get_root, temp_skills_dir, tenant_context):
        """Built-in skills are returned first"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)
        skill = service.get_skill('customer-comment-create')

        # Should get built-in skill
        assert skill is not None
        assert skill.id == 'customer-comment-create'

    @patch('app.services.skill_service.get_project_root')
    def test_get_custom_skill(self, mock_get_root, temp_skills_dir, tenant_context):
        """Get custom skill when not in built-in"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)

        # Create custom skill
        skill = Skill(
            id='my-custom-skill',
            name='Custom',
            implementation=SkillImplementation(type='http', endpoint='http://example.com'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )
        service.save_custom_skill(skill)

        # Get it back
        retrieved = service.get_skill('my-custom-skill')
        assert retrieved is not None
        assert retrieved.id == 'my-custom-skill'

    def test_get_nonexistent_skill_returns_none(self, tenant_context):
        """Get non-existent skill returns None"""
        service = SkillService(tenant_context)
        skill = service.get_skill('nonexistent-skill-xyz')

        assert skill is None


class TestSkillServiceListSkills:
    """List both built-in and custom skills"""

    @patch('app.services.skill_service.get_project_root')
    def test_list_all_skills(self, mock_get_root, temp_skills_dir, tenant_context):
        """List all skills (built-in + custom)"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)

        # Save a custom skill
        custom = Skill(
            id='custom-skill',
            name='Custom',
            implementation=SkillImplementation(type='http', endpoint='http://example.com'),
            inputSchema={'type': 'object'},
            outputSchema={'type': 'object'}
        )
        service.save_custom_skill(custom)

        # Get all
        builtin, custom_list = service.list_skills()

        assert len(builtin) > 0
        assert len(custom_list) > 0
        assert any(s.id == 'customer-comment-create' for s in builtin)
        assert any(s.id == 'custom-skill' for s in custom_list)


class TestSkillServiceEdgeCases:
    """Edge cases and error handling"""

    @patch('app.services.skill_service.get_project_root')
    def test_invalid_json_in_custom_skills_file(self, mock_get_root, temp_skills_dir, tenant_context):
        """Invalid JSON in custom skills file is handled"""
        mock_get_root.return_value = temp_skills_dir

        # Create invalid JSON file
        skills_dir = temp_skills_dir / 'skills'
        skills_dir.mkdir()
        skill_file = skills_dir / 'custom_skills.json'
        with open(skill_file, 'w') as f:
            f.write('invalid json {')

        service = SkillService(tenant_context)
        # Should return empty list, not raise
        skills = service.list_custom_skills()
        assert skills == []

    @patch('app.services.skill_service.get_project_root')
    def test_missing_custom_skills_file(self, mock_get_root, temp_skills_dir, tenant_context):
        """Missing custom skills file returns empty list"""
        mock_get_root.return_value = temp_skills_dir

        service = SkillService(tenant_context)
        skills = service.list_custom_skills()

        assert skills == []

    @patch('app.services.skill_service.get_project_root')
    def test_malformed_skill_in_json(self, mock_get_root, temp_skills_dir, tenant_context):
        """Malformed skill entry in JSON is skipped"""
        mock_get_root.return_value = temp_skills_dir

        # Create file with mixed valid/invalid skills
        skills_dir = temp_skills_dir / 'skills'
        skills_dir.mkdir()
        skill_file = skills_dir / 'custom_skills.json'

        skill_data = {
            'version': '1.0',
            'customSkills': [
                {
                    'id': 'valid-skill',
                    'name': 'Valid',
                    'implementation': {'type': 'http', 'endpoint': 'http://example.com'},
                    'inputSchema': {'type': 'object'},
                    'outputSchema': {'type': 'object'}
                },
                {
                    'id': 'invalid-skill',
                    # Missing required fields
                    'name': 'Invalid'
                }
            ]
        }
        with open(skill_file, 'w') as f:
            json.dump(skill_data, f)

        service = SkillService(tenant_context)
        skills = service.list_custom_skills()

        # Only valid skill should be loaded
        assert len(skills) == 1
        assert skills[0].id == 'valid-skill'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
