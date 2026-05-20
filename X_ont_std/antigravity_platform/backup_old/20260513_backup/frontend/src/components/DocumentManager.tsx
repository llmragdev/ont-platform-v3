"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { FileText, Upload, RefreshCw, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function DocumentManager() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [extracting, setExtracting] = useState<string | null>(null);
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    try {
      const res = await api.listDocuments();
      setDocuments(res.data.documents);
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setStatus(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.uploadDocument(formData);
      setStatus({ type: "success", msg: "문서가 성공적으로 업로드되었습니다." });
      loadDocs();
    } catch (err) {
      setStatus({ type: "error", msg: "업로드에 실패했습니다." });
    } finally {
      setIsUploading(false);
    }
  };

  const handleExtract = async (filename: string) => {
    setExtracting(filename);
    setStatus(null);
    try {
      await api.extractOntology(filename);
      setStatus({ type: "success", msg: `${filename}에서 온톨로지를 추출했습니다.` });
    } catch (err) {
      setStatus({ type: "error", msg: "추출에 실패했습니다." });
    } finally {
      setExtracting(null);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">문서 저장소</h2>
          <p className="text-sm text-slate-500">PDF를 업로드하여 지식 그래프를 확장하고 RAG 질의에 활용하세요.</p>
        </div>
        
        <label className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold cursor-pointer hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200">
          <Upload size={18} />
          {isUploading ? "업로드 중..." : "PDF 업로드"}
          <input type="file" className="hidden" accept=".pdf" onChange={handleUpload} disabled={isUploading} />
        </label>
      </div>

      {status && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-6 p-4 rounded-2xl flex items-center gap-3 ${
            status.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-100" : "bg-rose-50 text-rose-700 border border-rose-100"
          }`}
        >
          {status.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span className="text-sm font-medium">{status.msg}</span>
        </motion.div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {documents.length === 0 ? (
          <div className="py-20 text-center border-2 border-dashed border-slate-200 rounded-3xl">
            <FileText size={48} className="mx-auto text-slate-200 mb-4" />
            <p className="text-slate-400 font-medium">아직 업로드된 문서가 없습니다.</p>
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.doc_id} className="bg-white p-5 rounded-3xl border border-slate-100 flex items-center justify-between hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400">
                  <FileText size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-700">{doc.filename}</h3>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold mt-0.5">PDF Document</p>
                </div>
              </div>
              
              <button 
                onClick={() => handleExtract(doc.filename)}
                disabled={extracting === doc.filename}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-indigo-600 bg-indigo-50 rounded-xl hover:bg-indigo-100 transition-colors disabled:opacity-50"
              >
                {extracting === doc.filename ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                온톨로지 추출
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
