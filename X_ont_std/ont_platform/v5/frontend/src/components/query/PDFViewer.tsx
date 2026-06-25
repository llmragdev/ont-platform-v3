'use client';

// Author: Claude
// Date: 2026-06-20
// Purpose: 고급 PDF 문서 뷰어 (react-pdf 사용)

import React, { useState, useEffect } from 'react';

// react-pdf 설치 필요: npm install react-pdf pdfjs-dist
// 그 전까지는 폴백으로 iframe 사용

interface PDFViewerProps {
  filename: string;
  url: string;
  onClose: () => void;
}

export const PDFViewer = ({ filename, url, onClose }: PDFViewerProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState<number | null>(null);
  const [zoom, setZoom] = useState(100);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // PDF 로드 시뮬레이션
    setIsLoading(false);
    setTotalPages(10); // 임시값 (react-pdf 설치 후 실제 페이지 수 감지)
  }, [url]);

  const handlePreviousPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (totalPages && currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const handleZoomIn = () => {
    setZoom(Math.min(zoom + 10, 200));
  };

  const handleZoomOut = () => {
    setZoom(Math.max(zoom - 10, 50));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full h-[90vh] max-w-5xl flex flex-col overflow-hidden">
        {/* 헤더 */}
        <div className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
          <h2 className="text-lg font-bold truncate">📑 {filename}</h2>
          <button
            onClick={onClose}
            className="text-2xl hover:text-gray-300 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* 컨트롤 바 (상단) */}
        <div className="bg-gray-100 border-b border-gray-300 px-6 py-3 flex items-center justify-between">
          {/* 페이지 네비게이션 */}
          <div className="flex items-center gap-3">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage === 1}
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              ◀ 이전
            </button>

            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1"
                max={totalPages || 1}
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (page >= 1 && page <= (totalPages || 1)) {
                    setCurrentPage(page);
                  }
                }}
                className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
              />
              <span className="text-sm text-gray-700">/ {totalPages || '?'}</span>
            </div>

            <button
              onClick={handleNextPage}
              disabled={!totalPages || currentPage >= totalPages}
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              다음 ▶
            </button>
          </div>

          {/* 줌 컨트롤 */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 text-sm"
            >
              🔍-
            </button>

            <span className="text-sm text-gray-700 w-12 text-center">{zoom}%</span>

            <button
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 text-sm"
            >
              🔍+
            </button>
          </div>

          {/* 다운로드 */}
          <a
            href={url}
            download={filename}
            className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          >
            💾 다운로드
          </a>
        </div>

        {/* 메인 컨텐츠 (PDF 렌더링) */}
        <div className="flex-1 overflow-auto bg-gray-200 flex items-center justify-center">
          {isLoading ? (
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
              <p className="text-white text-lg">PDF를 불러오는 중...</p>
            </div>
          ) : error ? (
            <div className="text-center p-8 bg-white rounded-lg">
              <p className="text-red-600 font-semibold mb-4">❌ {error}</p>
              <button
                onClick={() => {
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = filename;
                  a.click();
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                🔗 대신 다운로드
              </button>
            </div>
          ) : (
            <div
              className="bg-white shadow-lg"
              style={{
                width: `${zoom}%`,
                maxWidth: '100%',
              }}
            >
              {/* react-pdf 설치 전 임시 구현: iframe */}
              <iframe
                src={`${url}#page=${currentPage}&zoom=${zoom}`}
                className="w-full aspect-[8.5/11] border-0"
                title={filename}
                onError={() => setError('PDF를 표시할 수 없습니다.')}
              />
            </div>
          )}
        </div>

        {/* 하단 상태바 */}
        <div className="bg-gray-100 border-t border-gray-300 px-6 py-2 text-sm text-gray-600 flex justify-between">
          <span>📄 {filename}</span>
          <span>
            페이지 {currentPage} / {totalPages || '?'} | 줌 {zoom}%
          </span>
        </div>
      </div>
    </div>
  );
};
