"use client";

import React, { useState } from "react";
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

export default function FileUpload() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'idle', message: string }>({ type: 'idle', message: '' });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setStatus({ type: 'idle', message: '' });

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://localhost:8000/api/v1/documents/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) throw new Error(`Failed to upload ${file.name}`);
      }
      
      setStatus({ type: 'success', message: "All documents uploaded and processed successfully." });
      setFiles([]);
    } catch (error: any) {
      setStatus({ type: 'error', message: error.message || "An error occurred during upload." });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card p-8">
      <div 
        className="border-2 border-dashed border-[var(--glass-border)] rounded-2xl p-12 flex flex-col items-center justify-center transition-all hover:border-primary/50 bg-white/5 cursor-pointer"
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input 
          id="file-input"
          type="file" 
          multiple 
          accept=".pdf" 
          className="hidden" 
          onChange={handleFileChange}
        />
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
          <Upload className="text-primary" size={32} />
        </div>
        <h3 className="text-xl font-semibold mb-2">Upload PDFs</h3>
        <p className="text-gray-400 text-center max-w-xs">
          Drag and drop your PDF documents here or click to browse.
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-8 space-y-3">
          <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Selected Files</h4>
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
              <div className="flex items-center gap-3">
                <File className="text-primary" size={20} />
                <span className="text-sm font-medium">{file.name}</span>
              </div>
              <button onClick={() => setFiles(files.filter((_, i) => i !== idx))} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>
          ))}
          <button 
            onClick={handleUpload}
            disabled={uploading}
            className="w-full bg-primary hover:bg-primary/80 text-white font-bold py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {uploading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Processing Documents...
              </>
            ) : (
              <>
                <CheckCircle2 size={20} />
                Start Upload & Indexing
              </>
            )}
          </button>
        </div>
      )}

      {status.type !== 'idle' && (
        <div className={`mt-6 p-4 rounded-xl flex items-center gap-3 ${
          status.type === 'success' ? 'bg-accent/10 border border-accent/20 text-accent' : 'bg-red-500/10 border border-red-500/20 text-red-500'
        }`}>
          {status.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span className="text-sm font-medium">{status.message}</span>
        </div>
      )}
    </div>
  );
}
