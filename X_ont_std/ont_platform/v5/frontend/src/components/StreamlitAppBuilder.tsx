"use client";

import { AppWindow, Bot, CheckCircle2, Code2, ExternalLink, FileCode2, Folder, FolderPlus, Play, Plus, Save, Share2, AlertCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

const ASSISTANT_SELECTION_KEY = "ont.aiAssistant.selection";
const ASSISTANT_APPLY_CODE_EVENT = "assistant-apply-code";

type StreamlitProgram = {
  id: string;
  folderId: string;
  name: string;
  fileName: string;
  code: string;
  updatedAt: string;
};

type StreamlitFolder = {
  id: string;
  name: string;
};

type ApplyCodeEvent = {
  selected_app_id: string;
  selected_file_path: string;
  code: string;
};

const INITIAL_FOLDERS: StreamlitFolder[] = [
  { id: "factory-apps", name: "공장 자동화" },
  { id: "customer-apps", name: "고객 서비스" },
];

const INITIAL_PROGRAMS: StreamlitProgram[] = [
  {
    id: "factory-repeat-fault-app",
    folderId: "factory-apps",
    name: "반복 고장 분석",
    fileName: "factory_repeated_fault_app.py",
    updatedAt: "2026-06-14 18:00",
    code: `import pandas as pd
import streamlit as st

st.set_page_config(page_title="공장 반복 고장 분석", layout="wide")
st.title("공장 반복 고장 분석")

st.info("우측 하단 AI Assistant에서 이 편집창을 선택한 상태로 코딩을 요청할 수 있습니다.")

data = pd.DataFrame([
    {"설비": "검사 카메라", "고장횟수": 3, "상태": "정비 필요"},
    {"설비": "배터리 탭 용접기", "고장횟수": 2, "상태": "관찰"},
])

st.dataframe(data, use_container_width=True)
`,
  },
];

function newId(prefix: string) {
  return `${prefix}-${Math.random().toString(16).slice(2, 10)}`;
}

function programPath(folder: StreamlitFolder | undefined, program: StreamlitProgram | undefined) {
  if (!program) return "";
  return `${folder?.name ?? "apps"}/${program.fileName}`;
}

export function StreamlitAppBuilder() {
  const [folders, setFolders] = useState<StreamlitFolder[]>(INITIAL_FOLDERS);
  const [programs, setPrograms] = useState<StreamlitProgram[]>(INITIAL_PROGRAMS);
  const [selectedFolderId, setSelectedFolderId] = useState(INITIAL_FOLDERS[0]?.id ?? "");
  const [selectedProgramId, setSelectedProgramId] = useState(INITIAL_PROGRAMS[0]?.id ?? "");
  const [folderName, setFolderName] = useState("");
  const [programName, setProgramName] = useState("");
  const [applyNotice, setApplyNotice] = useState<string | null>(null);
  const [runUrl, setRunUrl] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<"idle" | "loading" | "error">("idle");
  const [runError, setRunError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [savePath, setSavePath] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const selectedFolder = folders.find((folder) => folder.id === selectedFolderId);
  const selectedProgram = programs.find((program) => program.id === selectedProgramId);
  const folderPrograms = programs.filter((program) => program.folderId === selectedFolderId);

  const selectionPayload = useMemo(() => {
    if (!selectedProgram) return null;
    return {
      selected_app_id: selectedProgram.id,
      selected_app_name: selectedProgram.name,
      selected_folder_id: selectedFolder?.id ?? selectedProgram.folderId,
      selected_folder_name: selectedFolder?.name ?? "apps",
      selected_file_path: selectedProgram.fileName,
      selected_file_name: selectedProgram.fileName,
      selected_language: "python",
    };
  }, [selectedFolder, selectedProgram]);

  useEffect(() => {
    if (typeof window === "undefined" || !selectionPayload) return;
    window.localStorage.setItem(ASSISTANT_SELECTION_KEY, JSON.stringify(selectionPayload));
    window.dispatchEvent(new CustomEvent("assistant-selection-change", { detail: selectionPayload }));
  }, [selectionPayload]);

  useEffect(() => {
    function handleApplyCode(event: Event) {
      const custom = event as CustomEvent<ApplyCodeEvent>;
      const detail = custom.detail;
      if (!detail?.selected_app_id || !detail.code) return;
      setPrograms((items) =>
        items.map((program) =>
          program.id === detail.selected_app_id
            ? { ...program, code: detail.code, updatedAt: new Date().toLocaleString("ko-KR") }
            : program,
        ),
      );
      const targetProgram = programs.find((program) => program.id === detail.selected_app_id);
      const targetFolder = folders.find((folder) => folder.id === targetProgram?.folderId);
      if (targetProgram && targetFolder) {
        void saveProgramSource(targetProgram, targetFolder, detail.code, "AI Assistant 코드가 실제 파일로 저장되었습니다.");
      }
      setSelectedProgramId(detail.selected_app_id);
      setApplyNotice(`${detail.selected_file_path}에 AI Assistant 코드가 적용되었습니다.`);
      window.setTimeout(() => setApplyNotice(null), 4000);
    }

    window.addEventListener(ASSISTANT_APPLY_CODE_EVENT, handleApplyCode);
    return () => window.removeEventListener(ASSISTANT_APPLY_CODE_EVENT, handleApplyCode);
  }, [folders, programs]);

  function createFolder() {
    const name = folderName.trim();
    if (!name) return;
    const folder = { id: newId("folder"), name };
    setFolders((items) => [...items, folder]);
    setSelectedFolderId(folder.id);
    setFolderName("");
  }

  function createProgram() {
    const name = programName.trim();
    if (!name || !selectedFolderId) return;
    const fileName = `${name.replace(/\s+/g, "_").toLowerCase()}.py`;
    const program: StreamlitProgram = {
      id: newId("stapp"),
      folderId: selectedFolderId,
      name,
      fileName,
      updatedAt: new Date().toLocaleString("ko-KR"),
      code: `import streamlit as st

st.set_page_config(page_title="${name}", layout="wide")
st.title("${name}")

st.write("AI Assistant에게 이 편집창을 선택한 상태로 코딩을 요청하세요.")
`,
    };
    setPrograms((items) => [...items, program]);
    setSelectedProgramId(program.id);
    setProgramName("");
  }

  function updateCode(code: string) {
    if (!selectedProgram) return;
    setSaveStatus("idle");
    setPrograms((items) =>
      items.map((program) =>
        program.id === selectedProgram.id
          ? { ...program, code, updatedAt: new Date().toLocaleString("ko-KR") }
          : program,
      ),
    );
  }

  async function saveProgramSource(
    program = selectedProgram,
    folder = selectedFolder,
    code = selectedProgram?.code,
    notice = "편집창 소스가 실제 Python 파일로 저장되었습니다.",
  ) {
    if (!program || !folder || code === undefined) return;

    setSaveStatus("saving");
    setSaveError(null);
    try {
      const response = await api.streamlitApps.save({
        app_id: program.id,
        folder_name: folder.name,
        file_name: program.fileName,
        code,
      });
      setSaveStatus("saved");
      setSavePath(response.file_path);
      setApplyNotice(notice);
      window.setTimeout(() => setApplyNotice(null), 4000);
    } catch (err) {
      setSaveStatus("error");
      setSaveError(err instanceof Error ? err.message : String(err));
    }
  }

  async function runSelectedProgram() {
    if (!selectedProgram || !selectedFolder) return;

    setRunStatus("loading");
    setRunError(null);
    setRunUrl(null);

    try {
      const response = await api.streamlitApps.run({
        app_id: selectedProgram.id,
        folder_name: selectedFolder.name,
        file_name: selectedProgram.fileName,
        code: selectedProgram.code,
      });

      if (response.status === "error") {
        setRunStatus("error");
        setRunError(response.message);
        return;
      }

      setRunStatus("idle");
      setRunUrl(response.url);

      // 자동으로 URL 열기
      window.open(response.url, "_blank");
    } catch (error) {
      setRunStatus("error");
      setRunError(error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다");
    }
  }

  return (
    <div className="grid h-[calc(100vh-9.5rem)] min-h-[720px] gap-4 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
      <aside className="flex min-h-0 flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-4">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-700 text-white">
              <AppWindow className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-sm font-extrabold text-slate-950">Streamlit 앱</h2>
              <p className="text-xs text-slate-500">폴더와 프로그램</p>
            </div>
          </div>

          {/* 폴더 만들기 */}
          <div className="mt-3 flex gap-1.5">
            <input
              value={folderName}
              onChange={(event) => setFolderName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") createFolder();
              }}
              placeholder="새 폴더명..."
              className="min-w-0 flex-1 rounded border border-slate-200 px-2 py-1 text-[11px] outline-none focus:border-teal-650 focus:ring-1 focus:ring-teal-100 bg-white text-slate-900 font-sans"
            />
            <button
              type="button"
              onClick={createFolder}
              className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded bg-slate-900 text-white hover:bg-slate-800"
              title="폴더 생성"
            >
              <FolderPlus className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* 프로그램 만들기 */}
          <div className="mt-2 flex gap-1.5 border-t border-slate-100 pt-2">
            <input
              value={programName}
              onChange={(event) => setProgramName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") createProgram();
              }}
              placeholder="새 프로그램 (.py)..."
              className="min-w-0 flex-1 rounded border border-slate-200 px-2 py-1 text-[11px] outline-none focus:border-teal-650 focus:ring-1 focus:ring-teal-100 bg-white text-slate-900 font-sans"
            />
            <button
              type="button"
              onClick={createProgram}
              className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded bg-slate-900 text-white hover:bg-slate-800"
              title="프로그램 생성"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <div className="space-y-3">
            {folders.map((folder) => {
              const active = folder.id === selectedFolderId;
              const count = programs.filter((program) => program.folderId === folder.id).length;
              return (
                <button
                  key={folder.id}
                  type="button"
                  onClick={() => {
                    setSelectedFolderId(folder.id);
                    const firstProgram = programs.find((program) => program.folderId === folder.id);
                    if (firstProgram) setSelectedProgramId(firstProgram.id);
                  }}
                  className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left ${
                    active ? "border-teal-300 bg-teal-50 text-teal-900" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <Folder className="h-4 w-4 shrink-0" />
                    <span className="truncate text-xs font-bold">{folder.name}</span>
                  </span>
                  <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500">{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      </aside>

      <main className="flex min-h-[620px] flex-1 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {applyNotice && (
          <div className="flex items-center gap-2 border-b border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-800">
            <CheckCircle2 className="h-4 w-4" />
            {applyNotice}
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-500">
              <Code2 className="h-4 w-4 text-teal-700" />
              선택된 편집창
            </div>
            <h3 className="mt-1 truncate text-lg font-extrabold text-slate-950">
              {selectedProgram ? programPath(selectedFolder, selectedProgram) : "프로그램을 생성하세요"}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={runSelectedProgram}
              disabled={!selectedProgram}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              코딩 실행
            </button>
            <button
              type="button"
              onClick={() => saveProgramSource()}
              disabled={!selectedProgram || saveStatus === "saving"}
              className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-3 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {saveStatus === "saving" ? "저장 중" : "로컬 저장"}
            </button>
          </div>
        </div>

        {(savePath || saveError) && (
          <div className={`border-b px-4 py-2 text-xs ${saveError ? "border-rose-200 bg-rose-50 text-rose-800" : "border-slate-200 bg-slate-50 text-slate-600"}`}>
            {saveError ? (
              <span>저장 실패: {saveError}</span>
            ) : (
              <span>저장 파일: <span className="font-mono">{savePath}</span></span>
            )}
          </div>
        )}

        {runUrl && (
          <div className="border-b border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="font-extrabold">실행 URL 준비됨</div>
                <div className="mt-1 break-all font-mono text-xs">{runUrl}</div>
              </div>
              <a
                href={runUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white"
              >
                <ExternalLink className="h-4 w-4" />
                URL 열기
              </a>
            </div>
            <div className="mt-2 text-xs leading-5 text-emerald-800">
              실제 실행 연결은 다음 단계에서 서버가 선택된 Python 파일을 저장한 뒤 `streamlit run` 프로세스를 띄우는 방식으로 붙입니다.
            </div>
          </div>
        )}


        <div className="grid min-h-[460px] flex-1 lg:grid-cols-[220px_minmax(0,1fr)]">
          <div className="min-h-0 h-full overflow-y-auto border-b border-slate-200 p-3 lg:border-b-0 lg:border-r">
            <div className="space-y-2">
              {folderPrograms.length === 0 && (
                <div className="rounded-lg border border-dashed border-slate-300 p-4 text-center text-xs text-slate-500">
                  이 폴더에 프로그램이 없습니다.
                </div>
              )}
              {folderPrograms.map((program) => {
                const active = program.id === selectedProgramId;
                return (
                  <button
                    key={program.id}
                    type="button"
                    onClick={() => setSelectedProgramId(program.id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left ${
                      active ? "border-teal-300 bg-teal-50" : "border-slate-200 bg-white hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <FileCode2 className="h-4 w-4 shrink-0 text-teal-700" />
                      <span className="truncate text-xs font-extrabold text-slate-800">{program.name}</span>
                    </div>
                    <div className="mt-1 truncate text-[10px] text-slate-500">{program.fileName}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="relative flex min-h-[460px] flex-col bg-slate-950">
            {selectedProgram ? (
              <textarea
                value={selectedProgram.code}
                onChange={(event) => updateCode(event.target.value)}
                spellCheck={false}
                className="absolute inset-0 h-full w-full resize-none overflow-y-auto bg-slate-950 p-4 font-mono text-[13px] leading-6 text-slate-100 outline-none"
              />
            ) : (
              <div className="flex min-h-[460px] items-center justify-center text-sm text-slate-400">
                프로그램을 만들거나 선택하면 파이썬 편집기가 열립니다.
              </div>
            )}
          </div>
        </div>
      </main>

      <aside className="flex min-h-0 flex-col gap-4">
        <section className="rounded-xl border border-teal-200 bg-teal-50 p-4">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-700 text-white">
              <Bot className="h-4 w-4" />
            </span>
            <div>
              <h3 className="text-sm font-extrabold text-slate-950">챗봇 연동 상태</h3>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                현재 선택한 파이썬 편집창이 AI Assistant context로 전달됩니다.
                챗봇에서 “코딩해줘”라고만 입력해도 이 파일 기준으로 응답합니다.
              </p>
            </div>
          </div>
          <div className="mt-3 rounded-lg bg-white px-3 py-2 text-xs text-slate-600">
            <div className="font-extrabold text-slate-900">현재 대상</div>
            <div className="mt-1 break-all">{selectedProgram ? programPath(selectedFolder, selectedProgram) : "선택 없음"}</div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-extrabold text-slate-950">다음 연결</h3>
          <div className="mt-3 space-y-2 text-xs text-slate-600">
            <div className="rounded-lg bg-emerald-50 p-3 text-emerald-800">Assistant 응답 코드를 편집기에 적용 가능</div>
            <div className="rounded-lg bg-slate-50 p-3">App Spec 저장소와 프로그램 파일 저장 API 연결</div>
            <div className="rounded-lg bg-slate-50 p-3">미리보기 실행과 공유 URL 발급</div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-extrabold text-slate-950">
            <Share2 className="h-4 w-4 text-teal-700" />
            공유 상태
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            현재는 브라우저 로컬 상태 기반 MVP입니다. 실제 외부 URL은 서버 저장 후 `streamlit run`으로 생성합니다.
          </p>
          {runUrl && (
            <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs">
              <div className="font-extrabold text-slate-800">보기 URL</div>
              <div className="mt-1 break-all font-mono text-slate-600">{runUrl}</div>
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
