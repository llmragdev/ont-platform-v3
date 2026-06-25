"use client";

import React, { useEffect, useState } from "react";
import { 
  Database, 
  Table, 
  Columns, 
  Play, 
  Eraser, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ChevronRight, 
  ChevronDown, 
  Terminal,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import type { CatalogTableResponse } from "@/types/api";

export function DataCatalogView() {
  const [tables, setTables] = useState<CatalogTableResponse[]>([]);
  const [selectedTable, setSelectedTable] = useState<CatalogTableResponse | null>(null);
  const [expandedLayers, setExpandedLayers] = useState<Record<string, boolean>>({
    BRONZE: true,
    SILVER: true,
    GOLD: true,
  });

  const [query, setQuery] = useState("SELECT * FROM tb_equipment_status LIMIT 10;");
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<{
    columns: string[];
    rows: any[][];
    execution_time_ms: number;
    error: string | null;
  } | null>(null);

  const [loadingMetadata, setLoadingMetadata] = useState(true);
  const [metadataError, setMetadataError] = useState<string | null>(null);

  // 1. 초기 테이블 메타데이터 로드
  useEffect(() => {
    async function loadMetadata() {
      try {
        setLoadingMetadata(true);
        const data = await api.dataCatalog.getTables();
        setTables(data);
        if (data.length > 0) {
          // 기본 선택 테이블로 Silver 레이어 장비 테이블 지정
          const silverTable = data.find(t => t.table_name === "tb_equipment_status");
          setSelectedTable(silverTable || data[0]);
        }
      } catch (err) {
        setMetadataError(err instanceof Error ? err.message : "메타데이터를 불러오지 못했습니다.");
      } finally {
        setLoadingMetadata(false);
      }
    }
    void loadMetadata();
  }, []);

  // 2. LocalStorage에서 챗봇이 전송한 SQL 쿼리 연동 체크
  useEffect(() => {
    if (typeof window === "undefined") return;
    const pendingSql = window.localStorage.getItem("ont.dataCatalog.pendingSql");
    if (pendingSql) {
      setQuery(pendingSql);
      window.localStorage.removeItem("ont.dataCatalog.pendingSql");
      // 자동으로 실행
      void runQuery(pendingSql);
    }
  }, []);

  // 3. 쿼리 실행
  async function runQuery(sqlText = query) {
    if (!sqlText.trim() || executing) return;
    setExecuting(true);
    setExecResult(null);

    try {
      const res = await api.dataCatalog.executeQuery({ query: sqlText });
      setExecResult({
        columns: res.columns || [],
        rows: res.rows || [],
        execution_time_ms: res.execution_time_ms,
        error: res.error,
      });
    } catch (err) {
      setExecResult({
        columns: [],
        rows: [],
        execution_time_ms: 0,
        error: err instanceof Error ? err.message : "쿼리 실행 도중 네트워크 에러가 발생했습니다.",
      });
    } finally {
      setExecuting(false);
    }
  }

  const toggleLayer = (layer: string) => {
    setExpandedLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  const getLayerBadgeClass = (layer: string) => {
    switch (layer) {
      case "BRONZE":
        return "bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-200";
      case "SILVER":
        return "bg-indigo-50 text-indigo-700 border-indigo-250 dark:bg-indigo-950/35 dark:text-indigo-300";
      case "GOLD":
        return "bg-amber-50 text-amber-700 border-amber-250 dark:bg-amber-950/35 dark:text-amber-300";
      default:
        return "bg-slate-50 text-slate-600";
    }
  };

  // 레이어별 테이블 정렬
  const bronzeTables = tables.filter((t) => t.layer === "BRONZE");
  const silverTables = tables.filter((t) => t.layer === "SILVER");
  const goldTables = tables.filter((t) => t.layer === "GOLD");

  return (
    <div className="grid h-[calc(100vh-9.5rem)] min-h-[680px] gap-4 xl:grid-cols-[280px_minmax(0,1.1fr)_minmax(0,1.2fr)]">
      
      {/* [좌측 패널] 테이블 카탈로그 트리 */}
      <aside className="flex min-h-0 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-850 dark:bg-slate-900">
        <div className="border-b border-slate-200 p-4 dark:border-slate-850">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-700 text-white">
              <Database className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-sm font-extrabold text-slate-950 dark:text-white">데이터 카탈로그</h2>
              <p className="text-[10px] text-slate-500">스노우플레이크 메달리온 아키텍처</p>
            </div>
          </div>
        </div>

        {loadingMetadata ? (
          <div className="flex flex-1 items-center justify-center text-xs text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
            메타데이터 로딩 중...
          </div>
        ) : metadataError ? (
          <div className="p-4 text-xs text-rose-600 flex items-start gap-1.5">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{metadataError}</span>
          </div>
        ) : (
          <div className="min-h-0 flex-1 overflow-y-auto p-3 space-y-4">
            {/* 1. BRONZE LAYER */}
            <div>
              <button
                type="button"
                onClick={() => toggleLayer("BRONZE")}
                className="flex w-full items-center justify-between text-[11px] font-extrabold text-slate-400 hover:text-slate-600 tracking-wider uppercase mb-1.5 px-1"
              >
                <span>Bronze (원천 로그)</span>
                {expandedLayers.BRONZE ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
              </button>
              {expandedLayers.BRONZE && (
                <div className="space-y-1 pl-1">
                  {bronzeTables.map((t) => (
                    <button
                      key={t.table_name}
                      type="button"
                      onClick={() => setSelectedTable(t)}
                      className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs ${
                        selectedTable?.table_name === t.table_name
                          ? "bg-slate-100 font-bold text-slate-950 dark:bg-slate-800 dark:text-white"
                          : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-850"
                      }`}
                    >
                      <Table className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                      <span className="truncate">{t.table_name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 2. SILVER LAYER */}
            <div>
              <button
                type="button"
                onClick={() => toggleLayer("SILVER")}
                className="flex w-full items-center justify-between text-[11px] font-extrabold text-slate-400 hover:text-slate-600 tracking-wider uppercase mb-1.5 px-1"
              >
                <span>Silver (정제/연동)</span>
                {expandedLayers.SILVER ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
              </button>
              {expandedLayers.SILVER && (
                <div className="space-y-1 pl-1">
                  {silverTables.map((t) => (
                    <button
                      key={t.table_name}
                      type="button"
                      onClick={() => setSelectedTable(t)}
                      className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs ${
                        selectedTable?.table_name === t.table_name
                          ? "bg-indigo-50/70 font-bold text-indigo-900 border-l-2 border-indigo-500 dark:bg-indigo-950/20 dark:text-indigo-300"
                          : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-850"
                      }`}
                    >
                      <Table className="h-3.5 w-3.5 shrink-0 text-indigo-400" />
                      <span className="truncate">{t.table_name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 3. GOLD LAYER */}
            <div>
              <button
                type="button"
                onClick={() => toggleLayer("GOLD")}
                className="flex w-full items-center justify-between text-[11px] font-extrabold text-slate-400 hover:text-slate-600 tracking-wider uppercase mb-1.5 px-1"
              >
                <span>Gold (비즈니스 집계)</span>
                {expandedLayers.GOLD ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
              </button>
              {expandedLayers.GOLD && (
                <div className="space-y-1 pl-1">
                  {goldTables.map((t) => (
                    <button
                      key={t.table_name}
                      type="button"
                      onClick={() => setSelectedTable(t)}
                      className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs ${
                        selectedTable?.table_name === t.table_name
                          ? "bg-amber-50/70 font-bold text-amber-900 border-l-2 border-amber-500 dark:bg-amber-950/20 dark:text-amber-300"
                          : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-850"
                      }`}
                    >
                      <Table className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                      <span className="truncate">{t.table_name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </aside>

      {/* [중앙 패널] 선택한 테이블 상세 스키마 정보 */}
      <main className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-850 dark:bg-slate-900 overflow-hidden">
        {selectedTable ? (
          <div className="flex h-full flex-col min-h-0">
            <header className="border-b border-slate-200 p-4 dark:border-slate-850">
              <div className="flex items-center gap-2">
                <span className={`rounded-md border px-2 py-0.5 text-[10px] font-extrabold tracking-wide uppercase ${getLayerBadgeClass(selectedTable.layer)}`}>
                  {selectedTable.layer}
                </span>
                <h3 className="text-base font-extrabold text-slate-950 dark:text-white">{selectedTable.table_name}</h3>
              </div>
              <p className="mt-1.5 text-xs text-slate-500 leading-5">{selectedTable.description}</p>
            </header>

            <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-5">
              {/* 컬럼 스펙 리스트 */}
              <section>
                <div className="flex items-center gap-1.5 text-xs font-extrabold text-slate-500 mb-2.5 uppercase tracking-wide">
                  <Columns className="h-4 w-4 text-teal-700" />
                  <span>컬럼 명세서 ({selectedTable.columns.length})</span>
                </div>
                <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-950">
                      <tr>
                        <th className="px-4 py-2 text-left font-bold text-slate-500 uppercase">이름</th>
                        <th className="px-4 py-2 text-left font-bold text-slate-500 uppercase w-24">유형</th>
                        <th className="px-4 py-2 text-left font-bold text-slate-500 uppercase">설명</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-250 bg-white dark:bg-slate-900 dark:divide-slate-800">
                      {selectedTable.columns.map((col) => (
                        <tr key={col.name} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                          <td className="px-4 py-2 font-mono font-bold text-teal-700 dark:text-teal-400">{col.name}</td>
                          <td className="px-4 py-2 font-mono text-[11px] text-slate-400">{col.type}</td>
                          <td className="px-4 py-2 text-slate-600 dark:text-slate-350">{col.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* 퀵 쿼리 복사 버튼 */}
              <section className="bg-slate-50 border border-slate-200 rounded-lg p-3 dark:bg-slate-950 dark:border-slate-800">
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">콘솔용 퀵 쿼리</div>
                <div className="mt-2 flex items-center justify-between gap-3 bg-white border border-slate-250 p-2 rounded font-mono text-[11px] dark:bg-slate-900 dark:border-slate-850 text-slate-700 dark:text-slate-300">
                  <span className="truncate">SELECT * FROM {selectedTable.table_name} LIMIT 10;</span>
                  <button
                    type="button"
                    onClick={() => {
                      const newSql = `SELECT * FROM ${selectedTable.table_name} LIMIT 10;`;
                      setQuery(newSql);
                      void runQuery(newSql);
                    }}
                    className="shrink-0 bg-teal-700 text-white rounded px-2 py-0.5 text-[10px] font-bold hover:bg-teal-800"
                  >
                    콘솔에 복사 & 실행
                  </button>
                </div>
              </section>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            테이블을 선택하시면 상세 스키마 정보를 볼 수 있습니다.
          </div>
        )}
      </main>

      {/* [우측 패널] SQL 쿼리 콘솔 및 실행 결과 */}
      <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-850 dark:bg-slate-900 overflow-hidden">
        <header className="border-b border-slate-200 p-4 dark:border-slate-850 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950 text-slate-350">
              <Terminal className="h-4 w-4" />
            </span>
            <div>
              <h3 className="text-sm font-extrabold text-slate-950 dark:text-white">SQL 쿼리 에디터</h3>
              <p className="text-[10px] text-slate-500 font-mono">Database: Snowflake (SQLite Mock)</p>
            </div>
          </div>
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => setQuery("")}
              className="inline-flex h-8 px-2.5 items-center gap-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-[11px] font-bold dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300"
              title="에디터 비우기"
            >
              <Eraser className="h-3.5 w-3.5" />
              Clear
            </button>
            <button
              type="button"
              onClick={() => runQuery()}
              disabled={executing || !query.trim()}
              className="inline-flex h-8 px-3 items-center gap-1.5 rounded bg-teal-750 hover:bg-teal-800 text-white text-[11px] font-bold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {executing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              실행 (Run)
            </button>
          </div>
        </header>

        {/* 쿼리 입력창 */}
        <div className="h-[200px] shrink-0 border-b border-slate-200 dark:border-slate-850 relative bg-slate-950">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            spellCheck={false}
            className="absolute inset-0 w-full h-full p-4 font-mono text-xs leading-5 bg-slate-950 text-slate-200 outline-none resize-none overflow-y-auto"
            placeholder="SELECT * FROM tb_equipment_status LIMIT 10;"
          />
        </div>

        {/* 실행 결과 공간 */}
        <div className="flex-1 min-h-0 flex flex-col bg-slate-50/50 dark:bg-slate-950/20">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-bold text-slate-600 dark:border-slate-850 dark:bg-slate-950 flex items-center justify-between">
            <span>쿼리 실행 결과</span>
            {execResult && !execResult.error && (
              <div className="flex items-center gap-3 text-[10px] text-slate-400 font-mono font-normal">
                <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold">
                  <CheckCircle2 className="h-3 w-3" />
                  실행 완료
                </span>
                <span className="flex items-center gap-0.5">
                  <Clock className="h-3 w-3" />
                  {execResult.execution_time_ms}ms
                </span>
                <span>
                  Rows: {execResult.rows.length}
                </span>
              </div>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-auto p-3">
            {executing ? (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 space-y-2">
                <Loader2 className="h-7 w-7 animate-spin text-teal-700" />
                <div>스노우플레이크 모의 쿼리를 수행하고 있습니다...</div>
              </div>
            ) : execResult ? (
              execResult.error ? (
                <div className="rounded-lg border border-rose-250 bg-rose-50 p-3.5 text-xs text-rose-800 dark:bg-rose-950/20 dark:border-rose-900/50 dark:text-rose-400 flex items-start gap-1.5 font-sans">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div className="leading-5">{execResult.error}</div>
                </div>
              ) : execResult.rows.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  조회 결과 데이터가 비어 있습니다. (0 rows returned)
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-850 dark:bg-slate-900 max-h-[300px]">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-[11px] font-sans">
                    <thead className="bg-slate-50 dark:bg-slate-950">
                      <tr>
                        {execResult.columns.map((col, idx) => (
                          <th key={`${col}-${idx}`} className="px-3 py-2 text-left font-bold text-slate-500 uppercase tracking-wide border-r border-slate-200 dark:border-slate-800 last:border-r-0">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-250 bg-white dark:bg-slate-900 dark:divide-slate-800">
                      {execResult.rows.map((row, rowIdx) => (
                        <tr key={`row-${rowIdx}`} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                          {row.map((val, cellIdx) => (
                            <td key={`cell-${rowIdx}-${cellIdx}`} className="px-3 py-1.5 font-mono text-[10px] text-slate-800 dark:text-slate-250 border-r border-slate-100 dark:border-slate-850 last:border-r-0 max-w-xs truncate" title={String(val)}>
                              {typeof val === "object" ? JSON.stringify(val) : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs text-center space-y-2">
                <Terminal className="h-8 w-8 opacity-45 text-slate-400" />
                <div>상단의 실행(Run) 버튼을 누르면<br />이곳에 SQL 실행 결과 데이터셋이 정렬됩니다.</div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
