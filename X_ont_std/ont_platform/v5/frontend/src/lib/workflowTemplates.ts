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
    name: "공장 반복 고장 대응",
    category: "factory",
    summary: "세종 배터리팩 공장 3번 조립 라인의 배터리 탭 용접기 압력 낮음 같은 반복 장애를 묶어 정비/품질 확인 건으로 승격합니다.",
    appliesTo: "같은 공장, 같은 라인, 같은 장비에서 반복되는 고장/품질 이상",
    automationBoundary: "실제 설비 정지나 정비 완료 처리는 하지 않고 반복 판단, 이관, 관계 저장까지 수행",
    requiredSkills: ["request_input", "intent_classify", "equipment_map", "recurrence_check", "maintenance_task", "ontology_write"],
    requiredSources: ["설비 마스터", "라인/공정 매핑", "고장 이력", "정비 기준", "품질 이상 기준"],
    governance: ["Repeat fault rule", "Maintenance escalation", "Ontology trace"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 140 }, data: { label: "현장 요청 입력" } },
        { id: "category-classify", type: "intent_classify", position: { x: 300, y: 140 }, data: { label: "고장/품질 분류" } },
        { id: "asset-map", type: "equipment_map", position: { x: 520, y: 140 }, data: { label: "공장·라인·장비 매핑" } },
        { id: "recurrence-check", type: "recurrence_check", position: { x: 760, y: 140 }, data: { label: "반복 여부 확인" } },
        { id: "fault-register", type: "request_register", position: { x: 1000, y: 80 }, data: { label: "고장 상황 등록" } },
        { id: "maintenance-task", type: "maintenance_task", position: { x: 1240, y: 80 }, data: { label: "정비팀 확인 건 생성" } },
        { id: "quality-link", type: "quality_link", position: { x: 1240, y: 210 }, data: { label: "품질 문제 연결" } },
        { id: "draft-response", type: "draft_response", position: { x: 1480, y: 80 }, data: { label: "현장 안내 답변 생성" } },
        { id: "notify-teams", type: "notify_user", position: { x: 1720, y: 80 }, data: { label: "정비·품질팀 알림" } },
        { id: "ontology-write", type: "ontology_write", position: { x: 1960, y: 80 }, data: { label: "온톨로지 저장" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "category-classify" },
        { id: "e2", source: "category-classify", target: "asset-map" },
        { id: "e3", source: "asset-map", target: "recurrence-check" },
        { id: "e4", source: "recurrence-check", target: "fault-register", label: "first or repeated fault" },
        { id: "e5", source: "fault-register", target: "maintenance-task", label: "repeated" },
        { id: "e6", source: "fault-register", target: "draft-response", label: "first occurrence" },
        { id: "e7", source: "category-classify", target: "quality-link", label: "quality issue" },
        { id: "e8", source: "quality-link", target: "maintenance-task", label: "after equipment fault" },
        { id: "e9", source: "maintenance-task", target: "draft-response" },
        { id: "e10", source: "draft-response", target: "notify-teams" },
        { id: "e11", source: "notify-teams", target: "ontology-write" },
      ],
    },
  },
  {
    templateId: "service-request-auto-reply",
    name: "서비스 요청 자동댓글",
    category: "helpdesk",
    summary: "문장형 서비스 요청을 분류하고 FAQ/RAG 근거로 답변 초안을 만듭니다.",
    appliesTo: "산출물 변경이 없는 안내성 문의, 반복 문의, FAQ 기반 응대",
    automationBoundary: "근거 부족, 보안 위험, 변경 가능성이 있으면 수동 이관",
    requiredSkills: ["request_input", "intent_classify", "faq_search", "evidence_gate", "draft_response"],
    requiredSources: ["FAQ", "운영 규정", "유사 처리 사례"],
    governance: ["Evidence gate", "No-answer policy", "Audit log"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 120 }, data: { label: "Request Input" } },
        { id: "intent-classify", type: "intent_classify", position: { x: 300, y: 120 }, data: { label: "Intent Classify" } },
        { id: "rag-search", type: "knowledge_lookup", position: { x: 520, y: 120 }, data: { label: "FAQ / RAG Search" } },
        { id: "evidence-gate", type: "evidence_gate", position: { x: 740, y: 120 }, data: { label: "Evidence Gate" } },
        { id: "draft-response", type: "draft_response", position: { x: 960, y: 80 }, data: { label: "Draft Response" } },
        { id: "human-handoff", type: "human_handoff", position: { x: 960, y: 190 }, data: { label: "Human Handoff" } },
        { id: "notify-user", type: "notify_user", position: { x: 1180, y: 80 }, data: { label: "Notify User" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "intent-classify" },
        { id: "e2", source: "intent-classify", target: "rag-search" },
        { id: "e3", source: "rag-search", target: "evidence-gate" },
        { id: "e4", source: "evidence-gate", target: "draft-response", label: "enough evidence" },
        { id: "e5", source: "evidence-gate", target: "human-handoff", label: "insufficient" },
        { id: "e6", source: "draft-response", target: "notify-user" },
      ],
    },
  },
  {
    templateId: "approved-account-action",
    name: "승인 후 계정 조치",
    category: "access",
    summary: "비밀번호 초기화, 계정 잠금 해제처럼 승인 조건이 붙은 계정 요청을 처리합니다.",
    appliesTo: "결재 후 비밀번호 초기화, 계정 잠금 해제, 권한 변경 안내",
    automationBoundary: "실제 계정 변경은 외부 ITSM/API 연동 전까지 안내 또는 수동 이관",
    requiredSkills: ["request_input", "precondition_check", "approval_check", "account_action_guide"],
    requiredSources: ["계정 운영 규정", "승인 정책", "ITSM 처리 매뉴얼"],
    governance: ["Approval gate", "Forbidden action check", "Audit log"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 140 }, data: { label: "Request Input" } },
        { id: "intent-classify", type: "intent_classify", position: { x: 300, y: 140 }, data: { label: "Account Intent" } },
        { id: "approval-check", type: "approval_check", position: { x: 520, y: 140 }, data: { label: "Approval Check" } },
        { id: "action-guide", type: "action_plan", position: { x: 740, y: 90 }, data: { label: "Account Action Guide" } },
        { id: "wait-approval", type: "end_pending", position: { x: 740, y: 210 }, data: { label: "Wait Approval" } },
        { id: "notify-user", type: "notify_user", position: { x: 960, y: 90 }, data: { label: "Notify User" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "intent-classify" },
        { id: "e2", source: "intent-classify", target: "approval-check" },
        { id: "e3", source: "approval-check", target: "action-guide", label: "approved" },
        { id: "e4", source: "approval-check", target: "wait-approval", label: "pending" },
        { id: "e5", source: "action-guide", target: "notify-user" },
      ],
    },
  },
  {
    templateId: "permission-request-guide",
    name: "권한 요청 안내",
    category: "approval",
    summary: "SAP, VPN, 업무 시스템 권한 신청 절차를 식별하고 필요한 승인 경로를 안내합니다.",
    appliesTo: "권한 신청 방법, 승인자 문의, 필요 서류 안내",
    automationBoundary: "권한 부여 자체는 하지 않고 신청 경로와 승인 조건만 안내",
    requiredSkills: ["intent_classify", "policy_search", "approval_gate", "draft_answer"],
    requiredSources: ["권한 정책", "신청 양식", "조직별 승인자 매핑"],
    governance: ["Policy grounding", "Sensitive data check", "Audit log"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 120 }, data: { label: "Request Input" } },
        { id: "policy-search", type: "policy_search", position: { x: 320, y: 120 }, data: { label: "Policy Search" } },
        { id: "approval-gate", type: "approval_check", position: { x: 560, y: 120 }, data: { label: "Approval Gate" } },
        { id: "draft-answer", type: "draft_response", position: { x: 800, y: 120 }, data: { label: "Draft Guide" } },
        { id: "end", type: "end", position: { x: 1040, y: 120 }, data: { label: "End" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "policy-search" },
        { id: "e2", source: "policy-search", target: "approval-gate" },
        { id: "e3", source: "approval-gate", target: "draft-answer" },
        { id: "e4", source: "draft-answer", target: "end" },
      ],
    },
  },
  {
    templateId: "vpn-incident-triage",
    name: "VPN 장애 응대",
    category: "incident",
    summary: "VPN 접속 장애 요청을 1차 조치, 근거 안내, 수동 이관으로 분기합니다.",
    appliesTo: "VPN 접속 불가, MFA 오류, 네트워크 접속 장애",
    automationBoundary: "장애 지속 또는 계정 변경 필요 시 헬프데스크로 이관",
    requiredSkills: ["incident_classify", "similar_case_search", "troubleshoot_guide", "human_handoff"],
    requiredSources: ["장애 FAQ", "네트워크 운영 매뉴얼", "최근 장애 공지"],
    governance: ["Evidence gate", "Incident audit", "Manual handoff policy"],
    graph: {
      nodes: [
        { id: "request-input", type: "request_input", position: { x: 80, y: 150 }, data: { label: "Request Input" } },
        { id: "incident-classify", type: "intent_classify", position: { x: 310, y: 150 }, data: { label: "Incident Classify" } },
        { id: "similar-case", type: "knowledge_lookup", position: { x: 540, y: 150 }, data: { label: "Similar Case Search" } },
        { id: "troubleshoot", type: "draft_response", position: { x: 770, y: 90 }, data: { label: "Troubleshoot Guide" } },
        { id: "handoff", type: "human_handoff", position: { x: 770, y: 220 }, data: { label: "Helpdesk Handoff" } },
        { id: "end", type: "end", position: { x: 1000, y: 90 }, data: { label: "End" } },
      ],
      edges: [
        { id: "e1", source: "request-input", target: "incident-classify" },
        { id: "e2", source: "incident-classify", target: "similar-case" },
        { id: "e3", source: "similar-case", target: "troubleshoot", label: "known issue" },
        { id: "e4", source: "similar-case", target: "handoff", label: "unknown" },
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
