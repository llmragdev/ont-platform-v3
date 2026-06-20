"""Expression renderer tests — {{nodes.xxx.output.yyy}} 형식"""
import pytest
from app.services.expression_renderer import (
    resolve_input_value,
    prepare_skill_input,
    evaluate_expression,
    validate_skill_schema
)


class TestResolveInputValue:
    """Type preservation in expression binding"""

    def test_single_expression_preserves_array_type(self):
        """{{nodes.x.output.arr}} → [1, 2, 3]"""
        ctx = {
            'nodes': {
                'n-asset': {
                    'output': {'equipmentIds': [1, 2, 3]}
                }
            }
        }
        result = resolve_input_value("{{nodes.n-asset.output.equipmentIds}}", ctx)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_single_expression_preserves_object_type(self):
        """{{nodes.x.output.obj}} → {a: 1, b: 2}"""
        ctx = {
            'nodes': {
                'n-data': {
                    'output': {'config': {'version': '1.0', 'timeout': 30}}
                }
            }
        }
        result = resolve_input_value("{{nodes.n-data.output.config}}", ctx)
        assert result == {'version': '1.0', 'timeout': 30}
        assert isinstance(result, dict)

    def test_single_expression_preserves_integer_type(self):
        """{{nodes.x.output.count}} → 42"""
        ctx = {
            'nodes': {
                'n-count': {
                    'output': {'value': 42}
                }
            }
        }
        result = resolve_input_value("{{nodes.n-count.output.value}}", ctx)
        assert result == 42
        assert isinstance(result, int)

    def test_single_expression_preserves_string_type(self):
        """{{nodes.x.output.name}} → "Motor-01\""""
        ctx = {
            'nodes': {
                'n-asset': {
                    'output': {'name': 'Motor-01'}
                }
            }
        }
        result = resolve_input_value("{{nodes.n-asset.output.name}}", ctx)
        assert result == 'Motor-01'
        assert isinstance(result, str)

    def test_single_expression_preserves_bool_type(self):
        """{{nodes.x.output.isRecurring}} → true"""
        ctx = {
            'nodes': {
                'n-check': {
                    'output': {'isRecurring': True}
                }
            }
        }
        result = resolve_input_value("{{nodes.n-check.output.isRecurring}}", ctx)
        assert result is True
        assert isinstance(result, bool)

    def test_string_interpolation_with_single_expr(self):
        """Equipment: {{nodes.n-asset.output.name}} → "Equipment: Motor-01\""""
        ctx = {
            'nodes': {
                'n-asset': {
                    'output': {'name': 'Motor-01'}
                }
            }
        }
        result = resolve_input_value("Equipment: {{nodes.n-asset.output.name}}", ctx)
        assert result == "Equipment: Motor-01"
        assert isinstance(result, str)

    def test_string_interpolation_with_array(self):
        """IDs: {{nodes.x.output.ids}} → "IDs: [1, 2, 3]\""""
        ctx = {
            'nodes': {
                'n': {
                    'output': {'ids': [1, 2, 3]}
                }
            }
        }
        result = resolve_input_value("IDs: {{nodes.n.output.ids}}", ctx)
        assert result == "IDs: [1, 2, 3]"

    def test_missing_field_returns_empty_string(self):
        """{{nodes.x.missing}} → """"""
        ctx = {'nodes': {'n': {'output': {}}}}
        result = resolve_input_value("{{nodes.n.output.missing}}", ctx)
        assert result == ""

    def test_missing_node_returns_empty_string(self):
        """{{nodes.missing.output.x}} → """"""
        ctx = {'nodes': {}}
        result = resolve_input_value("{{nodes.missing.output.x}}", ctx)
        assert result == ""

    def test_no_expression_returns_as_is(self):
        """No {{}} → return value unchanged"""
        assert resolve_input_value("plain text", {}) == "plain text"
        assert resolve_input_value(42, {}) == 42
        assert resolve_input_value([1, 2], {}) == [1, 2]
        assert resolve_input_value(None, {}) is None

    def test_nested_object_traversal(self):
        """{{nodes.x.output.a.b.c}} → deeply nested value"""
        ctx = {
            'nodes': {
                'n': {
                    'output': {
                        'a': {'b': {'c': 'deep_value'}}
                    }
                }
            }
        }
        result = resolve_input_value("{{nodes.n.output.a.b.c}}", ctx)
        assert result == "deep_value"

    def test_multiple_interpolations(self):
        """Prefix {{x}} middle {{y}} suffix"""
        ctx = {
            'nodes': {
                'n1': {'output': {'val': 'A'}},
                'n2': {'output': {'val': 'B'}}
            }
        }
        result = resolve_input_value(
            "Prefix {{nodes.n1.output.val}} middle {{nodes.n2.output.val}} suffix",
            ctx
        )
        assert result == "Prefix A middle B suffix"


