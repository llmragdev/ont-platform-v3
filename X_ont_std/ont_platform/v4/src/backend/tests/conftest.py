"""pytest 설정"""
import sys
from pathlib import Path

# 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import asyncio


def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "asyncio: async test"
    )
    config.addinivalue_line(
        "markers", "benchmark: performance test"
    )


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정 (asyncio)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_sparql_result():
    """Mock SPARQL 결과"""
    return [
        {
            'neighbor': 'http://example.org/concept/2',
            'predicate': 'http://www.w3.org/2000/01/rdf-schema#subClassOf',
            'direction': 'outgoing',
            'nodeLabel': 'Child Concept',
            'nodeType': 'http://www.w3.org/2000/01/rdf-schema#Class'
        },
        {
            'neighbor': 'http://example.org/concept/3',
            'predicate': 'http://www.w3.org/2000/01/rdf-schema#subClassOf',
            'direction': 'incoming',
            'nodeLabel': 'Parent Concept',
            'nodeType': 'http://www.w3.org/2000/01/rdf-schema#Class'
        }
    ]


@pytest.fixture
def sample_rdf_turtle():
    """샘플 Turtle RDF"""
    return """
    @prefix ex: <http://example.org/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Concept1 rdfs:label "Concept 1" ;
               rdfs:subClassOf ex:Concept2 .

    ex:Concept2 rdfs:label "Concept 2" ;
               rdfs:subClassOf ex:Concept3 .
    """


@pytest.fixture
def sample_rdf_xml():
    """샘플 RDF/XML"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
             xmlns:ex="http://example.org/">
        <rdf:Description rdf:about="http://example.org/Concept1">
            <rdfs:label>Concept 1</rdfs:label>
            <rdfs:subClassOf rdf:resource="http://example.org/Concept2"/>
        </rdf:Description>
    </rdf:RDF>
    """
