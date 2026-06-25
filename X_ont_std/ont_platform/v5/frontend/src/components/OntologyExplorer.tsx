'use client';

import { useState } from 'react';
import SPARQLQueryBuilder from './SPARQLQueryBuilder';

interface QueryResult {
  query_id: string;
  variables: string[];
  results: Record<string, any>[];
  result_count: number;
  execution_time_ms: number;
  timestamp: string;
}

interface ExplorationTab {
  id: 'query' | 'entities' | 'relationships' | 'import' | 'history';
  label: string;
}

const TABS: ExplorationTab[] = [
  { id: 'query', label: 'SPARQL Query' },
  { id: 'entities', label: 'Entities' },
  { id: 'relationships', label: 'Relationships' },
  { id: 'import', label: 'Import' },
  { id: 'history', label: 'Query History' }
];

export default function OntologyExplorer() {
  const [activeTab, setActiveTab] = useState<ExplorationTab['id']>('query');
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryResult[]>([]);

  // Form states
  const [entityUri, setEntityUri] = useState('');
  const [typeUri, setTypeUri] = useState('');
  const [importSource, setImportSource] = useState('dbpedia');
  const [importSourceId, setImportSourceId] = useState('');

  const handleExecuteQuery = async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ontology/sparql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        throw new Error('Failed to execute query');
      }

      const result = await response.json();
      setQueryResult(result);
      setQueryHistory([result, ...queryHistory.slice(0, 9)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExploreEntity = async () => {
    if (!entityUri.trim()) {
      setError('Please enter an entity URI');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/ontology/explore?entity_uri=${encodeURIComponent(entityUri)}`
      );

      if (!response.ok) {
        throw new Error('Failed to explore entity');
      }

      const result = await response.json();
      setQueryResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQueryByType = async () => {
    if (!typeUri.trim()) {
      setError('Please enter a type URI');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/ontology/entities/by-type?type_uri=${encodeURIComponent(typeUri)}`
      );

      if (!response.ok) {
        throw new Error('Failed to query by type');
      }

      const result = await response.json();
      setQueryResult({
        query_id: Date.now().toString(),
        variables: ['x'],
        results: result.entities || [],
        result_count: result.count || 0,
        execution_time_ms: 0,
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportOntology = async () => {
    if (!importSourceId.trim()) {
      setError('Please enter a source ID');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ontology/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: importSource,
          source_id: importSourceId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to import ontology');
      }

      const result = await response.json();
      setError(null);
      alert(`Successfully imported ${result.total_triples} triples from ${importSource}`);
      setImportSourceId('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4 p-4">
      {/* Tabs */}
      <div className="flex gap-2 border-b bg-white rounded-t">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 border-b-2 font-medium ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Tab Content */}
      <div className="bg-white rounded shadow">
        {/* SPARQL Query Tab */}
        {activeTab === 'query' && (
          <div className="p-4">
            <SPARQLQueryBuilder onExecute={handleExecuteQuery} isLoading={isLoading} />
          </div>
        )}

        {/* Entities Tab */}
        {activeTab === 'entities' && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Explore Entity (by URI)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={entityUri}
                  onChange={(e) => setEntityUri(e.target.value)}
                  placeholder="Enter entity URI"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded"
                />
                <button
                  onClick={handleExploreEntity}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                  Explore
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Find by Type (URI)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={typeUri}
                  onChange={(e) => setTypeUri(e.target.value)}
                  placeholder="Enter type URI"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded"
                />
                <button
                  onClick={handleQueryByType}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                  Find
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Relationships Tab */}
        {activeTab === 'relationships' && (
          <div className="p-4">
            <p className="text-gray-600 mb-4">
              Use the SPARQL Query tab to find relationships with queries like:
            </p>
            <pre className="bg-gray-100 p-3 rounded font-mono text-sm overflow-auto">
              {`SELECT ?predicate ?object WHERE {
  <ENTITY_URI> ?predicate ?object
}`}
            </pre>
          </div>
        )}

        {/* Import Tab */}
        {activeTab === 'import' && (
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Source
              </label>
              <select
                value={importSource}
                onChange={(e) => setImportSource(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                <option value="dbpedia">DBpedia</option>
                <option value="wikidata">Wikidata</option>
                <option value="schema_org">schema.org</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Source ID
              </label>
              <input
                type="text"
                value={importSourceId}
                onChange={(e) => setImportSourceId(e.target.value)}
                placeholder={
                  importSource === 'dbpedia'
                    ? 'Entity type (e.g., Person)'
                    : importSource === 'wikidata'
                    ? 'Wikidata ID (e.g., Q42)'
                    : 'Schema type (e.g., Person)'
                }
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <button
              onClick={handleImportOntology}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              {isLoading ? 'Importing...' : 'Import Ontology'}
            </button>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="p-4">
            {queryHistory.length === 0 ? (
              <p className="text-gray-600">No query history yet</p>
            ) : (
              <div className="space-y-2">
                {queryHistory.map((result, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded border">
                    <div className="text-sm text-gray-600">
                      {new Date(result.timestamp).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-700 font-mono">
                      Results: {result.result_count} ({result.execution_time_ms}ms)
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {queryResult && (
        <div className="bg-white rounded shadow p-4">
          <h3 className="text-lg font-semibold mb-3">Query Results</h3>
          <div className="mb-3 text-sm text-gray-600">
            <div>ID: {queryResult.query_id}</div>
            <div>Count: {queryResult.result_count}</div>
            <div>Time: {queryResult.execution_time_ms}ms</div>
          </div>

          {queryResult.variables.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b bg-gray-50">
                    {queryResult.variables.map((v) => (
                      <th key={v} className="p-2 text-left font-medium">
                        {v}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queryResult.results.map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      {queryResult.variables.map((v) => (
                        <td key={v} className="p-2">
                          <div className="text-xs break-words max-w-xs">
                            {JSON.stringify(row[v] ?? row[`?${v}`])}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
