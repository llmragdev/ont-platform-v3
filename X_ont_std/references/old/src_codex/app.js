const state = {
  activeView: "ask",
  userKey: "analyst",
  me: null,
  selectedOrderId: "O001",
  orders: [],
  customers: [],
  queue: [],
  auditEvents: [],
  lastAsk: null,
  lastContext: null,
  objectTypes: [],
};

const titles = {
  ask: ["POST /api/ask", "권한 기반 AI 질의"],
  workflow: ["POST /api/workflow/execute", "워크플로우 액션"],
  objects: ["GET /api/objects/orders/:id/context", "객체와 관계 컨텍스트"],
  audit: ["GET /api/audit/events", "감사 로그"],
  architecture: ["운영형 서비스 경계", "아키텍처 확장 설계"],
};

const services = [
  ["Frontend", "업무 화면, 클라이언트 상태, 사용자 액션을 담당합니다.", "index.html / app.js"],
  ["API Gateway", "화면 요청을 표준 API로 받고 서비스 계층으로 위임합니다.", "server.py"],
  ["Auth Service", "사용자와 역할을 확인합니다.", "GET /api/me"],
  ["Policy Engine", "객체, 속성, 문서, 액션 권한과 마스킹을 적용합니다.", "backend/policy.py"],
  ["Ontology Service", "객체 타입, 객체 인스턴스, 관계 컨텍스트를 제공합니다.", "backend/ontology.py"],
  ["Workflow Service", "상태 전이, 액션 실행, 실행 이력을 관리합니다.", "backend/workflow.py"],
  ["Search / RAG Service", "BM25 검색, 검색 질의 강화, 프롬프트 생성을 담당합니다.", "backend/search.py / rag.py"],
  ["LLM Gateway", "교육용 규칙 기반 답변 생성기로 LLM 호출 지점을 캡슐화합니다.", "backend/rag.py"],
  ["Audit Service", "객체 조회, 검색, 질의, 액션 실행 로그를 남깁니다.", "backend/audit.py"],
];

async function init() {
  bindNavigation();
  bindActions();
  await refreshServerState();
  renderAll();
}

function bindNavigation() {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
      renderView();
    });
  });
}

function bindActions() {
  document.getElementById("ask-button").addEventListener("click", handleAsk);
  document.getElementById("question-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") handleAsk();
  });
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => executeWorkflow(button.dataset.action));
  });
}

async function refreshServerState() {
  const [me, orders, customers, queue, events, objectTypes] = await Promise.all([
    apiGet("/api/me"),
    apiGet("/api/objects/orders"),
    apiGet("/api/objects/customers"),
    apiGet("/api/workflow/queue"),
    apiGet("/api/audit/events"),
    apiGet("/api/ontology/object-types"),
  ]);
  state.me = me;
  state.orders = orders.orders || [];
  state.customers = customers.customers || [];
  state.queue = queue.queue || [];
  state.auditEvents = events.events || [];
  state.objectTypes = objectTypes.object_types || [];
  await refreshContext();
}

async function refreshContext() {
  if (!state.selectedOrderId) return;
  try {
    state.lastContext = await apiGet(`/api/objects/orders/${state.selectedOrderId}/context`);
  } catch (error) {
    state.lastContext = null;
    showError(error.message);
  }
}

async function handleAsk() {
  const question = document.getElementById("question-input").value.trim();
  if (!question) return;
  setPipelineStatus("running");
  try {
    const result = await apiPost("/api/ask", { question });
    state.lastAsk = result;
    state.selectedOrderId = result.ontology_context.order_id;
    await refreshServerState();
    renderAskResult();
    renderPipeline(result.steps || []);
    setPipelineStatus(`completed · ${result.latency_ms} ms`);
  } catch (error) {
    showError(error.message);
    setPipelineStatus("failed");
  }
}

async function executeWorkflow(action) {
  try {
    const result = await apiPost("/api/workflow/execute", {
      action,
      order_id: state.selectedOrderId,
      payload: { comment: "Executed from operational console" },
    });
    state.queue = result.queue || [];
    await refreshServerState();
    showInfo(`${action} 실행 완료: ${result.result.from_status} -> ${result.result.to_status}`);
    renderAll();
  } catch (error) {
    showError(error.message);
    await refreshServerState();
    renderAll();
  }
}

