'use client';

// Author: Claude
// Date: 2026-06-20
// Purpose: PDF 문서 업로드 및 처리 상태 추적

import React, { useState, useRef } from 'react';
import { api } from '@/lib/api';

interface UploadProgress {
  docId: string;
  fileName: string;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  error?: string;
}

export const DocumentUpload = ({ projectId }: { projectId: string }) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files ? Array.from(e.currentTarget.files) : [];
    handleFiles(files);
  };

  const handleFiles = async (files: File[]) => {
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('PDF 파일만 업로드 가능합니다.');
        continue;
      }

      // 업로드 시작
      const docId = `doc-${Date.now()}`;
      const newUpload: UploadProgress = {
        docId,
        fileName: file.name,
        status: 'uploading',
        progress: 0,
      };
      setUploads(prev => [...prev, newUpload]);

      try {
        // 파일 업로드 (projectId 전달)
        console.log(`📤 Uploading: ${file.name}`);
        const uploadResult = await api.documents.upload(file, projectId);
        const realDocId = uploadResult.id || uploadResult.doc_id || docId;

        // 업로드 완료 → "uploaded" 상태
        console.log(`✅ Upload complete: ${file.name}`);
        setUploads(prev =>
          prev.map(u =>
            u.docId === docId
              ? { ...u, status: 'complete', progress: 100, docId: realDocId }
              : u
          )
        );

      } catch (error) {
        console.error(`❌ Upload error: ${file.name}`, error);
        const errorMsg = error instanceof Error ? error.message : '알 수 없는 오류';
        setUploads(prev =>
          prev.map(u =>
            u.docId === docId
              ? { ...u, status: 'error', error: errorMsg }
              : u
          )
        );
      }
    }
  };

  const removeUpload = (docId: string) => {
    setUploads(prev => prev.filter(u => u.docId !== docId));
  };

  const clearCompleted = () => {
    setUploads(prev => prev.filter(u => u.status !== 'complete'));
  };

  return (
    <div className="w-full space-y-4 p-4 border rounded-lg bg-white shadow-sm">
      <h3 className="font-semibold text-gray-800">📄 문서 업로드</h3>

      {/* 드래그 & 드롭 영역 */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="text-4xl mb-2">📁</div>
        <p className="font-semibold text-gray-700">PDF 파일을 드래그하거나 클릭</p>
        <p className="text-sm text-gray-500 mt-1">최대 100MB, PDF만 가능</p>
      </div>

      {/* 업로드 상태 목록 */}
      {uploads.length > 0 && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <p className="text-sm font-semibold text-gray-600">업로드 진행 중</p>
            {uploads.some(u => u.status === 'complete') && (
              <button
                onClick={clearCompleted}
                className="text-xs text-gray-500 hover:text-gray-700 underline"
              >
                완료된 항목 제거
              </button>
            )}
          </div>

          {uploads.map(upload => (
            <div
              key={upload.docId}
              className={`p-3 border rounded-lg transition-colors ${
                upload.status === 'error'
                  ? 'bg-red-50 border-red-200'
                  : upload.status === 'complete'
                    ? 'bg-green-50 border-green-200'
                    : 'bg-blue-50 border-blue-200'
              }`}
            >
              {/* 파일명 + 상태 */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {upload.status === 'complete' ? (
                    <span className="text-green-600">✅</span>
                  ) : upload.status === 'error' ? (
                    <span className="text-red-600">❌</span>
                  ) : (
                    <span className="text-blue-600">⏳</span>
                  )}
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {upload.fileName}
                  </span>
                </div>
                <button
                  onClick={() => removeUpload(upload.docId)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* 진행률 바 */}
              {upload.status !== 'complete' && upload.status !== 'error' && (
                <div className="w-full bg-gray-300 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      upload.status === 'uploading'
                        ? 'bg-blue-500'
                        : 'bg-yellow-500'
                    }`}
                    style={{ width: `${upload.progress}%` }}
                  />
                </div>
              )}

              {/* 상태 텍스트 */}
              <div className="mt-2 text-xs text-gray-600">
                {upload.status === 'uploading' && `업로드 중: ${upload.progress}%`}
                {upload.status === 'processing' && `처리 중: ${upload.progress}%`}
                {upload.status === 'complete' && '✅ 업로드 완료 - 우측 문서 목록에서 벡터화 버튼을 클릭하세요'}
                {upload.status === 'error' && `❌ 오류: ${upload.error}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 업로드 완료 메시지 */}
      {uploads.length === 0 && (
        <p className="text-sm text-gray-400 text-center">
          아직 업로드된 문서가 없습니다.
        </p>
      )}
    </div>
  );
};
