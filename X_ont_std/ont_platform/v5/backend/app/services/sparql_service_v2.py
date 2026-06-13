"""Priority 2: Advanced SPARQL Engine with rdflib (Full SPARQL Support)"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
    from rdflib.namespace import XSD
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


class SPARQLServiceV2:
    """Advanced SPARQL service with full SPARQL support via rdflib"""

    def __init__(self, store_path: Optional[Path] = None):
        if not RDFLIB_AVAILABLE:
            raise ImportError("rdflib is required. Install with: pip install rdflib")

        self.graph = Graph()
        self.store_path = store_path
        self.namespaces = {
            "ex": Namespace("http://example.org/"),
            "rdf": RDF,
            "rdfs": RDFS,
            "xsd": XSD,
        }

        # Bind common namespaces
        for prefix, ns in self.namespaces.items():
            self.graph.bind(prefix, ns)

        if store_path and store_path.exists():
            self._load_from_file()

    def _load_from_file(self) -> None:
        """Load RDF graph from N-Triples file"""
        try:
            self.graph.parse(str(self.store_path), format="nt")
        except Exception as e:
            print(f"Warning: Failed to load graph from {self.store_path}: {e}")

    def add_triple(self, subject: str, predicate: str, obj: str) -> None:
        """Add a single triple to the graph"""
        s = URIRef(subject)
        p = URIRef(predicate)
        o = URIRef(obj)
        self.graph.add((s, p, o))

    def add_triple_literal(self, subject: str, predicate: str, obj: str,
                          datatype: Optional[str] = None) -> None:
        """Add a triple with a literal object"""
        s = URIRef(subject)
        p = URIRef(predicate)
        if datatype:
            o = Literal(obj, datatype=URIRef(datatype))
        else:
            # Auto-detect numeric types for better SPARQL filter support
            try:
                if '.' in obj:
                    float(obj)
                    o = Literal(obj, datatype=XSD.decimal)
                else:
                    int(obj)
                    o = Literal(obj, datatype=XSD.integer)
            except ValueError:
                o = Literal(obj)
        self.graph.add((s, p, o))

    def query(self, sparql_string: str) -> Dict[str, Any]:
        """Execute SPARQL query (supports SELECT, CONSTRUCT, DESCRIBE, ASK)"""
        try:
            results = self.graph.query(sparql_string)

            query_type = self._detect_query_type(sparql_string)

            if query_type == "SELECT":
                return self._format_select_results(results)
            elif query_type == "CONSTRUCT":
                return self._format_construct_results(results)
            elif query_type == "DESCRIBE":
                return self._format_describe_results(results)
            elif query_type == "ASK":
                return self._format_ask_results(results)
            else:
                return {"error": "Unknown query type"}
        except Exception as e:
            return {"error": str(e)}

    def _detect_query_type(self, sparql_string: str) -> str:
        """Detect SPARQL query type (handles PREFIX clauses)"""
        upper_query = sparql_string.upper().strip()
        # Skip PREFIX declarations to find the actual query keyword
        for keyword in ["SELECT", "CONSTRUCT", "DESCRIBE", "ASK"]:
            if keyword in upper_query:
                return keyword
        return "UNKNOWN"

    def _format_select_results(self, results) -> Dict[str, Any]:
        """Format SELECT query results"""
        rows = []
        for row in results:
            row_dict = {}
            for var in results.vars:
                value = row[var]
                # Standard format: {"variable": {"value": "..."}}
                row_dict[str(var)] = {
                    "value": str(value) if value else None,
                    "type": "uri" if str(value).startswith("http") else "literal"
                }
            rows.append(row_dict)

        return {
            "type": "SELECT",
            "results": rows,
            "count": len(rows)
        }

    def _format_construct_results(self, results) -> Dict[str, Any]:
        """Format CONSTRUCT query results (returns RDF triples)"""
        triples = []
        for s, p, o in results:
            triples.append({
                "subject": str(s),
                "predicate": str(p),
                "object": str(o)
            })

        return {
            "type": "CONSTRUCT",
            "triples": triples,
            "count": len(triples)
        }

    def _format_describe_results(self, results) -> Dict[str, Any]:
        """Format DESCRIBE query results"""
        triples = []
        for s, p, o in results:
            triples.append({
                "subject": str(s),
                "predicate": str(p),
                "object": str(o)
            })

        return {
            "type": "DESCRIBE",
            "triples": triples,
            "count": len(triples)
        }

    def _format_ask_results(self, results) -> Dict[str, Any]:
        """Format ASK query results"""
        return {
            "type": "ASK",
            "boolean": bool(results)
        }

    def save(self) -> None:
        """Save graph to N-Triples file"""
        if self.store_path:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            self.graph.serialize(destination=str(self.store_path), format="nt")

    def get_triple_count(self) -> int:
        """Get number of triples in graph"""
        return len(self.graph)

    def clear(self) -> None:
        """Clear all triples"""
        self.graph.close()
        self.graph = Graph()
        for prefix, ns in self.namespaces.items():
            self.graph.bind(prefix, ns)

    def get_subjects(self) -> List[str]:
        """Get all unique subjects"""
        return list(set(str(s) for s, _, _ in self.graph))

    def get_predicates(self) -> List[str]:
        """Get all unique predicates"""
        return list(set(str(p) for _, p, _ in self.graph))

    def get_objects(self) -> List[str]:
        """Get all unique objects"""
        return list(set(str(o) for _, _, o in self.graph))
