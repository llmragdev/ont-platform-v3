'use client';

import { useState } from 'react';

interface QueryTemplate {
  name: string;
  description: string;
  query: string;
}

const QUERY_TEMPLATES: QueryTemplate[] = [
  {
    name: 'List All Entities',
    description: 'Get all entities in the ontology',
    query: 'SELECT ?x WHERE { ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type }'
  },
  {
    name: 'Find by Type',
    description: 'Find all entities of a specific type',
    query: 'SELECT ?x WHERE { ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <TYPE_URI> }'
  },
  {
    name: 'Find Relationships',
    description: 'Find relationships of an entity',
    query: 'SELECT ?predicate ?object WHERE { <ENTITY_URI> ?predicate ?object }'
  },
  {
    name: 'Check Entity Existence',
    description: 'Check if an entity exists',
    query: 'ASK WHERE { <ENTITY_URI> ?p ?o }'
  },
  {
    name: 'Property Values',
    description: 'Get all values of a property',
    query: 'SELECT ?x ?value WHERE { ?x <PROPERTY_URI> ?value }'
  }
];

interface SPARQLQueryBuilderProps {
  onExecute: (query: string) => void;
  isLoading?: boolean;
}

export default function SPARQLQueryBuilder({ onExecute, isLoading = false }: SPARQLQueryBuilderProps) {
  const [query, setQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);

  const handleExecute = () => {
    if (query.trim()) {
      onExecute(query);
    }
  };

  const handleSelectTemplate = (template: QueryTemplate) => {
    setSelectedTemplate(template);
    setQuery(template.query);
  };

  const handleClear = () => {
    setQuery('');
    setSelectedTemplate(null);
  };

  return (
    <div className="space-y-4 p-4 bg-white rounded-lg shadow">
      <div>
        <h3 className="text-lg font-semibold mb-3">SPARQL Query Builder</h3>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quick Templates
          </label>
          <div className="grid grid-cols-1 gap-2">
            {QUERY_TEMPLATES.map((template, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectTemplate(template)}
                className={`p-3 text-left border rounded transition-all ${
                  selectedTemplate?.name === template.name
                    ? 'bg-blue-50 border-blue-500'
                    : 'bg-gray-50 border-gray-300 hover:border-blue-300'
                }`}
              >
                <div className="font-medium text-sm">{template.name}</div>
                <div className="text-xs text-gray-600">{template.description}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter SPARQL query or select a template above"
            className="w-full h-32 p-3 border border-gray-300 rounded font-mono text-sm"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleExecute}
            disabled={isLoading || !query.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {isLoading ? 'Executing...' : 'Execute Query'}
          </button>
          <button
            onClick={handleClear}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}