async function apiGet(path) {
  const response = await fetch(`${path}${path.includes("?") ? "&" : "?"}user=${state.userKey}`);
  return parseResponse(response);
}

async function apiPost(path, body) {
  const response = await fetch(`${path}?user=${state.userKey}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse(response);
}

async function parseResponse(response) {
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error?.message || `HTTP ${response.status}`);
  }
  return payload;
}

function renderAll() {
  renderUser();
  renderView();
  renderObjects();
  renderWorkflow();
  renderAskResult();
  renderContext();
  renderAudit();
  renderArchitecture();
  renderPipeline(state.lastAsk?.steps || []);
}

function renderUser() {
  document.getElementById("user-name").textContent = state.me?.name || "-";
  document.getElementById("user-role").textContent = `Role: ${state.me?.role || "-"}`;
}

function renderView() {
  const [kicker, title] = titles[state.activeView];
  document.getElementById("view-kicker").textContent = kicker;
  document.getElementById("view-title").textContent = title;
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${state.activeView}`));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === state.activeView));
}

function renderObjects() {
  const target = document.getElementById("order-table");
  target.innerHTML = state.orders.map((order) => `
    <div class="table-row ${order.id === state.selectedOrderId ? "selected" : ""}" data-order-id="${order.id}">
      <strong>${order.id}</strong>
      <span>${order.customer_id}</span>
      <span>${formatMoney(order.amount)}</span>
      <span class="badge ${statusTone(order.status)}">${order.status}</span>
    </div>
  `).join("");
  target.querySelectorAll("[data-order-id]").forEach((row) => {
    row.addEventListener("click", async () => {
      state.selectedOrderId = row.dataset.orderId;
      await refreshContext();
      renderAll();
    });
  });
  renderOntologyContext();
}

function renderOntologyContext() {
  const target = document.getElementById("ontology-context");
  const context = state.lastContext;
  if (!context) {
    target.innerHTML = `<div class="map-node"><b>컨텍스트 없음</b><span>객체를 선택하거나 서버를 실행하세요.</span></div>`;
    return;
  }
  target.innerHTML = [
    ["Order", `${context.order.id} · ${context.order.status} · ${formatMoney(context.order.amount)}`],
    ["Customer", `${context.customer.id} · ${context.customer.name} · ${context.customer.segment}`],
    ["Products", context.products.map((product) => `${product.id} ${product.name}`).join(", ")],
    ["Available Actions", (context.available_actions || []).join(", ") || "none"],
  ].map(([label, value]) => `<div class="map-node"><b>${label}</b><span>${value}</span></div>`).join("");
}

function renderWorkflow() {
  const queueTarget = document.getElementById("workflow-queue");
  queueTarget.innerHTML = state.queue.map((order) => `
    <button class="list-card ${order.id === state.selectedOrderId ? "selected" : ""}" data-workflow-order="${order.id}">
      <strong>${order.id} · ${formatMoney(order.amount)}</strong>
      <p>${order.customer.name} · ${order.status} · ${order.customer.risk_tier} risk</p>
      <p>Actions: ${(order.available_actions || []).join(", ")}</p>
    </button>
  `).join("") || `<div class="list-card"><strong>대기 항목 없음</strong><p>현재 사용자에게 허용된 워크플로우 큐가 없습니다.</p></div>`;
  queueTarget.querySelectorAll("[data-workflow-order]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedOrderId = button.dataset.workflowOrder;
      await refreshContext();
      renderAll();
    });
  });
  renderWorkflowDetail();
}

function renderWorkflowDetail() {
  const target = document.getElementById("workflow-detail");
  const context = state.lastContext;
  if (!context) {
    target.innerHTML = `<div class="list-card"><strong>선택 객체 없음</strong><p>주문을 선택하세요.</p></div>`;
    return;
  }
  target.innerHTML = `
    <div class="list-card">
      <strong>${context.order.id} · ${context.order.status}</strong>
      <p>${context.customer.name} 고객, ${formatMoney(context.order.amount)} 주문입니다.</p>
      <p>Server actions: ${(context.available_actions || []).join(", ") || "none"}</p>
    </div>
  `;
}

