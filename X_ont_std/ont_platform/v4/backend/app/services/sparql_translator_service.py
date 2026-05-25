"""SPARQL Translator Service - Wrapper with dependency injection and tenant filtering"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.services.sparql_translator import SPARQLTranslator


class SPARQLTranslatorService:
    """Service layer for SPARQL→SQL translation with DI and multi-tenant support"""

    def __init__(self, db: Session):
        """Initialize translator service with database session"""
        self.db = db

    def execute_sparql(
        self,
        query: str,
        domain_id: str = "default",
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SPARQL query and return formatted results

        Args:
            query: SPARQL query string
            domain_id: Tenant/domain identifier for filtering
            limit: Maximum number of results to return

        Returns:
            Dict with query results, error info, or execution metrics
        """
        try:
            # Create translator instance for this query
            translator = SPARQLTranslator(self.db, domain_id)

            # Execute query and get results
            result = translator.execute(query, limit=limit)

            # If successful, results dict already contains all needed fields
            if "error" not in result:
                return result

            # If there was an error, ensure consistent error response format
            return {
                "error": result.get("error", "Unknown error"),
                "error_type": result.get("error_type", "ExecutionError"),
                "query": query,
                "sql_attempted": result.get("sql_attempted"),
            }

        except Exception as e:
            # Catch any service-level errors
            return {
                "error": f"Service error: {str(e)}",
                "error_type": "ServiceError",
                "query": query,
            }

    def translate_only(self, query: str, domain_id: str = "default") -> Dict[str, Any]:
        """
        Translate SPARQL to SQL without executing

        Args:
            query: SPARQL query string
            domain_id: Tenant/domain identifier

        Returns:
            Dict with SQL translation and pattern info
        """
        try:
            translator = SPARQLTranslator(self.db, domain_id)
            sql = translator.translate(query)

            if not sql:
                return {"error": "Translation failed", "query": query}

            return {
                "sql": sql,
                "query_type": translator.query_type.value,
                "select_vars": translator.select_vars,
                "patterns": [str(p) for p in translator.triple_patterns],
                "bindings": translator.variable_bindings,
            }
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "query": query,
            }
