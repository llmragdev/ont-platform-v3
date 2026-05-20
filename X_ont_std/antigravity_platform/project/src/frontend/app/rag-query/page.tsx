"use client";

import React from "react";
import QueryConsole from "../../components/QueryConsole";

export default function RagQueryPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <QueryConsole 
        mode="rag"
        title="RAG Q&A 질의"
        description="업로드된 문서를 바탕으로 AI가 답변을 생성합니다. 근거 문서의 출처가 함께 표시됩니다."
      />
    </div>
  );
}