function renderAskResult() {
  const answer = document.getElementById("answer-text");
  const evidence = document.getElementById("evidence-list");
  const actionList = document.getElementById("action-list");
  const latency = document.getElementById("ask-latency");
  if (!state.lastAsk) {
    answer.textContent = "질의를 실행하면 Python API가 Auth, Policy, Ontology, BM25/RAG, LLM Gateway, Audit 순서로 처리합니다.";
    evidence.innerHTML = "";
    actionList.innerHTML = "";
    latency.textContent = "0 ms";
    return;
  }
  answer.textContent = state.lastAsk.answer;
  latency.textContent = `${state.lastAsk.latency_ms} ms`;
  evidence.innerHTML = state.lastAsk.evidence.map((item) => `
    <div class="list-card">
      <strong>${item.document_id} · ${item.title}</strong>
      <p>BM25 score ${item.score}</p>
      <p>${item.text}</p>
    </div>
  `).join("");
  actionList.innerHTML = state.lastAsk.available_actions.map((action) => `
    <button class="secondary-btn" data-inline-action="${action}">${action}</button>
  `).join("");
  actionList.querySelectorAll("[data-inline-action]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = "workflow";
      renderView();
    });
  });
}

function renderContext() {
  const context = state.lastContext;
  document.getElementById("selected-order-chip").textContent = `Order ${state.selectedOrderId}`;
  document.getElementById("cache-chip").textContent = "Server state";
  if (!context) return;
  document.getElementById("ctx-order-id").textContent = context.order.id;
  document.getElementById("ctx-status").textContent = context.order.status;
  document.getElementById("ctx-amount").textContent = formatMoney(context.order.amount);
  document.getElementById("ctx-customer").textContent = context.customer.name;
  document.getElementById("ctx-risk").textContent = context.customer.risk_tier;
  document.getElementById("policy-summary").innerHTML = [
    ["Object read", "server checked"],
    ["Masked fields", context.customer.contract_terms?.includes("***") || context.customer.contract_terms === "Restricted" ? "applied" : "none"],
    ["Actions", (context.available_actions || []).join(", ") || "none"],
    ["Recheck", "required before execute"],
  ].map(([label, value]) => `<div class="policy-line"><span>${label}</span><b>${value}</b></div>`).join("");
}

function renderAudit() {
  const target = document.getElementById("audit-list");
  target.innerHTML = state.auditEvents.map((event) => `
    <div class="audit-event">
      <strong>${event.occurred_at}</strong>
      <span>${event.event_type} · ${event.object_type} ${event.object_id}<br>${JSON.stringify(event.detail)}</span>
      <span>${event.actor}</span>
    </div>
  `).join("");
}

function renderArchitecture() {
  document.getElementById("architecture-grid").innerHTML = services.map(([title, body, code]) => `
    <article class="service-card">
      <h3>${title}</h3>
      <p>${body}</p>
      <code>${code}</code>
    </article>
  `).join("");
}

function renderPipeline(steps = []) {
  const labels = [
    "사용자가 질문 입력",
    "Auth에서 사용자 확인",
    "질문에서 객체 후보 추출",
    "Policy Engine에서 객체 접근 권한 확인",
    "Ontology Service에서 객체와 관계 조회",
    "Search Service에서 권한 필터링된 문서 검색",
    "RAG Service에서 컨텍스트와 프롬프트 구성",
    "LLM Gateway에서 답변 생성",
    "Audit Service에 로그 기록",
    "Frontend에 답변, 근거, 가능한 액션 반환",
  ];
  const doneNames = new Set(steps.map((step) => step.name));
  document.getElementById("pipeline-list").innerHTML = labels.map((label) => {
    const done = [...doneNames].some((name) => label.includes(name.split("에서")[0]) || name.includes(label.split("에서")[0]));
    return `<li class="${done ? "done" : ""}">${label}</li>`;
  }).join("");
}

function setPipelineStatus(text) {
  document.getElementById("pipeline-status").textContent = text;
}

function showError(message) {
  document.getElementById("answer-text").textContent = message;
}

function showInfo(message) {
  document.getElementById("answer-text").textContent = message;
}

function formatMoney(value) {
  return new Intl.NumberFormat("ko-KR").format(value || 0);
}

function statusTone(status) {
  if (status === "Approved" || status === "Fulfilled" || status === "Closed") return "ok";
  if (status === "Rejected") return "danger";
  if (status === "Review") return "warn";
  return "";
}

init().catch((error) => {
  showError(`서버 API에 연결할 수 없습니다. python server.py로 src_codex 서버를 실행하세요. (${error.message})`);
});
