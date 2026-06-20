import type { WorkflowGraph } from "@/types/api";

export type WorkflowTemplateCategory = "helpdesk" | "access" | "approval" | "incident" | "factory";

export interface WorkflowTemplate {
  templateId: string;
  name: string;
  category: WorkflowTemplateCategory;
  summary: string;
  appliesTo: string;
  automationBoundary: string;
  requiredSkills: string[];
  requiredSources: string[];
  governance: string[];
  graph: Pick<WorkflowGraph, "nodes" | "edges">;
}

export const workflowTemplates: WorkflowTemplate[] = [
  {
    templateId: "factory-repeated-fault-response",
    name: "현장 고장 요청 정비 지시 자동화",
    category: "factory",
    summary:
      "현장 고장 요청을 접수하면 요청 유형을 분류하고 공장, 라인, 설비를 식별한 뒤 반복 고장 여부에 따라 정비 지시서와 현장 안내 댓글을 생성합니다.",
    appliesTo: "공장 현장에서 접수되는 설비 고장, 반복 알림, 품질 영향 가능성이 있는 현장 요청",
    automationBoundary:
      "실제 설비 수리 완료 처리는 하지 않고, 요청 분류, 반복 판단, 정비 지시서 요청, 현장 안내 댓글, 온톨로지 이력 저장까지 수행",
    requiredSkills: ["request_input", "intent_classify", "equipment_map", "recurrence_check", "maintenance_task", "ontology_write"],
    requiredSources: ["설비 마스터", "라인/공정 매핑", "고장 이력", "정비 기준", "품질 이상 기준"],
    governance: ["중복 등록 방지", "정비 지시 감사 로그", "온톨로지 이력 저장"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 150 }, data: { label: "현장 고장 요청 접수" } },
        { id: "category-classify", type: "intent_classify", position: { x: 340, y: 150 }, data: { label: "요청 유형 분류" } },
        { id: "asset-map", type: "equipment_map", position: { x: 600, y: 150 }, data: { label: "공장·라인·설비 식별" } },
        { id: "recurrence-check", type: "recurrence_check", position: { x: 880, y: 150 }, data: { label: "반복 고장 여부 확인" } },
        { id: "fault-register", type: "request_register", position: { x: 1160, y: 90 }, data: { label: "고장 이력 등록" } },
        { id: "maintenance-task", type: "maintenance_task", position: { x: 1440, y: 90 }, data: { label: "정비 지시서 생성" } },
        { id: "quality-link", type: "quality_link", position: { x: 1440, y: 230 }, data: { label: "품질 영향 연결" } },
        { id: "draft-response", type: "draft_response", position: { x: 1720, y: 90 }, data: { label: "현장 안내 댓글 작성" } },
        { id: "notify-teams", type: "notify_user", position: { x: 2000, y: 90 }, data: { label: "정비·품질팀 알림" } },
        { id: "ontology-write", type: "ontology_write", position: { x: 2280, y: 90 }, data: { label: "온톨로지 이력 저장" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "category-classify" },
        { id: "e2", source: "category-classify", target: "asset-map" },
        { id: "e3", source: "asset-map", target: "recurrence-check" },
        { id: "e4", source: "recurrence-check", target: "fault-register", label: "고장 이력 확인" },
        { id: "e5", source: "fault-register", target: "maintenance-task", label: "정비 필요" },
        { id: "e6", source: "fault-register", target: "draft-response", label: "현장 안내" },
        { id: "e7", source: "category-classify", target: "quality-link", label: "품질 영향 가능" },
        { id: "e8", source: "quality-link", target: "maintenance-task", label: "정비 연계" },
        { id: "e9", source: "maintenance-task", target: "draft-response" },
        { id: "e10", source: "draft-response", target: "notify-teams" },
        { id: "e11", source: "notify-teams", target: "ontology-write" },
      ],
    },
  },
  {
    templateId: "service-request-auto-reply",
    name: "서비스 요청 자동 댓글",
    category: "helpdesk",
    summary: "고객 문의를 분류하고 FAQ/RAG 근거를 찾아 답변 초안을 만든 뒤 게시판 댓글로 등록합니다.",
    appliesTo: "정책 변경이 없는 반복 문의, FAQ 기반 안내, 단순 사용 문의",
    automationBoundary: "보안 위험, 계정 변경, 근거 부족 건은 수동 검토로 넘기고 자동 등록 대상만 댓글 처리",
    requiredSkills: ["request_input", "intent_classify", "knowledge_lookup", "evidence_gate", "draft_response"],
    requiredSources: ["FAQ", "운영 규정", "유사 처리 이력"],
    governance: ["근거 확인", "중복 등록 방지", "감사 로그"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 120 }, data: { label: "문의 접수" } },
        { id: "intent-classify", type: "intent_classify", position: { x: 320, y: 120 }, data: { label: "문의 분류" } },
        { id: "rag-search", type: "knowledge_lookup", position: { x: 560, y: 120 }, data: { label: "FAQ/RAG 조회" } },
        { id: "evidence-gate", type: "evidence_gate", position: { x: 800, y: 120 }, data: { label: "근거 확인" } },
        { id: "draft-response", type: "draft_response", position: { x: 1040, y: 70 }, data: { label: "답변 초안 작성" } },
        { id: "human-handoff", type: "human_handoff", position: { x: 1040, y: 190 }, data: { label: "수동 검토" } },
        { id: "notify-user", type: "notify_user", position: { x: 1280, y: 70 }, data: { label: "댓글 등록" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "intent-classify" },
        { id: "e2", source: "intent-classify", target: "rag-search" },
        { id: "e3", source: "rag-search", target: "evidence-gate" },
        { id: "e4", source: "evidence-gate", target: "draft-response", label: "근거 충분" },
        { id: "e5", source: "evidence-gate", target: "human-handoff", label: "근거 부족" },
        { id: "e6", source: "draft-response", target: "notify-user" },
      ],
    },
  },
  {
    templateId: "approved-account-action",
    name: "승인 후 계정 조치",
    category: "access",
    summary: "비밀번호 초기화나 계정 잠금 해제처럼 승인 조건이 필요한 계정 요청을 처리합니다.",
    appliesTo: "승인 후 비밀번호 초기화, 계정 잠금 해제, 권한 변경 안내",
    automationBoundary: "승인 전에는 실제 계정 변경을 하지 않고 조건 확인과 안내까지만 수행",
    requiredSkills: ["request_input", "intent_classify", "approval_check", "action_plan", "notify_user"],
    requiredSources: ["계정 정책", "승인 이력", "사용자 디렉터리"],
    governance: ["승인 확인", "권한 감사", "민감정보 보호"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 140 }, data: { label: "요청 접수" } },
        { id: "intent-classify", type: "intent_classify", position: { x: 320, y: 140 }, data: { label: "계정 요청 분류" } },
        { id: "approval-check", type: "approval_check", position: { x: 560, y: 140 }, data: { label: "승인 확인" } },
        { id: "action-guide", type: "action_plan", position: { x: 800, y: 90 }, data: { label: "조치 안내" } },
        { id: "wait-approval", type: "end_pending", position: { x: 800, y: 210 }, data: { label: "승인 대기" } },
        { id: "notify-user", type: "notify_user", position: { x: 1040, y: 90 }, data: { label: "사용자 안내" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "intent-classify" },
        { id: "e2", source: "intent-classify", target: "approval-check" },
        { id: "e3", source: "approval-check", target: "action-guide", label: "승인 완료" },
        { id: "e4", source: "approval-check", target: "wait-approval", label: "승인 필요" },
        { id: "e5", source: "action-guide", target: "notify-user" },
      ],
    },
  },
  {
    templateId: "vpn-incident-triage",
    name: "VPN 장애 1차 대응",
    category: "incident",
    summary: "VPN 접속 장애 요청을 분류하고 알려진 조치와 수동 이관 여부를 판단합니다.",
    appliesTo: "VPN 접속 불가, MFA 오류, 네트워크 접속 장애",
    automationBoundary: "장애 원인 확정이나 계정 변경은 하지 않고 1차 안내와 수동 이관까지만 수행",
    requiredSkills: ["intent_classify", "knowledge_lookup", "draft_response", "human_handoff"],
    requiredSources: ["장애 FAQ", "네트워크 운영 매뉴얼", "최근 장애 공지"],
    governance: ["근거 확인", "장애 감사", "수동 이관 정책"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 150 }, data: { label: "장애 접수" } },
        { id: "incident-classify", type: "intent_classify", position: { x: 320, y: 150 }, data: { label: "장애 분류" } },
        { id: "similar-case", type: "knowledge_lookup", position: { x: 560, y: 150 }, data: { label: "유사 사례 조회" } },
        { id: "troubleshoot", type: "draft_response", position: { x: 800, y: 90 }, data: { label: "조치 안내" } },
        { id: "handoff", type: "human_handoff", position: { x: 800, y: 220 }, data: { label: "헬프데스크 이관" } },
        { id: "end", type: "end", position: { x: 1040, y: 90 }, data: { label: "종료" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "incident-classify" },
        { id: "e2", source: "incident-classify", target: "similar-case" },
        { id: "e3", source: "similar-case", target: "troubleshoot", label: "알려진 장애" },
        { id: "e4", source: "similar-case", target: "handoff", label: "미확인 장애" },
        { id: "e5", source: "troubleshoot", target: "end" },
      ],
    },
  },
];

export function buildGraphFromTemplate(template: WorkflowTemplate): Partial<WorkflowGraph> {
  return {
    name: `${template.name} - 복제본`,
    nodes: template.graph.nodes.map((node) => ({ ...node, data: { ...node.data } })),
    edges: template.graph.edges.map((edge) => ({ ...edge })),
  };
}
