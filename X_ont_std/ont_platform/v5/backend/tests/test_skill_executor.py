"""Skill executor tests"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import json

from app.services.skill_executor import SkillExecutor, SkillExecutionError
from app.models.skill import (
    Skill, SkillImplementation, MCPHttpConfig, SkillAuth
)


class TestSkillExecutorBuiltin:
    """Built-in skill execution"""

    def test_execute_ontology_write(self):
        """Execute ontology-write skill"""
        skill = Skill(
            id='ontology-write',
            name='Ontology Write',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {
            'entityType': 'Equipment',
            'properties': {'name': 'Motor-01'}
        })

        assert 'entityId' in result
        assert result['saved'] is True
        assert result['entityType'] == 'Equipment'

    def test_execute_rag_lookup(self):
        """Execute rag-ontology-lookup skill"""
        skill = Skill(
            id='rag-ontology-lookup',
            name='RAG Lookup',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {'query': 'equipment maintenance'})

        assert 'documents' in result
        assert 'entities' in result
        assert len(result['documents']) > 0

    def test_execute_fault_recurrence_check(self):
        """Execute fault-recurrence-check skill"""
        skill = Skill(
            id='fault-recurrence-check',
            name='Fault Recurrence',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {
            'equipmentId': 'MOTOR-001',
            'faultType': 'overheat'
        })

        assert 'isRecurring' in result
        assert 'occurrenceCount' in result
        assert 'lastOccurrence' in result

    def test_execute_request_classify(self):
        """Execute request-classify skill"""
        skill = Skill(
            id='request-classify',
            name='Request Classify',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {
            'text': 'motor is overheating',
            'categories': ['overheat', 'noise', 'vibration']
        })

        assert 'category' in result
        assert 'confidence' in result

    def test_unknown_builtin_skill_raises_error(self):
        """Unknown built-in skill raises SkillExecutionError"""
        skill = Skill(
            id='unknown-builtin',
            name='Unknown',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'Unknown built-in skill' in str(exc_info.value)


class TestSkillExecutorHTTP:
    """HTTP skill execution"""

    @patch('requests.post')
    def test_execute_http_post(self, mock_post):
        """Execute HTTP POST skill"""
        mock_post.return_value.json.return_value = {'result': 'success'}
        mock_post.return_value.raise_for_status = Mock()

        skill = Skill(
            id='http-skill',
            name='HTTP Skill',
            implementation=SkillImplementation(
                type='http',
                endpoint='http://example.com/api/endpoint'
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {'param': 'value'})

        assert result == {'result': 'success'}
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_execute_http_with_basic_auth(self, mock_post):
        """HTTP skill with basic auth"""
        mock_post.return_value.json.return_value = {'result': 'ok'}
        mock_post.return_value.raise_for_status = Mock()

        skill = Skill(
            id='http-auth',
            name='HTTP Auth',
            implementation=SkillImplementation(
                type='http',
                endpoint='http://example.com/api',
                auth=SkillAuth(type='basic', username='user', password='pass')
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        executor.execute(skill, {'data': 'test'})

        # Check if Authorization header was set
        call_args = mock_post.call_args
        assert call_args is not None
        headers = call_args.kwargs.get('headers', {})
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Basic ')

    @patch('requests.post')
    def test_execute_http_with_bearer_auth(self, mock_post):
        """HTTP skill with bearer token"""
        mock_post.return_value.json.return_value = {'result': 'ok'}
        mock_post.return_value.raise_for_status = Mock()

        skill = Skill(
            id='http-bearer',
            name='HTTP Bearer',
            implementation=SkillImplementation(
                type='http',
                endpoint='http://example.com/api',
                auth=SkillAuth(type='bearer', password='token123')
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        executor.execute(skill, {'data': 'test'})

        call_args = mock_post.call_args
        headers = call_args.kwargs.get('headers', {})
        assert headers['Authorization'] == 'Bearer token123'

    @patch('requests.post')
    def test_http_timeout_raises_error(self, mock_post):
        """HTTP timeout raises SkillExecutionError"""
        mock_post.side_effect = requests.Timeout()

        skill = Skill(
            id='http-timeout',
            name='HTTP Timeout',
            implementation=SkillImplementation(
                type='http',
                endpoint='http://example.com/api'
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'timeout' in str(exc_info.value).lower()

    @patch('requests.post')
    def test_http_request_error_raises_error(self, mock_post):
        """HTTP request error raises SkillExecutionError"""
        mock_post.side_effect = requests.RequestException('Connection failed')

        skill = Skill(
            id='http-error',
            name='HTTP Error',
            implementation=SkillImplementation(
                type='http',
                endpoint='http://example.com/api'
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'HTTP request failed' in str(exc_info.value)


class TestSkillExecutorMCPHTTP:
    """MCP HTTP skill execution"""

    @patch('requests.post')
    def test_execute_mcp_http_tool_endpoint(self, mock_post):
        """MCP HTTP with tool_endpoint callStyle (Phase 1)"""
        mock_post.return_value.json.return_value = {'result': 'tool_result'}
        mock_post.return_value.raise_for_status = Mock()

        mcp_config = MCPHttpConfig(
            endpoint='http://127.0.0.1:8080/mcp/tools/customer-comment',
            tool='customer-comment-create',
            callStyle='tool_endpoint'
        )

        skill = Skill(
            id='customer-comment',
            name='Customer Comment',
            implementation=SkillImplementation(
                type='mcp_http',
                mcpConfig=mcp_config
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {
            'ticketId': 'TKT-001',
            'comment': 'Issue resolved'
        })

        assert result == {'result': 'tool_result'}

        # Verify tool_endpoint payload: input_data sent directly
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json', {})
        assert payload['ticketId'] == 'TKT-001'
        assert payload['comment'] == 'Issue resolved'

    @patch('requests.post')
    def test_execute_mcp_http_jsonrpc_proxy(self, mock_post):
        """MCP HTTP with jsonrpc_proxy callStyle (Phase 2+)"""
        mock_response = {
            'jsonrpc': '2.0',
            'result': {'data': 'response'}
        }
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()

        mcp_config = MCPHttpConfig(
            endpoint='http://127.0.0.1:8080/mcp',
            tool='some-tool',
            callStyle='jsonrpc_proxy'
        )

        skill = Skill(
            id='some-skill',
            name='Some Skill',
            implementation=SkillImplementation(
                type='mcp_http',
                mcpConfig=mcp_config
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        result = executor.execute(skill, {'arg': 'value'})

        # Result extracted from jsonrpc response
        assert result == {'data': 'response'}

        # Verify JSON-RPC wrapper
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json', {})
        assert payload['jsonrpc'] == '2.0'
        assert payload['method'] == 'tools/call'
        assert payload['params']['name'] == 'some-tool'
        assert payload['params']['arguments'] == {'arg': 'value'}

    @patch('requests.post')
    def test_mcp_http_timeout(self, mock_post):
        """MCP HTTP timeout raises error"""
        mock_post.side_effect = requests.Timeout()

        mcp_config = MCPHttpConfig(
            endpoint='http://127.0.0.1:8080/mcp/tools/test',
            tool='test-tool',
            callStyle='tool_endpoint'
        )

        skill = Skill(
            id='mcp-timeout',
            name='MCP Timeout',
            implementation=SkillImplementation(
                type='mcp_http',
                mcpConfig=mcp_config
            ),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'timeout' in str(exc_info.value).lower()


class TestSkillExecutorValidation:
    """Input validation"""

    def test_missing_required_field_raises_error(self):
        """Missing required input field raises SkillExecutionError"""
        skill = Skill(
            id='test-skill',
            name='Test',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={
                'type': 'object',
                'required': ['name']
            }
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'validation failed' in str(exc_info.value).lower()

    def test_invalid_input_type_raises_error(self):
        """Invalid input type raises SkillExecutionError"""
        skill = Skill(
            id='test-skill',
            name='Test',
            implementation=SkillImplementation(type='builtin'),
            inputSchema={
                'type': 'object',
                'properties': {
                    'ids': {'type': 'array'}
                }
            }
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {'ids': 'not-array'})

        assert 'validation failed' in str(exc_info.value).lower()


class TestSkillExecutorPhase1:
    """Phase 1 constraints"""

    def test_custom_skill_not_supported_in_phase1(self):
        """Custom code skill raises NotImplementedError"""
        skill = Skill(
            id='custom-script',
            name='Custom',
            implementation=SkillImplementation(type='custom'),
            inputSchema={'type': 'object'}
        )

        executor = SkillExecutor()
        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute(skill, {})

        assert 'not available in Phase 1' in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
