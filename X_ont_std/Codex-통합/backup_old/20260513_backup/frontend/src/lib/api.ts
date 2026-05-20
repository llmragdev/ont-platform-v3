import type { AskResponse, HybridAskResponse, ObjectContext, OntologyObject, OntologySchema, Relationship } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; overview: Record<string, number> }>("/api/health"),
  schema: () => request<OntologySchema>("/api/ontology/schema"),
  objects: (type?: string) => request<{ objects: OntologyObject[] }>(`/api/ontology/objects${type ? `?type=${encodeURIComponent(type)}` : ""}`),
  objectContext: (id: string) => request<ObjectContext>(`/api/ontology/objects/${encodeURIComponent(id)}/context`),
  relationships: (type?: string) => request<{ relationships: Relationship[] }>(`/api/ontology/relationships${type ? `?type=${encodeURIComponent(type)}` : ""}`),
  addRelationship: (payload: { type: string; source_id: string; target_id: string; properties: Record<string, unknown> }) =>
    request<Relationship>("/api/ontology/relationships", { method: "POST", body: JSON.stringify(payload) }),
  ask: (question: string, objectId?: string) =>
    request<AskResponse>("/api/ask", { method: "POST", body: JSON.stringify({ question, object_id: objectId || null }) }),
  hybridAsk: (question: string, objectId?: string) =>
    request<HybridAskResponse>("/api/hybrid/ask", { method: "POST", body: JSON.stringify({ question, object_id: objectId || null }) })
};
