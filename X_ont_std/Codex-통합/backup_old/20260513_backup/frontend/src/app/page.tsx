"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { HybridAskResponse, ObjectContext, OntologyObject, OntologySchema, Relationship, StructuredData } from "@/types/api";

type View = "ontology" | "objects" | "relationships" | "ask";

const views: Array<{ key: View; label: string; desc: string }> = [
  { key: "ontology", label: "온톨로지 관리", desc: "객체 타입, 관계 타입, 액션 타입" },
  { key: "objects", label: "객체 탐색", desc: "객체와 관계 컨텍스트" },
  { key: "relationships", label: "관계 관리", desc: "관계 인스턴스 조회와 추가" },
  { key: "ask", label: "하이브리드 질의", desc: "온톨로지 구조 질의 + 문서 RAG 근거" }
];

export default function Page() {
  const [view, setView] = useState<View>("ontology");
  const [schema, setSchema] = useState<OntologySchema | null>(null);
  const [overview, setOverview] = useState<Record<string, number> | null>(null);
  const [objects, setObjects] = useState<OntologyObject[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedType, setSelectedType] = useState<string>("Customer");
  const [selectedObjectId, setSelectedObjectId] = useState<string>("C001");
  const [context, setContext] = useState<ObjectContext | null>(null);
  const [ask, setAsk] = useState("5000 이상 주문 목록과 승인 근거를 알려줘");
  const [askResult, setAskResult] = useState<HybridAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const objectTypeNames = useMemo(() => schema?.object_types.map((item) => item.name) ?? [], [schema]);
  const relationshipTypeNames = useMemo(() => schema?.relationship_types.map((item) => item.name) ?? [], [schema]);

  async function refreshAll(typeName = selectedType) {
    try {
      const [health, schemaRes, objectRes, relationshipRes] = await Promise.all([
        api.health(),
        api.schema(),
        api.objects(typeName),
        api.relationships()
      ]);
      setOverview(health.overview);
      setSchema(schemaRes);
      setObjects(objectRes.objects);
      setRelationships(relationshipRes.relationships);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    void refreshAll(selectedType);
  }, [selectedType]);

  async function loadContext(id: string) {
    setSelectedObjectId(id);
    try {
      setContext(await api.objectContext(id));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function submitAsk() {
    try {
      setAskResult(await api.hybridAsk(ask));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function quickAddRelation() {
    try {
      await api.addRelationship({ type: "PLACED_ORDER", source_id: "C001", target_id: "O003", properties: {} });
      await refreshAll(selectedType);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const title = views.find((item) => item.key === view)!;

  return (
    <div className="flex min-h-screen">
      <aside className="w-72 border-r border-slate-200 bg-white p-4">
        <h1 className="text-lg font-bold">Codex Ontology</h1>
        <p className="mt-1 text-xs text-slate-500">설정형 객체, 관계, 액션 기반 업무 AI</p>
        <nav className="mt-6 space-y-2">
          {views.map((item) => (
            <button
              key={item.key}
              className={`w-full rounded-md px-3 py-2 text-left ${view === item.key ? "bg-blue-50 text-blue-700" : "hover:bg-slate-50"}`}
              onClick={() => setView(item.key)}
            >
              <div className="text-sm font-semibold">{item.label}</div>
              <div className="text-xs text-slate-500">{item.desc}</div>
            </button>
          ))}
        </nav>
      </aside>

      <main className="flex-1 p-6">
        <header className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">{title.label}</h2>
            <p className="text-sm text-slate-500">{title.desc}</p>
          </div>
          {overview && (
            <div className="flex gap-2">
              <span className="badge">Types {overview.object_type_count}</span>
              <span className="badge">Links {overview.relationship_type_count}</span>
              <span className="badge">Objects {overview.object_count}</span>
              <span className="badge">Relations {overview.relationship_count}</span>
            </div>
          )}
        </header>

        {error && <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

        {view === "ontology" && schema && <OntologyView schema={schema} />}

        {view === "objects" && (
          <div className="grid grid-cols-[1fr_360px] gap-4">
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">객체 목록</h3>
                <select className="input" value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                  {objectTypeNames.map((name) => <option key={name}>{name}</option>)}
                </select>
              </div>
              <div className="panel-body p-0">
                <table className="table">
                  <thead><tr><th>ID</th><th>Type</th><th>Name / Status</th><th>Action</th></tr></thead>
                  <tbody>
                    {objects.map((object) => (
                      <tr key={object.id}>
                        <td className="font-semibold">{object.id}</td>
                        <td>{object.type}</td>
                        <td>{String(object.name ?? object.status ?? "-")}</td>
                        <td><button className="btn btn-ghost py-1" onClick={() => loadContext(object.id)}>Context</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <ContextView context={context} selectedObjectId={selectedObjectId} />
          </div>
        )}

        {view === "relationships" && (
          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold">관계 인스턴스</h3>
              <div className="flex items-center gap-2">
                <select className="input" onChange={(e) => void api.relationships(e.target.value).then((r) => setRelationships(r.relationships))}>
                  <option value="">All</option>
                  {relationshipTypeNames.map((name) => <option key={name}>{name}</option>)}
                </select>
                <button className="btn btn-primary" onClick={quickAddRelation}>샘플 관계 추가</button>
              </div>
            </div>
            <div className="panel-body p-0">
              <table className="table">
                <thead><tr><th>ID</th><th>Type</th><th>Source</th><th>Target</th><th>Properties</th></tr></thead>
                <tbody>
                  {relationships.map((rel) => (
                    <tr key={rel.id}>
                      <td>{rel.id}</td>
                      <td>{rel.type}</td>
                      <td>{rel.source_id}</td>
                      <td>{rel.target_id}</td>
                      <td><code>{JSON.stringify(rel.properties)}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {view === "ask" && (
          <div className="space-y-4">
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">온톨로지 + 문서 RAG 질의</h3>
                <span className="text-xs text-slate-500">필터, 비교, 계산, 객체 관계를 자동 계획합니다</span>
              </div>
              <div className="panel-body flex gap-2">
                <input className="input flex-1" value={ask} onChange={(e) => setAsk(e.target.value)} />
                <button className="btn btn-primary" onClick={submitAsk}>질의 실행</button>
              </div>
            </section>
            {askResult && (
              <section className="panel">
                <div className="panel-header">
                  <h3 className="text-sm font-semibold">응답</h3>
                  <div className="flex gap-2">
                    <span className="badge">{askResult.query_type}</span>
                    <span className="badge">nodes {askResult.ontology_nodes.length}</span>
                  </div>
                </div>
                <div className="panel-body space-y-3">
                  <p className="text-sm leading-relaxed">{askResult.answer}</p>
                  <div>
                    <div className="text-xs font-semibold text-slate-500">구조형 결과</div>
                    <StructuredTable data={askResult.structured_data} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-500">Query Plan</div>
                    <pre className="mt-1 whitespace-pre-wrap rounded-md bg-slate-50 p-2 text-xs">{JSON.stringify(askResult.plan, null, 2)}</pre>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-500">Trace</div>
                    <div className="mt-1 text-xs text-slate-600">{askResult.trace.join(" -> ")}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-500">문서 근거</div>
                    <div className="mt-2 grid gap-2">
                      {askResult.vector_evidence.map((doc) => (
                        <div key={doc.id} className="rounded-md border border-slate-200 p-3 text-sm">
                          <div className="font-semibold">{doc.title} <span className="badge">score {doc.score}</span></div>
                          <div className="mt-1 text-xs text-slate-600">{doc.text}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function StructuredTable({ data }: { data: StructuredData }) {
  return (
    <div className="mt-2 overflow-x-auto rounded-md border border-slate-200">
      <table className="table">
        <thead>
          <tr>{data.headers.map((header) => <th key={header}>{header}</th>)}</tr>
        </thead>
        <tbody>
          {data.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OntologyView({ schema }: { schema: OntologySchema }) {
  return (
    <div className="grid gap-4">
      <section className="panel">
        <div className="panel-header"><h3 className="text-sm font-semibold">객체 타입</h3></div>
        <div className="panel-body grid gap-3 md:grid-cols-3">
          {schema.object_types.map((type) => (
            <div key={type.name} className="rounded-md border border-slate-200 p-3">
              <div className="font-semibold">{type.display_name ?? type.name} <span className="text-xs text-slate-400">{type.name}</span></div>
              <div className="mt-2 flex flex-wrap gap-1">
                {type.properties.map((prop) => <span className="badge" key={prop.name}>{prop.name}:{prop.type}</span>)}
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-header"><h3 className="text-sm font-semibold">관계 타입</h3></div>
        <div className="panel-body grid gap-3 md:grid-cols-2">
          {schema.relationship_types.map((rel) => (
            <div key={rel.name} className="rounded-md border border-slate-200 p-3">
              <div className="font-semibold">{rel.display_name ?? rel.name}</div>
              <div className="mt-1 text-sm text-slate-600">{rel.source_type} --{rel.name}--&gt; {rel.target_type}</div>
              <span className="badge mt-2">{rel.cardinality}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-header"><h3 className="text-sm font-semibold">액션 타입</h3></div>
        <div className="panel-body flex flex-wrap gap-2">
          {schema.action_types.map((action) => (
            <span key={action.name} className="badge">{action.display_name ?? action.name} / {action.target_type}</span>
          ))}
        </div>
      </section>
    </div>
  );
}

function ContextView({ context, selectedObjectId }: { context: ObjectContext | null; selectedObjectId: string }) {
  return (
    <aside className="panel">
      <div className="panel-header"><h3 className="text-sm font-semibold">객체 컨텍스트</h3></div>
      <div className="panel-body space-y-4">
        {!context ? (
          <div className="text-sm text-slate-500">{selectedObjectId}의 Context 버튼을 눌러보세요.</div>
        ) : (
          <>
            <div>
              <div className="text-xs text-slate-500">Selected</div>
              <div className="font-semibold">{context.object.id} ({context.object.type})</div>
              <pre className="mt-2 whitespace-pre-wrap rounded-md bg-slate-50 p-2 text-xs">{JSON.stringify(context.object, null, 2)}</pre>
            </div>
            <RelationBlock title="Incoming" items={context.incoming.map((item) => `${item.source.id} --${item.relationship}--> ${context.object.id}`)} />
            <RelationBlock title="Outgoing" items={context.outgoing.map((item) => `${context.object.id} --${item.relationship}--> ${item.target.id}`)} />
            <RelationBlock title="Documents" items={context.documents.map((item) => item.title)} />
            <RelationBlock title="Actions" items={context.available_actions.map((item) => item.display_name ?? item.name)} />
          </>
        )}
      </div>
    </aside>
  );
}

function RelationBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="text-xs font-semibold text-slate-500">{title}</div>
      <ul className="mt-1 space-y-1 text-sm">
        {items.length === 0 ? <li className="text-slate-400">None</li> : items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}
