"use client";

import React from "react";
import QueryConsole from "../../components/QueryConsole";

export default function HybridQueryPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <QueryConsole 
        mode="hybrid"
        title="통합 질의 (Hybrid)"
        description="온톨로지의 구조적 지식과 문서의 비정형 지식을 결합하여 가장 완벽한 답변을 도출합니다."
      />
    </div>
  );
}
