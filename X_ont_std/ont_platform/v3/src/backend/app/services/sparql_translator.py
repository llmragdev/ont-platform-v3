"""SPARQL to SQL Translator - Phase 1: Core Architecture"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from sqlalchemy import select, and_, or_, func, cast, String
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.db.models import Entity, Relationship


class QueryType(str, Enum):
    """SPARQL query types"""
    SELECT = "SELECT"
    ASK = "ASK"
    CONSTRUCT = "CONSTRUCT"
    DESCRIBE = "DESCRIBE"


class PatternType(str, Enum):
    """RDF triple pattern types"""
    ENTITY_LOOKUP = "entity_lookup"        # Constant subject
    PROPERTY_FILTER = "property_filter"    # Variable subject + property
    RELATION = "relation"                  # Relationship join
    UNSUPPORTED = "unsupported"


@dataclass
class TriplePattern:
    """Standardized RDF triple pattern representation"""
    subject: Optional[str]      # URI or ?variable or None
    predicate: str              # Always present (constant URI)
    obj: Optional[str]          # URI, literal, ?variable, or None

    # Metadata
    pattern_type: PatternType = PatternType.UNSUPPORTED
    is_property_pattern: bool = False   # True if predicate = entity property
    is_relation_pattern: bool = False   # True if targets relationships

    def get_variable_bindings(self) -> List[str]:
        """Extract ?variables from pattern"""
        bindings = []
        for part in [self.subject, self.obj]:
            if part and isinstance(part, str) and part.startswith("?"):
                if part not in bindings:
                    bindings.append(part)
        return bindings

    def __repr__(self) -> str:
        return f"({self.subject} {self.predicate} {self.obj}) [{self.pattern_type}]"


class PatternMatcher:
    """Matches triple patterns and extracts components"""

    # Regex patterns for different triple types
    PATTERNS = {
        # Constant subject: ex:ship1 ex:name ?name
        "entity_lookup": r"^<([^>]+)>\s+<([^>]+)>\s+(\?[\w]+)$",

        # Variable subject with type: ?x rdf:type "Entity"
        "type_filter": r"^(\?[\w]+)\s+rdf:type\s+(.+)$",

        # Variable subject with property: ?x ex:prop "value" or ?x ex:prop ?y
        "property_filter": r"^(\?[\w]+)\s+<([^>]+)>\s+(.+)$",

        # Relationship: ?x ex:rel ?y
        "relation": r"^(\?[\w]+)\s+<([^>]+)>\s+(\?[\w]+)$",
    }

    @staticmethod
    def match(pattern_str: str) -> Tuple[PatternType, Dict[str, Any]]:
        """Match triple pattern and extract components"""
        pattern_str = pattern_str.strip()

        # Try each pattern
        if " " not in pattern_str:
            return PatternType.UNSUPPORTED, {}

        # Split by whitespace (simple approach, will improve)
        parts = pattern_str.split()
        if len(parts) < 3:
            return PatternType.UNSUPPORTED, {}

        subject, predicate, obj = parts[0], parts[1], parts[2]

        # Helper: Extract URI from angle brackets or prefixed notation
        def extract_uri(s: str) -> str:
            if s.startswith("<") and s.endswith(">"):
                return s[1:-1]
            return s

        def is_uri(s: str) -> bool:
            return s.startswith("<") or ":" in s

        def is_variable(s: str) -> bool:
            return s.startswith("?")

        def is_literal(s: str) -> bool:
            return s.startswith('"') or s.startswith("'")

        # Determine pattern type
        if is_uri(subject) and is_uri(predicate) and is_variable(obj):
            # entity_lookup: <uri> <uri> ?var OR ex:uri ex:pred ?var
            return PatternType.ENTITY_LOOKUP, {
                "subject": extract_uri(subject),
                "predicate": extract_uri(predicate),
                "object_var": obj,
                "is_property": True,
            }

        elif is_variable(subject) and is_uri(predicate) and is_variable(obj):
            # relation: ?var <uri> ?var OR ?var ex:rel ?var
            return PatternType.RELATION, {
                "subject_var": subject,
                "predicate": extract_uri(predicate),
                "object_var": obj,
            }

        elif is_variable(subject) and is_uri(predicate):
            # property_filter: ?var <uri> "value" or ?var <uri> ?var
            return PatternType.PROPERTY_FILTER, {
                "subject_var": subject,
                "predicate": extract_uri(predicate),
                "object": obj.strip('"\''),
                "is_variable": is_variable(obj),
            }

        return PatternType.UNSUPPORTED, {}


class SPARQLParser:
    """Parses SPARQL query into components"""

    @staticmethod
    def extract_prefixes(query: str) -> Dict[str, str]:
        """Extract PREFIX declarations from SPARQL query"""
        prefixes = {}
        # Match PREFIX declarations: PREFIX alias: <uri>
        prefix_pattern = r'PREFIX\s+(\w+):\s*<([^>]+)>'
        for match in re.finditer(prefix_pattern, query, re.IGNORECASE):
            alias = match.group(1)
            uri = match.group(2)
            prefixes[alias] = uri
        return prefixes

    @staticmethod
    def expand_uri(uri_str: str, prefixes: Dict[str, str]) -> str:
        """Expand prefixed URI to full URI"""
        if uri_str.startswith("<") and uri_str.endswith(">"):
            # Already a full URI in angle brackets
            return uri_str[1:-1]

        if ":" in uri_str and not uri_str.startswith("?"):
            # Prefixed URI like ex:ship1
            prefix, local = uri_str.split(":", 1)
            if prefix in prefixes:
                return f"{prefixes[prefix]}{local}"

        return uri_str

    @staticmethod
    def detect_query_type(query: str) -> QueryType:
        """Detect SPARQL query type"""
        upper_query = query.upper().strip()

        if "SELECT" in upper_query:
            return QueryType.SELECT
        elif "ASK" in upper_query:
            return QueryType.ASK
        elif "CONSTRUCT" in upper_query:
            return QueryType.CONSTRUCT
        elif "DESCRIBE" in upper_query:
            return QueryType.DESCRIBE

        return QueryType.SELECT

    @staticmethod
    def extract_where_clause(query: str) -> str:
        """Extract WHERE clause from SPARQL query"""
        # Find WHERE keyword
        where_match = re.search(r'WHERE\s*\{', query, re.IGNORECASE)
        if not where_match:
            return ""

        # Extract content between { and }
        start = where_match.end()
        brace_count = 1
        i = start

        while i < len(query) and brace_count > 0:
            if query[i] == "{":
                brace_count += 1
            elif query[i] == "}":
                brace_count -= 1
            i += 1

        if brace_count == 0:
            return query[start:i-1]

        return ""

    @staticmethod
    def extract_select_vars(query: str) -> List[str]:
        """Extract SELECT variables from query"""
        select_match = re.search(r'SELECT\s+(.+?)\s+WHERE', query, re.IGNORECASE)
        if not select_match:
            return []

        vars_str = select_match.group(1).strip()

        # Handle DISTINCT
        if vars_str.upper().startswith("DISTINCT"):
            vars_str = vars_str[8:].strip()

        # Split by whitespace
        vars_list = [v.strip() for v in vars_str.split() if v.startswith("?")]
        return vars_list

    @staticmethod
    def extract_triple_patterns(where_clause: str) -> List[str]:
        """Extract triple patterns from WHERE clause"""
        # Remove comments
        where_clause = re.sub(r'#.*$', '', where_clause, flags=re.MULTILINE)

        # Split by . (dot) to get triple patterns
        patterns = []
        current = ""

        for char in where_clause:
            if char == ".":
                pattern = current.strip()
                if pattern and not pattern.startswith("FILTER"):
                    patterns.append(pattern)
                current = ""
            elif char == "{":
                # Skip nested blocks (OPTIONAL, etc.)
                current = ""
            else:
                current += char

        # Handle last pattern if no trailing dot
        if current.strip() and not current.strip().startswith("FILTER"):
            patterns.append(current.strip())

        return [p for p in patterns if p]  # Remove empty patterns

    @staticmethod
    def extract_filter_clause(query: str) -> Optional[str]:
        """Extract FILTER clause from query"""
        # Try pattern: FILTER ... (content)
        filter_match = re.search(r'FILTER\s*\((.+)\)', query)
        if filter_match:
            return filter_match.group(1)

        # Try pattern: FILTER function(...) where function call contains parens
        filter_match = re.search(r'FILTER\s+(\S+\(.+\))', query)
        if filter_match:
            return filter_match.group(1)

        return None


class SPARQLTranslator:
    """Main SPARQL to SQL translator"""

    def __init__(self, db_session: Session, domain_id: str):
        """Initialize translator with database session"""
        self.session = db_session
        self.domain_id = domain_id
        self.variable_bindings: Dict[str, Any] = {}  # ?var → SQL column mapping
        self.query_type = None
        self.select_vars: List[str] = []
        self.triple_patterns: List[TriplePattern] = []
        self.filter_clause: Optional[str] = None
        self.prefixes: Dict[str, str] = {}  # PREFIX declarations

    def translate(self, sparql_query: str) -> Optional[str]:
        """Translate SPARQL query to SQL string"""
        try:
            # Step 0: Extract PREFIX declarations
            self.prefixes = SPARQLParser.extract_prefixes(sparql_query)

            # Step 1: Detect query type
            self.query_type = SPARQLParser.detect_query_type(sparql_query)

            # Step 2: Extract SELECT variables
            self.select_vars = SPARQLParser.extract_select_vars(sparql_query)
            if not self.select_vars:
                self.select_vars = ["*"]

            # Step 3: Extract WHERE clause and patterns
            where_clause = SPARQLParser.extract_where_clause(sparql_query)
            patterns = SPARQLParser.extract_triple_patterns(where_clause)

            # Step 4: Parse each pattern with PREFIX expansion
            for pattern_str in patterns:
                # Expand prefixed URIs in the pattern
                expanded_pattern = self._expand_pattern_uris(pattern_str)

                pattern_type, components = PatternMatcher.match(expanded_pattern)
                triple = TriplePattern(
                    subject=components.get("subject") or components.get("subject_var"),
                    predicate=components.get("predicate", expanded_pattern),
                    obj=components.get("object") or components.get("object_var"),
                    pattern_type=pattern_type,
                    is_property_pattern=components.get("is_property", False),
                    is_relation_pattern=pattern_type == PatternType.RELATION,
                )
                self.triple_patterns.append(triple)

            # Step 5: Extract FILTER clause if present
            self.filter_clause = SPARQLParser.extract_filter_clause(sparql_query)

            # Step 6: Generate SQL (Phase 2: hot-path patterns)
            if self.query_type == QueryType.SELECT:
                return self._generate_select_sql()

            return None

        except Exception as e:
            print(f"Translation error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _expand_pattern_uris(self, pattern_str: str) -> str:
        """Expand all prefixed URIs in a triple pattern"""
        parts = pattern_str.split()
        expanded_parts = []

        for part in parts:
            expanded = SPARQLParser.expand_uri(part, self.prefixes)
            expanded_parts.append(expanded)

        return " ".join(expanded_parts)

    def _generate_select_sql(self) -> Optional[str]:
        """Generate SELECT SQL query for hot-path patterns"""
        if not self.triple_patterns:
            return None

        # Build query based on pattern types
        try:
            if len(self.triple_patterns) == 1:
                pattern = self.triple_patterns[0]

                # Pattern #18: Simple ID lookup (constant subject + predicate, variable object)
                if pattern.pattern_type == PatternType.ENTITY_LOOKUP:
                    return self._generate_entity_lookup_sql(pattern)

                # Pattern #19-21: Property filter (variable subject + predicate + [constant|variable] object)
                elif pattern.pattern_type == PatternType.PROPERTY_FILTER:
                    return self._generate_property_filter_sql(pattern)

                # Pattern #23-26: Relationship join (variable subject + relation + variable object)
                elif pattern.pattern_type == PatternType.RELATION:
                    return self._generate_relation_sql(pattern)

            return None

        except Exception as e:
            print(f"SQL generation error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_entity_lookup_sql(self, pattern: TriplePattern) -> Optional[str]:
        """Generate SQL for Pattern #18: Simple ID lookup"""
        entity_id = pattern.subject
        property_name = pattern.predicate.split("/")[-1]
        object_var = pattern.obj

        # Query: SELECT (properties->>'property') FROM entities WHERE id = ?
        self.variable_bindings[object_var] = f"properties->'{property_name}'"

        return f"""
        SELECT (properties->'{property_name}') as {object_var}
        FROM entities
        WHERE id = '{entity_id}'
        AND domain_id = '{self.domain_id}'
        """

    def _generate_property_filter_sql(self, pattern: TriplePattern) -> Optional[str]:
        """Generate SQL for Patterns #19-22: Property filter with optional FILTER"""
        subject_var = pattern.subject
        property_name = pattern.predicate.split("/")[-1]
        obj = pattern.obj

        # Start with base query
        sql = f"""
        SELECT id, (properties->'{property_name}') as {subject_var}
        FROM entities
        WHERE domain_id = '{self.domain_id}'
        """

        # If object is a constant (not a variable), add equality filter
        if obj and not obj.startswith("?"):
            # Pattern #21: Equality filter
            sql += f" AND (properties->'{property_name}') = '{obj}'"
        elif obj and obj.startswith("?"):
            # Pattern #19: Variable object (just select it)
            sql += f" AND (properties ? '{property_name}')"

        # Add FILTER clause if present (Pattern #20: GT, #22: REGEX)
        if self.filter_clause:
            sql = self._apply_filter_clause(sql, subject_var, property_name)

        return sql

    def _generate_relation_sql(self, pattern: TriplePattern) -> Optional[str]:
        """Generate SQL for Patterns #23-26: Relationship joins"""
        from_var = pattern.subject
        relation_type = pattern.predicate.split("/")[-1]
        to_var = pattern.obj

        # Pattern #23-24: Simple 1-hop relation
        sql = f"""
        SELECT r.to_entity_id as {to_var}
        FROM relationships r
        WHERE r.from_entity_id IN (
            SELECT id FROM entities WHERE domain_id = '{self.domain_id}'
        )
        AND r.relation_type = '{relation_type}'
        """

        return sql

    def _apply_filter_clause(self, sql: str, subject_var: str, property_name: str) -> str:
        """Apply FILTER clause to SQL query"""
        if not self.filter_clause:
            return sql

        filter_clause = self.filter_clause

        # Pattern #20: Numeric comparison (> < >= <=)
        if ">" in filter_clause:
            # Extract numeric value from filter like "?length > 75"
            match = re.search(r'>\s*(\d+(\.\d+)?)', filter_clause)
            if match:
                value = match.group(1)
                sql += f" AND (properties->'{property_name}')::numeric > {value}"

        elif "<" in filter_clause:
            match = re.search(r'<\s*(\d+(\.\d+)?)', filter_clause)
            if match:
                value = match.group(1)
                sql += f" AND (properties->'{property_name}')::numeric < {value}"

        elif ">=" in filter_clause:
            match = re.search(r'>=\s*(\d+(\.\d+)?)', filter_clause)
            if match:
                value = match.group(1)
                sql += f" AND (properties->'{property_name}')::numeric >= {value}"

        elif "<=" in filter_clause:
            match = re.search(r'<=\s*(\d+(\.\d+)?)', filter_clause)
            if match:
                value = match.group(1)
                sql += f" AND (properties->'{property_name}')::numeric <= {value}"

        # Pattern #22: Regex filter
        elif "regex" in filter_clause.lower():
            match = re.search(r'regex\(.*?,\s*["\']([^"\']*)["\']', filter_clause)
            if match:
                pattern_str = match.group(1)
                sql += f" AND (properties->'{property_name}') ~ '{pattern_str}'"

        return sql

    # Instance method wrappers for convenience
    def _detect_query_type(self, query: str) -> QueryType:
        """Instance wrapper for SPARQLParser.detect_query_type"""
        return SPARQLParser.detect_query_type(query)

    def _extract_select_vars(self, query: str) -> List[str]:
        """Instance wrapper for SPARQLParser.extract_select_vars"""
        return SPARQLParser.extract_select_vars(query)

    def _extract_where_clause(self, query: str) -> str:
        """Instance wrapper for SPARQLParser.extract_where_clause"""
        return SPARQLParser.extract_where_clause(query)

    def _extract_triple_patterns(self, where_clause: str) -> List[str]:
        """Instance wrapper for SPARQLParser.extract_triple_patterns"""
        return SPARQLParser.extract_triple_patterns(where_clause)

    def _extract_filter_clause(self, query: str) -> Optional[str]:
        """Instance wrapper for SPARQLParser.extract_filter_clause"""
        return SPARQLParser.extract_filter_clause(query)

    def _match_pattern(self, pattern_str: str) -> Tuple[PatternType, Dict[str, Any]]:
        """Instance wrapper for PatternMatcher.match"""
        return PatternMatcher.match(pattern_str)

    def execute(self, sparql_query: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute translated SPARQL query and return results"""
        sql = self.translate(sparql_query)

        if not sql:
            return {"error": "Translation failed", "query": sparql_query}

        # Phase 1: Skeleton - actual execution in Phase 2
        return {
            "query_type": self.query_type.value,
            "select_vars": self.select_vars,
            "patterns": [str(p) for p in self.triple_patterns],
            "bindings": self.variable_bindings,
            "sql_skeleton": sql,
        }