class TestPrepareSkillInput:
    """Skill input mapping preparation"""

    def test_basic_input_mapping(self):
        """Render simple inputMapping"""
        skill_config = {
            'inputMapping': {
                'equipmentId': '{{nodes.n-asset.output.id}}',
                'faultType': 'overheat'
            }
        }
        ctx = {
            'nodes': {
                'n-asset': {'output': {'id': 'MOTOR-001'}}
            }
        }
        result = prepare_skill_input(skill_config, ctx)
        assert result == {
            'equipmentId': 'MOTOR-001',
            'faultType': 'overheat'
        }

    def test_complex_input_mapping_preserves_types(self):
        """inputMapping with mixed types"""
        skill_config = {
            'inputMapping': {
                'ids': '{{nodes.n-ids.output.array}}',
                'name': 'Equipment: {{nodes.n-name.output.value}}',
                'count': '{{nodes.n-count.output.num}}'
            }
        }
        ctx = {
            'nodes': {
                'n-ids': {'output': {'array': [1, 2, 3]}},
                'n-name': {'output': {'value': 'Motor'}},
                'n-count': {'output': {'num': 42}}
            }
        }
        result = prepare_skill_input(skill_config, ctx)
        assert result['ids'] == [1, 2, 3]
        assert result['name'] == 'Equipment: Motor'
        assert result['count'] == 42

    def test_empty_input_mapping(self):
        """skillConfig without inputMapping"""
        result = prepare_skill_input({'other': 'field'}, {})
        assert result == {}

    def test_none_skill_config(self):
        """skillConfig is None"""
        result = prepare_skill_input(None, {})
        assert result == {}


class TestValidateSkillSchema:
    """JSON Schema validation"""

    def test_required_fields_present(self):
        """All required fields are present"""
        schema = {
            'type': 'object',
            'required': ['name', 'type']
        }
        data = {'name': 'Equipment', 'type': 'Motor'}
        valid, error = validate_skill_schema(schema, data)
        assert valid is True
        assert error is None

    def test_missing_required_field(self):
        """Required field is missing"""
        schema = {
            'type': 'object',
            'required': ['name', 'type']
        }
        data = {'name': 'Equipment'}
        valid, error = validate_skill_schema(schema, data)
        assert valid is False
        assert 'Required field missing: type' in error

    def test_type_mismatch_array(self):
        """Field type should be array but got string"""
        schema = {
            'type': 'object',
            'properties': {
                'ids': {'type': 'array'}
            }
        }
        data = {'ids': 'not-array'}
        valid, error = validate_skill_schema(schema, data)
        assert valid is False
        assert 'should be array' in error

    def test_type_mismatch_string(self):
        """Field type should be string but got int"""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'}
            }
        }
        data = {'name': 123}
        valid, error = validate_skill_schema(schema, data)
        assert valid is False
        assert 'should be string' in error

    def test_type_mismatch_integer(self):
        """Field type should be integer but got string"""
        schema = {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer'}
            }
        }
        data = {'count': 'not-int'}
        valid, error = validate_skill_schema(schema, data)
        assert valid is False
        assert 'should be integer' in error

    def test_no_schema(self):
        """No inputSchema defined"""
        valid, error = validate_skill_schema(None, {'anything': 'goes'})
        assert valid is True
        assert error is None

    def test_extra_fields_allowed(self):
        """Extra fields not in schema are allowed"""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'}
            }
        }
        data = {'name': 'Test', 'extra': 'field'}
        valid, error = validate_skill_schema(schema, data)
        assert valid is True


class TestEvaluateExpression:
    """Core expression evaluation"""

    def test_simple_path(self):
        """nodes.n.output.field"""
        ctx = {'nodes': {'n': {'output': {'field': 'value'}}}}
        result = evaluate_expression('nodes.n.output.field', ctx)
        assert result == 'value'

    def test_deep_path(self):
        """nodes.n.output.a.b.c"""
        ctx = {
            'nodes': {
                'n': {
                    'output': {
                        'a': {'b': {'c': 'deep'}}
                    }
                }
            }
        }
        result = evaluate_expression('nodes.n.output.a.b.c', ctx)
        assert result == 'deep'

    def test_missing_path_returns_none(self):
        """Path not found → None"""
        ctx = {'nodes': {}}
        result = evaluate_expression('nodes.n.output.field', ctx)
        assert result is None

    def test_array_value(self):
        """Path evaluates to array"""
        ctx = {'nodes': {'n': {'output': {'items': [1, 2, 3]}}}}
        result = evaluate_expression('nodes.n.output.items', ctx)
        assert result == [1, 2, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
