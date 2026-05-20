"use client";

import React from "react";
import FileUpload from "../../components/FileUpload";
import { Settings, FileText, ShieldCheck } from "lucide-react";

export default function QASettingsPage() {
  return (
    <div className="p-8">
      <header className="mb-10">
        <h1 className="mb-1">Q&A 설정</h1>
        <p className="text-gray-400 text-sm">지식 베이스 구축을 위한 문서 업로드 및 전처리 설정을 관리합니다.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <FileUpload />
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="text-accent" size={18} />
              보안 및 개인정보
            </h3>
            <p className="text-sm text-gray-400 mb-4">
              업로드된 모든 문서는 테넌트별로 물리적으로 격리된 저장소에 보관되며, PII(개인식별정보)는 자동으로 마스킹 처리됩니다.
            </p>
            <div className="flex items-center gap-2 text-xs font-medium text-accent bg-accent/10 p-2 rounded-lg">
              <ShieldCheck size={14} />
              V-ID Sharding 적용됨
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText className="text-primary" size={18} />
              인덱싱 상태
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">총 문서 수</span>
                <span className="text-sm font-bold">24</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">사용된 벡터 수</span>
                <span className="text-sm font-bold">1,402</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div className="bg-primary h-full w-[70%]" />
              </div>
              <p className="text-[10px] text-gray-500 text-right">7.2GB / 10GB 사용 중</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
