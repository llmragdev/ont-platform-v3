"use client";

import React from "react";
import QueryConsole from "../../components/QueryConsole";

export default function OntologyQueryPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <QueryConsole 
        mode="ontology"
        title="온톨로지 Q&A 질의"
        description="정형화된 온톨로지 지식 그래프를 기반으로 정확한 관계와 속성 정보를 추출합니다."
      />
    </div>
  );
}
