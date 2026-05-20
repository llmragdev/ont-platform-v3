import axios from "axios";

const BASE_URL = "http://localhost:8000/api";

export const api = {
  getSchema: () => axios.get(`${BASE_URL}/ontology/schema`),
  getGraph: (user: string) => axios.get(`${BASE_URL}/ontology/graph?user=${user}`),
  getObject: (id: string, user: string) => axios.get(`${BASE_URL}/objects/${id}?user=${user}`),
  getAskStream: (question: string, objectId: string, user: string) => 
    `${BASE_URL}/ask?question=${encodeURIComponent(question)}&object_id=${objectId}&user=${user}`,
  
  // New Hybrid & Document endpoints
  askHybrid: (question: string, docIds?: string[]) => 
    axios.post(`${BASE_URL}/hybrid/ask`, { question, doc_ids: docIds }),
  uploadDocument: (formData: FormData) => 
    axios.post(`${BASE_URL}/documents/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" }
    }),
  listDocuments: () => axios.get(`${BASE_URL}/documents`),
  extractOntology: (filename: string) => 
    axios.post(`${BASE_URL}/documents/${filename}/extract`)
};
